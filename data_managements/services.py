import asyncio
import ssl
from datetime import datetime
from decimal import Decimal, InvalidOperation

from asgiref.sync import sync_to_async
from django.conf import settings
from django.db import transaction
import httpx
import re

from .models import (
    DietarySupplements,
    DietarySupplementsIngredient,
    Ingredient,
    Manufacturer,
)


# 식품의약품안전처 API를 통해 기능성 원료 데이터를 동기화
class IngredientDataSyncService:

    BASE_URL = "http://openapi.foodsafetykorea.go.kr/api"
    SERVICE_ID = "I2710"
    DATA_TYPE = "json"

    def __init__(self):
        self.api_key = settings.INGREDIENT_SERVICE_API_KEY
        if not self.api_key:
            raise ValueError("INGREDIENT_SERVICE_API_KEY가 설정되지 않았습니다.")

    # 전체 원료 데이터를 가져와 DB에 동기화
    async def sync_ingredients(self):
        print("기능성 원료 데이터 동기화를 시작합니다...")
        total_count = await self._get_total_count()
        if total_count == 0:
            print("가져올 데이터가 없습니다.")
            return 0, 0

        print(f"총 {total_count}개의 원료 데이터가 있습니다.")

        results = []
        batch_size = 100  # 한 번에 요청할 데이터 수
        for start_index in range(1, total_count + 1, batch_size):
            end_index = start_index + batch_size - 1
            if end_index > total_count:
                end_index = total_count

            print(f"{start_index}-{end_index} 범위의 데이터를 처리합니다...")
            result = await self._fetch_and_process_batch(start_index, end_index)
            results.append(result)
            await asyncio.sleep(0.5)  # API 서버 부하를 줄이기 위해 0.5초 대기

        total_created = sum(r[0] for r in results)
        total_updated = sum(r[1] for r in results)

        print(f"동기화 완료! 생성: {total_created}개, 업데이트: {total_updated}개")
        return total_created, total_updated

    # API를 호출하여 전체 데이터 개수를 가져옴
    async def _get_total_count(self) -> int:
        url = f"{self.BASE_URL}/{self.api_key}/{self.SERVICE_ID}/{self.DATA_TYPE}/1/1"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                return int(data[self.SERVICE_ID]["total_count"])
            except (httpx.RequestError, KeyError, ValueError) as e:
                print(f"에러: 전체 데이터 개수를 가져올 수 없습니다. {e}")
                return 0

    # 지정된 범위의 데이터를 가져와 처리
    async def _fetch_and_process_batch(self, start: int, end: int) -> tuple[int, int]:
        url = f"{self.BASE_URL}/{self.api_key}/{self.SERVICE_ID}/{self.DATA_TYPE}/{start}/{end}"
        created_count = 0
        updated_count = 0

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                data = response.json()
                items = data.get(self.SERVICE_ID, {}).get("row", [])

                for item in items:
                    _, created = await self._update_or_create_ingredient(item)
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                return created_count, updated_count
            except (httpx.RequestError, KeyError, ValueError) as e:
                print(f"에러: {start}-{end} 데이터 처리 중 오류 발생. {e}")
                return 0, 0

    # API 아이템으로 Ingredient 모델을 생성하거나 업데이트
    async def _update_or_create_ingredient(self, item: dict):
        name = item.get("PRDCT_NM")
        if not name:
            return None, False

        defaults = {
            "functionality": item.get("PRIMARY_FNCLTY", ""),
            "precautions": item.get("IFTKN_ATNT_MATR_CN", ""),
            "unit": item.get("INTK_UNIT", ""),
            "remark": item.get("SKLL_IX_IRDNT_RAWMTRL", ""),
        }

        # 숫자 필드 변환 (값이 없거나 잘못된 경우 None으로 처리)
        try:
            defaults["daily_intake_low"] = Decimal(item.get("DAY_INTK_LOWLIMIT"))
        except (InvalidOperation, TypeError):
            defaults["daily_intake_low"] = None

        try:
            defaults["daily_intake_high"] = Decimal(item.get("DAY_INTK_HIGHLIMIT"))
        except (InvalidOperation, TypeError):
            defaults["daily_intake_high"] = None

        # 날짜 필드 변환 (YYYYMMDD 형식)
        try:
            defaults["registration_date"] = datetime.strptime(
                item.get("CRET_DTM"), "%Y%m%d"
            ).date()
        except (ValueError, TypeError):
            defaults["registration_date"] = None

        try:
            defaults["last_modified_date"] = datetime.strptime(
                item.get("LAST_UPDT_DTM"), "%Y%m%d"
            ).date()
        except (ValueError, TypeError):
            defaults["last_modified_date"] = None

        # 동기적인 transaction.atomic 블록을 @sync_to_async로 감싸 비동기 함수로 변환
        @sync_to_async
        def _save_in_transaction():
            with transaction.atomic():
                obj, created = Ingredient.objects.update_or_create(
                    name=name, defaults=defaults
                )
                return obj, created

        return await _save_in_transaction()


async def _fetch_data_from_api(client: httpx.AsyncClient, url: str):
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP 오류 발생: {e.response.status_code} - {e.response.text}")
        return {}
    except httpx.RequestError as e:
        print(f"요청 중 오류 발생: {e}")
        return {}


# 건강기능식품과 원료 관계를 설정
@sync_to_async
def _process_supplement_ingredients(supplement: DietarySupplements):
    if not supplement.standards_and_specifications:
        return 0

    # 모든 Ingredient 객체를 미리 조회하여 메모리에 로드 (N+1 문제 방지)
    all_ingredients = {}
    for ing in Ingredient.objects.all():
        all_ingredients[ing.name] = ing

    all_ingredient_names = set(all_ingredients.keys())
    new_relations_dict = {}

    pattern = re.compile(
        r"^\d+\.\s*([^:(]+?)(?:\s*\([^)]*\))?\s*:\s*(.+)$", re.MULTILINE
    )

    for match in pattern.finditer(supplement.standards_and_specifications):
        ingredient_name_from_api = match.group(1).strip()
        content_text = match.group(2).strip()

        # API에서 찾은 원료명이 DB에 존재하는지 확인
        found_ingredient_name = next(
            (
                db_name
                for db_name in all_ingredient_names
                if db_name in ingredient_name_from_api
            ),
            None,
        )

        if not found_ingredient_name:
            continue

        # 함량 텍스트에서 숫자만 추출
        content_match = re.search(r"[\d,.]+", content_text.replace(",", ""))
        if not content_match:
            continue

        try:
            content_value = Decimal(content_match.group(0))
            ingredient = all_ingredients[found_ingredient_name]
            new_relations_dict[ingredient.id] = {
                "ingredient": ingredient,
                "content": content_value,
            }
        except (InvalidOperation, KeyError):
            continue

    if not new_relations_dict:
        return 0

    created_count = 0
    with transaction.atomic():
        existing_ingredient_ids = set(
            supplement.ingredients.values_list("id", flat=True)
        )

        relations_to_create = [
            DietarySupplementsIngredient(
                dietary_supplements=supplement,
                ingredient=rel["ingredient"],
                content=rel["content"],
            )
            for rel in new_relations_dict.values()
            if rel["ingredient"].id not in existing_ingredient_ids
        ]

        if relations_to_create:
            DietarySupplementsIngredient.objects.bulk_create(relations_to_create)
            created_count = len(relations_to_create)

    return created_count


# 건강기능식품 데이터 동기화
async def sync_dietary_supplements(max_pages: int = None):

    api_key = settings.SUPPLEMENT_SERVICE_API_KEY
    base_url = "https://apis.data.go.kr/1471000/HtfsInfoService03/getHtfsItem01"
    page_no = 1
    num_of_rows = 100
    total_processed = 0
    created_count = 0
    updated_count = 0
    relations_created_count = 0

    # SSL 컨텍스트 생성 (SSLV3_ALERT_ILLEGAL_PARAMETER 오류 방지)
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT@SECLEVEL=1")

    async with httpx.AsyncClient(verify=context, timeout=30.0) as client:
        while True:
            # max_pages 옵션이 지정된 경우, 해당 페이지 수만큼만 처리
            if max_pages is not None and page_no > max_pages:
                print(f"--pages 옵션에 따라 {max_pages} 페이지만 처리하고 종료합니다.")
                break

            url = f"{base_url}?serviceKey={api_key}&pageNo={page_no}&numOfRows={num_of_rows}&type=json"

            data = await _fetch_data_from_api(client, url)

            if not data or data.get("header", {}).get("resultCode") != "00":
                error_msg = data.get("header", {}).get("resultMsg", "알 수 없는 오류")
                print(f"[DEBUG] API 응답 오류: {error_msg}")
                break

            items = data.get("body", {}).get("items", [])
            if not items:
                print("더 이상 가져올 데이터가 없습니다.")
                break

            for item_wrapper in items:
                item = item_wrapper.get("item")
                if not item:
                    continue

                # 제조사 정보 생성 또는 조회
                manufacturer_name = item.get("ENTRPS", "").strip()
                if not manufacturer_name:
                    continue
                manufacturer, created = await Manufacturer.objects.aupdate_or_create(
                    name=manufacturer_name
                )
                if created:
                    print(f"[DEBUG] 생성된 제조사: {manufacturer_name}")

                # 건강기능식품 정보 생성 또는 업데이트
                report_number = item.get("STTEMNT_NO")
                if not report_number:
                    continue

                defaults = {
                    "manufacturer": manufacturer,
                    "name": item.get("PRDUCT") or "",
                    "registration_date": item.get("REGIST_DT") or "",
                    "appearance": item.get("SUNGSANG") or "",
                    "usage_instructions": item.get("SRV_USE") or "",
                    "shelf_life": item.get("DISTB_PD") or "",
                    "storage_method": item.get("PRSRV_PD") or "",
                    "precautions": item.get("INTAKE_HINT1") or "",
                    "main_functionality": item.get("MAIN_FNCTN") or "",
                    # BASE_STANDARD 필드를 standards_and_specifications에 저장
                    "standards_and_specifications": item.get("BASE_STANDARD") or "",
                }

                supplement, created = (
                    await DietarySupplements.objects.aupdate_or_create(
                        report_number=report_number,
                        defaults=defaults,
                    )
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
                total_processed += 1

                # 원료 관계 설정
                relations_created = await _process_supplement_ingredients(supplement)
                relations_created_count += relations_created

            print(f"{page_no} 페이지의 데이터 동기화 완료.")
            page_no += 1

    print(
        f"총 {total_processed}개의 건강기능식품 데이터 처리 완료. "
        f"생성: {created_count}, 업데이트: {updated_count}, 신규 관계 설정: {relations_created_count}."
    )

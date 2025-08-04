import asyncio
from asgiref.sync import sync_to_async
import httpx
from datetime import datetime
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError

from django.conf import settings
from django.db import transaction

from .models import Ingredient


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
            except JSONDecodeError:
                print(f"에러: {start}-{end} 범위의 API 응답이 JSON 형식이 아닙니다.")
                print(f"서버 응답(첫 200자): {response.text[:200]}")
                return 0, 0
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

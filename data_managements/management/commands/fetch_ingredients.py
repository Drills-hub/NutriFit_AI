from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand
from data_managements.services import IngredientDataSyncService


class Command(BaseCommand):
    help = "식품의약품안전처 API에서 기능성 원료 데이터를 가져와 DB에 동기화합니다."

    def handle(self, *args, **options):
        async_to_sync(self.async_handle)(*args, **options)

    # 명령어 실행 시 호출되는 비동기 핸들러
    async def async_handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("기능성 원료 데이터 동기화 작업을 시작합니다.")
        )

        service = IngredientDataSyncService()
        try:
            created_count, updated_count = await service.sync_ingredients()
            self.stdout.write(
                self.style.SUCCESS(
                    f"성공적으로 동기화되었습니다. "
                    f"(생성: {created_count}, 업데이트: {updated_count})"
                )
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"작업 중 오류가 발생했습니다: {e}"))

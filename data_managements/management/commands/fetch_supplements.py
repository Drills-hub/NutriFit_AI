from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from data_managements.services import sync_dietary_supplements


class Command(BaseCommand):
    help = "Fetches and updates dietary supplements data from the public API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--pages",
            type=int,
            help="Fetch only the specified number of pages for testing.",
            default=None,
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("건강기능식품 데이터 동기화 작업을 시작"))
        pages_to_fetch = options["pages"]

        # 비동기 서비스 함수를 동기적으로 실행
        async_to_sync(sync_dietary_supplements)(max_pages=pages_to_fetch)
        self.stdout.write(self.style.SUCCESS("건강기능식품 데이터 동기화 작업을 완료"))

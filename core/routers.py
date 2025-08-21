from rest_framework.routers import DefaultRouter


# 중첩 라우터
class NestedRouter(DefaultRouter):

    # 중첩된 라우팅을 등록하는데 사용
    def register_nested(
        self, prefix, viewset, parent_prefix, parent_lookup_kwarg, basename=None
    ):
        nested_prefix = f"{parent_prefix}/(?P<{parent_lookup_kwarg}>[^/.]+)/{prefix}"

        if basename:
            self.register(nested_prefix, viewset, basename=f"{basename}")
        else:
            self.register(nested_prefix, viewset)

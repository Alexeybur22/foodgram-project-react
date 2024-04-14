from rest_framework.pagination import LimitOffsetPagination, _positive_int


class CustomPagination(LimitOffsetPagination):
    offset_query_param = 'page'

    def get_offset(self, request):
        try:
            page = _positive_int(
                request.query_params[self.offset_query_param],
            )
            limit = _positive_int(
                request.query_params[self.limit_query_param],
            )
            return page * limit
        except (KeyError, ValueError):
            return 0

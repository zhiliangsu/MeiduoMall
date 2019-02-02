from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 2
    page_size_query_param = 'page_size'  # 指定每页显示多少条的前端字段
    # page_query_param = 'page'
    max_page_size = 20

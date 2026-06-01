from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class BasePageNumberPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
            Перевизначаємо стандартну відповідь DRF, щоб додати корисні
            поля 'total_pages' та 'current_page'.
        """
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })

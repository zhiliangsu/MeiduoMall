from django.shortcuts import render
from drf_haystack.viewsets import HaystackViewSet
from rest_framework.generics import ListAPIView, GenericAPIView
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import SKU
from orders.models import OrderInfo
from .serializers import SKUSerializer, SKUSearchSerializer, OrderListSerializer


# Create your views here.
# /categories/(?P<category_id>\d+)/skus?page=xxx&page_size=xxx&ordering=xxx
class SKUListView(ListAPIView):
    """商品列表界面"""

    # 指定序列化器
    serializer_class = SKUSerializer

    # 指定过滤后端为排序
    filter_backends = [OrderingFilter]

    # 指定排序字段
    ordering_fields = ['create_time', 'price', 'sales']

    # 指定查询集
    # queryset = SKU.objects.filter(is_launched=True, category_id=category_id)
    def get_queryset(self):
        category_id = self.kwargs.get('category_id')  # 获取url路径中的正则组别名提取出来的参数
        return SKU.objects.filter(is_launched=True, category_id=category_id)


class SKUSearchViewSet(HaystackViewSet):
    """
    SKU搜索
    """
    index_models = [SKU]

    serializer_class = SKUSearchSerializer


# GET url(r'^orders/$', views.OrderListView.as_view())
class OrderListView(GenericAPIView):
    """订单列表数据"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderListSerializer

    def get(self, request):
        # queryset要排序,不然会报错
        # UnorderedObjectListWarning: Pagination may yield inconsistent results with an unordered object_list:
        # <class 'orders.models.OrderInfo'> QuerySet.
        queryset = OrderInfo.objects.filter(user=request.user).all().order_by('-create_time')
        # 以下四行从源码复制过来,不写分页不work,why?
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        count = queryset.count()
        serializer = self.get_serializer(queryset, many=True)

        return Response({'count': count, 'results': serializer.data})

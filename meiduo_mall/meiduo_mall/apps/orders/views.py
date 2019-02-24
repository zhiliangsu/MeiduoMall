from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal


from goods.models import SKU
from .models import OrderInfo
from .serializers import OrderSettlementSerializer, CommitOrderSerializer, OrderListSerializer


# Create your views here.
class OrdersViewSet(ModelViewSet):
    """保存订单/订单列表展示接口"""

    # 指定权限
    permission_classes = [IsAuthenticated]

    # 指定序列化器
    # serializer_class = CommitOrderSerializer
    def get_serializer_class(self):
        """根据action不同选择不同的序列化器"""
        if self.action == 'list':
            return OrderListSerializer
        else:
            return CommitOrderSerializer

    def list(self, request, *args, **kwargs):

        # queryset要排序,不然会报错
        queryset = OrderInfo.objects.filter(user=request.user).all().order_by('-create_time')
        # 以下四行从源码复制过来,不写分页不work,why?
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        count = queryset.count()
        serializer = self.get_serializer(queryset, many=True)

        return Response({'count': count, 'results': serializer.data})


class OrderSettlementView(APIView):
    """去结算接口"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """获取"""

        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart_dict = redis_conn.hgetall('cart_%d' % user.id)
        cart_selected_ids = redis_conn.smembers('selected_%d' % user.id)

        cart_selected_dict = {}
        for sku_id in cart_selected_ids:
            cart_selected_dict[int(sku_id)] = int(redis_cart_dict[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart_selected_dict.keys())
        for sku in skus:
            sku.count = cart_selected_dict[sku.id]

        # 运费
        freight = Decimal('10.00')

        # 创建序列化器返回响应
        # 创建序列化器时,给instance参数可以传递(模型/查询集(many=True)/字典)
        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})

        return Response(serializer.data)

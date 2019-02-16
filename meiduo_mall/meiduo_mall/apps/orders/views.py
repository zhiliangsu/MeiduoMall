from django.shortcuts import render
from django_redis import get_redis_connection
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal

from goods.models import SKU
from .serializers import OrderSettlementSerializer, CommitOrderSerializer


# Create your views here.
class CommitOrderView(CreateAPIView):
    """保存订单接口"""

    # 指定权限
    permission_classes = [IsAuthenticated]

    # 指定序列化器
    serializer_class = CommitOrderSerializer


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

from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from .models import SKU
from .search_indexes import SKUIndex
from orders.models import OrderInfo, OrderGoods


class SKUSerializer(serializers.ModelSerializer):
    """商品列表界面序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']


class SKUSearchSerializer(HaystackSerializer):
    """
    SKU索引结果数据序列化器
    """
    object = SKUSerializer(read_only=True)

    class Meta:
        index_classes = [SKUIndex]
        fields = ('text', 'object')


class GoodSerializer(serializers.ModelSerializer):
    """商品序列化器"""

    class Meta:
        model = SKU
        fields = ['default_image_url', 'name']


class OrderGoodsSerializer(serializers.ModelSerializer):
    """订单商品数据序列化器"""

    sku = GoodSerializer(read_only=True)

    class Meta:
        model = OrderGoods
        fields = ['sku', 'count', 'price']


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器"""

    create_time = serializers.DateTimeField(label='订单时间', format='%Y-%m-%d %H:%M')
    skus = OrderGoodsSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = ['skus', 'create_time', 'order_id', 'total_amount', 'freight', 'pay_method', 'status']

from rest_framework import serializers
from drf_haystack.serializers import HaystackSerializer

from .models import SKU
from .search_indexes import SKUIndex


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

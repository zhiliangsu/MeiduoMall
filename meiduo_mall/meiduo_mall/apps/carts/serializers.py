from rest_framework import serializers

from goods.models import SKU


class CartSerializer(serializers.Serializer):
    """购物车序列化器: 校验数据使用"""

    sku_id = serializers.IntegerField(label='商品sku_id', min_value=1)
    count = serializers.IntegerField(label='商品数量', min_value=1)
    selected = serializers.BooleanField(label='勾选状态', default=True)

    def validate_sku_id(self, value):
        """校验sku_id"""

        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('商品sku_id不存在')

        return value


class CartSKUSerializer(serializers.ModelSerializer):
    """查询购物车序列化器"""

    count = serializers.IntegerField(label='商品数量')
    selected = serializers.BooleanField(label='勾选状态')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'count', 'selected']

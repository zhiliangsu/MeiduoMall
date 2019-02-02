from rest_framework import serializers

from .models import SKU


class SKUSerializer(serializers.ModelSerializer):
    """商品列表界面序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']

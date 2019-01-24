from rest_framework import serializers

from .models import Area


class AreaSerializer(serializers.ModelSerializer):
    """如果此时是查询所有的省,所有的省数据就用此序列化器"""

    class Meta:
        model = Area
        fields = ['id', 'name']


class SubsAreaSerializer(serializers.ModelSerializer):
    """如果查询单个省或者单个市时,就用此序列化器"""

    subs = AreaSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']

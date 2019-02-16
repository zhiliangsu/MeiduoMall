# from datetime import timezone
# from time import timezone
from django.utils import timezone
from rest_framework import serializers
from decimal import Decimal

from goods.models import SKU
from orders.models import OrderInfo


class CommitOrderSerializer(serializers.ModelSerializer):
    """保存订单序列化器"""

    class Meta:
        model = OrderInfo
        # order_id:输出, address和pay_method:输入
        fields = ['order_id', 'address', 'pay_method']
        read_only_fields = ['order_id']
        # 指定address和pay_method为输出
        extra_kwargs = {
            'address': {
                'write_only': True,
                'require': True,
            },
            'pay_method': {
                'write_only': True,
                'require': True,
            }
        }

    def create(self, validated_data):
        """重写序列化器的create方法进行存储订单表/订单商品"""

        # 获取当前保存订单时需要的信息
        # 获取用户对象
        user = self.context['request'].user
        # 生成订单编号 当前时间 + user_id  2019021522320000000001
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 获取用户选择的收货地址
        address = validated_data.get('address')
        # 获取支付方式
        pay_method = validated_data.get('pay_method')

        # 订单状态: 如果用户选择的是货到付款,订单应该是待发货  如果用户选择的是支付宝支付,订单应该是待支付
        # status = '待支付' if 如果用户选择的支付方式是支付宝 else '待发货'
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID']
                  if OrderInfo.PAY_METHODS_ENUM['ALIPAY'] == pay_method
                  else OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        # 保存订单基本信息 OrderInfo（一）
        OrderInfo.objects.create(
            order_id=order_id,
            user=user,
            address=address,
            total_count=0,
            total_amount=Decimal('0.00'),
            freight=Decimal('10.00'),
            pay_method=pay_method,
            status=status
        )

        # 从redis读取购物车中被勾选的商品信息
        # 遍历购物车中被勾选的商品信息
        # 获取sku对象
        # 判断库存
        # 减少库存，增加销量SKU
        # 修改SPU销量
        # 保存订单商品信息 OrderGoods（多）
        # 累加计算总数量和总价
        # 最后加入邮费和保存订单信息
        # 清除购物车中已结算的商品
        pass


class CartSKUSerializer(serializers.ModelSerializer):
    """购物车商品数据序列化器"""

    count = serializers.IntegerField(label='商品数量')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'default_image_url', 'price', 'count']


class OrderSettlementSerializer(serializers.Serializer):
    """订单结算数据序列化器"""

    freight = serializers.DecimalField(label='运费', max_digits=10, decimal_places=2)
    skus = CartSKUSerializer(many=True)

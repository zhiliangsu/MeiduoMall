# from datetime import timezone
# from time import timezone
from django.utils import timezone
from django_redis import get_redis_connection
from django.db import transaction
from rest_framework import serializers
from decimal import Decimal

from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
from users.models import User


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
                'required': True,
            },
            'pay_method': {
                'write_only': True,
                'required': True,
            }
        }

    def create(self, validated_data):
        """重写序列化器的create方法进行存储订单表/订单商品"""
        # 订单基本信息表 订单商品表 sku spu 四个表要么一起成功,要么一起失败

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

        # 开始一个事务
        with transaction.atomic():

            # 创建事务保存点
            save_point = transaction.savepoint()

            try:

                # 保存订单基本信息 OrderInfo（一）
                order = OrderInfo.objects.create(
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
                redis_conn = get_redis_connection('cart')
                # {b'16': 1, b'1':1}
                redis_cart_dict = redis_conn.hgetall('cart_%d' % user.id)
                # {b'16'}
                redis_selected_ids = redis_conn.smembers('selected_%d' % user.id)

                # 把要购买的商品id和count重新包到一个字典
                cart_selected_dict = {}
                # for sku_id, count in redis_cart_dict.items():
                #     if sku_id in redis_selected_ids:
                #         cart_selected_dict[int(sku_id)] = int(count)
                for sku_id in redis_selected_ids:
                    cart_selected_dict[int(sku_id)] = int(redis_cart_dict[sku_id])

                # 遍历购物车中被勾选的商品信息
                for sku_id in cart_selected_dict:

                    while True:
                        # 获取sku对象
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前sku_id商品要购买的数量
                        sku_count = cart_selected_dict[sku_id]

                        # 获取查询出sku那一刻的库存和数量
                        origin_stock = sku.stock
                        origin_sales = sku.sales

                        # 判断库存
                        if sku_count > sku.stock:
                            raise serializers.ValidationError('库存不足')

                        # 只用于测试
                        # import time
                        # time.sleep(5)

                        # 计算新的库存和销量
                        new_stock = origin_stock - sku_count
                        new_sales = origin_sales + sku_count

                        # 减少库存，增加销量SKU ==> 乐观锁(使用乐观锁需要更改数据库的事务隔离级别为READ_COMMITTED)
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock,
                                                                                          sales=new_sales)

                        if result == 0:
                            continue  # 跳出本次循环进入下一次

                        # sku.stock -= sku_count
                        # sku.sales += sku_count
                        # sku.save()

                        # 修改SPU销量
                        spu = sku.goods
                        spu.sales += sku_count
                        spu.save()

                        # 保存订单商品信息 OrderGoods（多）
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=sku_count,
                            price=sku.price
                        )
                        # 累加计算总数量和总价
                        order.total_count += sku_count
                        order.total_amount += (sku.price * sku_count)

                        break  # 跳出无限循环,继续对下一个sku_id进行下单

                # 最后加入邮费和保存订单信息
                order.total_amount += order.freight
                order.save()
            except Exception:
                # 暴力回滚,无论中间出现什么问题全部回滚
                transaction.savepoint_rollback(save_point)
                raise
            else:
                # 如果中间没有出现异常提交事务
                transaction.savepoint_commit(save_point)

        # 清除购物车中已结算的商品
        pl = redis_conn.pipeline()
        pl.hdel('cart_%d' % user.id, *redis_selected_ids)
        pl.srem('selected_%d' % user.id, *redis_selected_ids)
        pl.execute()

        return order


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


class GoodSerializer(serializers.ModelSerializer):
    """商品序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'default_image_url', 'name']


class OrderGoodsSerializer(serializers.ModelSerializer):
    """订单商品数据序列化器"""

    sku = GoodSerializer(read_only=True)

    class Meta:
        model = OrderGoods
        fields = ['sku', 'count', 'price', 'order', 'comment', 'score', 'is_anonymous', 'is_commented']
        read_only_fields = ['count', 'price']

    def update(self, instance, validated_data):
        # TODO: 涉及到三张表的操作,可以使用事务

        instance.comment = validated_data.get('comment')
        instance.score = validated_data.get('score')
        instance.is_anonymous = validated_data.get('is_anonymous')
        instance.is_commented = True
        instance.save()

        sku = instance.sku
        sku.comments += 1
        sku.save()

        not_commented = OrderGoods.objects.filter(order_id=instance.order_id, is_commented=False).count()
        if not not_commented:
            order = instance.order
            order.status = OrderInfo.ORDER_STATUS_ENUM['FINISHED']
            order.save()

        return instance


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器"""

    create_time = serializers.DateTimeField(label='订单时间', format='%Y-%m-%d %H:%M')
    skus = OrderGoodsSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = ['skus', 'create_time', 'order_id', 'total_amount', 'freight', 'pay_method', 'status']

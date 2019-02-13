import base64
import pickle

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from .serializers import CartSerializer, CartSKUSerializer, CartDeleteSerializer, CartSelectedSerializer
from goods.models import SKU


# Create your views here.


class CartView(APIView):
    """购物车视图"""

    def perform_authentication(self, request):
        """禁用认证/延后认证"""
        pass

    def post(self, request):
        """添加购物车"""

        # 0.反序列化数据校验
        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        # 创建响应对象
        response = Response(data=serializer.data, status=status.HTTP_201_CREATED)

        try:
            user = request.user  # 获取登录用户  首次获取还会做认证
        except:
            user = None
        else:
            # 如果代码能继续向下走说明是登录用户, 存储购物车数据到redis
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            pl.hincrby('cart_%d' % user.id, sku_id, count)
            if selected:  # 判断当前商品是否勾选, 把勾选的商品sku_id添加到set集合中
                pl.sadd('selected_%d' % user.id, sku_id)
            pl.execute()

        if not user:
            # 未登录用户存储到cookie
            # 1.获取cookie中的购物车数据
            cart_str = request.COOKIES.get('carts')

            # 2.判断是否已有购物车数据存在
            if cart_str:
                # 把字符串转换成python中的字典
                # 把字符串转换成bytes类型的字符串
                cart_str_bytes = cart_str.encode()
                # 把bytes类型的字符串转换成bytes类型的ascii码
                cart_ascii_bytes = base64.b64decode(cart_str_bytes)
                # 把bytes类型的ascii码转换成python中的字典
                cart_dict = pickle.loads(cart_ascii_bytes)
            else:  # 之前没有cookie购物车数据
                cart_dict = {}

            # 3.判断本次添加的商品数据是否在购物车中已存在,如果已存在需要做增量计算
            if sku_id in cart_dict:
                count += cart_dict[sku_id]['count']

            # 4.把要保存到cookie的购物车数据组织成python字典,并转换成字符串
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 把python字典转换成字符串
            cart_ascii_bytes = pickle.dumps(cart_dict)
            cart_str_bytes = base64.b64encode(cart_ascii_bytes)
            cart_str = cart_str_bytes.decode()

            # 设置购物车数据到cookie
            response.set_cookie('carts', cart_str)

        return response

    def get(self, request):
        """查询购物车"""

        # 获取user,用于判断用户是否登录
        try:
            user = request.user
            # 如果获取到user说明是已登录用户(操作redis数据库)
        except:
            # 如果获取user出现异常说明当前是未登录用户(获取cookie购物车数据)
            user = None
        else:
            # 如果获取到user说明是已登录用户(操作redis数据库)
            # 获取redis购物车数据
            redis_conn = get_redis_connection('cart')
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            selected_ids = redis_conn.smembers('selected_%d' % user.id)

            # 定义一个用来转换数据格式的大字典
            cart_dict = {}
            for sku_id, count in cart_redis_dict.items():
                cart_dict[int(sku_id)] = {
                    'count': int(count),
                    'selected': sku_id in selected_ids
                }

        if not user:
            # 如果获取user出现异常说明当前是未登录用户(获取cookie购物车数据)
            cart_str = request.COOKIES.get('carts')
            # 判断是否存在cookie购物车数据
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        # 以下序列化的代码无论登录还是未登录都要执行,注意缩进问题
        # 获取购物车中的所有商品的sku模型
        skus = SKU.objects.filter(id__in=cart_dict.keys())

        # 遍历skus查询集, 给里面的每个sku模型追加两个属性
        for sku in skus:
            sku.count = cart_dict[sku.id]['count']
            sku.selected = cart_dict[sku.id]['selected']

        # 创建序列化器进行序列化操作
        serializer = CartSKUSerializer(skus, many=True)
        return Response(serializer.data)

    def put(self, request):
        """修改购物车"""

        serializer = CartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.data)

        try:
            user = request.user
        except:
            user = None
        else:
            # 已登录用户操作redis购物车数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 修改指定sku_id的购物车数据,把hash字典中指定sku_id的value覆盖掉
            pl.hset('cart_%d' % user.id, sku_id, count)
            # 修改商品勾选状态
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()

        if not user:
            # 未登录用户操作cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                if sku_id in cart_dict:  # 判断当前要修改的sku_id在cookie字典中是否存在
                    # 直接覆盖商品的数量及勾选状态
                    cart_dict[sku_id] = {
                        'count': count,
                        'selected': selected
                    }

                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cart_str)

        return response

    def delete(self, request):
        """删除购物车"""

        serializer = CartDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sku_id = serializer.validated_data.get('sku_id')

        response = Response(status=status.HTTP_204_NO_CONTENT)

        try:
            user = request.user
        except:
            user = None
        else:
            # 已登录用户操作redis购物车数据
            redis_conn = get_redis_connection('cart')
            pl = redis_conn.pipeline()
            # 把本次要删除的sku_id从hash字典中移除
            pl.hdel('cart_%d' % user.id, sku_id)
            # 把本次要删除的sku_id从set集合中移除
            pl.srem('selected_%d' % user.id, sku_id)
            pl.execute()

        if not user:
            # 未登录用户操作cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                # 把要删除的sku_id从cart_dict字典中移除
                if sku_id in cart_dict:
                    del cart_dict[sku_id]

                if len(cart_dict.keys()):  # if成立即cookie字典中还有商品
                    cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                    response.set_cookie('carts', cart_str)
                else:
                    # 如果cookie购物车数据已全部删除,就把cookie移除
                    response.delete_cookie('carts')

        return response


class CartSelectedView(APIView):
    """购物车全选"""

    def perform_authentication(self, request):
        """延后认证"""
        pass

    def put(self, request):

        # 创建序列化器进行反序列化
        serializer = CartSelectedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected = serializer.validated_data.get('selected')

        response = Response(serializer.data)

        try:
            user = request.user
        except:
            user = None
        else:
            # 已登录用户操作redis
            redis_conn = get_redis_connection('cart')
            # 获取redis中的hash字典
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            if selected:  # 判断是全选还是取消全选
                # 如果是全选就把所有sku_id添加到set集合中
                redis_conn.sadd('selected_%d' % user.id, *cart_redis_dict.keys())
            else:
                # 如果取消全选就把所有sku_id从set集合中移除
                redis_conn.srem('selected_%d' % user.id, *cart_redis_dict.keys())

        if not user:
            # 未登录用户操作cookie
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

                for sku_id_dict in cart_dict.values():
                    sku_id_dict['selected'] = selected

                cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
                response.set_cookie('carts', cart_str)

        return response

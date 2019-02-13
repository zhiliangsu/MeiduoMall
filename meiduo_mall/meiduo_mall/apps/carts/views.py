import base64
import pickle

from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django_redis import get_redis_connection

from .serializers import CartSerializer


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
                pl.sadd('select_%d' % user.id, sku_id)
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
            for sku_id, count in cart_redis_dict.items:
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

    def put(self, request):
        """修改购物车"""
        pass

    def delete(self, request):
        """删除购物车"""
        pass

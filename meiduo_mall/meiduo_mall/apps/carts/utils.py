"""
购物车cookie合并到redis
购物车合并 需求: 以cookie为准备, 用cookie去合并到redis

如果cookie中某个sku_id在redis中没有, 新增到redis
如果cookie中某个sku_id在redis中存在, 就用cookie的这个sku_id数据覆盖redis的重复sku_id数据

如果cookie和redis中有相同的sku_id, 并且在cookie或redis中有一方是勾选的, 那么这个商品最终在redis中就是勾选的
如果cookie中独立存在的sku_id,是未勾选的合并到redis之后还是未勾选
"""
import base64
import pickle
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, response, user):
    """
    登录后合并cookie中的购物车数据到redis中
    :param request: 本次请求对象,获取cookie中的数据
    :param response: 本次响应对象,清除cookie中的数据
    :param user: 登录用户信息,获取user_id
    :return: response
    """

    # 获取cookie购物车数据
    cart_str = request.COOKIES.get('carts')

    # 判断cookie中是否存在购物车数据,如不存在,直接return
    if not cart_str:
        return

    # 把cart_str转换成cart_dict
    cookie_cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 创建redis连接对象
    redis_conn = get_redis_connection('cart')
    pl = redis_conn.pipeline()

    # 遍历cookie字典,将sku_id和count直接加入redis中的hash字典和set集合,如果cookie中的sku_id在hash中已存在,会以cookie的为准覆盖hash
    for sku_id, sku_id_dict in cookie_cart_dict.items():
        pl.hset('cart_%d' % user.id, sku_id, sku_id_dict['count'])
        if sku_id_dict['selected']:
            pl.sadd('selected_%d' % user.id, sku_id)
        pl.execute()

    # 清空cookie购物车数据
    response.delete_cookie('carts')

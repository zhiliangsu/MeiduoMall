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
    cart_str = request.COOKIES.get('cart')

    # 判断cookie中是否存在购物车数据,如不存在,直接return
    if not cart_str:
        return

    # 把cart_str转换成cart_dict
    cookie_cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 定义一个中间合并大字典{}
    temp_cart_dict = {}

    # 获取redis购物车数据并存入中间合并大字典中
    redis_conn = get_redis_connection('carts')
    redis_cart_dict = redis_conn.hgetall('cart_%d' % user.id)
    redis_selected_ids = redis_conn.smembers('selected_%d' % user.id)

    for sku_id, count in redis_cart_dict.items():
        temp_cart_dict[int(sku_id)] = {
            'count': int(count),
        }

    # 把cookie购物车数据也存入到中间合并大字典中
    for sku_id, sku_id_dict in cookie_cart_dict.items():
        temp_cart_dict[sku_id] = {
            'count': sku_id_dict['count'],
        }
        if sku_id_dict['selected']:
            redis_selected_ids.add(sku_id)

    # 把合并后的大字典分别设置到redis中的hash字典和set集合中
    pl = redis_conn.pipeline()
    pl.hset('cart_%d' % user.id, temp_cart_dict)
    pl.sadd('selected_%d' % user.id, *redis_selected_ids)
    pl.execute()

    # 清空cookie购物车数据
    response.delete_cookies('carts')

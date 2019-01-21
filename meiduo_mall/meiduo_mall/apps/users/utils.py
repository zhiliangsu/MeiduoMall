import re

from django.contrib.auth.backends import ModelBackend

from .models import User


def jwt_response_payload_handler(token, user=None, request=None):
    """重写jwt登录认证方法的响应体"""
    return {
        'token': token,
        'username': user.username,
        'user_id': user.id,
    }


def get_user_by_account(account):
    """通过传入手机号或者用户名动态查找user"""
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    return user


class UsernameMobileAuthBackend(ModelBackend):
    """自定义Django认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写认证方式, 实现多账号登录
        :param request: 本次登录请求对象
        :param username: 用户名/手机名
        :param password: 密码
        :return: 要么返回查到的user/None
        """

        # 1.通过传入的username获取到user对象(通过手机号或者用户名动态查询user)
        user = get_user_by_account(username)

        # 2.判断user的密码
        if user and user.check_password(password):
            return user
        else:
            return None

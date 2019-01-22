from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.conf import settings


def generate_save_user_token(openid):
    """对openid进行加密"""

    # 1.创建序列化器对象
    serializer = Serializer(settings.SECRET_KEY, 600)

    # 2.调用序列化器的dumps
    openid_signature = serializer.dumps({'openid': openid}).decode()

    # 3.把加密后的openid返回
    return openid_signature

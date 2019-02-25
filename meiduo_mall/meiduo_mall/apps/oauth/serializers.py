from rest_framework import serializers
from django_redis import get_redis_connection

from users.models import User
from .models import QQAuthUser, OAuthSinaUser
from .utils import check_save_user_token


class QQAuthUserSerializer(serializers.Serializer):
    """绑定用户的序列化器"""

    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):

        access_token = attrs.get('access_token')  # 获取出加密的openid
        openid = check_save_user_token(access_token)
        if not openid:
            raise serializers.ValidationError('openid无效')
        attrs['access_token'] = openid  # 把解密后的openid保存到反序列化的大字典中以备后期绑定用户时使用

        # 验证短信验证码是否正确
        redis_conn = get_redis_connection('verify_codes')
        # 获取当前用户的手机号
        mobile = attrs.get('mobile')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # 获取前端传过来的验证码
        sms_code = attrs.get('sms_code')
        if real_sms_code.decode() != sms_code:  # 注意redis中取出来的验证码是bytes类型注意类型处理
            raise serializers.ValidationError('验证码错误')

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果出现异常说明是新用户
            pass
        else:
            # 表示此手机号是已注册过的用户
            if not user.check_password(attrs.get('password')):
                raise serializers.ValidationError('已存在用户,但密码不正确')
            else:
                attrs['user'] = user

        return attrs

    def create(self, validated_data):
        """把openid和user进行绑定"""
        user = validated_data.get('user')
        if not user:  # 如果用户是不存在的,那就新增一个用户
            user = User(
                username=validated_data.get('mobile'),
                password=validated_data.get('password'),
                mobile=validated_data.get('mobile')
            )
            user.set_password(validated_data.get('password'))  # 对密码进行加密
            user.save()

        # 让user和openid绑定
        QQAuthUser.objects.create(
            user=user,
            openid=validated_data.get('access_token')
        )

        return user


class SinaAuthUserSerializer(serializers.Serializer):
    """绑定用户的序列化器"""

    access_token = serializers.CharField(label='操作凭证')
    mobile = serializers.RegexField(label='手机号', regex=r'^1[3-9]\d{9}$')
    password = serializers.CharField(label='密码', max_length=20, min_length=8)
    sms_code = serializers.CharField(label='短信验证码')

    def validate(self, attrs):

        access_token_signature = attrs.get('access_token')  # 获取出加密的access_token
        access_token = check_save_user_token(access_token_signature)
        if not access_token:
            raise serializers.ValidationError('access_token无效')
        attrs['access_token'] = access_token  # 把解密后的access_token保存到反序列化的大字典中以备后期绑定用户时使用

        # 验证短信验证码是否正确
        redis_conn = get_redis_connection('verify_codes')
        # 获取当前用户的手机号
        mobile = attrs.get('mobile')
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        # 获取前端传过来的验证码
        sms_code = attrs.get('sms_code')
        if real_sms_code.decode() != sms_code:  # 注意redis中取出来的验证码是bytes类型注意类型处理
            raise serializers.ValidationError('验证码错误')

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果出现异常说明是新用户
            pass
        else:
            # 表示此手机号是已注册过的用户
            if not user.check_password(attrs.get('password')):
                raise serializers.ValidationError('已存在用户,但密码不正确')
            else:
                attrs['user'] = user

        return attrs

    def create(self, validated_data):
        """把access_token和user进行绑定"""
        user = validated_data.get('user')
        if not user:  # 如果用户是不存在的,那就新增一个用户
            user = User(
                username=validated_data.get('mobile'),
                password=validated_data.get('password'),
                mobile=validated_data.get('mobile')
            )
            user.set_password(validated_data.get('password'))  # 对密码进行加密
            user.save()

        # 让user和openid绑定
        OAuthSinaUser.objects.create(
            user=user,
            access_token=validated_data.get('access_token')
        )

        return user

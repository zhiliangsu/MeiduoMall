import re

from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .models import User


class EmailSerializer(serializers.ModelSerializer):
    """设置保存邮箱序列化器"""

    class Meta:
        model = User
        fields = ['id', 'email']
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email')
        instance.save()

        # 在此地发送邮箱

        return instance


class UserDetailSerializer(serializers.ModelSerializer):
    """用户个人信息序列化器"""

    class Meta:
        model = User
        fields = ['id', 'username', 'mobile', 'email', 'email_active']


class UserSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""

    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='短信验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='状态保持token', read_only=True)

    class Meta:
        model = User
        # 将来序列化器中需要的所有字段: 'id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow'
        # 模型中已存在的字段: 'id', 'username', 'password', 'mobile'
        # 输出: 'id', 'username'
        # 输入: 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow'
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']

        extra_kwargs = {
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_mobile(self, value):
        """验证手机号"""
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def validate_allow(self, value):
        """检验用户是否同意协议"""
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):

        # 判断两次输入的密码是否相等
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入的密码不一致')

        # 判断短信验证码
        redis_conn = get_redis_connection('verify_codes')
        mobile = attrs['mobile']
        real_sms_code = redis_conn.get('sms_%s' % mobile)
        if real_sms_code is None:
            raise serializers.ValidationError('无效的短信验证码')
        if attrs['sms_code'] != real_sms_code.decode():
            raise serializers.ValidationError('短信验证码错误')

        return attrs

    def create(self, validated_data):
        """重写create方法"""
        # validated_data: 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow'
        # 需要存储到mysql中的字段: username, password, mobile
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']

        # user = User.objects.create(**validated_data)
        user = User(**validated_data)
        user.set_password(validated_data['password'])  # 对密码进行加密
        user.save()

        # 手动生成token
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 加载生成载荷函数
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 加载生成token函数

        payload = jwt_payload_handler(user)  # 生成载荷
        token = jwt_encode_handler(payload)  # 根据载荷生成token
        # 给user多添加一个属性
        user.token = token

        # 创建一个序列化器对象时,如果给data参数传递实参,此时这个序列化器优先做反序列化,后面也会做好序列化操作,来获取数据之前,
        # 必须先调用.is_valid方法,才能.data
        # 创建序列化对象时,如果只给instance参数传递实参,此时这个序列化器只会做序列化操作,只能通过.data属性获取序列化后的字典

        return user

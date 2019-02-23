import re

from rest_framework import serializers
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .models import User, Address
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU


class UserBrowseHistorySerializer(serializers.Serializer):
    """浏览记录"""

    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        """
        对sku_id追加额外校验逻辑
        :param value: sku_id
        :return: value
        """

        try:
            sku_id = SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('sku_id不存在')

        return value

    def create(self, validated_data):
        """重写此方法把sku_id存储到redis  validated_data: {'sku_id': 1}"""

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        # 获取user_id
        user_id = self.context['request'].user.id
        # 获取sku_id
        sku_id = validated_data.get('sku_id')

        # 创建管道对象
        pl = redis_conn.pipeline()

        # 先去重
        # redis_conn.lrem(key, count, value)
        pl.lrem('history_%d' % user_id, 0, sku_id)
        # 存储到列表的最前面
        pl.lpush('history_%d' % user_id, sku_id)
        # 截取前5个
        pl.ltrim('history_%d' % user_id, 0, 4)
        # 执行管道
        pl.execute()

        # 返回
        return validated_data


class AddressTitleSerializer(serializers.ModelSerializer):
    """
    地址标题
    """

    class Meta:
        model = Address
        fields = ('title',)


class UserAddressSerializer(serializers.ModelSerializer):
    """
    用户地址序列化器
    """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')
        return value

    def create(self, validated_data):
        """
        保存
        """
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


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

        # 生成邮箱激活url
        # verify_url = 'http://www.baidu.com'
        # verify_url = 'http://www.meiduo.site:8080/success_verify_email.html?token=2'
        verify_url = instance.generate_verify_email_url()

        # 在此地发送激活邮件
        send_verify_email.delay(instance.email, verify_url)

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


class PasswordModificationSerializer(serializers.Serializer):
    """修改密码序列化器"""

    old_password = serializers.CharField(label='旧密码', write_only=True)
    password = serializers.CharField(label='新密码', write_only=True, min_length=8, max_length=20)
    password2 = serializers.CharField(label='确认新密码', write_only=True, min_length=8, max_length=20)

    def validate_old_password(self, value):
        """校验原密码是否输入正确"""

        user = self.context['request'].user
        if user.check_password(value):
            return value
        else:
            raise serializers.ValidationError('原密码输入不正确')

    def validate(self, attrs):
        """校验新密码"""

        # 判断新密码是否和原密码一样
        if attrs['old_password'] == attrs['password']:
            raise serializers.ValidationError('新密码不能与原密码一样')

        # 判断两次输入的密码是否相等
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两次输入的密码不一致')
        return attrs

    def update(self, instance, validated_data):
        """保存并更新密码"""
        instance.set_password(validated_data['password'])
        instance.save()
        return instance

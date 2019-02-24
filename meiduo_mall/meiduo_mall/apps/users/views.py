import logging
from random import randint

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, UpdateModelMixin
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken

from oauth.utils import generate_save_user_token, check_save_user_token
from .models import User, Address
from .serializers import UserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer
from .serializers import AddressTitleSerializer, UserBrowseHistorySerializer, PasswordModificationSerializer
from goods.models import SKU
from goods.serializers import SKUSerializer
from carts.utils import merge_cart_cookie_to_redis
from meiduo_mall.utils.captcha.captcha import captcha
from celery_tasks.sms.tasks import send_sms_code
from . import constants

logger = logging.getLogger('django')


# Create your views here.
class UserAuthorizeView(ObtainJSONWebToken):
    """重写账号密码登录视图"""

    def post(self, request, *args, **kwargs):
        response = super(UserAuthorizeView, self).post(request, *args, **kwargs)
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            merge_cart_cookie_to_redis(request, response, user)

        return response


# POST/GET /browse_histories/
class UserBrowseHistoryView(CreateAPIView):
    """用户浏览记录"""

    # 指定序列化器(校验)
    serializer_class = UserBrowseHistorySerializer

    # 指定权限
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """读取用户浏览记录"""

        # 创建redis连接对象
        redis_conn = get_redis_connection('history')
        # 查询出redis中当前登录用户的浏览记录[b'1', b'2', b'3']
        sku_ids = redis_conn.lrange('history_%d' % request.user.id, 0, -1)
        # 把sku_id对应的模型取出来
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)

        # 序列化器
        serializer = SKUSerializer(sku_list, many=True)

        # 返回
        return Response(serializer.data)


class AddressViewSet(UpdateModelMixin, CreateModelMixin, GenericViewSet):
    """用户收货地址"""
    permission_classes = [IsAuthenticated]

    serializer_class = UserAddressSerializer

    def create(self, request, *args, **kwargs):
        """新增收货地址"""

        # 判断用户的收货地址数量是否到达上限
        # address_count = Address.objects.filter(user=request.user).count()
        address_count = request.user.addresses.count()
        if address_count > 20:
            return Response({'message': '收货地址数量上限'}, status=status.HTTP_400_BAD_REQUEST)
        # # 创建序列化器给data参数传值(反序列化)
        # serializer = UserAddressSerializer(data=request.data, context={'request': request})
        # # 调用序列化器的is_valid方法
        # serializer.is_valid(raise_exception=True)
        # # 调用序列化器的save
        # serializer.save()
        # # 响应
        # return Response(serializer.data, status=status.HTTP_201_CREATED)
        return super(AddressViewSet, self).create(request, *args, **kwargs)

    def get_queryset(self):
        return self.request.user.addresses.filter(is_deleted=False)

    # GET /addresses/
    def list(self, request, *args, **kwargs):
        """
        用户地址列表数据
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user_id': user.id,
            'default_address_id': user.default_address_id,
            'limit': 20,
            'addresses': serializer.data,
        })

    def destroy(self, request, *args, **kwargs):
        """
        处理删除
        """
        address = self.get_object()

        # 进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """
        设置默认地址
        """
        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

    # put /addresses/pk/title/
    # 需要请求体参数 title
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """
        修改标题
        """
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EmailVerifyView(APIView):
    """激活邮箱"""

    def get(self, request):

        # 1.获取token查询参数
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '缺少token'}, status=status.HTTP_400_BAD_REQUEST)

        # 2.对token解密并返回查询到的user
        user = User.check_verify_email_token(token)
        if not user:
            return Response({'message': '无效的token'}, status=status.HTTP_400_BAD_REQUEST)

        # 3.修改user的email_active字段
        user.email_active = True
        user.save()
        return Response({'message': 'ok'})


# PUT /email/
class EmailView(UpdateAPIView):
    """设置并保存邮箱"""
    permission_classes = [IsAuthenticated]

    # 指定序列化器
    serializer_class = EmailSerializer

    def get_object(self):
        return self.request.user


# GET /user/
class UserDetailView(RetrieveAPIView):
    """提供用户个人信息接口"""

    # 指定权限,必须是通过认证的用户才能访问此接口(就是当前本网站的登录用户)
    permission_classes = [IsAuthenticated]

    # 指定查询集

    # 指定序列化器
    serializer_class = UserDetailSerializer

    def get_object(self):  # 返回指定模型对象
        return self.request.user


"""
# GET /user/
class UserDetailView(APIView):
    # 提供用户个人信息接口

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = self.request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)
"""


# POST /users/
class UserView(CreateAPIView):
    """用户注册"""

    # 指定序列化器
    serializer_class = UserSerializer


# url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UserCountView.as_view())
class UserCountView(APIView):
    """验证用户名是否已存在"""

    def get(self, request, username):
        # 查询用户名是否已存在
        count = User.objects.filter(username=username).count()

        # 构建响应数据
        data = {
            'count': count,
            'username': username,
        }

        return Response(data)


# url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view())
class MobileCountView(APIView):
    """验证用户名是否已存在"""

    def get(self, request, mobile):
        # 查询手机号数量
        count = User.objects.filter(mobile=mobile).count()

        # 构建响应数据
        data = {
            'count': count,
            'mobile': mobile,
        }

        return Response(data)


# PUT /user/(?P<user_id>\d+)/password/
class UpdatePasswordView(CreateAPIView, UpdateAPIView):
    """修改/重置密码"""

    # permission_classes = [IsAuthenticated]

    serializer_class = PasswordModificationSerializer

    def get_object(self):
        user_id = self.kwargs.get('user_id')
        user = User.objects.get(id=user_id)
        if user and user.is_authenticated:
            return user
        else:
            return Response({'message': '未登录用户不允许修改密码'}, status=status.HTTP_401_UNAUTHORIZED)

    def post(self, request, *args, **kwargs):

        # 获取参数
        user_id = kwargs.get('user_id')
        password = request.data.get('password')
        password2 = request.data.get('password2')
        access_token = request.data.get('access_token')

        mobile = check_save_user_token(access_token)
        if not mobile:
            return Response({'message': '操作超时,请重新操作'}, status=status.HTTP_400_BAD_REQUEST)

        if password != password2:
            return Response({'message': '两次输入的密码不一致'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id, mobile=mobile)
        except User.DoesNotExist:
            return Response({'message': '查询用户对象异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user.set_password(password)
        user.save()

        return Response({'message': 'ok'})


# GET url(r'^/image_codes/(?P<image_code_id>[a-z0-9-]{36})/$', views.ImageView.as_view())
class ImageView(APIView):
    """获取图片验证码"""

    def get(self, request, image_code_id):
        redis_conn = get_redis_connection('verify_codes')
        image_name, real_image_code, image_data = captcha.generate_captcha()
        logger.info(real_image_code)
        try:
            redis_conn.setex('CODEID_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, real_image_code)
        except Exception:
            return HttpResponse({'message': '保存图片验证码失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 使用Response会报错, why?
        return HttpResponse(image_data, content_type='image/JPEG')


# GET url(r'^accounts/(?P<username>\w{5,20})/sms/token/$', views.UserAccountView.as_view())
class UserAccountView(APIView):
    """输入账户名"""

    def get(self, request, username):

        # 获取参数
        image_code = request.query_params.get('text')
        image_code_id = request.query_params.get('image_code_id')

        try:
            user = User.objects.filter(Q(username=username) | Q(mobile=username)).first()
        except User.DoesNotExist:
            return Response({'message': '查询用户对象异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not user:
            return Response({'message': '此账户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 建立Redis连接对象并校验图片验证码
        redis_conn = get_redis_connection('verify_codes')
        try:
            real_image_code = redis_conn.get('CODEID_' + image_code_id)
        except Exception:
            return Response({'message': '获取真实的图片验证码异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not real_image_code:
            return Response({'message': '图片验证码过期了'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            try:
                redis_conn.delete('CODEID_' + image_code_id)
            except Exception:
                return Response({'message': '删除图片验证码异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if image_code.lower() != real_image_code.decode().lower():
            return Response({'message': '图片验证码填写错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 构造字典,响应mobile和access_token
        # 使用itdangerous生成access_token返回给前端(有效期10分钟)
        access_token = generate_save_user_token(user.mobile)
        mobile = user.mobile[:3] + '****' + user.mobile[-4:]

        data = {
            'mobile': mobile,
            'access_token': access_token
        }

        return Response(data)


# GET url(r'^sms_codes/$', views.SMSView.as_view())
class SMSView(APIView):
    """获取短信验证码"""

    def get(self, request):
        # 获取access_token并校验
        access_token = request.query_params.get('access_token')
        mobile = check_save_user_token(access_token)
        if not mobile:
            return Response({'message': '操作超时,请重新操作'}, status=status.HTTP_400_BAD_REQUEST)

        # 创建连接对象
        redis_conn = get_redis_connection('verify_codes')
        flag = redis_conn.get('SENDFLAG_%s' % mobile)
        if flag:  # 如果if成立说明此手机号60秒内发过短信
            return Response({'message': '频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        pl = redis_conn.pipeline()
        pl.setex('SMSCODE_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('SENDFLAG_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 4.集成容联云通讯发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
        # 触发异步任务(让发短信不用阻塞主线程)
        send_sms_code.delay(mobile, sms_code)

        # 5.响应结果
        return Response({'message': 'ok'})


# GET url(r'^accounts/(?P<username>\w{5,20})/password/token/$', views.VerificationView.as_view())
class VerificationView(APIView):
    """验证身份"""

    def get(self, request, username):

        # 获取参数
        sms_code = request.query_params.get('sms_code')

        try:
            user = User.objects.filter(Q(username=username) | Q(mobile=username)).first()
        except User.DoesNotExist:
            return Response({'message': '查询用户对象异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not user:
            return Response({'message': '此账户不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 建立Redis连接对象并校验短信验证码
        redis_conn = get_redis_connection('verify_codes')
        try:
            real_sms_code = redis_conn.get('SMSCODE_%s' % user.mobile)
        except Exception:
            return Response({'message': '获取真实的图片验证码异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not real_sms_code:
            return Response({'message': '图片验证码过期了'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            try:
                redis_conn.delete('SMSCODE_%s' % user.mobile)
            except Exception:
                return Response({'message': '删除图片验证码异常'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if sms_code != real_sms_code.decode():
            return Response({'message': '图片验证码填写错误'}, status=status.HTTP_400_BAD_REQUEST)

        # 构造字典,响应mobile和access_token
        # 使用itdangerous生成access_token返回给前端(有效期10分钟)
        access_token = generate_save_user_token(user.mobile)

        data = {
            'user_id': user.id,
            'access_token': access_token
        }

        return Response(data)

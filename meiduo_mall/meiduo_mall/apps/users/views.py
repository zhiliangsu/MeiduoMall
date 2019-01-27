from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin

from .models import User, Address
from .serializers import UserSerializer, UserDetailSerializer, EmailSerializer, UserAddressSerializer


# Create your views here.
class AddressViewSet(CreateModelMixin, GenericViewSet):
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

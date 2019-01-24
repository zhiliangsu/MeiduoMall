from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer, UserDetailSerializer, EmailSerializer


# Create your views here.
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

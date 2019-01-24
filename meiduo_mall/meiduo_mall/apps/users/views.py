from django.shortcuts import render
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer, UserDetailSerializer


# Create your views here.
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

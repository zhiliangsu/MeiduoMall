from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import User
from .serializers import UserSerializer, UserDetailSerializer


# Create your views here.
class UserDetailView(APIView):
    """提供用户个人信息接口"""

    permission_classes = [IsAuthenticated]

    def get(self, request):

        user = self.request.user
        serializer = UserDetailSerializer(user)
        return Response(serializer.data)


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

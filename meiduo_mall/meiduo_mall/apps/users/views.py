from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserSerializer


# Create your views here.

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

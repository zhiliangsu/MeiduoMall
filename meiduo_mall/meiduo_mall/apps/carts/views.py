from django.shortcuts import render
from rest_framework.views import APIView


# Create your views here.


class CartView(APIView):
    """购物车视图"""

    def post(self, request):
        """添加购物车"""
        pass

    def get(self, request):
        """查询购物车"""
        pass

    def put(self, request):
        """修改购物车"""
        pass

    def delete(self, request):
        """删除购物车"""
        pass

from alipay import AliPay
from django.shortcuts import render
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import os

from orders.models import OrderInfo


# Create your views here.
# 1.生成支付宝登录url


class PaymentView(APIView):
    """生成支付宝登录url"""
    permission_classes = [IsAuthenticated]  # 必须是登录用户才能访问此视图

    def get(self, request, order_id):
        # 获取当前登录用户
        user = request.user
        # 获取到美多商城订单编号
        try:
            # 校验订单编号
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return Response({'message': '订单信息有误'}, status=status.HTTP_400_BAD_REQUEST)

        """
        ALIPAY_APPID = '2016091900551154'
        ALIPAY_DEBUG = True  # 将来换成真实环境些改为False
        ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'  # 真实去掉alipaydev 后面dev
        """

        # 创建alipay支付对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False
        )
        # 调用它里面的方法 生成支付宝登录url后面的 查询参数部分
        # 电脑网站支付，需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 美多商城订单编号
            total_amount=str(order.total_amount),  # 一定要把总价转换成字符串类型,不然会报错
            subject='美多商城%s' % order_id,
            return_url="http://www.meiduo.site:8080/pay_success.html"  # 支付成功后回调的url
        )
        # 拼接完整的支付宝登录url
        # 沙箱环境: https://openapi.alipaydev.com/gateway.do? + 查询参数部分
        # 真实环境: https://openapi.alipay.com/gateway.do? + 查询参数部分
        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return Response({'alipay_url': alipay_url})


# 2.支付成功后的验证和修改订单状态 保存订单及支付流水号
class PaymentStatusView(APIView):

    def put(self, request):
        # 获取查询参数中的所有数据 query_params / django GET
        # 把查询参数中的sign签名部分数据单独提取出
        # 调用alipay中的verify方法进行验证支付信息

        # 把交易号和订单编号进行绑定存储
        # 修改订单状态
        pass

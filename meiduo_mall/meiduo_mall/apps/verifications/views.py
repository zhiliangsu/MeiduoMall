import logging

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from random import randint
from django_redis import get_redis_connection

from meiduo_mall.libs.yuntongxun.sms import CCP

logger = logging.getLogger('django')  # 创建日志输出器


# Create your views here.

# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(APIView):
    """发送短信验证码"""

    def get(self, request, mobile):
        # 1.接受手机号码，并校验(通过路由正则组已校验过了)
        # 2.生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        # 3.创建redis连接对象,并保存短信验证码到Redis中
        redis_conn = get_redis_connection('verify_codes')
        # redis_conn.setex(key, 过期时间, value)
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)

        # 4.集成容联云通讯发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 5.响应结果
        return Response({'message': 'ok'})

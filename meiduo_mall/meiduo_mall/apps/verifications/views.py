import logging

from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from random import randint
from django_redis import get_redis_connection
from rest_framework import status

from meiduo_mall.libs.yuntongxun.sms import CCP

logger = logging.getLogger('django')  # 创建日志输出器


# Create your views here.

# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(APIView):
    """发送短信验证码"""

    def get(self, request, mobile):
        # 1.接受手机号码，并校验(通过路由正则组已校验过了)

        # 3.创建redis连接对象,并保存短信验证码到Redis中
        redis_conn = get_redis_connection('verify_codes')
        # 获取此手机号是否有发送过的标记
        flag = redis_conn.get('send_flag_%s' % mobile)

        # 如果已发送就提前响应,不执行后续代码
        if flag:  # 如果if成立说明此手机号60秒内发过短信
            return Response({'message': '频繁发送短信'}, status=status.HTTP_400_BAD_REQUEST)

        # 2.生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)

        # redis_conn.setex(key, 过期时间, value)
        redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        # 存储此手机已发送短信标记
        redis_conn.setex('send_flag_%s' % mobile, 60, 1)

        # 4.集成容联云通讯发送短信验证码
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        # 5.响应结果
        return Response({'message': 'ok'})

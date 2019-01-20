# 编写异步任务代码
import logging

from .yuntongxun.sms import CCP
from . import constants
from celery_tasks.main import celery_app

logger = logging.getLogger('django')


@celery_app.task(name='send_sms_code')  # 用celery_app调用task方法装饰我们的函数为一个异步任务
def send_sms_code(mobile, sms_code):
    try:
        result = CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)
    except Exception as e:
        logger.error("发送短信验证码[异常][mobile: %s, message: %s]" % (mobile, e))
    else:
        if result == 0:
            logger.info("发送验证码短信[正常][ mobile: %s ]" % mobile)
        else:
            logger.warning("发送验证码短信[失败][ mobile: %s ]" % mobile)

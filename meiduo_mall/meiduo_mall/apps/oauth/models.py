from django.db import models

from meiduo_mall.utils.models import BaseModel
from users.models import User


# Create your models here.


class QQAuthUser(BaseModel):
    user = models.ForeignKey(User, verbose_name='openid关联的用户', on_delete=models.CASCADE)
    openid = models.CharField(max_length=64, verbose_name='QQ用户唯一标识', db_index=True)

    class Meta:
        db_table = 'tb_qq_auth'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name


class OAuthSinaUser(BaseModel):
    """
    Sina登录用户数据
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    access_token = models.CharField(max_length=64, verbose_name='access_token', db_index=True)

    class Meta:
        db_table = 'tb_oauth_sina'
        verbose_name = 'sina登录用户数据'
        verbose_name_plural = verbose_name

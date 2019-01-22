from django.db import models


class BaseModel(models.Model):
    """模型基类"""

    create_time = models.DateTimeField(auto_now_add=True, verbose_name='数据创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True  # 表示此模型是一个抽象模型,将来迁移建表时,不会对它进行迁移建表操作,它只用于当其它模型的基类

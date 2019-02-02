from django.contrib import admin

from . import models
from celery_tasks.html.tasks import generate_static_list_search_html


class GoodsCategoryAdmin(admin.ModelAdmin):
    # 模型站点管理类,不光可以控制admin的页面展示样式,还可以监听它里面的数据变化

    def save_model(self, request, obj, form, change):
        """
        监听运营人员在admin界面点击了商品分类数据保存事件
        :param request: 本次保存时的请求对象
        :param obj: 本次要保存的模型对象
        :param form: 要进行修改的表单数据
        :param change: 是否要进行修改 True或False
        :return:
        """
        obj.save()
        generate_static_list_search_html.delay()

    def delete_model(self, request, obj):
        """
        监听运营人员在admin界面点击了商品分类数据删除
        :param request: 本次删除时的请求对象
        :param obj: 要删除的模型对象
        :return:
        """
        obj.delete()
        generate_static_list_search_html.delay()


# Register your models here.
admin.site.register(models.GoodsCategory, GoodsCategoryAdmin)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage)

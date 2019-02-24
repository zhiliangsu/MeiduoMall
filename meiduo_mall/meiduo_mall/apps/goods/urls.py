from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    # 商品列表界面
    url(r'^categories/(?P<category_id>\d+)/skus/$', views.SKUListView.as_view()),

    # 订单列表界面
    url(r'^orders/$', views.OrderListView.as_view()),
]

router = DefaultRouter()
router.register('skus/search', views.SKUSearchViewSet, base_name='skus_search')
urlpatterns += router.urls

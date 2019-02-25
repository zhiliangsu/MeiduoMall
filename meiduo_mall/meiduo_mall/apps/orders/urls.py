from django.conf.urls import url

from . import views

urlpatterns = [
    # 去结算
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    # 保存订单
    url(r'^orders/$', views.OrdersViewSet.as_view({'get': 'list', 'post': 'create'})),
    # 订单商品评价页面展示
    url(r'^orders/(?P<order_id>\d+)/uncommentgoods/$', views.OrderGoodsCommentView.as_view()),
    # 订单商品评价
    url(r'^orders/(?P<order_id>\d+)/comments/$', views.OrderGoodsCommentView.as_view()),
    # 商品详情评价展示
    url(r'^skus/(?P<sku_id>\d+)/comments/$', views.GoodDetailCommentView.as_view()),
]

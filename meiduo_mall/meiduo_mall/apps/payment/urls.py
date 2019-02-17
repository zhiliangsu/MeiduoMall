from django.conf.urls import url

from . import views

urlpatterns = [
    # 生成支付登录url
    url(r'^orders/(?P<order_id>\d+)/payment/$', views.PaymentView.as_view()),

    # 支付成功后修改订单
    url(r'^payment/status/$', views.PaymentStatusView.as_view()),
]

from django.conf.urls import url

from . import views

urlpatterns = [

    # 购物车增删改查
    url(r'^carts/$', views.CartView.as_view()),
    # 购物车全选
    url(r'^carts/selection/$', views.CartSelectedView.as_view()),
]

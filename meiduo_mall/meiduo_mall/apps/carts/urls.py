from django.conf.urls import url

from . import views

urlpatterns = [

    # 购物车
    url(r'^carts/$', views.CartView.as_view()),
]

from django.conf.urls import url
from . import views

urlpatterns = [
    # 获取qq扫码url
    url(r'^qq/authorization/$', views.QQAuthURLView.as_view()),
    # qq扫描后回调处理
    url(r'^qq/user/$', views.QQAuthUserView.as_view()),
    # 获取weibo扫码url
    url(r'^sina/authorization/$', views.SinaAuthURLView.as_view()),
    # weibo扫描后回调处理
    url(r'^sina/user/$', views.SinaAuthUserView.as_view()),
]

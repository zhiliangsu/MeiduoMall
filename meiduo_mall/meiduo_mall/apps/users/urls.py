from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import DefaultRouter

from . import views

urlpatterns = [
    # 注册用户
    url(r'^users/$', views.UserView.as_view()),

    # 判断用户名是否已存在
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UserCountView.as_view()),

    # 判断手机号是否已存在
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # JWT登录
    # 账号密码登录时需要 做cookie购物车合并到redis操作
    # url(r'^authorizations/$', obtain_jwt_token),
    url(r'^authorizations/$', views.UserAuthorizeView.as_view()),

    # 获取用户个人信息
    url(r'^user/$', views.UserDetailView.as_view()),

    # 保存邮箱
    url(r'^email/$', views.EmailView.as_view()),

    # 激活邮箱
    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),

    # 浏览记录
    url(r'^browse_histories/$', views.UserBrowseHistoryView.as_view()),

    # 获取图片验证码
    url(r'^image_codes/(?P<image_code_id>[0-9a-z-]{36})/$', views.ImageView.as_view()),

    # 输入账号名
    url(r'^accounts/(?P<username>\w{5,20})/sms/token/$', views.UserAccountView.as_view()),

    # 获取短信验证码
    url(r'^sms_codes/$', views.SMSView.as_view()),

    # 验证身份
    url(r'^accounts/(?P<username>\w{5,20})/password/token/$', views.VerificationView.as_view()),

    # 修改密码
    url(r'^users/(?P<user_id>\d+)/password/$', views.UpdatePasswordView.as_view()),
    # 重置密码
    # url(r'^users/(?P<user_id>\d+)/password/$', views.VerificationView.as_view()),
]

router = DefaultRouter()
router.register(r'addresses', views.AddressViewSet, base_name='addresses')
urlpatterns += router.urls

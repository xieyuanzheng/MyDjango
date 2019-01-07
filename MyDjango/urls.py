#-*- coding:utf-8 -*-
"""MyDjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url,include
from django.contrib import admin
from django.views.generic import TemplateView
import xadmin
from django.views.static import serve

from  users.views import IndexView,LoginView,LogoutView,RegisterView,ActiveUserView,ForgetPwdView,ResetView,ModifyPwdView,ShareView

from MyDjango.settings import MEDIA_ROOT

urlpatterns = [
    url(r'^xadmin/', xadmin.site.urls),
    url('^$',IndexView.as_view(),name="index"),
    url('^login/$',LoginView.as_view(),name="login"),
    url('^logout/$',LogoutView.as_view(),name="logout"),
    url('^register/$',RegisterView.as_view(),name="register"),
    url('^forget_pwd/$',ForgetPwdView.as_view(),name="forget_pwd"),
    url('^active/(?P<active_code>\w+)/$',ActiveUserView.as_view(),name="active"),
    url('^reset/(?P<active_code>\w+)/$',ResetView.as_view(),name="reset"),
    url('^modify_pwd/$',ModifyPwdView.as_view(),name="modify_pwd"),
    url('^captcha/',include('captcha.urls')),
    #配置上传文件的访问处理函数
    url(r'^media/(?P<path>.*)$',serve,{"document_root":MEDIA_ROOT}),
    #富文本相关url
    url(r'^ueditor/',include('DjangoUeditor.urls')),

    url(r'^course/',include('courses.urls',namespace='course')),
    url(r'^org/',include('organization.urls',namespace='org')),
    url(r'^users/',include('users.urls',namespace='users')),
    url(r'^share/',ShareView.as_view(),name="share")
]

handler404 = 'users.views.page_not_found'
handler500 = 'users.views.page_error'
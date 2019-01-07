# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import  json
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from django.views.generic.base import View
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse

from .models import UserProfile, EmailVerifyRecord
from .forms import LoginForm, RegisterForm, ForgetForm, ModifyPwdForm, UploadImageForm
from .forms import UserInfoForm
from utils.email_send import send_register_email
from utils.mixin_utils import LoginRequiredMixin
from operation.models import UserCourse, UserFavorite, UserMessage
from organization.models import CourseOrg, Teacher
from courses.models import Course
from .models import Banner

# Create your views here.

class CustomBackend(ModelBackend):
    def authenticate(self, username=None, password=None, **kwargs):
        try:
            user = UserProfile.objects.get(Q(username=username)|Q(email=username))
            if user.check_password(password):
                return user
        except Exception as e:
            return None


class ActiveUserView(View):
    def get(self,request,active_code):
        all_records = EmailVerifyRecord.objects.filter(code=active_code)
        if all_records:
            for record in all_records:
                email = record.email
                user = UserProfile.objects.get(email=email)
                user.is_active = True
                user.save()
                return render(request,"index.html",{})
        else:
            return render(request,"active_fail.html")


class RegisterView(View):
    def get(self,request):
        register_form = RegisterForm()
        return render(request,"register.html",{'register_form':register_form})

    def post(self,request):
        register_form = RegisterForm(request.POST)
        if register_form.is_valid():
            user_name = request.POST.get("email","")
            if UserProfile.objects.filter(email=user_name):
                return render(request,"register.html",{"register_form":register_form, "msg":"用户已经存在"})
            pass_word = request.POST.get("password","")
            user_profile = UserProfile()
            user_profile.username = user_name
            user_profile.email = user_name
            user_profile.is_active = False
            user_profile.password = make_password(pass_word)
            user_profile.save()

            # 写入欢迎注册消息
            user_message = UserMessage()
            user_message.user = user_profile.id
            user_message.message = "欢迎注册慕学在线网"
            user_message.save()

            send_register_email(user_name,"register")
            return render(request,"login.html")
        else:
            return render(request,"register.html",{"register_form":register_form})


class LogoutView(View):
    """
    用户登出
    """
    def get(self,request):
        logout(request)
        return HttpResponseRedirect(reverse("index"))


class LoginView(View):
    def get(self,request):
        return render(request,"login.html",{})
    def post(self,request):
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = request.POST.get("username","")
            pass_word = request.POST.get("password","")
            user = authenticate(username = user_name, password = pass_word)
            if user is not None:
                if user.is_active:
                    login(request,user)
                    return HttpResponseRedirect(reverse("index"))
                else:
                    return render(request,"login.html",{"msg":"用户未激活！"})
            else:
                return render(request,"login.html",{"msg":"用户名或密码错误！"})
        else:
            return render(request,"login.html",{"login_form":login_form})


class ForgetPwdView(View):
    def get(self,request):
        forget_form = ForgetForm(request.POST)
        return render(request,"forgetpwd.html",{"forget_form":forget_form})
    def post(self,request):
        forget_form = ForgetForm(request.POST)
        if forget_form.is_valid():
            email = request.POST.get("email", "")
            send_register_email(email,"forget")
            return render(request,"send_success.html")
        else:
            return render(request, "forgetpwd.html",{"forget_form":forget_form})


class ResetView(View):
    def get(self,request,active_code):
        all_record = EmailVerifyRecord.objects.filter(code=active_code)
        if all_record:
            for record in all_record:
                email = record.email
                return render(request,"password_reset.html",{"email":email})
        else:
            return render(request,"active_fail.html")
        return render(request,"login.html")


class ModifyPwdView(View):
    def get(self,request):
        render(request,"password_reset.html")
    def post(self,request):
        modify_form = ModifyPwdForm(request.POST)
        if modify_form.is_valid():
            password1 = request.POST.get("password1", "")
            password2 = request.POST.get("password2", "")
            email = request.POST.get("email", "")
            if password1 == password2:
                user = UserProfile.objects.get(email=email)
                user.password = make_password(password1)
                user.save()
                return render(request,"login.html")
            else:
                return render(request,"password_reset.html",{"email":email,"modify_form":modify_form,"msg":"两个密码不一致！"})
        else:
            email = request.POST.get("email", "")
            return render(request,"password_reset.html",{"email":email,"modify_form":modify_form})


class IndexView(View):
    # 慕学在线网 首页
    def get(self,request):
        all_banners = Banner.objects.all().order_by("index")
        courses = Course.objects.filter(is_banner=False)[:6]
        banner_courses = Course.objects.filter(is_banner=True)[:3]
        course_orgs = CourseOrg.objects.filter()[:15]
        return render(request,'index.html',{
            "all_banners":all_banners,
            "courses":courses,
            "banner_courses":banner_courses,
            "course_orgs":course_orgs
        })


class UserinfoView(LoginRequiredMixin,View):
    """
    用户个人信息
    """
    def get(self,request):
        return render(request,"usercenter-info.html",{})
    def post(self,request):
        userInfoForm = UserInfoForm(request.POST,instance=request.user)
        if userInfoForm.is_valid():
            userInfoForm.save()
            return HttpResponse('{"status":"success"}',content_type="application/json")
        else:
            return HttpResponse(json.dumps(userInfoForm.errors),content_type="application/json")


class UploadImageView(LoginRequiredMixin,View):
    """
    用户修改头像
    """
    def post(self,request):
        uploadImageForm = UploadImageForm(request.POST,request.FILES,instance=request.user)
        if uploadImageForm.is_valid():
            uploadImageForm.save()
            return HttpResponse('{"status":"success"}',content_type="application/json")
        return HttpResponse('{"status":"fail"}', content_type="application/json")


class UpdatePwdView(LoginRequiredMixin,View):
    """
    个人中心修改用户密码
    """
    def post(self,request):
        modifyPwdForm = ModifyPwdForm(request.POST)
        if modifyPwdForm.is_valid():
            pwd1 = request.POST.get("password1","")
            pwd2 = request.POST.get("password2","")
            if pwd1 != pwd2:
                return HttpResponse('{"status":"fail","msg":"密码不一致"}',content_type="application/json")
            user = request.user
            user.password = make_password(pwd2)
            user.save()
            return HttpResponse('{"status":"success"}',content_type="application/json")
        return HttpResponse(json.dumps(modifyPwdForm.errors), content_type="application/json")


class SendEmailCodeView(LoginRequiredMixin,View):
    """
    发送邮箱验证码
    """
    def get(self,request):
        email = request.GET.get("email","")
        if UserProfile.objects.filter(email=email):
            return HttpResponse('{"email":"邮箱已存在"}',content_type="application/json")
        send_register_email(email,"update_email")
        return HttpResponse('{"status":"success"}',content_type="application/json")


class UpdateEmailView(LoginRequiredMixin,View):
    """
    修改个人邮箱
    """
    def post(self,request):
        email = request.POST.get("email","")
        code = request.POST.get("code","")
        emailVerifyRecord = EmailVerifyRecord.objects.filter(email=email,code=code,send_type='update_email')
        if emailVerifyRecord:
            user = request.user
            user.email = email
            user.save()
            return HttpResponse('{"status":"success"}', content_type="application/json")
        else:
            return HttpResponse('{"email":"验证码出错"}', content_type="application/json")


class MyCourseView(LoginRequiredMixin,View):
    def get(self,request):
        usercourses = UserCourse.objects.filter(user=request.user)
        return render(request,"usercenter-mycourse.html",{
            "usercourses":usercourses
        })


class MyFavOrgView(LoginRequiredMixin,View):
    def get(self,request):
        org_list = []
        org_favs = UserFavorite.objects.filter(user=request.user,fav_type=2)
        for org_fav in org_favs:
            org_id = org_fav.fav_id
            course_org = CourseOrg.objects.get(id=org_id)
            org_list.append(course_org)
        return render(request,"usercenter-fav-org.html",{
            "org_list":org_list
        })


class MyFavTeacherView(LoginRequiredMixin,View):
    def get(self,request):
        teacher_list = []
        teacher_favs = UserFavorite.objects.filter(user=request.user,fav_type=3)
        for teacher_fav in teacher_favs:
            teacher_id = teacher_fav.fav_id
            teacher = Teacher.objects.get(id=teacher_id)
            teacher_list.append(teacher)
        return render(request,"usercenter-fav-teacher.html",{
            "teacher_list":teacher_list
        })


class MyFavCourseView(LoginRequiredMixin,View):
    def get(self, request):
        course_list = []
        courses_favs = UserFavorite.objects.filter(user=request.user, fav_type=1)
        for course_fav in courses_favs:
            course_id = course_fav.fav_id
            course = Course.objects.get(id=course_id)
            course_list.append(course)
        return render(request, "usercenter-fav-course.html", {
            "course_list":course_list
        })


class MyMessageView(LoginRequiredMixin,View):
    """
    我的消息
    """
    def get(self,request):
        all_message = UserMessage.objects.filter(user=request.user.id)
        #用户进入个人消息后清空未读消息的记录
        all_unread_messages = UserMessage.objects.filter(user=request.user.id,has_read=False)
        for unread_message in all_unread_messages:
            unread_message.has_read = True
            unread_message.save()

        #对个人消息进行分页
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_message, 2, request=request)

        messages = p.page(page)
        return render(request,"usercenter-message.html",{
            "messages":messages
        })


class ShareView(View):
    def get(self,request):
        return render(request,'sharedemo.html',{

        })

def page_not_found(request):
    from django.shortcuts import render_to_response
    response = render_to_response('404.html',{})
    response.status_code = 404
    return response

def page_error(request):
    from django.shortcuts import render_to_response
    response = render_to_response("500.html",{})
    response.status_code = 500
    return response
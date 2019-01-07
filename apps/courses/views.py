# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic.base import View
from pure_pagination import Paginator,EmptyPage,PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q

from .models import Course,CourseOrg,CourseResource,BannerCourse
from operation.models import UserFavorite,UserProfile,UserMessage,UserCourse,UserAsk,CourseComments
from utils.mixin_utils import LoginRequiredMixin

# Create your views here.


class CourseListView(View):
    def get(self,request):
        all_courses = Course.objects.all().order_by("-add_time")
        hot_courses = Course.objects.all().order_by("-click_nums")[:3]
        search_keywords = request.GET.get('keywords', "")
        if search_keywords:
            all_courses = all_courses.filter(Q(name__icontains=search_keywords)|Q(desc__icontains=search_keywords)|Q(detail__icontains=search_keywords))
        sort = request.GET.get("sort","")
        if sort:
            if sort == "students":
                all_courses = all_courses.order_by("-students")
            elif sort == "hot":
                all_courses = all_courses.order_by("-click_nums")

        try:
            page = request.GET.get("page",1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_courses,3,request=request)
        courses = p.page(page)

        return render(request,"course-list.html",{
            "all_courses":courses,
            "sort":sort,
            "hot_courses":hot_courses
        })


class CourseDetailView(View):
    def get(self,request,course_id):
        course = Course.objects.get(id = int(course_id))
        course.click_nums += 1
        course.save

        has_fav_course = False
        has_fav_org = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_type=1,fav_id=course.id):
                has_fav_course = True
            if UserFavorite.objects.filter(user=request.user,fav_type=2,fav_id=course.course_org.id):
                has_fav_org = True

        tag = course.tag
        if tag:
            courses_relate = Course.objects.filter(tag=tag)[:2]
        else:
            courses_relate = []

        return render(request,"course-detail.html",{
            "course" : course,
            "has_fav_course" : has_fav_course,
            "has_fav_org" : has_fav_org,
            "courses_relate" : courses_relate
        })


class CourseInfoView(View):
    def get(self,request,course_id):
        course = Course.objects.get(id=int(course_id))
        course.students += 1
        course.save()
        # 查询用户是否已经关联了该课程
        user_course = UserCourse.objects.filter(user=request.user,course=course)
        if not user_course:
            user_course = UserCourse(user=request.user,course=course)
            user_course.save()

        user_courses = UserCourse.objects.filter(course=course)
        user_ids = [user_course.user.id for user_course in user_courses ]
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [user_course.course.id for user_course in all_user_courses]
        # 获取学过该用户学过其他的所有课程
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:5]
        all_resources = CourseResource.objects.filter(course=course)
        return render(request,"course-video.html",{
            "course":course,
            "course_resources":all_resources,
            "relate_courses":relate_courses
        })


class CommentsView(LoginRequiredMixin,View):
    def get(self,request,course_id):
        course = Course.objects.get(id=int(course_id))
        all_resources = CourseResource.objects.filter(course=course)
        all_comments = CourseComments.objects.filter(course=course).order_by("-id")

        user_courses = UserCourse.objects.filter(course=course)
        user_ids = [user_course.user.id for user_course in user_courses]
        all_user_courses = UserCourse.objects.filter(user_id__in=user_ids)
        # 取出所有课程id
        course_ids = [user_course.course.id for user_course in all_user_courses]
        # 获取学过该用户学过其他的所有课程
        relate_courses = Course.objects.filter(id__in=course_ids).order_by("-click_nums")[:5]
        return render(request,"course-comment.html",{
            "course":course,
            "all_resources":all_resources,
            "all_comments":all_comments,
            "relate_courses":relate_courses
        })


class AddComentsView(View):
    """
    用户添加课程评论
    """
    def post(self,request):
        if not request.user.is_authenticated():
            HttpResponse('{"status":"fail", "msg":"用户未登录"}', content_type='application/json')
        course_id = request.POST.get("course_id",0)
        comments = request.POST.get("comments","")
        if course_id >0 and comments:
            coursecommet = CourseComments()
            course = Course.objects.get(id=int(course_id))
            coursecommet.course = course
            coursecommet.user = request.user
            coursecommet.comments = comments
            coursecommet.save()
            return HttpResponse('{"status":"success", "msg":"添加成功"}', content_type='application/json')
        else:
            return HttpResponse('{"status":"fail", "msg":"添加失败"}', content_type='application/json')
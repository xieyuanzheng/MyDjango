# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.views.generic import View
from pure_pagination import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.db.models import Q

from .models import CourseOrg, CityDict, Teacher
from .forms import UserAskForm
from operation.models import UserFavorite
from courses.models import Course
from utils.mixin_utils import LoginRequiredMixin

# Create your views here.
class OrgView(View):
    """
    课程机构列表功能
    """
    def get(self,request):
        all_orgs = CourseOrg.objects.all()
        hot_orgs = CourseOrg.objects.order_by("-click_nums")[:3]
        all_citys = CityDict.objects.all()

        search_keywords = request.GET.get("keywords","")
        if search_keywords:
            all_orgs = all_orgs.filter(Q(name__icontains=search_keywords)|Q(desc__icontains=search_keywords))
        # 取出筛选城市
        city_id = request.GET.get("city","")
        if city_id:
            all_orgs = all_orgs.filter(city_id=int(city_id))
        # 类别筛选
        category = request.GET.get("ct","")
        if category:
            all_orgs = all_orgs.filter(category=category)

        sort = request.GET.get("sort","")
        if sort:
            if sort == "students":
                all_orgs = all_orgs.order_by("-students")
            elif sort == "courses":
                all_orgs = all_orgs.order_by("-course_nums")

        org_nums = all_orgs.count()

        #对课程机构进行分页
        try:
            page = request.GET.get("page",1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(all_orgs,3,request=request)
        orgs = p.page(page)

        return render(request,"org-list.html",{
            "all_orgs": orgs,
            "all_citys": all_citys,
            "org_nums": org_nums,
            "city_id": city_id,
            "category": category,
            "hot_orgs": hot_orgs,
            "sort": sort
        })


class AddUserAskView(View):
    """
     用户添加咨询
     """
    def post(self,request):
        userask_form = UserAskForm(request.POST)
        if userask_form.is_valid():
            userask_form.save(commit=True)
            return HttpResponse('{"status":"success"}',content_type="application/json")
        else:
            return HttpResponse('{"status":"fail", "msg":"添加出错"}',content_type="application/json")


class OrgHomeView(View):
    """
    机构首页
    """
    def get(self,request,org_id):
        current_page = "机构首页"
        course_org = CourseOrg.objects.get(id=int(org_id))
        course_org.click_nums += 1
        course_org.save()

        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_type=2,fav_id=course_org.id):
                has_fav = True

        all_courses = course_org.course_set.all()[:3]
        all_teachers = course_org.teacher_set.all()
        t_ids = [teacher.id for teacher in all_teachers]
        return render(request,"org-detail-homepage.html",{
            "current_page":current_page,
            "course_org":course_org,
            "has_fav":has_fav,
            "all_courses":all_courses,
            "all_teachers":all_teachers
        })


class OrgCourseView(View):
    """
    机构课程列表页
    """
    def get(self,request,org_id):
        current_page = "course"
        course_org = CourseOrg.objects.get(id=int(org_id))
        courses = Course.objects.filter(course_org=course_org)
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_type=2,fav_id=course_org.id):
                has_fav = True
        return render(request,'org-detail-course.html',{
            "current_page":current_page,
            "courses":courses,
            "has_fav":has_fav,
            "course_org":course_org
        })


class OrgDescView(View):
    """
    机构介绍页
    """
    def get(self,request,org_id):
        current_page = "desc"
        course_org = CourseOrg.objects.get(id=int(org_id))
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_type=2,fav_id=course_org.id):
                has_fav = True
        return render(request,'org-detail-desc.html',{
            "current_page":current_page,
            "course_org":course_org,
            "has_fav":has_fav
        })


class OrgTeacherView(View):
    """
    机构教师页
    """
    def get(self,request,org_id):
        current_page = "teacher"
        course_org = CourseOrg.objects.get(id=int(org_id))
        teachers = course_org.teacher_set.all()
        has_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_type=2,fav_id=course_org.id):
                has_fav = True
        return render(request,'org-detail-teachers.html',{
            "current_page":current_page,
            "course_org":course_org,
            "has_fav":has_fav,
            "teachers":teachers
        })


class TeacherListView(View):
    def get(self,request):
        all_teachers = Teacher.objects.all()
        search_keywords = request.GET.get("keywords","")
        if search_keywords:
            all_teachers = all_teachers.filter(Q(name__icontains=search_keywords)|Q(work_company__icontains=search_keywords)|Q(work_position__icontains=search_keywords))
        sort = request.GET.get("sort","")
        if sort:
            if sort == "hot":
                all_teachers = all_teachers.order_by("-click_nums")
        sorted_teachers = Teacher.objects.order_by("-click_nums")[:3]

        try:
            page = request.GET.get("page",1)
        except PageNotAnInteger:
            page = 1
        p = Paginator(all_teachers,3,request=request)
        teachers = p.page(page)
        return render(request,"teachers-list.html",{
            "all_teachers":teachers,
            "sort":sort,
            "sorted_teachers":sorted_teachers
        })


class TeacherDetailView(View):
    def get(self,request,teacher_id):
        teacher = Teacher.objects.get(id=int(teacher_id))
        teacher.click_nums += 1
        teacher.save()
        all_courses = Course.objects.filter(teacher=teacher)
        courseOrg = CourseOrg.objects.get(id=teacher.org.id)
        has_teacher_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_id=teacher.id,fav_type=3):
                has_teacher_fav = True
        has_org_fav = False
        if request.user.is_authenticated():
            if UserFavorite.objects.filter(user=request.user,fav_id=teacher.org_id,fav_type=2):
                has_org_fav = True

        sorted_teachers = Teacher.objects.all().order_by("-click_nums")[:3]
        return render(request,"teacher-detail.html",{
            "teacher":teacher,
            "all_courses":all_courses,
            "has_teacher_fav":has_teacher_fav,
            "has_org_fav":has_org_fav,
            "sorted_teachers":sorted_teachers,
            "courseOrg":courseOrg
        })


class AddFavView(View):
    """
    用户收藏，用户取消收藏
    """
    def post(self,request):
        fav_id = request.POST.get("fav_id",0)
        fav_type = request.POST.get("fav_type", 0)

        if not request.user.is_authenticated():
            return HttpResponse('{"status":"fail","msg":"用户未登录"}',content_type="application/json")

        exist_record = UserFavorite.objects.filter(user=request.user,fav_id=int(fav_id),fav_type=int(fav_type))
        if exist_record:
            """如果记录存在，证明是要取消收藏"""
            exist_record.delete()
            if int(fav_type) == 1:
                course = Course.objects.get(id = int(fav_id))
                course.fav_nums -= 1
                if course.fav_nums < 0:
                    course.fav_nums = 0
                course.save()
            elif int(fav_type) == 2:
                courseorg = CourseOrg.objects.get(id = int(fav_id))
                courseorg.fav_nums -= 1
                if courseorg.fav_nums < 0:
                    courseorg.fav_nums = 0
                courseorg.save()
            elif int(fav_type) == 3:
                teacher = Teacher.objects.get(id = int(fav_id))
                teacher.fav_nums -= 1
                if teacher.fav_nums < 0:
                    teacher.fav_nums = 0
                teacher.save()
            return HttpResponse('{"status":"success", "msg":"收藏"}', content_type='application/json')
        else:
            """如果记录不存在，证明是要收藏"""
            userfavorite = UserFavorite()
            if int(fav_id)>0 and int(fav_type)>0:
                userfavorite.user = request.user
                userfavorite.fav_id = int(fav_id)
                userfavorite.fav_type = int(fav_type)
                userfavorite.save()
                if int(fav_type) == 1:
                    course = Course.objects.get(id=int(fav_id))
                    course.fav_nums += 1
                    course.save()
                elif int(fav_type) == 2:
                    courseorg = CourseOrg.objects.get(id=int(fav_id))
                    courseorg.fav_nums += 1
                    courseorg.save()
                elif int(fav_type) == 3:
                    teacher = Teacher.objects.get(id=int(fav_id))
                    teacher.fav_nums += 1
                    teacher.save()
                return HttpResponse('{"status":"success", "msg":"已收藏"}', content_type='application/json')
            else:
                return HttpResponse('{"status":"fail", "msg":"收藏出错"}', content_type='application/json')
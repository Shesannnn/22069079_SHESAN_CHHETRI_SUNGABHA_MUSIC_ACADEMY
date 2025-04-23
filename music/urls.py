from django.urls import path
from . import views
from django.contrib import admin
from .views import home


urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses_list, name='courses_list'),
    path('login/', views.login_view, name='login'),  # Add 'name' for URL reverse lookup
    path('register/', views.register_view, name='register'),  # Add 'name' for URL reverse lookup
    path('logout/', views.logout_view, name='logout'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/payment/', views.course_detail_payment, name='course_detail_payment'),
    path('teacher-dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
]


# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('courses/', views.courses_list, name='courses_list'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/payment/', views.course_detail_payment, name='course_detail_payment'),
    path('teacher-dashboard/', views.teacher_dashboard_view, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('initiate-payment/', views.initiate_payment, name='initiate_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/success/<int:payment_id>/', views.payment_success_page, name='payment_success_page'),
    path('payment/failure/<int:payment_id>/', views.payment_failure_page, name='payment_failure_page'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('download-invoice/<int:payment_id>/', views.download_invoice, name='download_invoice'),
    path('course/<int:course_id>/content/', views.course_content_view, name='course_content'),
    path('notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('about/', views.about, name='about'),
    path('team/', views.team, name='team'),  # New URL for Team page
    path('contact/', views.contact, name='contact'),  # URL for Contact page
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('delete-phone-number/', views.delete_phone_number, name='delete_phone_number'),
]
from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    path('', views.user_login, name='login'),
    path('forgot-password/', views.forgot_password, name='forgot_password'), # NEW
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Student
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('feedback/<int:booking_id>/', views.submit_feedback, name='submit_feedback'),
    
    # Faculty
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    
    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('classroom/add/', views.add_classroom, name='add_classroom'),
    path('classroom/delete/<int:classroom_id>/', views.delete_classroom, name='delete_classroom'),
    
    # Common & AJAX
    path('availability/', views.view_availability, name='view_availability'),
    path('ajax/load-subjects/', views.load_subjects, name='ajax_load_subjects'),
    path('ajax/load-semesters/', views.load_semesters, name='ajax_load_semesters'),
    path('ajax/load-divisions/', views.load_divisions, name='ajax_load_divisions'),

    # Chatbot
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/download/<str:filename>/', views.download_pdf, name='download_pdf'),
]
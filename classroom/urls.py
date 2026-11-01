from django.urls import path
from . import views

app_name = 'classroom'

urlpatterns = [
    # --- Authentication ---
    path('', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),

    # --- Dashboards ---
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),

    # --- Faculty Actions ---
    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('document/upload/', views.upload_document, name='upload_document'),
    path('document/delete/<int:doc_id>/', views.delete_document, name='delete_document'),

    # --- Student Actions ---
    path('feedback/submit/<int:booking_id>/', views.submit_feedback, name='submit_feedback'),

    # --- Admin Actions ---
    path('classroom/add/', views.add_classroom, name='add_classroom'),
    path('classroom/delete/<int:classroom_id>/', views.delete_classroom, name='delete_classroom'),
    path('availability/', views.view_availability, name='view_availability'),
    path('analytics/data/', views.get_analytics_data, name='get_analytics_data'),
    path('analytics/export/', views.export_analytics, name='export_analytics'),
    path('authorizations/', views.manage_authorizations, name='manage_auth'),

    # --- AJAX / API Endpoints ---
    # The error was here. We map the URL to 'views.get_subjects' but keep the name 'ajax_load_subjects'
    path('ajax/load-subjects/', views.get_subjects, name='ajax_load_subjects'),
    path('api/divisions/', views.api_get_divisions, name='api_get_divisions'),
    path('api/semesters/', views.api_get_semesters, name='api_get_semesters'),

    # --- AI Chatbot ---
    path('chat/', views.chat_view, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
]
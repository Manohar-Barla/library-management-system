from django.urls import path
from . import views

urlpatterns = [
    path('', views.members, name='members'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('send-email-otp/', views.send_email_otp, name='send_email_otp'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),

    # path('send-mobile-otp/', views.send_mobile_otp, name='send_mobile_otp'),
    # path('verify-mobile-otp/', views.verify_mobile_otp, name='verify_mobile_otp'),
    path('fetch-user-details/', views.fetch_user_details, name='fetch_user_details'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    
    # Student specific pages
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/library/', views.student_library, name='student_library'),
    path('student/issued/', views.student_issued, name='student_issued'),
    path('student/change-password/', views.student_change_password, name='student_change_password'),
    
    # Category Management
    path('admin/categories/', views.category_list, name='category_list'),
    path('admin/categories/add/', views.category_add, name='category_add'),
    path('admin/categories/edit/<int:pk>/', views.category_edit, name='category_edit'),
    path('admin/categories/delete/<int:pk>/', views.category_delete, name='category_delete'),
    
    # Author Management
    path('admin/authors/', views.author_list, name='author_list'),
    path('admin/authors/add/', views.author_add, name='author_add'),
    path('admin/authors/edit/<int:pk>/', views.author_edit, name='author_edit'),
    path('admin/authors/delete/<int:pk>/', views.author_delete, name='author_delete'),
    
    # Book Management
    path('admin/books/', views.book_list, name='book_list'),
    path('admin/books/add/', views.book_add, name='book_add'),
    path('admin/books/edit/<int:pk>/', views.book_edit, name='book_edit'),
    path('admin/books/delete/<int:pk>/', views.book_delete, name='book_delete'),
    
    # Book Issue/Return
    path('admin/issues/', views.issue_list, name='issue_list'),
    path('admin/issues/add/', views.issue_add, name='issue_add'),
    path('admin/issues/return/<int:pk>/', views.issue_return, name='issue_return'),
    
    # Student Management
    path('admin/students/', views.student_list, name='student_list'),
    path('admin/students/<int:user_id>/', views.student_detail, name='student_detail'),
    
    # Profile / Auth
    path('admin/change-password/', views.admin_change_password, name='admin_change_password'),
    path('logout/', views.logout_view, name='logout'),
]
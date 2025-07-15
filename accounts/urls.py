from django.urls import path
from . import views
from .views import data_leak_scanner


urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Admin Actions
    path('toggle-staff/<int:user_id>/', views.toggle_staff_status, name='toggle_staff_status'),
    path('toggle-superuser/<int:user_id>/', views.toggle_superuser_status, name='toggle_superuser_status'),
    path('toggle-active/<int:user_id>/', views.toggle_active_status, name='toggle_active_status'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),

    # ... other paths
    path('data-leak-scanner/', data_leak_scanner, name='data_leak_scanner'),
    path('password_manager/', views.password_manager, name='password_manager'),

]

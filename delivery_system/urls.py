from django.urls import path
from . import views

app_name = 'delivery_system'

urlpatterns = [
    path('apply/', views.apply_delivery_boy, name='apply'),
    path('applications/', views.view_applications, name='view_applications'),
    path('applications/<int:application_id>/approve/', views.approve_application, name='approve_application'),
    path('manage-delivery-boys/', views.manage_delivery_boys, name='manage_delivery_boys'),
    path('login/', views.delivery_login, name='delivery_login'),
    path('logout/', views.delivery_logout, name='delivery_logout'),
    path('change-password/', views.change_first_password, name='change_first_password'),
    path('dashboard/', views.delivery_dashboard, name='delivery_dashboard'),
    path('profile/', views.delivery_profile, name='delivery_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('toggle-availability/', views.toggle_availability, name='toggle_availability'),
    path('update-order-status/', views.update_order_status, name='update_order_status'),
    path('remove-delivery-boy/', views.remove_delivery_boy, name='remove_delivery_boy'),
    path('view_assigned_work/', views.view_assigned_work, name='view_assigned_work'),
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('update-delivery-status/', views.update_delivery_status, name='update_delivery_status'),
    path('work-history/', views.work_history, name='work_history'),
] 
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name='custom_admin'
urlpatterns = [
    path('admin/', views.admin_index, name='admin_index'), 
    path('requested-users/',views.requested_users_view, name='requested_users'),
    path('approve-user/<int:user_id>/',views. approve_user, name='approve_user'),  # New URL for approval
    path('view_customers/', views.view_customers, name='view_customers'),  # URL for viewing customers

    path('categories/', views.view_categories, name='view_categories'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/toggle/<int:category_id>/', views.toggle_category, name='toggle_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    path('category-requests/', views.view_category_requests, name='view_category_requests'),
    path('handle-category-request/<int:request_id>/', views.handle_category_request, name='handle_category_request'),
    path('complaints/', views.admin_view_complaints, name='view_complaints'),
    path('reply-to-complaint/<int:complaint_id>/', views.admin_reply_to_complaint, name='reply_to_complaint'),
]

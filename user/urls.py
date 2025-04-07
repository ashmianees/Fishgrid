from django.urls import path
from user import views

from .views import  create_shop_request, chat_api, chatbot_view  # Import the new view and chat views

app_name='user'
urlpatterns = [
    
    path('indexfish/', views.indexfish, name='indexfish'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile_completion/', views.profile_completion, name='profile_completion'),
    path('profile_view/', views.profile_view, name='profile_view'),
    path('profile_update/', views.profile_update, name='profile_update'), 
    path('create-shop-request/', create_shop_request, name='create_shop_request'),  # Add this line
    path('shopdetails/<int:id>/', views.ShopDetailView.as_view(), name='shop_detail'), 
    
      # URL for shop details
    
    path('dashboard-content/', views.dashboard_content, name='dashboard_content'),
    path('order-history/', views.order_history, name='order_history'),
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),
    path('chat_api/', chat_api, name='chat_api'),  # Ensure this line is present
    path('chatbot/', chatbot_view, name='chatbot_view'),
    path('disease-detection/', views.disease_detection, name='disease_detection'),
    path('predict-disease/', views.predict_disease, name='predict_disease'),
    path('view-custom-order/', views.view_custom_order, name='view_custom_order'),
]

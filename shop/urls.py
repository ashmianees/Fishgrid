from django.urls import path

from fish_grid import settings
from . import views
from django.conf.urls.static import static

app_name='shop'
urlpatterns = [
    path('', views.shop_index, name='shop_index'),
    path('profile/', views.shop_profile_view, name='shop_profile_view'),
    path('products/<int:shop_id>/', views.product_list, name='product_list'),
 
    
    path('shop_dashboard/', views.shop_dashboard, name='shop_dashboard'),
    path('shop_creation/', views.shop_creation, name='shop_creation'),
    path('shop_details_edit/<int:shop_id>/', views.shop_details_edit, name='shop_details_edit'), 
    # Delete category
    
    path('products/<int:product_id>/',views.product_detail, name='product_detail'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/edit/', views.product_edit, name='product_edit'),
    path('products/disable/', views.product_disable, name='product_disable'),
    path('single_product/<int:product_id>/<int:shop_id>/', views.view_singleproduct, name='view_singleproduct'),
    path('check-product-exists/', views.check_product_exists, name='check_product_exists'),
    #cart 
    path('cart/add/<int:product_id>/<int:shop_id>/', views.add_to_cart, name='add_to_cart'),
    path('viewcart/', views.view_cart, name='view_cart'),
    path('remove_from_cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('shop/<int:shop_id>/', views.shop_product_views, name='shop_product_views'),

    #Feedback
    path('submit_feedback/<int:product_id>/<int:shop_id>/', views.submit_feedback, name='submit_feedback'),

    path('toggle-wishlist/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', views.view_wishlist, name='view_wishlist'),

    path('checkout/', views.checkout, name='checkout'),  # This should match the URL you are trying to reverse
    path('add-address/', views.add_new_address, name='add_new_address'),
    # path('place-order/', views.place_order, name='place_order'),
    path('view_orders/', views.order_view, name='view_orders'),
    path('complaint/submit/<int:shop_id>/', views.submit_complaint, name='submit_complaint'),
    path('shop/<int:shop_id>/complaints/', views.view_complaints, name='view_complaints'),  # URL for viewing complaints
    
    path('orders/', views.order_view, name='order_view'),
    path('create_razorpay_order/', views.create_razorpay_order, name='create_razorpay_order'),
    path('create_order/', views.create_order, name='create_order'),
    path('<int:shop_id>/orders/', views.order_list, name='order_list'),
    path('recommendations/', views.product_recommendations, name='product_recommendations'),
    path('load-more-recommendations/', views.load_more_recommendations, name='load_more_recommendations'),
    path('add-product/', views.add_product, name='add_product'),
    path('filter-products/<int:shop_id>/', views.filter_products, name='filter_products'),
    path('shop/<int:shop_id>/feedback-complaints/', views.view_feedback_complaints, name='view_feedback_complaints'),
    path('request-category/', views.request_category, name='request_category'),
    path('my-category-requests/', views.view_category_requests, name='view_category_requests'),
    path('reply-to-complaint/<int:complaint_id>/', views.reply_to_complaint, name='reply_to_complaint'),
    path('update-cart-item/', views.update_cart_item, name='update_cart_item'),
    
    # Add this new URL pattern for toggling product status
    path('toggle-product/<int:product_id>/', views.toggle_product, name='toggle_product'),
    path('manage-deliveries/', views.manage_order_deliveries, name='manage_deliveries'),
    path('assign-delivery-boy/', views.assign_delivery_boy, name='assign_delivery_boy'),
    
    # Add these URL patterns to the existing urlpatterns list
    path('aquarium-builder/', views.aquarium_builder, name='aquarium_builder'),
    path('aquarium-builder/<int:design_id>/', views.aquarium_builder_edit, name='aquarium_builder_edit'),
    path('api/fish-list/', views.fish_list_api, name='fish_list_api'),
    path('api/plant-list/', views.plant_list_api, name='plant_list_api'),
    path('api/decoration-list/', views.decoration_list_api, name='decoration_list_api'),
    path('api/save-aquarium-design/', views.save_aquarium_design, name='save_aquarium_design'),
    path('api/check-compatibility/', views.check_compatibility, name='check_compatibility'),
    path('delivery-payments/', views.manage_delivery_payments, name='manage_delivery_payments'),
    path('process-delivery-payment/', views.process_delivery_payment, name='process_delivery_payment'),
    path('verify-delivery-payment/', views.verify_delivery_payment, name='verify_delivery_payment'),
    path('complete-payment/', views.complete_payment, name='complete_payment'),
    path('api/calculate-aquarium-price/', views.calculate_aquarium_price, name='calculate_aquarium_price'),
    path('aquarium-pricing/', views.aquarium_pricing, name='aquarium_pricing'),
]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

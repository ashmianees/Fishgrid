from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model  # Use this to get the custom user model
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from user.models import ShopRequest  # Import the ShopRequest model
from shop.models import Category, CategoryRequest, Complaint, Order, ShopDetails, Product
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.db.models import Prefetch

@login_required
def admin_index(request):
    return render(request,'admin/index.html')

def is_admin(user):
    return user.is_authenticated and user.role=='admin'

@login_required
def requested_users_view(request):

    User = get_user_model()  # Get the custom user model
    requested_users = User.objects.filter(shoprequest__isnull=False).distinct().prefetch_related('shoprequest')  # Prefetch related ShopRequest
    return render(request, 'admin/requested_users.html', {'requested_users': requested_users})

@csrf_exempt  # Use this if you want to allow AJAX requests without CSRF token validation
def approve_user(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    
    # Toggle is_shop status
    if user.is_shop:
        user.is_shop = False
        status = 'removed'
        template = 'admin/email_templates/shop_request_rejected.txt'
    else:
        user.is_shop = True
        status = 'approved'
        template = 'admin/email_templates/shop_request_approved.txt'
    
    # Update ShopRequest status
    ShopRequest.objects.filter(user=user).update(status=status)
    
    user.save()  # Save the user object

    # Prepare email context
    context = {
        'user_name': user.get_full_name() or user.username,
        'status': status,
    }

    # Render email content
    html_message = render_to_string(template, context)
    plain_message = strip_tags(html_message)
    subject = f"Update on your shop request: {status.capitalize()}"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    # Send email
    try:
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
        messages.success(request, f'Shop request {status} and email sent successfully.')
    except Exception as e:
        messages.error(request, f'Shop request {status} but failed to send email: {str(e)}')

    return redirect('custom_admin:requested_users')  # Redirect to the requested users view

def view_customers(request):
    User = get_user_model()   # Fetch all customers
    return render(request, 'admin/view_users.html', {'User': User})

@login_required
@user_passes_test(is_admin)
def view_categories(request):
    categories = Category.objects.all()
    return render(request, 'admin/view_categories.html', {'categories': categories})

@login_required
@user_passes_test(is_admin)
def create_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_desc = request.POST.get('category_desc')
        try:
            Category.objects.create(category_name=category_name, category_desc=category_desc)
            messages.success(request, 'Category created successfully.')
            return redirect('custom_admin:view_categories')
        except Exception as e:
            messages.error(request, f'Error creating category: {str(e)}')
    return render(request, 'admin/create_category.html')

@user_passes_test(is_admin)
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_desc = request.POST.get('category_desc')
        
        try:
            # Update the category fields
            category.category_name = category_name
            category.category_desc = category_desc
            
            # Manually call full_clean to trigger validation
            category.full_clean()
            
            # If validation passes, save the category
            category.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('custom_admin:view_categories')
        except ValidationError as e:
            # If there's a validation error, add it to the messages
            for field, errors in e.message_dict.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f'Error updating category: {str(e)}')
    
    return render(request, 'admin/edit_category.html', {'category': category})

@require_POST
@user_passes_test(is_admin)
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    try:
        category.delete()
        messages.success(request, 'Category deleted successfully.')
    except Exception as e:
        messages.error(request, f'Error deleting category: {str(e)}')
    return redirect('custom_admin:view_categories')

@login_required
@user_passes_test(is_admin)
def view_category_requests(request):
    category_requests = CategoryRequest.objects.filter(status='pending')
    return render(request, 'admin/view_category_requests.html', {'category_requests': category_requests})

@login_required
@user_passes_test(is_admin)
def handle_category_request(request, request_id):
    category_request = get_object_or_404(CategoryRequest, id=request_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        context = {
            'shop_owner_name': category_request.user.get_full_name() or category_request.user.username,
            'category_name': category_request.category_name,
            'category_desc': category_request.category_desc,
            'reason': reason
        }
        
        if action == 'approve':
            # Check if category already exists
            existing_category = Category.objects.filter(category_name__iexact=category_request.category_name).first()
            if existing_category:
                category_request.status = 'rejected'
                category_request.reason = f"Category '{existing_category.category_name}' already exists."
                template = 'admin/email_templates/category_request_rejected.txt'
            else:
                Category.objects.create(
                    category_name=category_request.category_name,
                    category_desc=category_request.category_desc
                )
                category_request.status = 'approved'
                template = 'admin/email_templates/category_request_approved.txt'
        elif action == 'reject':
            category_request.status = 'rejected'
            category_request.reason = reason
            template = 'admin/email_templates/category_request_rejected.txt'
        
        category_request.save()
        
        # Send email
        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)
        subject = f"Update on your category request: {category_request.category_name}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [category_request.user.email]
        
        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            messages.success(request, f'Category request {action}d and email sent successfully.')
        except Exception as e:
            messages.error(request, f'Category request {action}d but failed to send email: {str(e)}')
        
    return redirect('custom_admin:view_category_requests')

@user_passes_test(is_admin)
def admin_view_complaints(request):
    complaints = Complaint.objects.all().order_by('-created_at').select_related('user', 'shop').prefetch_related(
        Prefetch('user__order_set', queryset=Order.objects.order_by('-order_date'), to_attr='user_orders')
    )
    
    context = {
        'complaints': complaints,
    }
    return render(request, 'admin/view_complaints.html', context)

@user_passes_test(is_admin)
def admin_reply_to_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    if request.method == 'POST':
        context = {
            'customer_name': complaint.user.get_full_name() or complaint.user.username,
            'shop_name': complaint.shop.shop_name,
            'complaint_id': complaint.id,
        }
        
        html_message = render_to_string('admin/email_templates/complaint_response.txt', context)
        plain_message = strip_tags(html_message)
        
        subject = f"Response to your complaint about {complaint.shop.shop_name}"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [complaint.user.email]

        try:
            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
            complaint.status = 'responded'
            complaint.save()
            messages.success(request, 'Reply sent successfully.')
        except Exception as e:
            messages.error(request, f'Failed to send email: {str(e)}')

    return redirect('custom_admin:view_complaints')

@require_POST
@user_passes_test(is_admin)
def toggle_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_active = not category.is_active
    category.save()
    action = "enabled" if category.is_active else "disabled"
    messages.success(request, f'Category {action} successfully.')
    return redirect('custom_admin:view_categories')

@login_required
def toggle_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.user == product.shop.user:
        product.status = not product.status
        product.save()
        action = "enabled" if product.status else "disabled"
        messages.success(request, f'Product {action} successfully.')
    else:
        messages.error(request, 'You do not have permission to perform this action.')
    return redirect('shop:product_list', shop_id=product.shop.id)

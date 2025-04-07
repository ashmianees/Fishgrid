from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth import get_user_model  # Use this to get the custom user model
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
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
import xlsxwriter
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import datetime

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

@login_required
def view_customers(request):
    User = get_user_model()
    # Fetch all customers (users with role='customer')
    customers = User.objects.filter(role='customer').order_by('id')
    return render(request, 'admin/customer_view.html', {'profiles': customers})

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

@login_required
@user_passes_test(is_admin)
def toggle_user(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    return redirect('custom_admin:view_customers')

@login_required
@user_passes_test(is_admin)
def download_customers_excel(request):
    # Create a new workbook and add a worksheet
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Add a bold format
    bold = workbook.add_format({'bold': True})

    # Write headers
    headers = ['Sl No', 'Name', 'Email', 'Contact', 'House Name', 'City', 'Postal Code', 'Status']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, bold)

    # Get all customers
    User = get_user_model()
    customers = User.objects.filter(role='customer').order_by('id')

    # Write data rows
    for row, customer in enumerate(customers, start=1):
        worksheet.write(row, 0, row)  # Sl No
        worksheet.write(row, 1, f"{customer.first_name} {customer.last_name}")
        worksheet.write(row, 2, customer.email)
        worksheet.write(row, 3, customer.contact)
        worksheet.write(row, 4, customer.house_name)
        worksheet.write(row, 5, customer.city)
        worksheet.write(row, 6, customer.postal_code)
        worksheet.write(row, 7, 'Active' if customer.is_active else 'Inactive')

    # Close the workbook
    workbook.close()

    # Create the HttpResponse with Excel content type
    output.seek(0)
    filename = f'customers_list_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
@user_passes_test(is_admin)
def download_customers_pdf(request):
    # Create the HttpResponse object with PDF headers
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []

    # Get the stylesheet
    styles = getSampleStyleSheet()

    # Add title
    elements.append(Paragraph("Customer List", styles['Heading1']))
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))

    # Get all customers
    User = get_user_model()
    customers = User.objects.filter(role='customer').order_by('id')

    # Prepare data for table
    data = [['Sl No', 'Name', 'Email', 'Contact', 'House Name', 'City', 'Postal Code', 'Status']]
    for i, customer in enumerate(customers, start=1):
        data.append([
            i,
            f"{customer.first_name} {customer.last_name}",
            customer.email,
            customer.contact,
            customer.house_name,
            customer.city,
            customer.postal_code,
            'Active' if customer.is_active else 'Inactive'
        ])

    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)

    # Build PDF document
    doc.build(elements)

    # FileResponse sets the Content-Disposition header
    buffer.seek(0)
    filename = f'customers_list_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

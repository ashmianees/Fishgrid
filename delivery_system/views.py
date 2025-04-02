import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import DeliveryBoyApplication, DeliveryBoy
from shop.models import ShopDetails, OrderDeliveryAssignment, DeliveryBoyPayment
from django.core.mail import send_mail
from django.conf import settings
from django.http import Http404, JsonResponse
from django.utils.crypto import get_random_string
from django.views.decorators.http import require_POST
from django.utils import timezone

def apply_delivery_boy(request):
    if request.method == 'POST':
        application = DeliveryBoyApplication.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            phone=request.POST['phone'],
            address=request.POST['address'],
            vehicle_details=request.POST['vehicle_details'],
            vehicle_type=request.POST['vehicle_type'],
            pincode=request.POST['pincode'],
            license=request.FILES['license']
        )
        messages.success(request, 'Application submitted successfully! Shops will review your application.')
        return redirect('main:index')
    return render(request, 'delivery_system/apply.html')

@login_required
def view_applications(request):
    try:
        shop = get_object_or_404(ShopDetails, user=request.user)
        applications = DeliveryBoyApplication.objects.filter(
            pincode=shop.pincode,
            status='pending'
        )
        return render(request, 'delivery_system/applications.html', {
            'applications': applications,
            'shop': shop
        })
    except Http404:
        messages.error(request, "You need to create a shop first to view delivery applications.")
        return redirect('shop:shop_creation')

@login_required
def approve_application(request, application_id):
    application = get_object_or_404(DeliveryBoyApplication, id=application_id)
    shop = get_object_or_404(ShopDetails, user=request.user)
    
    if request.method == 'POST':
        temp_password = get_random_string(12)
        
        delivery_boy = DeliveryBoy.objects.create(
            name=application.name,
            email=application.email,
            phone=application.phone,
            address=application.address,
            vehicle_details=application.vehicle_details,
            vehicle_type=application.vehicle_type,
            pincode=application.pincode,
            license=application.license
        )
        delivery_boy.set_password(temp_password)
        delivery_boy.save()
        
        delivery_boy.shops.add(shop)
        
        application.status = 'approved'
        application.save()
        
        send_mail(
            'Delivery Boy Account Credentials',
            f'''Your application to be a delivery boy for {shop.shop_name} has been approved!
            
            Your login credentials:
            Email: {application.email}
            Password: {temp_password}
            
            Please change your password when you first login.''',
            settings.DEFAULT_FROM_EMAIL,
            [application.email],
            fail_silently=False,
        )
        
        messages.success(request, f'{application.name} has been approved as a delivery boy.')
        return redirect('delivery_system:view_applications')
    
    return render(request, 'delivery_system/approve_application.html', {
        'application': application
    })

@login_required
def manage_delivery_boys(request):
    try:
        shop = get_object_or_404(ShopDetails, user=request.user)
        delivery_boys = DeliveryBoy.objects.filter(shops=shop, is_active=True)
        active_count = delivery_boys.count()
        
        return render(request, 'delivery_system/manage_delivery_boys.html', {
            'delivery_boys': delivery_boys,
            'active_count': active_count,
            'shop': shop
        })
    except Http404:
        messages.error(request, "You need to create a shop first to manage delivery boys.")
        return redirect('shop:shop_creation')

def delivery_login(request):
    if request.session.get('delivery_boy_id'):
        print("Delivery Boy ID in session:", request.session['delivery_boy_id'])  # Debugging line
        delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
        if delivery_boy.is_first_login:
            return redirect('delivery_system:change_first_password')
        return redirect('delivery_system:delivery_dashboard')
        
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            delivery_boy = DeliveryBoy.objects.get(email=email)
            if delivery_boy.check_password(password):
                request.session['delivery_boy_id'] = delivery_boy.id
                print("Session variable set:", request.session['delivery_boy_id'])  # Debugging line
                
                if delivery_boy.is_first_login:
                    return redirect('delivery_system:change_first_password')
                    
                return redirect('delivery_system:delivery_dashboard')
            else:
                messages.error(request, 'Invalid email or password')
        except DeliveryBoy.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            
    return render(request, 'delivery_system/delivery_login.html')

def delivery_logout(request):
    if 'delivery_boy_id' in request.session:
        del request.session['delivery_boy_id']
    return redirect('delivery_system:delivery_login')

def delivery_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        delivery_boy_id = request.session.get('delivery_boy_id')
        print("Checking delivery boy ID:", delivery_boy_id)  # Debugging line
        if not delivery_boy_id:
            messages.error(request, 'Please login to continue')
            return redirect('delivery_system:delivery_login')
        return view_func(request, *args, **kwargs)
    return wrapper


def change_first_password(request):
    delivery_boy_id = request.session.get('delivery_boy_id')
    if not delivery_boy_id:
        return redirect('delivery_system:delivery_login')
        
    delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)
    
    if not delivery_boy.is_first_login:
        return redirect('delivery_system:delivery_dashboard')
        
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'delivery_system/change_first_password.html')
            
        delivery_boy.set_password(new_password)
        delivery_boy.is_first_login = False
        delivery_boy.save()
        
        messages.success(request, 'Password changed successfully! Please log in again.')
        return redirect('delivery_system:delivery_login')
    
    return render(request, 'delivery_system/change_first_password.html')



def delivery_dashboard(request):
    if 'delivery_boy_id' not in request.session:
        return redirect('delivery_system:delivery_login')
    
    delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
    
    # Get today's date
    today = timezone.now().date()
    
    # Get count of today's deliveries
    today_deliveries = OrderDeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        assigned_at__date=today,
        status='delivered'
    ).count()
    
    # Get count of all completed deliveries
    completed_deliveries = OrderDeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        status='delivered'
    ).count()
    
    # Get count of pending assignments
    pending_assignments = OrderDeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        status__in=['pending', 'accepted', 'picked_up']
    ).count()
    
    # Calculate total earnings from successful payments
    from django.db.models import Sum
    total_earnings = DeliveryBoyPayment.objects.filter(
        delivery_boy=delivery_boy,
        status='success'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Calculate earnings per delivery (assuming ₹100 per delivery)
    delivery_earnings = completed_deliveries * 100
    
    context = {
        'delivery_boy': delivery_boy,
        'today_deliveries': today_deliveries,
        'completed_deliveries': completed_deliveries,
        'pending_assignments': pending_assignments,
        'delivery_earnings': delivery_earnings,
        'total_earnings': total_earnings
    }
    
    return render(request, 'delivery_system/delivery_dashboard.html', context)


def toggle_availability(request):
    if request.method == 'POST':
        delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
        delivery_boy.is_active = not delivery_boy.is_active
        delivery_boy.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


def update_order_status(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')
        # Add logic to update order status
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@delivery_login_required
def delivery_profile(request):
    delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
    return render(request, 'delivery_system/delivery_profile.html', {'delivery_boy': delivery_boy})

@delivery_login_required
def edit_profile(request):
    delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
    return render(request, 'delivery_system/edit_profile.html', {'delivery_boy': delivery_boy})

@delivery_login_required
def update_profile(request):
    if request.method == 'POST':
        delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
        
        # Update allowed fields
        delivery_boy.phone = request.POST.get('phone')
        delivery_boy.vehicle_type = request.POST.get('vehicle_type')
        delivery_boy.vehicle_details = request.POST.get('vehicle_details')
        
        # Handle license update if a new file is uploaded
        if 'license' in request.FILES:
            delivery_boy.license = request.FILES['license']
        
        try:
            delivery_boy.save()
            messages.success(request, 'Profile updated successfully!')
        except Exception as e:
            messages.error(request, 'Error updating profile. Please try again.')
            
        return redirect('delivery_system:delivery_profile')
    
    return redirect('delivery_system:edit_profile')

@login_required
@require_POST
def remove_delivery_boy(request):
    try:
        delivery_boy_id = request.POST.get('delivery_boy_id')
        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id)
        
        # Get the current shop
        shop = get_object_or_404(ShopDetails, user=request.user)
        
        # Remove the shop association and set is_active to False
        if delivery_boy.shops.filter(id=shop.id).exists():
            delivery_boy.shops.remove(shop)
            delivery_boy.is_active = False
            delivery_boy.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Delivery boy removed successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Delivery boy is not associated with this shop'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Error removing delivery boy. Please try again.'
        }, status=500)


def view_assigned_work(request):
    try:
        delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
        
        assignments = OrderDeliveryAssignment.objects.filter(
            delivery_boy=delivery_boy,
            status__in=['pending', 'accepted', 'picked_up']
        ).select_related('order', 'order__shop', 'order__address')
        
        context = {
            'assignments': assignments,
            'delivery_boy': delivery_boy
        }
        
        return render(request, 'delivery_system/view_assignedWork.html', context)
        
    except Exception as e:
        messages.error(request, "Error accessing assignments. Please try again.")
        print(f"Error in view_assigned_work: {str(e)}")  # Log the error
        return redirect('delivery_system:delivery_dashboard')


@require_POST
def update_delivery_status(request):
    try:
        assignment_id = request.POST.get('assignment_id')
        new_status = request.POST.get('status')
        
        delivery_boy_id = request.session.get('delivery_boy_id')
        assignment = get_object_or_404(
            OrderDeliveryAssignment, 
            id=assignment_id,
            delivery_boy_id=delivery_boy_id
        )
        
        # Update both assignment and order status
        assignment.status = new_status
        assignment.order.status = new_status
        
        if new_status == 'picked_up':
            # Generate OTP
            otp = str(random.randint(100000, 999999))
            assignment.otp = otp
            
            # Update order status to out_for_delivery
            assignment.status = 'out_for_delivery'
            assignment.order.status = 'out_for_delivery'
            
            # Send OTP to customer via email
            send_mail(
                'Your OTP for Order Delivery',
                f'Your OTP for order #{assignment.order.id} is: {otp}. Please enter this OTP to confirm delivery.',
                settings.DEFAULT_FROM_EMAIL,
                [assignment.order.user.email],
                fail_silently=False,
            )
        
        # Save both models
        assignment.save()
        assignment.order.save()
        
        if new_status == 'delivered':
            assignment.order.is_delivered = True
            assignment.order.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Delivery status updated successfully'
        })
        
    except Exception as e:
        print(f"Error in update_delivery_status: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@require_POST
def verify_otp(request):
    try:
        assignment_id = request.POST.get('assignment_id')
        entered_otp = request.POST.get('otp')
        
        # Add delivery boy session check
        delivery_boy_id = request.session.get('delivery_boy_id')
        if not delivery_boy_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Unauthorized access'
            }, status=401)
        
        assignment = get_object_or_404(
            OrderDeliveryAssignment, 
            id=assignment_id,
            delivery_boy_id=delivery_boy_id
        )
        
        if not assignment.otp:
            return JsonResponse({
                'status': 'error',
                'message': 'No OTP found for this order. Please ensure order is picked up first.'
            }, status=400)
        
        if assignment.otp == entered_otp:
            return JsonResponse({
                'status': 'success',
                'message': 'OTP verified successfully'
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid OTP. Please try again.'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

def work_history(request):
    if 'delivery_boy_id' not in request.session:
        return redirect('delivery_system:delivery_login')
    
    delivery_boy = get_object_or_404(DeliveryBoy, id=request.session['delivery_boy_id'])
    
    # Get completed deliveries
    completed_deliveries = OrderDeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        status='delivered'
    ).select_related('order', 'order__shop').order_by('-assigned_at')
    
    context = {
        'delivery_boy': delivery_boy,
        'completed_deliveries': completed_deliveries
    }
    
    return render(request, 'delivery_system/work_history.html', context)
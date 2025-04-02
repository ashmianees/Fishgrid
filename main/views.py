from django.shortcuts import render,redirect
from user.models import ShopRequest, User
from django.contrib.auth import authenticate, login,logout
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from shop.models import ShopDetails
from fish_grid import settings 

def index(request):
    return render(request,'main/index.html')

def login_view(request):
    if request.user.is_authenticated:
        user=request.user
        if user.role=='customer':
            return redirect('user:indexfish')
        if user.role=='admin':
            return redirect('custom_admin:admin_index')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            if user.role=='customer':
                return redirect('user:indexfish')
            if user.role=='admin':
                return redirect('custom_admin:admin_index') # Redirect to home page after login
    return render(request, 'main/login.html')

def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        con_password = request.POST.get('con_password')

        # Validate all required fields are present
        if not all([first_name, last_name, email, password, con_password]):
            messages.error(request, "All fields are required.")
            return render(request, 'main/register_page.html')

        # Validate passwords match
        if password != con_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'main/register_page.html')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return render(request, 'main/register_page.html')

        # Create user
        try:
            user = User.objects.create_user(
                username=email, 
                email=email, 
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            # Log the user in
            login(request, user)

            return redirect('main:login_page')
              # Redirect to home page after registration
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('main:login_page')

    return render(request, 'main/register_page.html')
def user_logout(request):
    logout(request)
    response = redirect('main:login_page')
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response

def shop_login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            # Check if the user has an approved shop request
            shop_request = ShopRequest.objects.filter(user=user, status='approved').first()
            if shop_request:
                login(request, user)
                # Check if the user has a shop associated
                shop = ShopDetails.objects.filter(user=user).first()
                if shop:
                    request.session['shop_id'] = shop.id
                    return redirect('shop:shop_dashboard')
                else:
                    # Redirect to shop creation page
                    return redirect('shop:shop_creation')
            else:
                messages.error(request, "Your shop request has not been approved yet.")
        else:
            messages.error(request, "Invalid credentials.")
    return render(request, 'main/shop_login.html')
def check_shop_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        has_shop = user is not None and ShopDetails.objects.filter(user=user).exists()
        return JsonResponse({'has_shop': has_shop})
    return JsonResponse({'has_shop': False})


# Adjust the path as necessary

def logout_view(request):
    logout(request)
    del request.session['user_role']  # Clear specific session data
    return redirect('main:login_page')  # Redirect to login page

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
from user.models import User, PasswordResetToken
from django.utils import timezone
from django.contrib.auth import update_session_auth_hash

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            token = PasswordResetToken.objects.create(user=user)
            reset_link = request.build_absolute_uri(reverse('main:reset_password', args=[token.token]))
            
            send_mail(
                'Password Reset for FishGrid',
                f'Click the following link to reset your password: {reset_link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            messages.success(request, "Password reset link has been sent to your email.")
            return redirect('main:login_page')
        except User.DoesNotExist:
            messages.error(request, "No user found with this email address.")
    
    return render(request, 'main/forgot_password.html')

def reset_password(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        if not reset_token.is_valid():
            messages.error(request, "This password reset link has expired.")
            return redirect('main:login_page')
        
        if request.method == 'POST':
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')
            
            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
            else:
                user = reset_token.user
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                reset_token.delete()  # Remove the used token
                messages.success(request, "Your password has been reset successfully.")
                return redirect('main:login_page')
        
        return render(request, 'main/reset_password.html', {'token': token})
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "Invalid password reset link.")
        return redirect('main:login_page')
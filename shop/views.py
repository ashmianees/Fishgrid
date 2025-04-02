from django.http import Http404, JsonResponse, HttpResponseBadRequest
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product, Feedback, Address, Order, Complaint, AquariumPricing
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from shop.models import Payment
import razorpay
from django.db.models import Q
from django.utils import timezone

from .models import Cart, CartItem, Category, Complaint, Wishlist
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Product, Feedback, ShopDetails

from .models import Product
from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q
from .models import Cart, CartItem, Category, Complaint
from django.http import HttpResponseBadRequest
from .models import Product, Feedback, ShopDetails

from .models import Product
from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q
from .models import Cart, CartItem, Category, Complaint
from django.http import HttpResponseBadRequest

import logging
import json
from delivery_system.models import DeliveryBoyApplication  # Add this import
from .models import DeliveryBoyPayment
from delivery_system.models import DeliveryBoy  # Add this import
from .models import (
    WaterType, FishSpecies, PlantSpecies, Decoration, 
    AquariumDesign, AquariumFish, AquariumPlant, AquariumDecoration,
    FishCompatibility
)
from datetime import datetime
from .models import OrderDeliveryAssignment  # Add this import

logger = logging.getLogger(__name__)

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def shop_product_views(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    categories = Category.objects.filter(is_active=True)
    selected_category = request.GET.get('category', '')
    
    # Filter out expired products
    products = Product.objects.filter(
        shop_id=shop_id,
        categories__is_active=True,
        status=True
    ).exclude(
        Q(expiry_date__isnull=False) & Q(expiry_date__lte=timezone.now().date())
    )
    
    if selected_category and selected_category.isdigit():
        products = products.filter(categories__id=selected_category)
    
    search_query = request.GET.get('search', '')
    if search_query:
        products = products.filter(
            Q(product_name__icontains=search_query) |
            Q(product_description__icontains=search_query)
        )
    
    context = {
        'shop': shop,
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'search_query': search_query,
    }
    return render(request, 'shop/shop_product_views.html', context)

def view_singleproduct(request, product_id, shop_id):
    product = get_object_or_404(Product, id=product_id, shop__id=shop_id, categories__is_active=True)
    shop = product.shop
    
    # If user is not the shop owner and product is expired, return 404
    if request.user != shop.user and product.expiry_date and product.expiry_date <= timezone.now().date():
        raise Http404("Product not found")
        
    category = product.categories
    feedback = Feedback.objects.filter(product=product).order_by('-created_at')
    is_in_wishlist = False
    has_purchased = False

    if request.user.is_authenticated:
        is_in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        has_purchased = Order.objects.filter(
            user=request.user,
            order_details__product=product
        ).exists()

    context = {
        'product': product,
        'category': category,
        'shop': shop,
        'feedback': feedback,
        'is_in_wishlist': is_in_wishlist,
        'has_purchased': has_purchased,
    }
    return render(request, 'shop/view_singleproduct.html', context)

from django.shortcuts import get_object_or_404, redirect
from .models import Product, Feedback, ShopDetails

from .models import Product
from .models import Product, ShopDetails
from pyexpat.errors import messages
from django.shortcuts import render, redirect, get_object_or_404
from shop.models import ShopDetails, Product,Feedback, Address,Order, Complaint
from shop.models import Payment
import razorpay
from django.db.models import Q

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
def shop_index(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()  # Get the first shop detail
    else:
        shop_detail = None  # Handle the case where no shop details exist

    return render(request, 'shop/shop_index.html', {'shop_detail': shop_detail})  # Pass shop_detail to the template

@login_required
def shop_dashboard(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()
        # Get delivery boy statistics
        delivery_boys_count = shop_detail.delivery_boys.filter(is_active=True).count()
        pending_applications_count = DeliveryBoyApplication.objects.filter(
            pincode=shop_detail.pincode,
            status='pending'
        ).count()
    else:
        shop_detail = None
        delivery_boys_count = 0
        pending_applications_count = 0

    context = {
        'shop_detail': shop_detail,
        'delivery_boys_count': delivery_boys_count,
        'pending_applications_count': pending_applications_count,
    }
    return render(request, 'shop/shop_index.html', context)

@login_required
def shop_creation(request):
    if request.method == 'POST':
        shop_name = request.POST.get('shop_name')
        shop_location = request.POST.get('shop_location')
        pincode = request.POST.get('pincode')
        mobile_number = request.POST.get('mobile_number')
        shop_image = request.FILES.get('shop_image')

        # Save the shop details to the database
        ShopDetails.objects.create(
            user=request.user,  # Associate the shop with the logged-in user
            shop_name=shop_name,
            shop_location=shop_location,
            pincode=pincode,
            mobile_number=mobile_number,
            shop_image=shop_image
        )

        return redirect('shop:shop_dashboard')  # Redirect to the shop dashboard after successful creation

    return render(request, 'shop/shop_creation.html') 


@login_required
def shop_profile_view(request):
    shop_details = ShopDetails.objects.filter(user=request.user)

    if shop_details.exists():
        shop_detail = shop_details.first()  # Get the first shop detail
    else:
        shop_detail = None  # Handle the case where no shop details exist

    return render(request, 'shop/shop_profile.html', {'shop_detail': shop_detail})

@login_required
def shop_details_edit(request, shop_id):
    # Retrieve the shop details for the given shop_id
    shop_details = get_object_or_404(ShopDetails, id=shop_id)

    if request.method == 'POST':
        # Get the updated values from the form
        shop_name = request.POST.get('shop_name')
        shop_location = request.POST.get('shop_location')
        owner_name = request.POST.get('owner_name')  # This is for display purposes
        mobile_number = request.POST.get('mobile_number')
        shop_image = request.FILES.get('shop_image')

        # Update the shop details
        shop_details.shop_name = shop_name
        shop_details.shop_location = shop_location
        shop_details.mobile_number = mobile_number

        # Update the shop image only if a new one is provided
        if shop_image:
            shop_details.shop_image = shop_image

        # Save the updated shop details to the database
        shop_details.save()

        # Redirect to the shop dashboard after successful update
        return redirect('shop_dashboard')  # Adjust this to your actual shop dashboard URL name

    # Render the edit shop template with the current shop details
    return render(request, 'shop/shop_details_edit.html', {'shop_details': shop_details})

from django.shortcuts import render, redirect, get_object_or_404

from .models import Cart, CartItem, Category, Complaint

def category_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, pk=shop_id)
    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'shop_detail': shop,
        'categories': categories,
    }
    return render(request, 'shop/shop_category.html', context)

def category_add(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_description = request.POST.get('category_description')  # Ensure this matches the form field name
        
        # Check if category_description is not None or empty
        if category_name and category_description:  # Ensure both fields are provided
            Category.objects.create(category_name=category_name, category_desc=category_description)
            return redirect('shop:shop_category')  # Redirect to the category list after adding
        else:
            # Handle the case where the fields are empty
            return render(request, 'shop/shop_category.html', {'error': 'Both fields are required.'})

    return render(request, 'shop/shop_category.html')  # Render the form if not a POST request

@csrf_exempt
def category_edit(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category_name = request.POST.get('category_name').strip()
        category_description = request.POST.get('category_description').strip()

        # Get the category instance to edit
        category = get_object_or_404(Category, id=category_id)

        # Update the category fields
        category.category_name = category_name
        category.category_desc = category_description
        category.save()

        # Redirect to the category page after successful update
        return JsonResponse({'status': 'success'}, status=200)

    return JsonResponse({'status': 'failed'}, status=400)

@require_POST
def category_delete(request):
    category_id = request.POST.get('id')
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return JsonResponse({'success': True})



from django.http import HttpResponseBadRequest


def product_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, pk=shop_id)
    products = Product.objects.filter(shop=shop)
    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'shop': shop,
        'products': products,
        'categories': categories,
    }
    return render(request, 'shop/shop_product.html', context)

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'shop/product_detail.html', {'product': product})


def product_add(request):
    try:
        shop_details = ShopDetails.objects.get(user=request.user)
    except ShopDetails.DoesNotExist:
        return HttpResponseBadRequest("Shop details not found for the user.")
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        description = request.POST.get('product_description')
        price = request.POST.get('product_price')
        size = request.POST.get('product_size')  # New field for size
        quantity = request.POST.get('product_quantity') 
        category_id = request.POST.get('product_category')  # New field for category
        image = request.FILES.get('product_image')
        expiry_date = request.POST.get('expire_date')  # Get expiry date from form
        
        if product_name and description and price and category_id:  # Basic validation
            category = Category.objects.get(id=category_id)  # Fetch the category by id
            
            # Create product with optional expiry date
            product = Product.objects.create(
                product_name=product_name,
                product_description=description,
                price=price,
                size=size,  # Include size
                quantity=quantity,
                categories=category,  # Associate with the category instance
                image=image,
                shop_id=shop_details.id,
                expiry_date=expiry_date if expiry_date else None  # Set expiry date if provided
            )
            return redirect('shop:product_list', shop_id=shop_details.id)  # Redirect to the product list with shop_id

    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    return render(request, 'shop/product_add.html', {'categories': categories})

def product_edit(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        product = get_object_or_404(Product, id=product_id)

        product_name = request.POST.get('product_name')
        description = request.POST.get('product_description')
        price = request.POST.get('product_price')
        size = request.POST.get('product_size')
        quantity = request.POST.get('product_quantity')
        add_quantity = int(request.POST.get('add_quantity', 0))  # Get the additional quantity
        category_id = request.POST.get('product_category')
        image = request.FILES.get('product_image')
        expiry_date = request.POST.get('expire_date')

        if product_name and description and price and category_id:
            category = Category.objects.get(id=category_id)
            product.product_name = product_name
            product.product_description = description
            product.price = price
            product.size = size
            product.quantity = int(quantity) + add_quantity
            product.categories = category
            product.expiry_date = expiry_date if expiry_date else None
            if image:
                product.image = image
            product.save()

            return redirect('shop:product_list', shop_id=product.shop.id)

    categories = Category.objects.filter(is_active=True)
    return render(request, 'shop/shop_product.html', {'categories': categories})

def product_disable(request):
    product_id = request.GET.get('id')
    product = get_object_or_404(Product, pk=product_id)
    product.status = False  # Disable the product
    product.save()
    return redirect('shop:product_list')

from django.contrib import messages

@login_required
def add_to_cart(request, product_id, shop_id):
    logger.info(f"Add to cart called for product {product_id} and shop {shop_id}")
    if request.method == 'POST':
        try:
            cart, created = Cart.objects.get_or_create(user=request.user)
            product = get_object_or_404(Product, id=product_id)
            shop = get_object_or_404(ShopDetails, id=shop_id)

            quantity = int(request.POST.get('quantity', 1))
            logger.info(f"Attempting to add {quantity} of product {product.product_name} to cart")

            if quantity > product.quantity:
                logger.warning(f"Requested quantity {quantity} exceeds available stock {product.quantity}")
                messages.error(request, f"Sorry, only {product.quantity} items are available.")
                return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)

            cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, shop=shop)

            if not created:
                cart_item.quantity += quantity
                logger.info(f"Updated existing cart item. New quantity: {cart_item.quantity}")
            else:
                cart_item.quantity = quantity
                logger.info(f"Created new cart item with quantity: {quantity}")
            cart_item.save()

            logger.info(f"Successfully added {quantity} {product.product_name}(s) to cart")
            messages.success(request, f"{quantity} {product.product_name}(s) added to cart.")
        except Product.DoesNotExist:
            logger.error(f"Product with id {product_id} not found")
            messages.error(request, "Product not found.")
        except ShopDetails.DoesNotExist:
            logger.error(f"Shop with id {shop_id} not found")
            messages.error(request, "Shop not found.")
        except Exception as e:
            logger.error(f"Error adding product to cart: {str(e)}")
            messages.error(request, f"Error adding product to cart: {str(e)}")

    return redirect('shop:view_cart')

@login_required
def view_cart(request):
    cart = Cart.objects.filter(user=request.user).first()
    if cart:
        cart_items = CartItem.objects.filter(cart=cart)
        total_price = sum(item.total_price() for item in cart_items)
        return render(request, 'shop/cart.html', {'items': cart_items, 'total_price': total_price})
    else:
        return render(request, 'shop/cart.html', {'items': [], 'total_price': 0})

def remove_from_cart(request, item_id):
    if request.method == 'POST':
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.delete()
        return redirect('shop:view_cart')





def submit_feedback(request, product_id, shop_id):
    if request.method == 'POST':
        shop = get_object_or_404(ShopDetails, id=shop_id)
        product = get_object_or_404(Product, id=product_id, shop=shop)
        rating = request.POST['rating']
        comment = request.POST['comment']
        Feedback.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            comment=comment
        )
        messages.success(request, 'Your feedback has been submitted successfully.')
        return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)
    return redirect('shop:view_singleproduct', product_id=product_id, shop_id=shop_id)

from .models import Product

def check_product_exists(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        shop_id = request.POST.get('shop_id')  # Get the shop ID from the request
        exists = Product.objects.filter(product_name=product_name, shop_id=shop_id).exists()  # Check in the specific shop
        return JsonResponse({'exists': exists})
    return JsonResponse({'exists': False})

from django.shortcuts import get_object_or_404
from .models import Product, ShopDetails

@login_required
def add_product(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        shop_id = request.POST.get('shop_id')  # Get the shop ID from the request

        # Check if the product already exists in the shop
        if Product.objects.filter(product_name=product_name, shop_id=shop_id).exists():
            return JsonResponse({'status': 'error', 'message': 'Product already exists in this shop.'})

        # Proceed to create the product if it does not exist
        shop = get_object_or_404(ShopDetails, id=shop_id)
        Product.objects.create(
            product_name=product_name,
            shop=shop,
            # Add other fields as necessary
        )
        return JsonResponse({'status': 'success', 'message': 'Product added successfully.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

from django.shortcuts import render, redirect, get_object_or_404

from .models import Address, Order, Cart, OrderDetails  # Ensure all necessary models are imported

@login_required
def checkout(request):
    cart = Cart.objects.filter(user=request.user).first()
    if not cart or cart.items.count() == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('shop:view_cart')

    addresses = Address.objects.filter(user=request.user)

    if request.method == 'POST':
        selected_address_id = request.POST.get('selected_address')
        
        if not selected_address_id:
            return JsonResponse({'status': 'error', 'message': 'Please select an address or add a new one.'})

        address = get_object_or_404(Address, id=selected_address_id, user=request.user)

        # Create the order
        order = Order.objects.create(
            user=request.user,
            shop=cart.items.first().shop,  # Assuming all items are from the same shop
            address=address,
            total_price=cart.total_price(),
            status='Pending'
        )

        # Create order details for each item in the cart
        for item in cart.items.all():
            OrderDetails.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            
            # Update product quantity
            product = item.product
            product.quantity -= item.quantity
            product.save()

        # Clear the cart
        cart.items.all().delete()

        return JsonResponse({'status': 'success', 'message': 'Your order has been placed successfully!'})

    context = {
        'cart': cart,
        'addresses': addresses,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }
    return render(request, 'shop/checkout.html', context)

from django.shortcuts import render, redirect, get_object_or_404
from .models import Address  # Ensure this import is correct

@login_required  # Ensure the user is logged in
def add_new_address(request):
    if request.method == 'POST':
        new_name = request.POST.get('new_name')
        new_address = request.POST.get('new_address')
        new_phone = request.POST.get('new_phone')
        new_landmark = request.POST.get('new_landmark')
        new_pincode = request.POST.get('new_pincode')

        # Create and save the new address with the logged-in user
        address = Address.objects.create(
            user=request.user,  # Associate the address with the logged-in user
            name=new_name,
            address=new_address,
            phone=new_phone,
            landmark=new_landmark,
            pincode=new_pincode
        )

        return JsonResponse({
            'status': 'success',
            'message': 'New address added successfully!',
            'address_id': address.id,
            'name': address.name,
            'address': address.address,
            'phone': address.phone,
            'pincode': address.pincode
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

from django.shortcuts import render
from .models import Order


def order_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date', '-order_time')
    context = {
        'orders': orders,
        'category': {'shop_name': 'Fish Grid'},  # You can replace this with actual shop name logic if needed
    }
    return render(request, 'shop/Orders_view.html', context)

@login_required
def submit_complaint(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    
    # Check if the user has made a purchase from this shop
    has_purchased = Order.objects.filter(user=request.user, shop=shop).exists()

    if not has_purchased:
        messages.warning(request, "You can only submit a complaint if you have made a purchase from this shop.")
        return render(request, 'shop/complaints.html', {'shop': shop, 'has_purchased': has_purchased})

    if request.method == 'POST':
        complaint_text = request.POST.get('complaint_text')
        if complaint_text:
            Complaint.objects.create(
                user=request.user,
                shop=shop,
                complaint_text=complaint_text
            )
            messages.success(request, 'Your complaint has been submitted successfully.')
            return redirect('shop:shop_product_views', shop_id=shop.id)
        else:
            messages.error(request, 'Please enter your complaint.')

    return render(request, 'shop/complaints.html', {'shop': shop, 'has_purchased': has_purchased})

@login_required
def view_complaints(request, shop_id):
    # Fetch the shop details
    shop = get_object_or_404(ShopDetails, id=shop_id)
    
    # Fetch complaints related to the shop
    complaints = Complaint.objects.filter(shop=shop).order_by('-created_at')  # Order by creation date

    return render(request, 'shop/view_complaints.html', {'shop': shop, 'complaints': complaints})

@login_required
def order_success(request):
    return render(request, 'shop/order_success.html')


@login_required
def create_razorpay_order(request):
    if request.method == 'POST':
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            return JsonResponse({'status': 'error', 'message': 'Your cart is empty.'})

        total_price = cart.total_price()
        razorpay_order = razorpay_client.order.create({
            'amount': int(total_price * 100),  # Razorpay expects amount in paise
            'currency': 'INR',
            'payment_capture': '1'
        })

        return JsonResponse({
            'status': 'success',
            'order_id': razorpay_order['id'],
            'amount': razorpay_order['amount'],
        })

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def create_order(request):
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        razorpay_order_id = request.POST.get('order_id')
        signature = request.POST.get('signature')

        # Verify the payment signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return JsonResponse({'status': 'error', 'message': 'Invalid payment signature'})

        # Create the order
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            return JsonResponse({'status': 'error', 'message': 'Your cart is empty.'})

        # Get the shop from the first item in the cart
        first_item = cart.items.first()
        if not first_item:
            return JsonResponse({'status': 'error', 'message': 'No items in cart.'})

        shop = first_item.shop

        address_id = request.POST.get('selected_address')
        address = get_object_or_404(Address, id=address_id, user=request.user)

        order = Order.objects.create(
            user=request.user,
            shop=shop,
            address=address,
            total_price=cart.total_price(),
            status='Paid'
        )

        for item in cart.items.all():
            # Check if there's enough stock
            if item.quantity > item.product.quantity:
                order.delete()  # Delete the order if there's not enough stock
                return JsonResponse({'status': 'error', 'message': f'Not enough stock for {item.product.product_name}'})

            OrderDetails.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
            logger.info(f"Created OrderDetails for order {order.id}, product {item.product.id}, quantity {item.quantity}")

            # Update product quantity
            product = item.product
            product.quantity -= item.quantity
            product.save()
            logger.info(f"Updated stock for product {product.id}. New quantity: {product.quantity}")

        # Create payment record
        Payment.objects.create(
            order=order,
            payment_id=payment_id,
            amount=cart.total_price(),
            status='Completed'
        )

        # Clear the cart
        cart.delete()

        return JsonResponse({'status': 'success', 'message': 'Order placed successfully!'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def filter_products(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id)
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    # Base query for products in this shop
    products = Product.objects.filter(shop=shop)
    
    # If user is not the shop owner, filter out disabled and expired products
    if request.user != shop.user:
        products = products.filter(
            status=True
        ).exclude(
            Q(expiry_date__isnull=False) & Q(expiry_date__lte=timezone.now().date())
        )
    
    # Apply search filter if provided
    if search:
        products = products.filter(
            Q(product_name__icontains=search) |
            Q(product_description__icontains=search)
        )
    
    # Apply category filter if provided
    if category:
        products = products.filter(categories__id=category)
    
    products_data = [
        {
            'id': product.id,
            'name': product.product_name,
            'description': product.product_description,
            'price': str(product.price),
            'image': product.image.url if product.image else None,
            'shop_id': shop.id,
            'status': product.status,
            'is_expired': bool(product.expiry_date and product.expiry_date <= timezone.now().date()),
            'expiry_date': product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else None
        }
        for product in products
    ]
    
    return JsonResponse({'products': products_data})

@login_required
def order_list(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id, user=request.user)
    orders = Order.objects.filter(shop=shop).order_by('-order_date', '-order_time')
    context = {
        'shop_detail': shop,
        'orders': orders,
    }
    return render(request, 'shop/order_list.html', context)

from .utils.ml_utils import get_product_recommendations, update_model_with_new_orders
from django.template.loader import render_to_string


@login_required
def product_recommendations(request):
    update_model_with_new_orders()
    shop = ShopDetails.objects.filter(user=request.user).first()
    if shop:
        recommended_products = get_product_recommendations(shop.id, limit=12)
    else:
        recommended_products = []
    context = {
        'recommended_products': recommended_products,
        'shop_detail': shop,  # Add this line
    }
    return render(request, 'shop/product_recommendations.html', context)

@login_required
def load_more_recommendations(request):
    offset = int(request.GET.get('offset', 0))
    shop = ShopDetails.objects.get(user=request.user)
    recommended_products = get_product_recommendations(shop.id, offset=offset, limit=6)
    html = render_to_string('shop/product_card.html', {'recommended_products': recommended_products})
    return JsonResponse({'html': html, 'count': len(recommended_products)})

@login_required
def add_product(request):
    try:
        shop_details = ShopDetails.objects.get(user=request.user)
    except ShopDetails.DoesNotExist:
        return HttpResponseBadRequest("Shop details not found for the user.")
    
    product_name = request.GET.get('product_name', '')
    
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        product_description = request.POST.get('product_description')
        price = request.POST.get('price')
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')
        
        try:
            category = Category.objects.get(id=category_id)
            Product.objects.create(
                shop=shop_details,
                product_name=product_name,
                product_description=product_description,
                price=price,
                size=size,
                quantity=quantity,
                categories=category,
                image=image
            )
            return redirect('shop:product_list', shop_id=shop_details.id)
        except Exception as e:
            return HttpResponseBadRequest(str(e))

    categories = Category.objects.filter(is_active=True)  # Only fetch active categories
    context = {
        'categories': categories,
        'shop_details': shop_details,
        'product_name': product_name
    }
    return render(request, 'shop/add_product.html', context)

from django.db.models import Prefetch

@login_required
def view_feedback_complaints(request, shop_id):
    shop = get_object_or_404(ShopDetails, id=shop_id, user=request.user)
    
    # Fetch feedback for all products of this shop
    feedback = Feedback.objects.filter(product__shop=shop).order_by('-created_at').select_related('user', 'product').prefetch_related(
        Prefetch('user__order_set', queryset=Order.objects.filter(shop=shop).order_by('-order_date'), to_attr='shop_orders')
    )
    
    # Fetch complaints for this shop
    complaints = Complaint.objects.filter(shop=shop).order_by('-created_at').select_related('user').prefetch_related(
        Prefetch('user__order_set', queryset=Order.objects.filter(shop=shop).order_by('-order_date'), to_attr='shop_orders')
    )
    
    context = {
        'shop': shop,
        'shop_detail': shop,  # Add this line
        'feedback': feedback,
        'complaints': complaints,
    }
    return render(request, 'shop/view_feedback_complaints.html', context)


from .models import CategoryRequest

@login_required
def request_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        category_desc = request.POST.get('category_desc')
        CategoryRequest.objects.create(
            user=request.user,
            category_name=category_name,
            category_desc=category_desc
        )
        messages.success(request, 'Category request submitted successfully!')
        return redirect('shop:shop_index')
    return render(request, 'shop/request_category.html')

@login_required
def view_category_requests(request):
    category_requests = CategoryRequest.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'shop/view_category_requests.html', {'category_requests': category_requests})

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.shortcuts import redirect, get_object_or_404
from .models import Complaint

@login_required
def reply_to_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, shop__user=request.user)
    if request.method == 'POST':
        context = {
            'customer_name': complaint.user.get_full_name() or complaint.user.username,
            'shop_name': complaint.shop.shop_name,
            'complaint_id': complaint.id,
        }
        
        html_message = render_to_string('shop/email_templates/complaint_response.txt', context)
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

    return redirect('shop:view_feedback_complaints', shop_id=complaint.shop.id)

import logging
import traceback
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CartItem, Cart
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

@require_POST
def update_cart_item(request):
    try:
        item_id = request.POST.get('item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        logger.info(f"Updating cart item: {item_id} with quantity: {quantity}")
        
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        
        if quantity > cart_item.product.quantity:
            return JsonResponse({'success': False, 'error': 'Not enough stock available.'})
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'quantity': cart_item.quantity,
            'total_price': f"{cart_item.total_price():.2f}"
        })
    except CartItem.DoesNotExist:
        logger.error(f"Cart item not found: {item_id}")
        return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)
    except ValueError as e:
        logger.error(f"Invalid quantity value: {e}")
        return JsonResponse({'success': False, 'error': 'Invalid quantity value.'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in update_cart_item: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': 'An unexpected error occurred.'}, status=500)
    
@require_POST
def remove_from_cart(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        
        # Calculate the new total price
        cart = Cart.objects.get(user=request.user)
        new_total_price = sum(item.total_price() for item in cart.items.all())
        
        return JsonResponse({
            'success': True, 
            'new_total_price': f"{new_total_price:.2f}",
            'items_count': cart.items.count()
        })
    except CartItem.DoesNotExist:
        logger.error(f"Cart item not found: {item_id}")
        return JsonResponse({'success': False, 'error': 'Cart item not found.'}, status=404)
    except Exception as e:
        logger.error(f"Error removing item from cart: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred while removing the item.'}, status=500)

@require_POST
def toggle_wishlist(request, product_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'User not authenticated'}, status=401)

    try:
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return JsonResponse({'success': True, 'action': 'removed'})
        else:
            return JsonResponse({'success': True, 'action': 'added'})

    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user,
        product__categories__is_active=True,
        product__status=True
    ).select_related('product')
    return render(request, 'shop/wishlist.html', {'wishlist_items': wishlist_items})

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
def manage_order_deliveries(request):
    shop = get_object_or_404(ShopDetails, user=request.user)
    
    # Get unassigned and undelivered orders
    unassigned_orders = Order.objects.filter(
        shop=shop,
        is_delivered=False,
        delivery_assignment__isnull=True
    ).order_by('-order_date', '-order_time')
    
    # Get available delivery boys
    delivery_boys = shop.delivery_boys.filter(is_active=True)
    
    # Get current assignments
    pending_deliveries = OrderDeliveryAssignment.objects.filter(
        order__shop=shop,
        order__is_delivered=False,
        status__in=['pending', 'accepted', 'picked_up']
    ).select_related('order', 'delivery_boy').order_by('-assigned_at')
    
    context = {
        'unassigned_orders': unassigned_orders,
        'pending_deliveries': pending_deliveries,
        'delivery_boys': delivery_boys,
    }
    return render(request, 'shop/manage_deliveries.html', context)

@login_required
@require_POST
def assign_delivery_boy(request):
    try:
        order_id = request.POST.get('order_id')
        delivery_boy_id = request.POST.get('delivery_boy_id')
        
        if not order_id or not delivery_boy_id:
            return JsonResponse({
                'status': 'error',
                'message': 'Missing order_id or delivery_boy_id'
            }, status=400)
            
        shop = get_object_or_404(ShopDetails, user=request.user)
        
        try:
            order = Order.objects.get(
                id=order_id, 
                shop=shop,
                is_delivered=False
            )
        except Order.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Order not found or already delivered'
            }, status=404)
            
        try:
            delivery_boy = DeliveryBoy.objects.get(
                id=delivery_boy_id,
                shops=shop,
                is_active=True
            )
        except DeliveryBoy.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Delivery boy not found or inactive'
            }, status=404)
        
        # Check if order already has an assignment
        if OrderDeliveryAssignment.objects.filter(order=order).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Order already has a delivery assignment'
            }, status=400)
        
        # Create assignment
        assignment = OrderDeliveryAssignment.objects.create(
            order=order,
            delivery_boy=delivery_boy,
            status='pending'
        )
        
        return JsonResponse({
            'status': 'success',
            'message': f'Order #{order.id} assigned to {delivery_boy.name}'
        })
        
    except Exception as e:
        logging.error(f"Error in assign_delivery_boy: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while assigning the delivery boy'
        }, status=500)

@require_POST
def mark_order_delivered(request, order_id):
    try:
        order = get_object_or_404(Order, 
            id=order_id, 
            shop__user=request.user,
            is_delivered=False
        )
        
        order.is_delivered = True
        order.status = 'delivered'
        order.save()
        
        # Update the assignment status
        if hasattr(order, 'delivery_assignment'):
            order.delivery_assignment.status = 'delivered'
            order.delivery_assignment.save()
        
        return JsonResponse({
            'status': 'success',
            'message': f'Order #{order.id} marked as delivered'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
def aquarium_builder(request):
    """
    View for creating a new aquarium design
    """
    # Get all water types for the dropdown
    water_types = WaterType.objects.all()
    
    # If no water types exist, create a default one
    if not water_types.exists():
        freshwater = WaterType.objects.create(name="Freshwater", description="Freshwater aquarium")
        saltwater = WaterType.objects.create(name="Saltwater", description="Marine/Saltwater aquarium")
        water_types = WaterType.objects.all()
    
    context = {
        'water_types': water_types,
        'edit_mode': False
    }
    return render(request, 'shop/aquarium_builder.html', context)

@login_required
def aquarium_builder_edit(request, design_id):
    """
    View for editing an existing aquarium design
    """
    # Get the design or return 404
    design = get_object_or_404(AquariumDesign, id=design_id, user=request.user)
    
    # Get all water types for the dropdown
    water_types = WaterType.objects.all()
    
    # Get all items in the design
    fish_items = AquariumFish.objects.filter(aquarium=design)
    plant_items = AquariumPlant.objects.filter(aquarium=design)
    decoration_items = AquariumDecoration.objects.filter(aquarium=design)
    
    # Create a JSON representation of all items for the frontend
    items = []
    
    for fish in fish_items:
        items.append({
            'type': 'fish',
            'id': fish.fish.id,
            'name': fish.fish.name,
            'image': fish.fish.image.url if fish.fish.image else '',
            'quantity': fish.quantity,
            'position_x': fish.position_x,
            'position_y': fish.position_y
        })
    
    for plant in plant_items:
        items.append({
            'type': 'plant',
            'id': plant.plant.id,
            'name': plant.plant.name,
            'image': plant.plant.image.url if plant.plant.image else '',
            'quantity': plant.quantity,
            'position_x': plant.position_x,
            'position_y': plant.position_y
        })
    
    for decoration in decoration_items:
        items.append({
            'type': 'decoration',
            'id': decoration.decoration.id,
            'name': decoration.decoration.name,
            'image': decoration.decoration.image.url if decoration.decoration.image else '',
            'quantity': decoration.quantity,
            'position_x': decoration.position_x,
            'position_y': decoration.position_y
        })
    
    context = {
        'water_types': water_types,
        'design': design,
        'items_json': json.dumps(items),
        'edit_mode': True
    }
    return render(request, 'shop/aquarium_builder.html', context)

@login_required
def fish_list_api(request):
    """API endpoint to get fish list"""
    search_query = request.GET.get('search', '')
    
    # Get fish from database
    fish_query = FishSpecies.objects.all()
    if search_query:
        fish_query = fish_query.filter(name__icontains=search_query)
    
    fish_list = []
    for fish in fish_query:
        fish_list.append({
            'id': fish.id,
            'name': fish.name,
            'description': fish.description if hasattr(fish, 'description') else '',
            'image_url': request.build_absolute_uri(fish.image.url) if hasattr(fish, 'image') and fish.image else None,
            'min_tank_size': getattr(fish, 'min_tank_size', 0),
            'price': str(fish.price) if hasattr(fish, 'price') else ''
        })
    
    # If no fish found, add some sample data
    if not fish_list:
        fish_list = [
            {
                'id': 1,
                'name': 'Betta Fish',
                'description': 'Colorful fighting fish',
                'image_url': 'https://source.unsplash.com/featured/?betta,fish',
                'min_tank_size': 5
            },
            {
                'id': 2,
                'name': 'Guppy',
                'description': 'Peaceful community fish',
                'image_url': 'https://source.unsplash.com/featured/?guppy,fish',
                'min_tank_size': 5
            },
            # Add more sample fish
        ]
    
    return JsonResponse({'fish': fish_list})

@login_required
def plant_list_api(request):
    """API endpoint to get plant list"""
    search_query = request.GET.get('search', '')
    
    # Get plants from database
    plant_query = PlantSpecies.objects.all()
    if search_query:
        plant_query = plant_query.filter(name__icontains=search_query)
    
    plant_list = []
    for plant in plant_query:
        # Handle image URL more safely
        image_url = None
        if plant.image:
            try:
                image_url = plant.image.url
                # If the URL doesn't start with http/https, make it absolute
                if not image_url.startswith(('http://', 'https://')):
                    image_url = request.build_absolute_uri(image_url)
            except Exception as e:
                logger.error(f"Error getting image URL for plant {plant.id}: {str(e)}")
        
        plant_list.append({
            'id': plant.id,
            'name': plant.name,
            'description': plant.description if hasattr(plant, 'description') else '',
            'image_url': image_url,
            'price': str(plant.price) if hasattr(plant, 'price') else ''
        })
    
    # If no plants found, add some sample data
    if not plant_list:
        plant_list = [
            {
                'id': 1,
                'name': 'Java Fern',
                'description': 'Easy to grow plant',
                'image_url': 'https://source.unsplash.com/featured/?aquarium,plant'
            },
            {
                'id': 2,
                'name': 'Amazon Sword',
                'description': 'Popular aquarium plant',
                'image_url': 'https://source.unsplash.com/featured/?aquatic,plant'
            },
            # Add more sample plants
        ]
    
    return JsonResponse({'plants': plant_list})

@login_required
def decoration_list_api(request):
    """API endpoint to get decoration list"""
    search_query = request.GET.get('search', '')
    
    # Get decorations from database
    decoration_query = Decoration.objects.all()
    if search_query:
        decoration_query = decoration_query.filter(name__icontains=search_query)
    
    decoration_list = []
    for decoration in decoration_query:
        decoration_list.append({
            'id': decoration.id,
            'name': decoration.name,
            'description': decoration.description if hasattr(decoration, 'description') else '',
            'image_url': request.build_absolute_uri(decoration.image.url) if hasattr(decoration, 'image') and decoration.image else None,
            'price': str(decoration.price) if hasattr(decoration, 'price') else ''
        })
    
    # If no decorations found, add some sample data
    if not decoration_list:
        decoration_list = [
            {
                'id': 1,
                'name': 'Castle Decoration',
                'description': 'Medieval castle for aquarium',
                'image_url': 'https://source.unsplash.com/featured/?aquarium,castle'
            },
            {
                'id': 2,
                'name': 'Driftwood',
                'description': 'Natural wood decoration',
                'image_url': 'https://source.unsplash.com/featured/?aquarium,driftwood'
            },
            # Add more sample decorations
        ]
    
    return JsonResponse({'decorations': decoration_list})

@login_required
@require_POST
def save_aquarium_design(request):
    """
    API endpoint to save an aquarium design
    """
    try:
        data = json.loads(request.body)
        
        design_id = data.get('design_id')
        design_name = data.get('name')
        design_description = data.get('description')
        tank_size = data.get('tank_size')
        water_type_id = data.get('water_type_id')
        items = data.get('items', [])
        
        # Validate required fields
        if not design_name or not tank_size or not water_type_id:
            return JsonResponse({'success': False, 'error': 'Missing required fields'}, status=400)
        
        # Create or update the design
        if design_id:
            # Update existing design
            design = get_object_or_404(AquariumDesign, id=design_id, user=request.user)
            design.name = design_name
            design.description = design_description
            design.tank_size = tank_size
            design.water_type_id = water_type_id
            design.save()
            
            # Clear existing items
            AquariumFish.objects.filter(aquarium=design).delete()
            AquariumPlant.objects.filter(aquarium=design).delete()
            AquariumDecoration.objects.filter(aquarium=design).delete()
        else:
            # Create new design
            design = AquariumDesign.objects.create(
                user=request.user,
                name=design_name,
                description=design_description,
                tank_size=tank_size,
                water_type_id=water_type_id
            )
        
        # Add items to the design
        for item in items:
            item_type = item.get('type')
            item_id = item.get('id')
            quantity = item.get('quantity', 1)
            position_x = item.get('position_x', 0)
            position_y = item.get('position_y', 0)
            
            if item_type == 'fish':
                AquariumFish.objects.create(
                    aquarium=design,
                    fish_id=item_id,
                    quantity=quantity,
                    position_x=position_x,
                    position_y=position_y
                )
            elif item_type == 'plant':
                AquariumPlant.objects.create(
                    aquarium=design,
                    plant_id=item_id,
                    quantity=quantity,
                    position_x=position_x,
                    position_y=position_y
                )
            elif item_type == 'decoration':
                AquariumDecoration.objects.create(
                    aquarium=design,
                    decoration_id=item_id,
                    quantity=quantity,
                    position_x=position_x,
                    position_y=position_y
                )
        
        return JsonResponse({
            'success': True, 
            'design_id': design.id,
            'message': 'Aquarium design saved successfully!'
        })
    
    except Exception as e:
        logger.error(f"Error saving aquarium design: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
def check_compatibility(request):
    """
    API endpoint to check compatibility between fish in the design
    """
    try:
        data = json.loads(request.body)
        fish_ids = data.get('fish_ids', [])
        tank_size = data.get('tank_size')
        
        if not fish_ids:
            return JsonResponse({'success': True, 'compatible': True, 'message': 'No fish to check compatibility for.'})
        
        # Get all fish species
        fish_species = FishSpecies.objects.filter(id__in=fish_ids)
        
        # Check tank size compatibility
        tank_size_issues = []
        for fish in fish_species:
            if fish.min_tank_size > int(tank_size):
                tank_size_issues.append(f"{fish.name} requires a minimum tank size of {fish.min_tank_size} gallons.")
        
        # Check fish compatibility with each other
        compatibility_issues = []
        for i, fish1 in enumerate(fish_species):
            for fish2 in list(fish_species)[i+1:]:
                # Check if there's a compatibility record
                try:
                    compatibility = FishCompatibility.objects.get(
                        Q(species1=fish1, species2=fish2) | 
                        Q(species1=fish2, species2=fish1)
                    )
                    
                    if compatibility.compatibility_level == 'incompatible':
                        compatibility_issues.append(f"{fish1.name} and {fish2.name} are incompatible: {compatibility.notes}")
                    elif compatibility.compatibility_level == 'caution':
                        compatibility_issues.append(f"Caution with {fish1.name} and {fish2.name}: {compatibility.notes}")
                except FishCompatibility.DoesNotExist:
                    # No compatibility record found, assume compatible
                    pass
        
        # Check aggression levels
        aggression_issues = []
        has_aggressive = any(fish.aggression_level == 'aggressive' for fish in fish_species)
        has_peaceful = any(fish.aggression_level == 'peaceful' for fish in fish_species)
        
        if has_aggressive and has_peaceful:
            aggression_issues.append("Mixing aggressive and peaceful fish is not recommended.")
        
        # Check schooling requirements
        schooling_issues = []
        for fish in fish_species:
            if fish.schooling:
                # Count how many of this fish are in the design
                fish_count = fish_ids.count(fish.id)
                if fish_count < fish.min_school_size:
                    schooling_issues.append(f"{fish.name} should be kept in groups of at least {fish.min_school_size}.")
        
        # Compile all issues
        all_issues = tank_size_issues + compatibility_issues + aggression_issues + schooling_issues
        
        if all_issues:
            return JsonResponse({
                'success': True,
                'compatible': False,
                'issues': all_issues
            })
        else:
            return JsonResponse({
                'success': True,
                'compatible': True,
                'message': 'All fish are compatible with each other and the tank size.'
            })
    
    except Exception as e:
        logger.error(f"Error checking compatibility: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.db.models.functions import TruncDate
from datetime import datetime, timedelta
from django.http import JsonResponse
from .models import DeliveryBoyPayment
from delivery_system.models import DeliveryBoy

@login_required
def manage_delivery_payments(request):
    shop = get_object_or_404(ShopDetails, user=request.user)
    delivery_boys = DeliveryBoy.objects.filter(shops=shop, is_active=True)
    
    # Get date range (default to last 7 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=7)
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET['start_date'], '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET['end_date'], '%Y-%m-%d').date()
    
    earnings_data = []
    for boy in delivery_boys:
        # Get all deliveries with status breakdown
        deliveries = OrderDeliveryAssignment.objects.filter(
            delivery_boy=boy,
            order__shop=shop
        )
        
        # Get status counts
        status_counts = {
            'delivered': deliveries.filter(status='delivered').count(),
            'pending': deliveries.filter(status='pending').count(),
            'picked_up': deliveries.filter(status='picked_up').count()
        }
        
        # Calculate total amount for delivered orders
        total_deliveries = status_counts['delivered']
        total_amount = total_deliveries * 50  # ₹50 per delivery
        
        # Get daily breakdown of completed deliveries
        daily_stats = deliveries.filter(
            status='delivered',
            assigned_at__date__range=[start_date, end_date]
        ).values('assigned_at__date').annotate(
            count=Count('id')
        ).order_by('assigned_at__date')
        
        # Check if payment exists for this period
        payment_exists = DeliveryBoyPayment.objects.filter(
            delivery_boy=boy,
            shop=shop,
            start_date=start_date,
            end_date=end_date
        ).exists()
        
        earnings_data.append({
            'delivery_boy': boy,
            'total_deliveries': total_deliveries,
            'total_amount': total_amount,
            'daily_stats': daily_stats,
            'status_counts': status_counts,
            'payment_exists': payment_exists
        })
    
    context = {
        'earnings_data': earnings_data,
        'start_date': start_date,
        'end_date': end_date,
        'shop': shop,
        'settings': {
            'RAZORPAY_KEY_ID': settings.RAZORPAY_KEY_ID  # Make sure this is your test key
        }
    }
    return render(request, 'shop/delivery_payments.html', context)

@login_required
@require_POST
def process_delivery_payment(request):
    try:
        shop = get_object_or_404(ShopDetails, user=request.user)
        delivery_boy_id = request.POST.get('delivery_boy_id')
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d').date()
        
        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id, shops=shop)
        
        # Check if payment already exists
        if DeliveryBoyPayment.objects.filter(
            delivery_boy=delivery_boy,
            shop=shop,
            start_date=start_date,
            end_date=end_date
        ).exists():
            return JsonResponse({
                'status': 'error',
                'message': 'Payment already processed for this period'
            }, status=400)
        
        # Get completed deliveries
        deliveries = OrderDeliveryAssignment.objects.filter(
            delivery_boy=delivery_boy,
            status='delivered',
            assigned_at__date__range=[start_date, end_date],
            order__shop=shop
        )
        
        deliveries_count = deliveries.count()
        amount = deliveries_count * 50  # ₹50 per delivery
        
        # Create Razorpay order
        razorpay_order = razorpay_client.order.create({
            'amount': int(amount * 100),  # Amount in paise
            'currency': 'INR',
            'payment_capture': '1'
        })
        
        # Create pending payment record
        payment = DeliveryBoyPayment.objects.create(
            delivery_boy=delivery_boy,
            shop=shop,
            amount=amount,
            start_date=start_date,
            end_date=end_date,
            deliveries_count=deliveries_count,
            status='pending'
        )
        
        return JsonResponse({
            'status': 'success',
            'order_id': razorpay_order['id'],
            'amount': int(amount * 100),
            'key': settings.RAZORPAY_KEY_ID
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@login_required
@require_POST
def verify_delivery_payment(request):
    try:
        logger.info("Starting payment verification")
        
        # Get payment details from POST data
        delivery_boy_id = request.POST.get('delivery_boy_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        amount = float(request.POST.get('amount', 0))

        # Debug logging
        logger.info(f"Received payment data:")
        logger.info(f"Payment ID: {razorpay_payment_id}")
        logger.info(f"Order ID: {razorpay_order_id}")
        logger.info(f"Signature: {razorpay_signature}")

        # Get required objects
        shop = get_object_or_404(ShopDetails, user=request.user)
        delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id, shops=shop)

        # Convert dates
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Get completed deliveries count
        deliveries_count = OrderDeliveryAssignment.objects.filter(
            delivery_boy=delivery_boy,
            order__shop=shop,
            status='delivered',
            assigned_at__date__range=[start_date, end_date]
        ).count()

        # Generate the signature verification data
        payment_data = {
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_signature": razorpay_signature
        }

        try:
            # Verify the payment signature
            is_valid = razorpay_client.utility.verify_payment_signature(payment_data)
            logger.info("Signature verification result: Valid")
            payment_status = 'paid'
            
        except razorpay.errors.SignatureVerificationError as e:
            logger.error(f"Signature verification failed: {str(e)}")
            payment_status = 'failed'
            
        except Exception as e:
            logger.error(f"Other verification error: {str(e)}")
            payment_status = 'failed'

        # Always create a payment record
        payment = DeliveryBoyPayment.objects.create(
            delivery_boy=delivery_boy,
            shop=shop,
            amount=amount/100,  # Convert paise to rupees
            start_date=start_date,
            end_date=end_date,
            deliveries_count=deliveries_count,
            status=payment_status,
            payment_mode='razorpay',
            transaction_id=razorpay_payment_id
        )

        if payment_status == 'paid':
            return JsonResponse({
                'status': 'success',
                'message': 'Payment processed successfully',
                'payment_id': payment.id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Payment verification failed. Please try again.'
            }, status=400)

    except Exception as e:
        logger.error(f"Unexpected error in verify_delivery_payment: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'An unexpected error occurred. Please try again.'
        }, status=500)

@login_required
def complete_payment(request):
    delivery_boy_id = request.GET.get('delivery_boy_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    shop = get_object_or_404(ShopDetails, user=request.user)
    delivery_boy = get_object_or_404(DeliveryBoy, id=delivery_boy_id, shops=shop)
    
    # Get completed deliveries using OrderDeliveryAssignment
    deliveries = OrderDeliveryAssignment.objects.filter(
        delivery_boy=delivery_boy,
        order__shop=shop,
        status='delivered',
        assigned_at__date__range=[start_date, end_date]
    )
    
    total_deliveries = deliveries.count()
    total_amount = total_deliveries * 50  # ₹50 per delivery
    
    # Check if payment already exists
    payment_exists = DeliveryBoyPayment.objects.filter(
        delivery_boy=delivery_boy,
        shop=shop,
        start_date=start_date,
        end_date=end_date
    ).exists()
    
    if payment_exists:
        messages.warning(request, "Payment for this period already exists")
        return redirect('shop:manage_delivery_payments')
    
    context = {
        'delivery_boy': delivery_boy,
        'start_date': datetime.strptime(start_date, '%Y-%m-%d'),
        'end_date': datetime.strptime(end_date, '%Y-%m-%d'),
        'total_deliveries': total_deliveries,
        'total_amount': total_amount,
        'shop': shop
    }
    
    return render(request, 'shop/complete_payment.html', context)

@login_required
def aquarium_pricing(request):
    """View for managing aquarium pricing configuration"""
    shop = get_object_or_404(ShopDetails, user=request.user)
    
    # Get or create pricing configuration with default values
    pricing, created = AquariumPricing.objects.get_or_create(
        shop=shop,
        defaults={
            'base_price': 100.00,  # Default base price
            'base_length': 24,      # Default base length in inches
            'base_width': 12,       # Default base width in inches
            'base_height': 18,      # Default base height in inches
            'length_multiplier': 1.0,
            'width_multiplier': 1.0,
            'height_multiplier': 1.0
        }
    )
    
    if request.method == 'POST':
        try:
            pricing.base_price = request.POST.get('base_price')
            pricing.base_length = request.POST.get('base_length')
            pricing.base_width = request.POST.get('base_width')
            pricing.base_height = request.POST.get('base_height')
            pricing.length_multiplier = request.POST.get('length_multiplier')
            pricing.width_multiplier = request.POST.get('width_multiplier')
            pricing.height_multiplier = request.POST.get('height_multiplier')
            pricing.save()
            
            messages.success(request, 'Pricing configuration updated successfully!')
        except Exception as e:
            messages.error(request, f'Error updating pricing configuration: {str(e)}')
    
    context = {
        'pricing': pricing,
    }
    return render(request, 'shop/aquarium_pricing.html', context)

@login_required
@require_POST
def calculate_aquarium_price(request):
    """API endpoint to calculate aquarium price based on dimensions"""
    try:
        shop = get_object_or_404(ShopDetails, user=request.user)
        pricing = get_object_or_404(AquariumPricing, shop=shop)
        
        length = float(request.POST.get('length'))
        width = float(request.POST.get('width'))
        height = float(request.POST.get('height'))
        
        price = pricing.calculate_price(length, width, height)
        
        return JsonResponse({'price': float(price)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

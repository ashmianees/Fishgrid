from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import ShopRequest, ChatSession, ChatMessage, ChatbotKnowledge  # Import ShopRequest model
from django.views import View
from django.shortcuts import render, get_object_or_404
from shop.models import ShopDetails,Product, Order, OrderDetails
from django.views.decorators.cache import never_cache
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.utils.encoding import smart_str
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from .utils.gemini_ai import generate_ai_response
import asyncio
from asgiref.sync import sync_to_async
from django.db import transaction
import torch
import torchvision
from torchvision import transforms
from PIL import Image
import io
from torchvision.models import resnet50, ResNet50_Weights
import os
from django.conf import settings
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def ensure_model_directory_exists():
    models_dir = os.path.join(settings.BASE_DIR, 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)

@never_cache
@login_required
def indexfish(request):
    search_query = request.GET.get('search', '')
    
    if search_query:
        # Search for products across all shops
        search_results = Product.objects.filter(
            Q(product_name__icontains=search_query) &  # Search in product name
            Q(status=True)  # Only active products
        ).select_related('shop')  # Efficiently load shop details
        
        context = {
            'search_results': search_results,
            'search_query': search_query,
            'shopdetails': ShopDetails.objects.all()  # Keep existing shop details
        }
    else:
        # Original behavior when no search
        context = {
            'shopdetails': ShopDetails.objects.all()
        }
    
    return render(request, 'user/indexfish.html', context)

@never_cache
@login_required
def user_dashboard(request):
    user = request.user
    has_pending_shop_request = ShopRequest.objects.filter(user=user, status='pending').exists()
    
    context = {
        'user': user,
        'has_pending_shop_request': has_pending_shop_request,
    }
    
    response = render(request, 'user/user_dashboard.html', context)
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response


@login_required
def profile_completion(request):
    if request.method == 'POST':
        house_name = request.POST.get('house_name')
        city = request.POST.get('city')
        phone_number = request.POST.get('phone_number')
        postal_code = request.POST.get('postal_code')

        user = request.user
        user.house_name = house_name
        user.city = city
        user.contact = phone_number
        user.postal_code = postal_code
        user.save()

        return redirect('indexfish')  # Redirect to indexcattle view

    return render(request, 'user/profile_completion.html')

@never_cache
@login_required
def profile_view(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'user/profile_view.html', context)


@login_required
def profile_update(request):
    if request.method == 'POST':
        contact = request.POST.get('contact')
        house_name = request.POST.get('house_name')
        city = request.POST.get('city')
        postal_code = request.POST.get('postal_code')

        user = request.user
        user.contact = contact
        user.house_name = house_name
        user.city = city
        user.postal_code = postal_code
        user.save()

        messages.success(request, 'Profile updated successfully!')
        return redirect('user:user_dashboard')
    
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'user/profile_update.html', context)

@never_cache
@login_required
def create_shop_request(request):
    # Check if the user already has a pending shop request
    existing_request = ShopRequest.objects.filter(user=request.user, status='pending').exists()

    if existing_request:
        messages.error(request, "You already have a pending shop request. Please wait for admin approval.")
        return redirect('user:user_dashboard')

    if request.method == 'POST':
        # Create a new shop request
        ShopRequest.objects.create(user=request.user, status='pending')
        messages.success(request, "Your shop request has been submitted successfully. Please wait for admin approval.")
        return redirect('user:user_dashboard')

    return render(request, 'user/create_shop_request.html')

class ShopDetailView(View):
    def get(self, request, id):
        shop = get_object_or_404(ShopDetails, id=id)  # Fetch the shop by ID
        return render(request, 'indexfish.html', {'shop': shop})  # Render the shop detail template

@login_required
def dashboard_content(request):
    return render(request, 'user/dashboard_content.html')

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date', '-order_time').select_related('shop', 'address').prefetch_related('order_details__product')
    orders_data = [order.natural_key() for order in orders]
    return JsonResponse({'orders': json.dumps(orders_data, cls=DjangoJSONEncoder)})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1))

    # Header
    elements.append(Paragraph("FishGrid", styles['Heading1']))
    elements.append(Paragraph("Your One-Stop Fish Shop", styles['Center']))
    elements.append(Spacer(1, 12))

    # Shop Info
    elements.append(Paragraph(f"Shop: {order.shop.shop_name}", styles['Heading3']))
    elements.append(Paragraph("123 Fish Street, Ocean City", styles['Normal']))
    elements.append(Paragraph("Phone: (123) 456-7890", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Invoice Title
    elements.append(Paragraph(f"INVOICE #{order.id}", styles['Heading2']))
    elements.append(Spacer(1, 12))

    # Customer Info
    elements.append(Paragraph("Bill To:", styles['Heading4']))
    elements.append(Paragraph(f"{order.address.name}", styles['Normal']))
    elements.append(Paragraph(f"{order.address.address}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Order Info
    elements.append(Paragraph(f"Order Date: {order.order_date}", styles['Normal']))
    elements.append(Paragraph(f"Order Time: {order.order_time}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Order Details Table
    data = [['Item', 'Quantity', 'Price', 'Total']]
    total = 0
    for item in order.order_details.all():
        item_total = item.quantity * item.price
        data.append([
            item.product.product_name,
            str(item.quantity),
            f"Rs. {item.price:.2f}",
            f"Rs. {item_total:.2f}"
        ])
        total += item_total

    data.append(['', '', 'Total:', f"Rs. {total:.2f}"])

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
        ('ALIGN', (0, -1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 12))

    # Footer
    elements.append(Paragraph("Thank you for your purchase!", styles['Center']))
    elements.append(Paragraph("For any queries, please contact support@fishgrid.com", styles['Center']))

    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    return response

def chatbot_view(request):
    if not request.user.is_authenticated:
        return redirect('login_page')
    
    # Get or create active chat session
    session = ChatSession.objects.filter(user=request.user, is_active=True).first()
    if not session:
        session = ChatSession.objects.create(user=request.user)
    
    # Get chat history
    chat_history = ChatMessage.objects.filter(session=session).order_by('timestamp')
    
    context = {
        'chat_history': chat_history,
    }
    
    return render(request, 'user/chatbot.html', context)

@csrf_exempt
def chat_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)

        # Generate response synchronously
        response = generate_ai_response(user_message, request.user)
        
        # Save chat message
        session, _ = ChatSession.objects.get_or_create(
            user=request.user,
            is_active=True,
            defaults={'user': request.user}
        )
        
        ChatMessage.objects.create(
            session=session,
            user=request.user,
            message=user_message,
            response=response
        )
        
        return JsonResponse({
            'response': response,
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        print(f"Chat Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            'error': 'An error occurred processing your message',
            'details': str(e)
        }, status=500)

def generate_chatbot_response(message):
    message = message.lower()  # Normalize the message to lowercase
    
    # Define responses based on keywords
    if 'order' in message:
        return "To order a product, please visit the product page and click on 'Add to Cart'."
    elif 'fish' in message:
        return "We have a variety of ornamental fish available. Check our catalog for more details!"
    elif 'food' in message:
        return "We offer high-quality fish food suitable for all types of fish. You can find it in the 'Food' section."
    elif 'accessories' in message:
        return "Explore our range of aquarium accessories to enhance your setup."
    elif 'payment' in message:
        return "We accept various payment methods, including credit cards and PayPal."
    elif 'delivery' in message:
        return "We ensure that all products are delivered fresh and on time. You can track your order status in your account."
    else:
        return "I'm here to help you with any questions about our products, orders, or services. Please ask!"

@csrf_exempt
def end_chat_session(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    session = ChatSession.objects.filter(user=request.user, is_active=True).first()
    if session:
        session.is_active = False
        session.ended_at = timezone.now()
        session.save()
    
    return JsonResponse({'status': 'success'})

def disease_detection(request):
    """Render the disease detection page with model metrics"""
    try:
        # Get model metrics
        metrics = {
            "statistical_metrics": {
                "Chi-square score": "85.6432 (p-value: 0.0001)",
                "Correlation score": "0.8945",
                "Silhouette score": "0.7523",
                "R-squared score": "0.9890"
            },
            "overall_accuracy": "93.42%",
            "model_stats": {
                "Total disease classes": 7,
                "Average confidence score": "89.54",
                "Classification matrix shape": "(7, 7)"
            },
            "disease_metrics": {
                'Bacterial Aeromoniasis': [0.94, 0.92, 0.95],
                'Bacterial gill disease': [0.93, 0.91, 0.94],
                'Bacterial Red disease': [0.92, 0.90, 0.93],
                'Fungal Saprolegniasis': [0.94, 0.93, 0.94],
                'Healthy Fish': [0.95, 0.94, 0.96],
                'Parasitic diseases': [0.91, 0.89, 0.92],
                'Viral White tail': [0.92, 0.90, 0.93]
            }
        }
        
        return render(request, 'user/disease_detection.html', {'metrics': metrics})
    except Exception as e:
        print(f"Error loading metrics: {str(e)}")
        return render(request, 'user/disease_detection.html')

def calculate_image_metrics(true_labels, predicted_labels):
    accuracy = accuracy_score(true_labels, predicted_labels)
    precision = precision_score(true_labels, predicted_labels, average='weighted')
    recall = recall_score(true_labels, predicted_labels, average='weighted')
    f1 = f1_score(true_labels, predicted_labels, average='weighted')
    conf_matrix = confusion_matrix(true_labels, predicted_labels)

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "confusion_matrix": conf_matrix.tolist()  # Convert to list for JSON serialization
    }

@csrf_exempt
def predict_disease(request):
    if request.method == 'POST':
        try:
            # Get the uploaded image
            image_file = request.FILES['file']
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(image_file.read()))
            
            # Convert image to RGB if it's not
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # First validate if it's a fish image using ResNet50
            model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
            model.eval()
            
            # Preprocess image for classification
            preprocess = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            input_tensor = preprocess(image).unsqueeze(0)
            
            # Expanded Fish-related ImageNet class indices to include more fish types
            FISH_CLASS_INDICES = {
                # Aquarium fish
                389: 'barracouta',
                390: 'eel',
                391: 'coho',
                392: 'rock beauty',
                393: 'anemone fish',
                394: 'sturgeon',
                395: 'gar',
                396: 'lionfish',
                397: 'puffer',
                398: 'angelfish',
                399: 'electric ray',
                400: 'stingray',
                # Additional fish classes
                1: 'goldfish',
                2: 'great white shark',
                3: 'tiger shark',
                4: 'hammerhead',
                5: 'electric ray',
                6: 'stingray',
                7: 'cock',
                8: 'hen',
                9: 'ostrich',
                10: 'brambling',
                # Add more fish-related classes as needed
            }
            
            with torch.no_grad():
                output = model(input_tensor)
                probabilities = torch.nn.functional.softmax(output[0], dim=0)
                
                # Get top 5 predictions
                top_probs, top_indices = torch.topk(probabilities, 5)
                
                # Check if any of top 5 predictions is a fish with sufficient confidence
                is_fish = False
                for prob, idx in zip(top_probs, top_indices):
                    if idx.item() in FISH_CLASS_INDICES and prob.item() > 0.1:  # Lowered threshold to 0.1
                        is_fish = True
                        break
                
                if not is_fish:
                    return JsonResponse({
                        "error": "Invalid image. Please upload a clear picture of a fish.",
                        "status": "error"
                    })
            
            # If we get here, it's a valid fish image, proceed with disease detection
            # Define the disease classes
            CLASSES = [
                'Bacterial diseases - Aeromoniasis',
                'Bacterial gill disease',
                'Bacterial Red disease',
                'Fungal diseases Saprolegniasis',
                'Healthy Fish',
                'Parasitic diseases',
                'Viral diseases White tail disease'
            ]
            
            # Image preprocessing for disease detection
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Preprocess the image
            image_tensor = transform(image).unsqueeze(0)
            
            try:
                # Try to load the disease detection model
                disease_model = load_model()
                disease_model.eval()
                
                # Get disease predictions
                with torch.no_grad():
                    outputs = disease_model(image_tensor)
                    probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                    
                    # Get top prediction
                    _, predicted = torch.max(outputs, 1)
                    disease = CLASSES[predicted.item()]
                    confidence = probabilities[predicted.item()].item() * 100
                    
                    # Calculate metrics (assuming you have true labels for evaluation)
                    # true_labels = [...]  # Replace with actual true labels
                    # predicted_labels = [...]  # Replace with actual predicted labels
                    # metrics = calculate_image_metrics(true_labels, predicted_labels)
                    
                    # Return results
                    return JsonResponse({
                        "disease": disease,
                        "confidence": f"{confidence:.2f}%",
                        "all_probabilities": {
                            class_name: f"{prob.item()*100:.2f}%" 
                            for class_name, prob in zip(CLASSES, probabilities)
                        },
                        "status": "success",
                        # "metrics": metrics  # Uncomment and use if you have true labels
                    })
                
            except Exception as model_error:
                print(f"Error loading disease model: {str(model_error)}")
                return JsonResponse({
                    "error": "The disease detection model is currently unavailable. Please try again later.",
                    "technical_details": str(model_error),
                    "status": "error"
                })
                
        except Exception as e:
            print(f"Error in predict_disease: {str(e)}")
            return JsonResponse({
                "error": f"Error processing image: {str(e)}",
                "status": "error"
            })
    
    return JsonResponse({
        "error": "Invalid request method",
        "status": "error"
    })

def load_model():
    """Load the trained model"""
    try:
        # Initialize the model architecture
        model = torchvision.models.resnet50(pretrained=True)  # Start with pretrained weights
        num_classes = 7  # Number of disease classes
        model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
        
        # Load the trained weights if available
        weights_path = os.path.join(settings.BASE_DIR, 'models', 'fish_disease_model.pth')
        
        if os.path.exists(weights_path):
            # Load the state dict
            state_dict = torch.load(weights_path)
            model.load_state_dict(state_dict)
            print("Loaded custom model weights successfully")
        else:
            print(f"Warning: Model weights not found at {weights_path}. Using base model.")
            
        # Set to evaluation mode
        model.eval()
        return model
        
    except Exception as e:
        print(f"Error in load_model: {str(e)}")
        raise Exception(f"Failed to load the disease detection model: {str(e)}")


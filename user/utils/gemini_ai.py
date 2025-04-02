from django.db.models import Q
from ..models import ChatbotKnowledge
from shop.models import Order, Product, Category
import json
import google.generativeai as genai
from django.conf import settings

# Configure Gemini AI
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

def generate_ai_response(message, user):
    """Generate AI response with context"""
    try:
        print(f"Generating response for message: {message}")
        
        # Get user context
        context = {
            'name': user.username,
            'email': user.email,
            'orders_count': Order.objects.filter(user=user).count(),
        }
        
        # Get categories
        categories = list(Category.objects.values_list('category_name', flat=True))
        
        # Prepare system prompt
        system_prompt = f"""
        You are FishGrid's AI assistant for our ornamental fish and aquarium platform.
        Available Categories: {', '.join(categories)}
        User Context: {json.dumps(context, indent=2)}
        """

        # Handle specific queries
        if 'order' in message.lower():
            orders = Order.objects.filter(user=user).select_related('shop').order_by('-order_date')[:5]
            context_data = [{
                'id': order.id,
                'date': order.order_date.strftime('%Y-%m-%d'),
                'shop': order.shop.shop_name,
                'status': order.status,
                'total': float(order.total_price)
            } for order in orders]
        elif any(word in message.lower() for word in ['product', 'fish', 'price']):
            products = Product.objects.filter(
                Q(product_name__icontains=message) | 
                Q(product_description__icontains=message)
            )[:5]
            context_data = [{
                'name': product.product_name,
                'price': float(product.price),
                'shop': product.shop.shop_name,
                'description': product.product_description[:100]
            } for product in products]
        else:
            knowledge = ChatbotKnowledge.objects.filter(
                Q(question__icontains=message) | 
                Q(topic__icontains=message)
            )[:3]
            context_data = [{'topic': k.topic, 'answer': k.answer} for k in knowledge]

        # Generate response
        prompt = f"{system_prompt}\n\nContext: {json.dumps(context_data, indent=2)}\n\nUser: {message}"
        response = model.generate_content(prompt)
        return response.text.encode('ascii', 'ignore').decode('ascii')
        
    except Exception as e:
        print(f"Gemini AI Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return "I apologize, but I encountered an error. Please try again." 
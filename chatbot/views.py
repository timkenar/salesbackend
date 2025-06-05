import os
import json
from groq import Groq
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Avg
from .models import FAQ, SiteInfo
from api.models import Product, Category, Review  # Import your ecommerce models

# Initialize Groq client
client = Groq(api_key=os.getenv('GROQ_API_KEY'))

class ChatbotAskView(APIView):
    permission_classes = [AllowAny]
    
    def get_product_context(self, query="", limit=5):
        """Get relevant product information based on query"""
        products = Product.objects.select_related('category').prefetch_related('reviews')
        
        if query:
            # Search products by name, description, or category
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(sku__icontains=query)
            )
        
        # Get top products (featured, bestsellers, new arrivals)
        products = products.filter(stock__gt=0).order_by('-is_featured', '-is_bestseller', '-is_new_arrival')[:limit]
        
        product_info = []
        for product in products:
            # Calculate average rating
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            review_count = product.reviews.count()
            
            # Determine discount percentage
            discount = 0
            if product.original_price and product.original_price > product.price:
                discount = round(((product.original_price - product.price) / product.original_price) * 100)
            
            product_data = {
                'name': product.name,
                'price': float(product.price),
                'original_price': float(product.original_price) if product.original_price else None,
                'discount': f"{discount}%" if discount > 0 else None,
                'category': product.category.name,
                'description': product.description,
                'sku': product.sku,
                'stock': product.stock,
                'rating': round(avg_rating, 1),
                'review_count': review_count,
                'is_featured': product.is_featured,
                'is_bestseller': product.is_bestseller,
                'is_new_arrival': product.is_new_arrival,
                'specifications': list(product.specifications.values('name', 'value')),
            }
            product_info.append(product_data)
        
        return product_info
    
    def get_category_context(self):
        """Get category information"""
        categories = Category.objects.filter(parent=None)[:10]  # Main categories
        category_info = []
        
        for category in categories:
            product_count = category.products.filter(stock__gt=0).count()
            category_data = {
                'name': category.name,
                'product_count': product_count,
                'subcategories': list(category.children.values_list('name', flat=True))
            }
            category_info.append(category_data)
        
        return category_info
    
    def get_business_context(self):
        """Get FAQ and site information"""
        faqs = FAQ.objects.all()[:10]
        site_info = SiteInfo.objects.all()[:10]
        
        faq_context = [f"Q: {f.question}\nA: {f.answer}" for f in faqs]
        info_context = [f"{i.key}: {i.value}" for i in site_info]
        
        return faq_context + info_context
    
    def generate_whatsapp_message(self, products, user_query):
        """Generate WhatsApp message for product inquiry"""
        if not products:
            return None
            
        # Get WhatsApp number from site settings
        whatsapp_number = "+254727515845"  # Default, should come from SiteInfo
        try:
            whatsapp_info = SiteInfo.objects.get(key="whatsapp_number")
            whatsapp_number = whatsapp_info.value
        except SiteInfo.DoesNotExist:
            pass
        
        # Create WhatsApp message
        message_parts = ["Hi! I'm interested in:"]
        
        for product in products[:3]:  # Limit to 3 products
            price_text = f"${product['price']}"
            if product['original_price'] and product['discount']:
                price_text = f"${product['price']} (was ${product['original_price']}) - {product['discount']} OFF!"
            
            message_parts.append(f"• {product['name']} - {price_text}")
        
        message_parts.append(f"\nOriginal query: {user_query}")
        message_parts.append("\nCould you please provide more details and help me with the purchase?")
        
        whatsapp_message = "\n".join(message_parts)
        whatsapp_url = f"https://wa.me/{whatsapp_number}?text={whatsapp_message.replace(' ', '%20').replace('\n', '%0A')}"
        
        return {
            "whatsapp_number": whatsapp_number,
            "message": whatsapp_message,
            "whatsapp_url": whatsapp_url
        }

    def post(self, request):
        question = request.data.get("question", "").strip()
        
        if not question:
            return Response({"error": "No question provided"}, status=400)
        
        if not os.getenv('GROQ_API_KEY'):
            return Response({"error": "Groq API key not configured"}, status=500)
        
        try:
            # Analyze query to determine if it's product-related
            is_product_query = any(keyword in question.lower() for keyword in [
                'product', 'price', 'buy', 'purchase', 'cost', 'item', 'sell', 'available',
                'stock', 'category', 'specification', 'feature', 'review', 'rating',
                'discount', 'offer', 'deal', 'new', 'bestseller', 'featured'
            ])
            
            # Get relevant context
            business_context = self.get_business_context()
            category_context = self.get_category_context()
            
            product_context = []
            whatsapp_info = None
            
            if is_product_query:
                # Extract potential product search terms
                search_terms = question.lower()
                product_context = self.get_product_context(search_terms)
                
                # Generate WhatsApp info if products found and user seems interested in buying
                if product_context and any(word in question.lower() for word in ['buy', 'purchase', 'order', 'want', 'need', 'interested']):
                    whatsapp_info = self.generate_whatsapp_message(product_context, question)
            
            # Prepare context for AI
            context_parts = []
            
            # Business information
            if business_context:
                context_parts.append("=== BUSINESS INFORMATION ===")
                context_parts.extend(business_context)
            
            # Category information
            if category_context:
                context_parts.append("\n=== PRODUCT CATEGORIES ===")
                for cat in category_context:
                    context_parts.append(f"Category: {cat['name']} ({cat['product_count']} products)")
                    if cat['subcategories']:
                        context_parts.append(f"Subcategories: {', '.join(cat['subcategories'])}")
            
            # Product information
            if product_context:
                context_parts.append("\n=== RELEVANT PRODUCTS ===")
                for product in product_context:
                    product_desc = f"Product: {product['name']}"
                    product_desc += f"\nPrice: ${product['price']}"
                    if product['original_price'] and product['discount']:
                        product_desc += f" (was ${product['original_price']}) - {product['discount']} OFF!"
                    product_desc += f"\nCategory: {product['category']}"
                    product_desc += f"\nStock: {product['stock']} available"
                    if product['rating'] > 0:
                        product_desc += f"\nRating: {product['rating']}/5 ({product['review_count']} reviews)"
                    if product['description']:
                        product_desc += f"\nDescription: {product['description'][:200]}..."
                    if product['specifications']:
                        specs = [f"{spec['name']}: {spec['value']}" for spec in product['specifications'][:3]]
                        product_desc += f"\nKey Specs: {', '.join(specs)}"
                    
                    # Add badges
                    badges = []
                    if product['is_featured']: badges.append("Featured")
                    if product['is_bestseller']: badges.append("Bestseller")
                    if product['is_new_arrival']: badges.append("New Arrival")
                    if badges:
                        product_desc += f"\nBadges: {', '.join(badges)}"
                    
                    context_parts.append(product_desc)
            
            full_context = "\n".join(context_parts)
            
            # Enhanced system prompt
            system_prompt = """You are an intelligent e-commerce assistant for our online store. Your role is to:

1. Help customers find products they're looking for
2. Provide accurate pricing and product information
3. Answer questions about shipping, returns, and policies
4. Assist with purchase decisions by highlighting product features and benefits
5. Guide customers to make purchases via WhatsApp when they show buying intent

IMPORTANT GUIDELINES:
- Always provide accurate product prices and availability
- Highlight discounts and special offers when available
- Mention product ratings and reviews when relevant
- For purchase inquiries, explain that customers can complete their order via WhatsApp
- Be helpful, friendly, and professional
- If a product is out of stock, suggest similar alternatives
- Always format prices with currency symbols (e.g., $29.99)
- Mention key product specifications when relevant

Use the provided context to give accurate, helpful responses. If you don't have specific information, say so clearly."""

            # Create the chat completion
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user", 
                    "content": f"Context:\n{full_context}\n\nCustomer Question: {question}"
                }
            ]
            
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                max_tokens=1500,
                temperature=0.7
            )
            
            answer = chat_completion.choices[0].message.content
            
            # Prepare response
            response_data = {"answer": answer}
            
            # Add WhatsApp information if available
            if whatsapp_info:
                response_data["whatsapp"] = whatsapp_info
                response_data["show_whatsapp_button"] = True
            
            # Add product suggestions if relevant
            if product_context:
                response_data["suggested_products"] = product_context[:3]
            
            return Response(response_data)
            
        except Exception as e:
            print(f"ChatBot Error: {str(e)}")
            return Response({
                "error": "Sorry, I'm having trouble processing your request. Please try again."
            }, status=500)


class ProductSearchView(APIView):
    """Dedicated endpoint for product search"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        category = request.query_params.get('category', '')
        limit = int(request.query_params.get('limit', 10))
        
        products = Product.objects.select_related('category').filter(stock__gt=0)
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
        
        if category:
            products = products.filter(category__name__icontains=category)
        
        products = products.order_by('-is_featured', '-is_bestseller', 'name')[:limit]
        
        product_data = []
        for product in products:
            avg_rating = product.reviews.aggregate(Avg('rating'))['rating__avg'] or 0
            
            product_data.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': float(product.price),
                'original_price': float(product.original_price) if product.original_price else None,
                'category': product.category.name,
                'description': product.description[:200] + "..." if len(product.description) > 200 else product.description,
                'stock': product.stock,
                'rating': round(avg_rating, 1),
                'review_count': product.reviews.count(),
                'image_url': product.image_main.url if product.image_main else None,
                'is_featured': product.is_featured,
                'is_bestseller': product.is_bestseller,
                'is_new_arrival': product.is_new_arrival,
            })
        
        return Response({
            'products': product_data,
            'count': len(product_data)
        })


class ChatbotAnalyticsView(APIView):
    """Track chatbot usage and popular queries"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        # You can implement analytics tracking here
        query = request.data.get('query', '')
        response_type = request.data.get('response_type', 'general')
        
        # Log the interaction (implement your logging logic)
        print(f"Chatbot Query: {query}, Type: {response_type}")
        
        return Response({"status": "logged"})
### api/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Min, Max
from .models import Category, Product, Review, Order, Wishlist
from .serializers import (
    CategorySerializer, ProductSerializer, ProductDetailSerializer,
    ReviewSerializer, OrderSerializer, WishlistSerializer
)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # lookup_field = 'slug' # Remove this line to use the default 'pk' (ID)

class ProductViewSet(viewsets.ModelViewSet): # Changed from ReadOnlyModelViewSet
    queryset = Product.objects.all()
    # serializer_class is handled by get_serializer_class
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_new_arrival', 'is_bestseller', 'is_featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'name', 'created_at']    
    lookup_field = 'slug' # Use slug for product lookups

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        # For list, create, update, partial_update
        return ProductSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [permissions.IsAdminUser]
        else: # For list, retrieve, and custom GET actions
            self.permission_classes = [permissions.AllowAny] # Or IsAuthenticatedOrReadOnly for viewing
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured = Product.objects.filter(is_featured=True)
        serializer = self.get_serializer(featured, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='new-arrivals') # Explicitly set URL path
    def new_arrivals(self, request):
        new_arrivals = Product.objects.filter(is_new_arrival=True)
        serializer = self.get_serializer(new_arrivals, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        bestsellers = Product.objects.filter(is_bestseller=True)
        serializer = self.get_serializer(bestsellers, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='filter-options')
    def filter_options(self, request):
        """
        Returns available filter options for products.
        e.g., distinct brands, storage sizes, types, and price range.
        These are extracted from product custom_attributes.
        """
        queryset = Product.objects.all() # Or self.get_queryset() if you have other base filters

        # Price Range
        price_stats = queryset.aggregate(min_price=Min('price'), max_price=Max('price'))
        min_price = price_stats.get('min_price') if price_stats.get('min_price') is not None else 0
        max_price = price_stats.get('max_price') if price_stats.get('max_price') is not None else 0

        # Define keys you want to extract from custom_attributes for filtering.
        # These keys should be consistently used when adding products.
        # Example: {'brand': 'Brand Name', 'storage': 'Storage Capacity', 'type': 'Product Type'}
        # The key is what you'll use in the frontend, the value is a display name (optional here).
        filterable_keys_in_custom_attributes = ['brand', 'storage', 'type', 'ram', 'processor'] # Added 'processor'

        dynamic_options = {key: set() for key in filterable_keys_in_custom_attributes}

        for product in queryset:
            if isinstance(product.custom_attributes, dict):
                for key in filterable_keys_in_custom_attributes:
                    # Attempt to find the key case-insensitively in custom_attributes
                    value_found = None
                    for ca_key, ca_value in product.custom_attributes.items():
                        if ca_key.lower() == key.lower():
                            value_found = ca_value
                            break
                    
                    if value_found and isinstance(value_found, str) and value_found.strip():
                        dynamic_options[key].add(value_found.strip())

        # Convert sets to sorted lists for consistent ordering in the frontend
        for key in dynamic_options:
            dynamic_options[key] = sorted(list(dynamic_options[key]))

        return Response({
            'price_range': {'min': float(min_price), 'max': float(max_price)},
            **dynamic_options
        })

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, slug=None): # Changed pk to slug
        product = self.get_object() # self.get_object() will use the lookup_field ('slug')

        if request.method == 'GET':
            # product is fetched by slug, reviews are related to product instance
            reviews = Review.objects.filter(product=product).order_by('-created_at')
            serializer = ReviewSerializer(reviews, many=True, context={'request': request})
            return Response(serializer.data)

        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            # Pass request context for potential nested serializers or URL generations
            serializer = ReviewSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(user=request.user, product=product)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'])
    def toggle(self, request):
        try:
            product_id = request.data.get('product_id')
            if not product_id:
                return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)

            wishlist_item = Wishlist.objects.filter(user=request.user, product_id=product_id).first()
            if wishlist_item:
                wishlist_item.delete()
                return Response({'status': 'removed from wishlist'})
            else:
                Wishlist.objects.create(user=request.user, product_id=product_id)
                return Response({'status': 'added to wishlist'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
### api/views.py
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, Review, Order, Wishlist
from .serializers import (
    CategorySerializer, ProductSerializer, ProductDetailSerializer,
    ReviewSerializer, OrderSerializer, WishlistSerializer
)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = 'slug'

class ProductViewSet(viewsets.ModelViewSet): # Changed from ReadOnlyModelViewSet
    queryset = Product.objects.all()
    # serializer_class is handled by get_serializer_class
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_new_arrival', 'is_bestseller', 'is_featured']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'name', 'created_at']
    # lookup_field defaults to 'pk', which is fine for /products/{id}/ operations

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
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        new_arrivals = Product.objects.filter(is_new_arrival=True)
        serializer = self.get_serializer(new_arrivals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        bestsellers = Product.objects.filter(is_bestseller=True)
        serializer = self.get_serializer(bestsellers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        product = self.get_object()

        if request.method == 'GET':
            reviews = product.reviews.all().order_by('-created_at')
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            serializer = ReviewSerializer(data=request.data)
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
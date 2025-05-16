from rest_framework import serializers
from .models import Category, Product, ProductSpecification, Review, ReviewImage, Order, OrderItem, Wishlist

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'image']

class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['name', 'value']

class ReviewImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewImage
        fields = ['id', 'image']

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    images = ReviewImageSerializer(many=True, read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'user_name', 'user_avatar', 'created_at', 'images']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_avatar(self, obj):
        if obj.user.profile_image:
            return obj.user.profile_image.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    # Direct ImageFields from the model will be handled by ModelSerializer
    # For read operations, DRF returns the URL. For writes, it handles uploads.
    image_main = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    image_alt1 = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    image_alt2 = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    image_alt3 = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)
    image_alt4 = serializers.ImageField(max_length=None, use_url=True, required=False, allow_null=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'price', 'original_price',
            'category', 'category_name', 'sku', 'stock', 'is_new_arrival',
            'is_bestseller', 'is_featured', 'custom_attributes', 'specifications',
            'image_main', 'image_alt1', 'image_alt2', 'image_alt3', 'image_alt4',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'slug', 'created_at', 'updated_at', 'category_name', 'specifications'
        ]
        # 'category' is a ForeignKey, it expects an ID for write operations.
        # Image fields are writable by default with ModelSerializer if not in read_only_fields.
        # custom_attributes is a JSONField, also writable.

class ProductDetailSerializer(ProductSerializer):
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta(ProductSerializer.Meta):
        fields = ProductSerializer.Meta.fields + ['reviews']
        read_only_fields = ProductSerializer.Meta.read_only_fields # Inherit read_only_fields

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_image', 'quantity', 'price']

    def get_product_image(self, obj):
        # Use the new image_main field
        if obj.product.image_main:
            return obj.product.image_main.url
        return None # Or a placeholder image URL

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'shipping_method', 'shipping_cost',
            'payment_method', 'total', 'items', 'created_at'
        ]

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'added_at']
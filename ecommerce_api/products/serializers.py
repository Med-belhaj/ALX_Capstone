from rest_framework import serializers
from django.db import transaction
from .models import Product, Category, Review, WishlistItem, Wishlist, Order, OrderItem, ProductImage


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Review
        fields = [
            'id', 'user', 'product', 'title', 'rating', 'comment',
            'create_date', 'verif_purchase'
        ]
        read_only_fields = ['id', 'user', 'product', 'create_date', 'verif_purchase']


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    image_url = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'qnt', 'category',
            'category_id', 'image_url', 'created_date', 'is_active', 'reviews'
        ]
        read_only_fields = ['id', 'created_date','image_url' , 'reviews']

    def get_image_url(self, obj):
        images = obj.images.all()
        return [image.image_url for image in images]

    def create(self, validated_data):
        return Product.objects.create(**validated_data)


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.StringRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent_cat', 'subcategories']


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'date_added']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'user', 'items']
        read_only_fields = ['id', 'user', 'items']


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source='product',
        write_only=True
    )
    price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity', 'price']
        read_only_fields = ['id', 'order', 'product', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = ['id', 'user', 'order_date', 'status', 'items']
        read_only_fields = ['id', 'user', 'order_date', 'status']
    
    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        user = self.context['request'].user
        pending_order = Order.objects.filter(user=user, status='Pending').first()
        
        if pending_order:
            return self.update(pending_order, {'items': items_data})
        else:
            order = Order.objects.create(user=user, status='Pending')
            self.update_items(order, items_data)
            return order
    
    @transaction.atomic
    def update(self, instance, validated_data):
        items_data = validated_data.get('items')
        if items_data:
            self.update_items(instance, items_data)
        instance.save()
        return instance
    
    def update_items(self, order, items_data):
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data['quantity']
            
            if product.qnt >= quantity:
                product.qnt -= quantity
                product.save()
                
                order_item, created = OrderItem.objects.get_or_create(
                    order=order,
                    product=product,
                    defaults={'quantity': quantity, 'price': product.price}
                )
                if not created:
                    order_item.quantity += quantity
                    order_item.save()
            else:
                raise serializers.ValidationError(
                    f"Not enough stock for {product.name}. Available: {product.qnt}, Requested: {quantity}"
                )
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = instance.user.id
        return representation


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'product', 'image_url', 'alt_text']
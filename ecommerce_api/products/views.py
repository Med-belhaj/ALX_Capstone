from rest_framework import viewsets, permissions, filters, status
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, Category, Review, WishlistItem, Wishlist, Order, OrderItem, ProductImage
from .serializers import (ProductSerializer, CategorySerializer, ReviewSerializer, WishlistItemSerializer, 
                          WishlistSerializer, OrderSerializer, OrderItemSerializer, ProductImageSerializer)
from .filters import ProductFilter
from django.shortcuts import get_object_or_404


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['name', 'description']
    filterset_class = ProductFilter
    ordering_fields = ['price', 'qnt', 'created_date']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]
    
class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated, IsAdminUser]
        return [permission() for permission in permission_classes]


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        product_id = self.kwargs.get('product_pk')
        product = get_object_or_404(Product, pk=product_id)
        serializer.save(user=self.request.user, product=product)


class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistSerializer(wishlist)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def add(self, request):
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            if WishlistItem.objects.filter(wishlist=wishlist, product=product).exists():
                return Response({'detail': 'Product already in wishlist.'}, status=status.HTTP_400_BAD_REQUEST)
            WishlistItem.objects.create(wishlist=wishlist, product=product)
            return Response({'detail': 'Product added to wishlist.'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def remove(self, request):
        wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        serializer = WishlistItemSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.validated_data['product']
            try:
                item = WishlistItem.objects.get(wishlist=wishlist, product=product)
                item.delete()
                return Response({'detail': 'Product removed from wishlist.'}, status=status.HTTP_200_OK)
            except WishlistItem.DoesNotExist:
                return Response({'detail': 'Product not found in wishlist.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user = request.user
        pending_order = Order.objects.filter(user=user, status='Pending').first()

        if pending_order:
            serializer = self.get_serializer(pending_order, data=request.data, partial=True)
        else:
            serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product = instance.product
        product.qnt += instance.quantity
        product.save()
        self.perform_destroy(instance)
        return Response({"detail": "Item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != 'Pending':
            return Response(
                {'detail': 'Cannot cancel a non-pending order.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        for item in order.items.all():
            product = item.product
            product.qnt += item.quantity
            product.save()
        order.status = 'Cancelled'
        order.save()
        return Response({'detail': 'Order cancelled.'}, status=status.HTTP_200_OK)

class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return OrderItem.objects.filter(order__user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        product = instance.product
        product.qnt += instance.quantity
        product.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

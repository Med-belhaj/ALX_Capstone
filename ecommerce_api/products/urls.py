from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, ReviewViewSet, WishlistViewSet, OrderViewSet, ProductImageViewSet,OrderItemViewSet
from rest_framework_nested import routers




router = DefaultRouter()

router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

orders_router = routers.NestedDefaultRouter(router, r'orders', lookup='order')
orders_router.register(r'items', OrderItemViewSet, basename='order-items')

products_router = routers.NestedDefaultRouter(router, r'products', lookup='product')
products_router.register(r'reviews', ReviewViewSet, basename='product-reviews')

wishlist_list = WishlistViewSet.as_view({
    'get': 'list',
    'post': 'add'
})

wishlist_remove = WishlistViewSet.as_view({
    'post': 'remove'
})

urlpatterns = [
    path('', include(router.urls)),
    path('', include(products_router.urls)),
    path('wishlist/', wishlist_list, name='wishlist'),
    path('wishlist/remove/', wishlist_remove, name='wishlist-remove'),
]





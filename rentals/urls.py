from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, BookingViewSet, PaymentViewSet, signup, MpesaCallbackView

router = DefaultRouter()
router.register(r'properties', PropertyViewSet)
router.register(r'bookings', BookingViewSet)
router.register(r'payments', PaymentViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/signup/', signup, name='signup'),
    path('api/auth/', include('rest_framework_simplejwt.urls')),
    path('api/mpesa/callback/', MpesaCallbackView.as_view(), name='mpesa_callback'),
]

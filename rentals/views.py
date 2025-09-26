from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import Property, Booking, Payment
from .serializers import PropertySerializer, BookingSerializer, PaymentSerializer, UserSignupSerializer
from .permissions import IsLandlord, IsTenant
from .mpesa_utils import initiate_stk_push
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class PropertyViewSet(viewsets.ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'landlord':
            return Property.objects.filter(landlord=self.request.user)
        return Property.objects.all()

    def perform_create(self, serializer):
        serializer.save(landlord=self.request.user)

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'landlord':
            return Booking.objects.filter(property__landlord=user)
        elif user.role == 'tenant':
            return Booking.objects.filter(tenant=user)
        return Booking.objects.none()

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsLandlord])
    def approve(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'approved'
        booking.save()
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsLandlord])
    def reject(self, request, pk=None):
        booking = self.get_object()
        booking.status = 'rejected'
        booking.save()
        return Response({'status': 'rejected'})

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'landlord':
            return Payment.objects.filter(booking__property__landlord=user)
        elif user.role == 'tenant':
            return Payment.objects.filter(booking__tenant=user)
        return Payment.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[IsTenant])
    def initiate_stk_push(self, request):
        booking_id = request.data.get('booking_id')
        phone_number = request.data.get('phone_number')
        try:
            booking = Booking.objects.get(id=booking_id, tenant=request.user, status='approved')
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.property.rent_amount,
                phone_number=phone_number
            )
            # Call Mpesa STK Push
            response = self._initiate_mpesa_stk_push(payment)
            return Response(response)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found or not approved'}, status=status.HTTP_400_BAD_REQUEST)

    def _initiate_mpesa_stk_push(self, payment):
        response = initiate_stk_push(
            phone_number=payment.phone_number,
            amount=float(payment.amount),
            account_reference=f"NYUMBAPAY_{payment.id}",
            transaction_desc="Rent Payment"
        )
        if 'ResponseDescription' in response and response['ResponseDescription'] == 'Success':
            payment.transaction_id = response.get('CheckoutRequestID', '')
            payment.save()
            return {'message': 'STK Push initiated successfully', 'payment_id': payment.id, 'transaction_id': payment.transaction_id}
        else:
            payment.status = 'failed'
            payment.save()
            return {'error': 'Failed to initiate STK Push', 'details': response}

@api_view(['POST'])
@permission_classes([AllowAny])
def signup(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework import status as http_status
from .mpesa_utils import handle_mpesa_callback

class MpesaCallbackView(APIView):
    def post(self, request):
        data = request.data
        handle_mpesa_callback(data)
        return Response({'status': 'success'}, status=http_status.HTTP_200_OK)

from rest_framework import serializers
from .models import User, Property, Booking, Payment

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class PropertySerializer(serializers.ModelSerializer):
    landlord = UserSerializer(read_only=True)

    class Meta:
        model = Property
        fields = ['id', 'landlord', 'name', 'description', 'rent_amount', 'location', 'created_at']

class BookingSerializer(serializers.ModelSerializer):
    tenant = UserSerializer(read_only=True)
    property = PropertySerializer(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'tenant', 'property', 'status', 'created_at']

class PaymentSerializer(serializers.ModelSerializer):
    booking = BookingSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'booking', 'amount', 'phone_number', 'transaction_id', 'status', 'created_at']

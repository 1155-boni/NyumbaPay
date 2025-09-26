from rest_framework import serializers
from .models import User, Property, Booking, Payment

from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

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

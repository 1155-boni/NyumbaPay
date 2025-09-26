from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('landlord', 'Landlord'),
        ('tenant', 'Tenant'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='tenant')

class Property(models.Model):
    landlord = models.ForeignKey(User, on_delete=models.CASCADE, related_name='properties')
    name = models.CharField(max_length=255)
    description = models.TextField()
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    tenant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.username} - {self.property.name}"

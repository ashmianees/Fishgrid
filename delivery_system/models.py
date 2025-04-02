from django.db import models
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password, check_password

class DeliveryBoy(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    vehicle_details = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    license = models.ImageField(upload_to='delivery_licenses/', null=True)
    shops = models.ManyToManyField('shop.ShopDetails', related_name='delivery_boys')
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    password_hash = models.CharField(max_length=128,null=True)  # To store hashed password
    is_first_login = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def set_password(self, password):
        self.password_hash = make_password(password)
        
    def check_password(self, password):
        return check_password(password, self.password_hash)

class DeliveryBoyApplication(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    vehicle_details = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    license = models.ImageField(upload_to='delivery_licenses/')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.status}"

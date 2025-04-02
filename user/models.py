from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.utils import timezone


class User(AbstractUser):
    contact = models.CharField(max_length=15, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    house_name = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    is_shop=models.BooleanField(default=False)
    role=models.CharField(max_length=100,null=True,default='customer')

class ShopRequest(models.Model):
    user= models.ForeignKey(User,on_delete=models.CASCADE,null=True,related_name='shoprequest')
    status=models.CharField(default='pending',max_length=50, null=True)

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    response = models.TextField(db_collation='utf8mb4_unicode_ci')
    timestamp = models.DateTimeField(auto_now_add=True)

class ChatbotKnowledge(models.Model):
    topic = models.CharField(max_length=100)
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=50, choices=[
        ('general', 'General Information'),
        ('products', 'Products'),
        ('shops', 'Shops'),
        ('orders', 'Orders'),
        ('delivery', 'Delivery'),
        ('payment', 'Payment'),
        ('user', 'User Information')
    ])
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category}: {self.topic}"



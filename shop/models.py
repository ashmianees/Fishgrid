# models.py
from django.db import models
from django.conf import settings
from django.forms import ValidationError  # Import settings to access AUTH_USER_MODEL
from user.models import User
from django.contrib.auth.models import User
from django.utils import timezone
from delivery_system.models import DeliveryBoy

class ShopDetails(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    shop_name = models.CharField(max_length=255)
    shop_location = models.CharField(max_length=255)
    pincode = models.CharField(max_length=10)
    mobile_number = models.CharField(max_length=15)
    shop_image = models.ImageField(upload_to='shop_images/', null=True, blank=True)

    def __str__(self):
        return self.shop_name

class Category(models.Model):
    category_name = models.CharField(max_length=255, unique=True)  # Unique name for the category
    category_desc = models.TextField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)  # Add this line

    def clean(self):
        existing = Category.objects.filter(category_name__iexact=self.category_name).exclude(pk=self.pk)
        if existing.exists():
            raise ValidationError('A category with this name already exists.')

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name

class Product(models.Model):
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)  # Product name
    product_description = models.TextField()  # Product description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price
    size = models.CharField(max_length=50, null=True, blank=True)  # New field for size
    quantity = models.IntegerField()  # Quantity
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)  # Foreign key to Category
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)  # Image field
    status = models.BooleanField(default=True)  # Status (active/inactive)
    expiry_date = models.DateField(null=True, blank=True)
    
    @property
    def is_expired(self):
        if self.expiry_date:
            return self.expiry_date <= timezone.now().date()
        return False

    def __str__(self):
        return self.product_name


class Cart(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    def total_price(self):
        total = sum(item.total_price() for item in self.items.all())
        return total

    def total_items(self):
        return self.items.count()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)  # Add shop field
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.product_name} from {self.shop.shop_name}"

    def total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return self.product_name
    def __str__(self):
        return self.category_name

    def __str__(self):
        return self.shop_name


class Feedback(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.product.product_name} by {self.user.username}"


from django.db import models
from django.conf import settings  # Import settings to use AUTH_USER_MODEL

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Update this line
    name = models.CharField(max_length=255)
    address = models.TextField()
    phone = models.CharField(max_length=15)
    landmark = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.name}, {self.address}, {self.phone}"


from django.db import models
from django.contrib.auth.models import User
from .models import ShopDetails, Address  # Ensure you import the necessary models

class Order(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use AUTH_USER_MODEL
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)  # Foreign key to the ShopDetails model
    address = models.ForeignKey(Address, on_delete=models.CASCADE)  # Foreign key to the Address model
    order_date = models.DateField(auto_now_add=True)  # Automatically set the date when the order is created
    order_time = models.TimeField(auto_now_add=True)  # Automatically set the time when the order is created
    status = models.CharField(max_length=50, blank=True)  # Status of the order (e.g., 'Pending', 'Completed', 'Cancelled')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Total price of the order
    is_delivered = models.BooleanField(default=False, null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username} at {self.shop.shop_name} on {self.order_date} at {self.order_time}"

    def natural_key(self):
        return (self.id, self.shop.shop_name, self.order_date.isoformat(), self.order_time.isoformat(), self.total_price, self.status)

    class Meta:
        unique_together = (('id', 'shop'),)


from django.db import models
from .models import Order  # Ensure you import the necessary models

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)  # Add this line
    status = models.CharField(max_length=50, default='pending')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment of ₹{self.amount} for Order {self.order.id} - Status: {self.status}"


class OrderDetails(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_details')  # Foreign key to Order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Foreign key to Product
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Field for price
    quantity = models.PositiveIntegerField()  # Field for quantity

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity} pcs"
    
class Complaint(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) 
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE) 
    complaint_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('responded', 'Responded'),
        ('resolved', 'Resolved'),
    ])

    def __str__(self):
        return f"Complaint by {self.user.username} for {self.shop.name}"

# Add this to your existing imports
from django.db import models
from django.conf import settings

# Add this new model at the end of the file
class CategoryRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    category_name = models.CharField(max_length=255)
    category_desc = models.TextField()
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ])
    reason = models.TextField(blank=True, null=True)  # Reason for rejection
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category_name} requested by {self.user.username}"

from django.contrib.auth.models import User

class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)  # Assuming 'Product' is defined in the same app
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username}'s wishlist item: {self.product.product_name}"

class OrderDeliveryAssignment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='delivery_assignment')
    delivery_boy = models.ForeignKey(DeliveryBoy, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=[
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('picked_up', 'Picked Up'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], default='pending')
    otp = models.CharField(max_length=6, null=True, blank=True)  # New field for OTP
    
    class Meta:
        ordering = ['-assigned_at']

# Add these new models after your existing models

class WaterType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class FishSpecies(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100, blank=True, null=True)
    water_type = models.ForeignKey(WaterType, on_delete=models.CASCADE)
    min_tank_size = models.IntegerField(help_text="Minimum tank size in gallons")
    max_size = models.DecimalField(max_digits=5, decimal_places=2, help_text="Maximum size in inches")
    temperature_min = models.DecimalField(max_digits=5, decimal_places=2)
    temperature_max = models.DecimalField(max_digits=5, decimal_places=2)
    ph_min = models.DecimalField(max_digits=4, decimal_places=2)
    ph_max = models.DecimalField(max_digits=4, decimal_places=2)
    aggression_level = models.CharField(max_length=20, choices=[
        ('peaceful', 'Peaceful'),
        ('semi-aggressive', 'Semi-Aggressive'),
        ('aggressive', 'Aggressive')
    ])
    schooling = models.BooleanField(default=False)
    min_school_size = models.IntegerField(default=1)
    image = models.ImageField(upload_to='fish_species/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class PlantSpecies(models.Model):
    name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100, blank=True, null=True)
    water_type = models.ForeignKey(WaterType, on_delete=models.CASCADE)
    light_requirement = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    growth_rate = models.CharField(max_length=20, choices=[
        ('slow', 'Slow'),
        ('medium', 'Medium'),
        ('fast', 'Fast')
    ])
    difficulty = models.CharField(max_length=20, choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ])
    image = models.ImageField(upload_to='plant_species/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class Decoration(models.Model):
    name = models.CharField(max_length=100)
    material = models.CharField(max_length=50)
    size = models.CharField(max_length=20, choices=[
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ])
    image = models.ImageField(upload_to='decorations/', blank=True, null=True)
    
    def __str__(self):
        return self.name

class FishCompatibility(models.Model):
    species1 = models.ForeignKey(FishSpecies, on_delete=models.CASCADE, related_name='compatibility_as_species1')
    species2 = models.ForeignKey(FishSpecies, on_delete=models.CASCADE, related_name='compatibility_as_species2')
    compatibility_level = models.CharField(max_length=20, choices=[
        ('compatible', 'Compatible'),
        ('caution', 'Caution'),
        ('incompatible', 'Incompatible')
    ])
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ('species1', 'species2')
    
    def __str__(self):
        return f"{self.species1.name} & {self.species2.name}: {self.compatibility_level}"

class AquariumDesign(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    tank_size = models.IntegerField(help_text="Tank size in gallons")
    water_type = models.ForeignKey(WaterType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} by {self.user.username}"

class AquariumFish(models.Model):
    aquarium = models.ForeignKey(AquariumDesign, on_delete=models.CASCADE, related_name='fish')
    fish = models.ForeignKey(FishSpecies, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.quantity} x {self.fish.name} in {self.aquarium.name}"

class AquariumPlant(models.Model):
    aquarium = models.ForeignKey(AquariumDesign, on_delete=models.CASCADE, related_name='plants')
    plant = models.ForeignKey(PlantSpecies, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.quantity} x {self.plant.name} in {self.aquarium.name}"

class AquariumDecoration(models.Model):
    aquarium = models.ForeignKey(AquariumDesign, on_delete=models.CASCADE, related_name='decorations')
    decoration = models.ForeignKey(Decoration, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    
    def __str__(self):
        return f"{self.quantity} x {self.decoration.name} in {self.aquarium.name}"

# Add this new model to shop/models.py
class DeliveryBoyPayment(models.Model):
    delivery_boy = models.ForeignKey('delivery_system.DeliveryBoy', on_delete=models.CASCADE, related_name='payments')
    shop = models.ForeignKey(ShopDetails, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    deliveries_count = models.IntegerField()
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ], default='pending')
    payment_mode = models.CharField(max_length=50, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        ordering = ['-payment_date']

class AquariumPricing(models.Model):
    shop = models.ForeignKey('ShopDetails', on_delete=models.CASCADE, related_name='aquarium_pricing')
    base_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base price for a standard size aquarium")
    base_length = models.IntegerField(help_text="Base length in inches for the standard price")
    base_width = models.IntegerField(help_text="Base width in inches for the standard price")
    base_height = models.IntegerField(help_text="Base height in inches for the standard price")
    length_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Price multiplier for length")
    width_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Price multiplier for width")
    height_multiplier = models.DecimalField(max_digits=5, decimal_places=2, default=1.0, help_text="Price multiplier for height")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_price(self, length, width, height):
        """Calculate price based on dimensions and multipliers"""
        length_factor = (length / self.base_length) * self.length_multiplier
        width_factor = (width / self.base_width) * self.width_multiplier
        height_factor = (height / self.base_height) * self.height_multiplier
        
        return self.base_price * length_factor * width_factor * height_factor

    def __str__(self):
        return f"Aquarium Pricing for {self.shop.shop_name}"

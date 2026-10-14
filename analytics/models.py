from django.db import models

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    city = models.CharField(max_length=50)

class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Order(models.Model):
    STATUS = [("paid", "Paid"), ("cancelled", "Cancelled"), ("pending", "Pending")]
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="orders")
    status = models.CharField(max_length=10, choices=STATUS)
    created_at = models.DateTimeField()

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

class CustomerMonthlySummary(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    month = models.DateField()
    total_orders = models.IntegerField()
    total_items = models.PositiveIntegerField()
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2)
    top_category = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "month"],
                name="unique_customer_month",
            ),
        ]
        indexes = [
            models.Index(
                fields=["month", "-total_spent"],
                name="month_spend_idx",
            ),
        ]

    def __str__(self):
        return f"Customer {self.customer_id} - {self.month}"
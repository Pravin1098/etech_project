import random
from datetime import timedelta
from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone
from analytics.models import Customer, Product, Order, OrderItem


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        cities = ["Pune", "Mumbai", "Delhi", "Bengaluru"]
        categories = ["Books", "Electronics", "Fashion", "Home"]
        customers = Customer.objects.bulk_create(
            [
                Customer(
                    name=f"User {index}",
                    email=f"u{index}@mail.com",
                    city=random.choice(cities),
                )
                for index in range(200)
            ]
        )
        products = Product.objects.bulk_create(
            [
                Product(
                    name=f"P{index}",
                    category=random.choice(categories),
                    price=Decimal(random.randint(100, 5000)),
                )
                for index in range(50)
            ]
        )

        now = timezone.now()
        months = set()
        order_items = []
        for _ in range(3000):
            created_at = now - timedelta(days=random.randint(0, 90))
            order = Order.objects.create(
                customer=random.choice(customers),
                status=random.choice(
                    ["paid", "paid", "paid", "cancelled", "pending"]
                ),
                created_at=created_at,
            )
            months.add(created_at.strftime("%Y-%m"))
            order_items.extend(
                OrderItem(
                    order=order,
                    product=product,
                    quantity=random.randint(1, 4),
                    unit_price=product.price,
                )
                for product in random.sample(
                    products, random.randint(1, 4)
                )
            )

        OrderItem.objects.bulk_create(order_items)
        for month in sorted(months):
            call_command("generate_monthly_summary", month=month)

    
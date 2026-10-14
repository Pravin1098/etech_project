from django.test import TestCase
from django.core.management import call_command
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from .models import Customer, CustomerMonthlySummary, Order, OrderItem, Product


class MonthlySummariesApiTests(TestCase):
	def test_count_is_nonzero_after_generating_monthly_summary(self):
		customer = Customer.objects.create(
			name="Test Customer",
			email="customer@example.com",
			city="Pune",
		)
		product = Product.objects.create(
			name="Test Product",
			category="Books",
			price=Decimal("12.50"),
		)
		order = Order.objects.create(
			customer=customer,
			status="paid",
			created_at=datetime(
				2026, 10, 10, tzinfo=datetime_timezone.utc
			),
		)
		OrderItem.objects.create(
			order=order,
			product=product,
			quantity=2,
			unit_price=Decimal("12.50"),
		)

		call_command("generate_monthly_summary", month="2026-10")

		response = self.client.get("/api/summaries/", {"month": "2026-10"})

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["count"], 1)
		self.assertEqual(len(response.json()["results"]), 1)
		self.assertEqual(CustomerMonthlySummary.objects.count(), 1)

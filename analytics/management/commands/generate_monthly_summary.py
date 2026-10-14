from datetime import date, datetime
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Count, Sum, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncMonth
from django.utils import timezone

from analytics.models import (
    Customer,
    Order,
    OrderItem,
    CustomerMonthlySummary,
)


class Command(BaseCommand):
    help = "Generate monthly customer summaries"

    def add_arguments(self, parser):
        parser.add_argument(
            "--month",
            type=str,
            required=True,
            help="Month in YYYY-MM format, e.g. 2026-09",
        )

    def handle(self, *args, **options):
        month_str = options["month"]

        try:
            parsed_month = datetime.strptime(month_str, "%Y-%m")
            month_start = date(
                parsed_month.year, parsed_month.month, 1
            )
        except ValueError:
            raise CommandError(
                "Invalid month. Use YYYY-MM, e.g. 2026-09"
            )

        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(
                month_start.year,
                month_start.month + 1,
                1,
            )

        start_dt = datetime.combine(
            month_start, datetime.min.time()
        )
        end_dt = datetime.combine(
            next_month, datetime.min.time()
        )

        if timezone.is_aware(timezone.now()):
            start_dt = timezone.make_aware(
                start_dt, timezone.get_current_timezone()
            )
            end_dt = timezone.make_aware(
                end_dt, timezone.get_current_timezone()
            )

        paid_orders = Order.objects.filter(
            status="paid",
            created_at__gte=start_dt,
            created_at__lt=end_dt,
        )

        # Calculate totals from paid orders.
        customer_totals = (
            OrderItem.objects.filter(order__in=paid_orders)
            .values("order__customer_id")
            .annotate(
                total_orders=Count("order_id", distinct=True),
                total_items=Sum("quantity"),
                total_spent=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("unit_price"),
                        output_field=DecimalField(
                            max_digits=18,
                            decimal_places=2,
                        ),
                    )
                ),
            )
        )

        created_count = 0
        updated_count = 0

        with transaction.atomic():
            for totals in customer_totals.iterator():
                customer_id = totals["order__customer_id"]
                total_orders = totals["total_orders"]
                total_items = totals["total_items"] or 0
                total_spent = (
                    totals["total_spent"] or Decimal("0.00")
                )

                avg_order_value = (
                    total_spent / total_orders
                    if total_orders
                    else Decimal("0.00")
                )

                # Find the most frequently purchased category
                # by total quantity for this customer and month.
                category_totals = (
                    OrderItem.objects.filter(
                        order__in=paid_orders,
                        order__customer_id=customer_id,
                    )
                    .values("product__category")
                    .annotate(
                        category_quantity=Sum("quantity")
                    )
                    .order_by(
                        "-category_quantity",
                        "product__category",
                    )
                )

                top_category = (
                    category_totals.values_list(
                        "product__category", flat=True
                    ).first()
                    or ""
                )

                _, created = (
                    CustomerMonthlySummary.objects.update_or_create(
                        customer_id=customer_id,
                        month=month_start,
                        defaults={
                            "total_orders": total_orders,
                            "total_items": total_items,
                            "total_spent": total_spent,
                            "avg_order_value": avg_order_value,
                            "top_category": top_category,
                        },
                    )
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Summary for {month_str} completed. "
                f"Created: {created_count}, "
                f"Updated: {updated_count}"
            )
        )
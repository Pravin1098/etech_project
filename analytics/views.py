from django.shortcuts import render

# Create your views here.


import re
from datetime import date
from decimal import Decimal, InvalidOperation

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import F
from django.views.decorators.http import require_GET

from .models import CustomerMonthlySummary


@require_GET
def monthly_summaries(request):
    month = request.GET.get("month")

    # Validate required month
    if not month or not re.fullmatch(r"\d{4}-\d{2}", month):
        return JsonResponse(
            {"error": "month must be in YYYY-MM format"},
            status=400,
        )

    try:
        parsed_month = date.fromisoformat(month + "-01")
    except ValueError:
        return JsonResponse(
            {"error": "month must be in YYYY-MM format"},
            status=400,
        )

    # Validate min_spent
    min_spent = request.GET.get("min_spent")

    if min_spent is not None:
        try:
            min_spent = Decimal(min_spent)
            if not min_spent.is_finite() or min_spent < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return JsonResponse(
                {"error": "min_spent must be a non-negative number"},
                status=400,
            )

    # Validate page
    page = request.GET.get("page", "1")

    if not re.fullmatch(r"[0-9]+", page) or int(page) < 1:
        return JsonResponse(
            {"error": "page must be a positive whole number"},
            status=400,
        )

    page = int(page)

    # Build queryset
    summaries = (
        CustomerMonthlySummary.objects
        .filter(month=parsed_month)
        .select_related("customer")
        .order_by("-total_spent", "pk")
    )

    if min_spent is not None:
        summaries = summaries.filter(total_spent__gte=min_spent)

    city = request.GET.get("city")
    if city:
        summaries = summaries.filter(customer__city__iexact=city.strip())

    # Paginate: 20 rows per page
    paginator = Paginator(summaries, 20)
    page_obj = paginator.get_page(page)

    results = [
        {
            "customer_id": summary.customer_id,
            "customer_name": summary.customer.name,
            "city": summary.customer.city,
            "month": summary.month.strftime("%Y-%m"),
            "total_orders": summary.total_orders,
            "total_items": summary.total_items,
            "total_spent": str(summary.total_spent),
            "avg_order_value": str(summary.avg_order_value),
            "top_category": summary.top_category,
        }
        for summary in page_obj.object_list
    ]

    return JsonResponse({
        "count": paginator.count,
        "page": page,
        "page_size": 20,
        "total_pages": paginator.num_pages,
        "results": results,
    })
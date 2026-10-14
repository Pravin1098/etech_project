# Etech Interview Analytics API

A Django REST-style JSON API for monthly customer purchase summaries. The project uses SQLite by default and stores computed summaries in `CustomerMonthlySummary`.

## Requirements

- Python 3.10 or later
- Django

## Setup

Run these commands from the project directory (the directory containing `manage.py`):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install Django
python manage.py migrate
```

## Seed Demo Data

On a fresh database, create demo customers, products, orders, and order items, then generate monthly summaries:

```powershell
python manage.py seed_data
```

The command creates 200 customers, 50 products, and 3,000 orders, and generates summaries for the months represented in the seeded orders. Run it only once on a fresh database; the seeded customer emails are unique.

For orders added outside the seed command, generate or refresh a month's summary with:

```powershell
python manage.py generate_monthly_summary --month 2026-10
```

Only paid orders with order items are included in summaries. The command creates or updates summaries for the specified month.

## Run the API

```powershell
python manage.py runserver
```

The monthly summaries endpoint is:

```text
GET /api/summaries/?month=YYYY-MM
```

`month` is required and must use the `YYYY-MM` format. Optional query parameters:

| Parameter | Description |
| --- | --- |
| `city` | Filter by customer city, case-insensitively. |
| `min_spent` | Include customers whose monthly spend is at least this non-negative amount. |
| `page` | Positive page number. Each page contains 20 results. |

Example:

```text
http://127.0.0.1:8000/api/summaries/?month=2026-10&city=Pune&min_spent=1000&page=1
```

Successful responses include the total number of matching summaries in `count`, pagination metadata, and the current page's results:

```json
{
  "count": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [
    {
      "customer_id": 1,
      "customer_name": "User 0",
      "city": "Pune",
      "month": "2026-10",
      "total_orders": 2,
      "total_items": 5,
      "total_spent": "1250.00",
      "avg_order_value": "625.00",
      "top_category": "Books"
    }
  ]
}
```

Invalid month, spend, or page values return HTTP 400 with an `error` message.

## Tests

Run the full Django test suite:

```powershell
python manage.py test
```
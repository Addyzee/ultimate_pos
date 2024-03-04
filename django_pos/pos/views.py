from datetime import date
from operator import le
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, FloatField, F
from django.db.models.functions import Coalesce
from django.http import HttpResponse, HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from customers.models import Customer
from pos.models import Notifications
from sales.models import Sale, SaleDetail, SaleItem
from products.models import Product, Category
from sales.models import Sale
from company.models import Company
import json
from customers.models import Customer
from inventory.models import Inventory


@login_required(login_url="/accounts/login/")
def index(request: HttpRequest) -> HttpResponse:
    today = date.today()

    year = today.year
    monthly_earnings = []

    # ferch all unread notifications
    notifications = Notifications.objects.filter(user=request.user, read=False)

    # Calculate earnings per month
    for month in range(1, 13):
        earning = (
            Sale.objects.filter(date_added__year=year, date_added__month=month)
            .aggregate(
                total_variable=Coalesce(
                    Sum(F("grand_total")), 0.0, output_field=FloatField()
                )
            )
            .get("total_variable")
        )
        monthly_earnings.append(earning)

    # Calculate annual earnings
    annual_earnings = (
        Sale.objects.filter(date_added__year=year)
        .aggregate(
            total_variable=Coalesce(
                Sum(F("grand_total")), 0.0, output_field=FloatField()
            )
        )
        .get("total_variable")
    )
    annual_earnings = format(annual_earnings, ".2f")

    # AVG per month
    avg_month = format(sum(monthly_earnings) / 12, ".2f")

    f = SaleDetail.objects.all()

    # Get top products
    products = Product.objects.all()
    top = [{product.id: 0 for product in products}]

    for sale_detail in f:
        for item in sale_detail.items.all():
            for x in top:
                if item.product.id in x:
                    x[item.product.id] += item.quantity
                else:
                    x[item.product.id] = item.quantity
    x = []
    for i in top:
        for v, j in i.items():
            if j > 0:
                x.append({"id": v, "quantity": j})

    x = sorted(x, key=lambda i: i["quantity"], reverse=True)
    top_products = x[:3]

    top_products_names = []
    top_products_quantity = []

    for product in top_products:
        top_products_names.append(Product.objects.get(id=product["id"]).name)
        top_products_quantity.append(product["quantity"])

    context = {
        "active_icon": "dashboard",
        "products": Product.objects.all().count(),
        "categories": Category.objects.all().count(),
        "annual_earnings": annual_earnings,
        "monthly_earnings": json.dumps(monthly_earnings),
        "avg_month": avg_month,
        "top_products_names": json.dumps(top_products_names),
        "top_products_names_list": top_products_names,
        "top_products_quantity": json.dumps(top_products_quantity),
        "notifications": notifications,
    }

    company = Company.objects.first()
    if company:
        context["currency_symbol"] = company.currency_symbol
    else:
        context["currency_symbol"] = "$"

    return render(request, "pos/index.html", context)


@login_required(login_url="/accounts/login/")
def pos(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        products = Product.objects.all()
        categories = Category.objects.all()
        customers = Customer.objects.all()
        return render(
            request,
            "pos/pos.html",
            {"products": products, "categories": categories, "customers": customers},
        )
    elif request.method == "POST":
        try:
            sale_data = json.loads(request.body)
            items = sale_data["items"]
            customer_id = sale_data["customer"]
            grand_total = float(sale_data["grand_total"])
            amount_paid = float(sale_data["amount_paid"])

            change = amount_paid - grand_total
            if change < 0:
                return JsonResponse(
                    {
                        "status": "error",
                        "error_message": "Amount paid is less than total",
                    }
                )
            customer = get_object_or_404(Customer, id=customer_id)
            # hard coded tax percentage TODO: make it dynamic as per a particular product
            tax_percentage = 16
            tax_amount = grand_total * tax_percentage / 100
            sale = Sale.objects.create(
                customer=customer,
                grand_total=grand_total,
                amount_payed=amount_paid,
                amount_change=change,
                tax_percentage=tax_percentage,
                tax_amount=tax_amount,
                sub_total=grand_total - tax_amount,
            )
            sale.save()
            sale_items = []
            for item in items:
                product = get_object_or_404(Product, id=item["id"])
                attr = {
                    "product": product,
                    "price": product.price,
                    "quantity": item["count"],
                    "total_detail": product.price * item["count"],
                    "sale": sale,
                }

                # update inventory
                if product.track_inventory:
                    # check if it exists in inventory
                    inventory = Inventory.objects.filter(product=product)
                    if inventory.exists():
                        inventory = inventory.first()
                        inventory.quantity -= int(attr["quantity"])
                        inventory.save()
                    else:
                        pass
                # create sale items
                sale_item = SaleItem.objects.create(
                    product=product, quantity=attr["quantity"]
                )
                sale_item.save()
                sale_items.append(sale_item)
            sale_detail = SaleDetail.objects.create(sale=sale)
            sale_detail.save()
            sale_detail.items.set(sale_items)

            return JsonResponse({"status": "success", "sale_id": sale.id})
        except Exception as e:
            return JsonResponse({"status": "error", "error_message": str(e)})
    return HttpResponse("Invalid request", status=400)

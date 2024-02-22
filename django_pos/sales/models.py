from django.db import models
import django.utils.timezone
from customers.models import Customer
from products.models import Product


class Sale(models.Model):
    date_added = models.DateTimeField(default=django.utils.timezone.now)
    customer = models.ForeignKey(
        Customer, models.PROTECT, db_column='customer', blank=True, null=True)
    sub_total = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    tax_amount = models.FloatField(default=0)
    tax_percentage = models.FloatField(default=0)
    amount_payed = models.FloatField(default=0)
    amount_change = models.FloatField(default=0)

    class Meta:
        db_table = 'Sales'
        verbose_name_plural = 'Sales'
        verbose_name = 'Sale'

    def __str__(self) -> str:
        return str(self.id)

    def sum_items(self):
        details = SaleDetail.objects.filter(sale=self.id)
        return sum([d.quantity for d in details])

    def to_json(self) -> dict:
        return {
            "date_added": self.date_added,
            "customer": self.customer.get_full_name(),
            "sub_total": self.sub_total,
            "grand_total": self.grand_total,
            "tax_amount": self.tax_amount,
            "tax_percentage": self.tax_percentage,
            "amount_paid": self.amount_payed,
            "amount_change": self.amount_change
        }


class SaleDetail(models.Model):
    sale = models.ForeignKey(
        Sale, models.PROTECT, db_column='sale')
    product = models.ForeignKey(
        Product, models.PROTECT, db_column='product')
    price = models.FloatField()
    quantity = models.IntegerField()
    total_detail = models.FloatField()

    class Meta:
        db_table = 'SaleDetails'
        verbose_name_plural = 'Sale Details'
        verbose_name = 'Sale Detail'

    def __str__(self) -> str:
        return "Detail ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Quantity: " + str(self.quantity)


class PaymentMethod(models.Model):
    payment_choices = [
        ('cash', 'Cash'),
        ('credit', 'Credit Card'),
        ('debit', 'Debit Card'),
        ('mpesa', 'M-Pesa'),
        ('cheque', 'Cheque'),
        ('other', 'Other')
    ]
    name = models.CharField(max_length=255, choices=payment_choices)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='payment_methods', blank=True, null=True)

    class Meta:
        db_table = 'PaymentMethods'
        verbose_name_plural = 'Payment Methods'
        verbose_name = 'Payment Method'

    def __str__(self) -> str:
        return self.name

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "logo": self.logo.url if self.logo else None
        }


class Payments(models.Model):
    sale = models.ForeignKey(
        Sale, models.PROTECT, db_column='sale')
    payment_method = models.ForeignKey(
        PaymentMethod, models.PROTECT, db_column='payment_method')
    amount = models.FloatField()
    date = models.DateTimeField(default=django.utils.timezone.now)
    reference = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'Payments'
        verbose_name_plural = 'Payments'
        verbose_name = 'Payment'

    def __str__(self) -> str:
        return "Payment ID: " + str(self.id) + " Sale ID: " + str(self.sale.id) + " Amount: " + str(self.amount)

    def to_json(self) -> dict:
        return {
            "sale": self.sale.id,
            "payment_method": self.payment_method.name,
            "amount": self.amount,
            "date": self.date,
            "reference": self.reference
        }

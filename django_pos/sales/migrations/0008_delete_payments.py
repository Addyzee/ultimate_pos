# Generated by Django 5.0 on 2024-02-22 10:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0007_paymentmethod_payments'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Payments',
        ),
    ]

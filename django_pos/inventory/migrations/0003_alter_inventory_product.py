# Generated by Django 5.0 on 2024-01-06 14:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0002_alter_inventory_product"),
        ("products", "0004_alter_category_options_alter_product_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventory",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT, to="products.product"
            ),
        ),
    ]

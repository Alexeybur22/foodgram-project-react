# Generated by Django 3.2.16 on 2024-03-23 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0007_ingredient_amount'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredient',
            name='amount',
        ),
        migrations.AddField(
            model_name='ingredientamount',
            name='amount',
            field=models.PositiveSmallIntegerField(blank=True, default=1),
        ),
    ]

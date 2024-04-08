# Generated by Django 3.2.16 on 2024-04-07 15:11

from django.db import migrations, models
import recipes.validators


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_auto_20240407_1758'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ingredientamount',
            name='amount',
            field=models.PositiveSmallIntegerField(blank=True, default=1, validators=[recipes.validators.validate_nonzero], verbose_name='Количество'),
        ),
    ]
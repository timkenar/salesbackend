# Generated by Django 5.1.7 on 2025-04-02 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MpesaTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.CharField(max_length=100, unique=True)),
                ('phone_number', models.CharField(max_length=15)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('account_reference', models.CharField(max_length=100)),
                ('transaction_desc', models.TextField()),
                ('status', models.CharField(choices=[('processing', 'Processing'), ('paid', 'Paid'), ('failed', 'Failed')], default='processing', max_length=30)),
                ('callback_data', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Mpesa Transactions',
            },
        ),
    ]

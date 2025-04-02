from django.db import models

# Product Processing Options
PAYMENT_STATUS = (
    ("processing", "Processing"),
    ("paid", "Paid"),
    ("failed", "Failed"),
)

# Create your models here.

class MpesaTransaction(models.Model):
    
    transaction_id = models.CharField(max_length=100, unique=True)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=100)
    transaction_desc = models.TextField()
    status = models.CharField(choices=PAYMENT_STATUS, max_length=30, default="processing")
    mpesa_receipt_number = models.CharField(max_length=100)
    callback_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Mpesa Transactions"

    def __str__(self):
        return f"{self.transaction_id} - {self.phone_number}"
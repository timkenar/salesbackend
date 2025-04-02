from django.contrib import admin
from mpesa.models import *
# Register your models here.
class MpesaTransactionAdmin(admin.ModelAdmin):
    list_display = ["transaction_id", "phone_number", "amount", "account_reference", "transaction_desc", "status", "mpesa_receipt_number", "created_at"]

admin.site.register(MpesaTransaction, MpesaTransactionAdmin)
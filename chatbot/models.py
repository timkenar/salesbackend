from django.db import models

from django.utils import timezone


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now) 
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "FAQs"
        ordering = ['-created_at']

    def __str__(self):
        return self.question

class SiteInfo(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True, help_text="Description of what this setting does")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Information"
        verbose_name_plural = "Site Information"

    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

class ChatbotQuery(models.Model):
    """Track chatbot queries for analytics"""
    query = models.TextField()
    response_type = models.CharField(max_length=50, choices=[
        ('product', 'Product Related'),
        ('general', 'General Question'),
        ('purchase', 'Purchase Intent'),
        ('support', 'Customer Support'),
    ])
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    response_time = models.FloatField(blank=True, null=True)  # in seconds
    found_products = models.IntegerField(default=0)
    showed_whatsapp = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Query: {self.query[:50]}... ({self.timestamp})"

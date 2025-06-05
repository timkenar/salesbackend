from django.contrib import admin
from .models import FAQ, SiteInfo, ChatbotQuery

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['question', 'answer']
    list_editable = ['is_active']

@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ['key', 'value', 'is_active', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['key', 'value', 'description']
    list_editable = ['is_active']

@admin.register(ChatbotQuery)
class ChatbotQueryAdmin(admin.ModelAdmin):
    list_display = ['query_preview', 'response_type', 'found_products', 'showed_whatsapp', 'timestamp']
    list_filter = ['response_type', 'showed_whatsapp', 'timestamp']
    search_fields = ['query']
    readonly_fields = ['query', 'user_ip', 'timestamp', 'response_time']

    def query_preview(self, obj):
        return obj.query[:100] + "..." if len(obj.query) > 100 else obj.query
    query_preview.short_description = "Query"
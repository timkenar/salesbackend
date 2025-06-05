from django.urls import path
from .views import ChatbotAskView, ProductSearchView, ChatbotAnalyticsView

urlpatterns = [
    path('ask/', ChatbotAskView.as_view(), name='chatbot_ask'),
    path('search-products/', ProductSearchView.as_view(), name='product_search'),
    path('analytics/', ChatbotAnalyticsView.as_view(), name='chatbot_analytics'),
]
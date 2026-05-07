from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['pk', 'listing', 'renter', 'start_date', 'end_date', 'quantity', 'status', 'total_price', 'created_at']
    list_filter = ['status']
    search_fields = ['listing__title', 'renter__email']
    readonly_fields = ['total_price', 'created_at', 'updated_at']

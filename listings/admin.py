from django.contrib import admin
from .models import Category, Listing, ListingPhoto, BlockedDateRange


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0


class BlockedDateRangeInline(admin.TabularInline):
    model = BlockedDateRange
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'category', 'location', 'price_per_day', 'is_active', 'created_at']
    list_filter = ['is_active', 'category']
    search_fields = ['title', 'owner__email']
    inlines = [ListingPhotoInline, BlockedDateRangeInline]

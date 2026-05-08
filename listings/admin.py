from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _, ngettext
from .models import Category, Listing, ListingPhoto, BlockedDateRange


class ListingPhotoInline(admin.TabularInline):
    model = ListingPhoto
    extra = 0


class BlockedDateRangeInline(admin.TabularInline):
    model = BlockedDateRange
    extra = 0


@admin.action(description=_('Deactivate selected listings'))
def deactivate_listings(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    messages.success(request, ngettext(
        '%(n)d listing deactivated.', '%(n)d listings deactivated.', updated,
    ) % {'n': updated})


@admin.action(description=_('Activate selected listings'))
def activate_listings(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    messages.success(request, ngettext(
        '%(n)d listing activated.', '%(n)d listings activated.', updated,
    ) % {'n': updated})


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
    actions = [deactivate_listings, activate_listings]

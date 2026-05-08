from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _, ngettext
from .models import User, SiteSettings


@admin.action(description=_('Block selected users (prevent login)'))
def block_users(modeladmin, request, queryset):
    updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
    messages.success(request, ngettext(
        '%(n)d user blocked.', '%(n)d users blocked.', updated,
    ) % {'n': updated})


@admin.action(description=_('Unblock selected users'))
def unblock_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    messages.success(request, ngettext(
        '%(n)d user unblocked.', '%(n)d users unblocked.', updated,
    ) % {'n': updated})


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Profile'), {'fields': ('account_type', 'company_name', 'phone', 'location', 'avatar', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Profile'), {'fields': ('account_type', 'company_name', 'phone', 'location')}),
    )
    list_display = ('email', 'get_full_name', 'account_type', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('account_type', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'company_name')
    actions = [block_users, unblock_users]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fields = ['registration_open']

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

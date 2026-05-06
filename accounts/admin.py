from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (_('Profile'), {'fields': ('account_type', 'company_name', 'phone', 'location', 'avatar', 'bio')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_('Profile'), {'fields': ('account_type', 'company_name', 'phone', 'location')}),
    )
    list_display = ('email', 'username', 'account_type', 'is_active', 'is_staff')
    list_filter = ('account_type', 'is_active', 'is_staff')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'company_name')

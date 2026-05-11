from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        extra = sociallogin.account.extra_data
        user.account_type = 'person'
        user.is_active = True
        if not user.first_name:
            user.first_name = extra.get('given_name', '')
        if not user.last_name:
            user.last_name = extra.get('family_name', '')
        user.save(update_fields=['account_type', 'is_active', 'first_name', 'last_name'])
        return user

    def is_open_for_signup(self, request, sociallogin):
        from accounts.models import SiteSettings
        return SiteSettings.get().registration_open

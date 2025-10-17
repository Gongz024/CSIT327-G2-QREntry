from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.db.models.signals import post_migrate
        from .utils import create_organizer_account

        def create_default_account(sender, **kwargs):
            create_organizer_account()

        post_migrate.connect(create_default_account, sender=self)
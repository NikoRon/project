"""Create ONLY fake, local banking data for the OWASP teaching exercise."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from server.pages.models import Account, AuditEvent


class Command(BaseCommand):
    help = 'Reset fake balances and demo credentials (not for real data).'

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError('Seed is disabled when DEBUG is False.')

        demo_users = (
            ('bob', 'squarepants', 100, '2468'),
            ('alice', 'redqueen', 250, '1357'),
            ('patrick', 'asteroid', 42, '9876'),
        )
        for username, password, balance, pin in demo_users:
            user, _ = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.save()
            Account.objects.update_or_create(
                user=user,
                defaults={'balance': balance, 'card_pin': pin},
            )

        admin, _ = User.objects.get_or_create(username='admin')
        admin.set_password('admin')
        admin.is_staff = True
        admin.is_superuser = True
        admin.is_active = True
        admin.save()

        AuditEvent.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Demo accounts reset: bob, alice, patrick; admin.'))

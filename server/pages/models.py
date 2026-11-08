from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField()

    # A02 Cryptographic Failures: a sensitive card PIN stored as PLAIN TEXT.
    # The seed command populates distinct example PINs for the three users.
    card_pin = models.CharField(max_length=4, default='0000')


class AuditEvent(models.Model):
    """An empty audit trail until the A09 exercise is fixed."""

    created_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150)
    event = models.CharField(max_length=100)
    details = models.CharField(max_length=255, blank=True)

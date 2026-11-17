from django.contrib.auth.models import User
from django.db import models


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField()

    # A02 Cryptographic Failures:
    # Card PIN is stored in plaintext in the database.
    card_pin = models.CharField(max_length=4, default='0000')

    # A02 FIX: Replace the field above with the following.
    # Increase max_length to accommodate a salted password hash.
    # The PIN must also be hashed before saving (see seed_demo.py).
    # card_pin = models.CharField(max_length=255, default='')


class AuditEvent(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150)
    event = models.CharField(max_length=100)
    details = models.CharField(max_length=255, blank=True)
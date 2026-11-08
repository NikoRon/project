from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Account, AuditEvent


def balanceView(request):
    """Return a balance as JSON, keeping the original session exercise API."""
    if not request.user.is_authenticated:
        return JsonResponse({'username': 'anonymous', 'balance': 0})

    # A01 Broken Access Control: no check that the selected user is the caller.
    username = request.GET.get('user', request.user.username)
    try:
        account = Account.objects.select_related('user').get(user__username=username)
    except Account.DoesNotExist:
        return JsonResponse({'error': 'Account not found'}, status=404)
    return JsonResponse({'username': account.user.username, 'balance': account.balance})


@login_required
def homePageView(request):
    accounts = Account.objects.select_related('user').order_by('user__username')
    return render(request, 'pages/index.html', {'accounts': accounts})


@login_required
@require_POST
def transferView(request):
    """Transfer demo money. POST and CSRF remain in place for focused lessons."""
    from_username = request.POST.get('from_user', '')
    to_username = request.POST.get('to', '')

    try:
        amount = int(request.POST.get('amount', ''))
    except ValueError:
        return HttpResponseBadRequest('Amount must be an integer')

    if amount <= 0 or from_username == to_username:
        return HttpResponseBadRequest('Invalid transfer')

    try:
        with transaction.atomic():
            source = Account.objects.select_for_update().get(user__username=from_username)
            destination = Account.objects.select_for_update().get(user__username=to_username)
            if source.balance < amount:
                return HttpResponseBadRequest('Insufficient funds')

            # A01 Broken Access Control: client-supplied from_user is trusted.
            # The source account is never checked against request.user.
            source.balance -= amount
            destination.balance += amount
            source.save(update_fields=['balance'])
            destination.save(update_fields=['balance'])
    except Account.DoesNotExist:
        return HttpResponseBadRequest('Unknown account')

    # A09 Security Logging and Monitoring Failures:
    # deliberately NO AuditEvent for transfers (or failed login attempts).
    messages.success(request, 'Transfer completed.')
    return redirect('home')


@login_required
def searchView(request):
    """Find a demo account by username."""
    username = request.GET.get('username', '')
    results = []
    if username:
        # A03 Injection: interpolating user input into SQL without parameters.
        query = f"SELECT username FROM auth_user WHERE username = '{username}'"
        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

    return render(request, 'pages/search.html', {'username': username, 'results': results})


@login_required
def auditView(request):
    """Admin-only readout to observe the intentionally missing audit events."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Admin only')
    events = AuditEvent.objects.order_by('-created_at')[:50]
    return render(request, 'pages/audit.html', {'events': events})
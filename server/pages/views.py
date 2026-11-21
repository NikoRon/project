
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Account, AuditEvent


# A01 FIX: Require authentication before accessing account information.
# @login_required
def balanceView(request):
    """Return a balance as JSON, keeping the original session exercise API."""
    if not request.user.is_authenticated:
        return JsonResponse({'username': 'anonymous', 'balance': 0})

    # A01 Broken Access Control:
    # The user can select anyone's account through the URL parameter.
    username = request.GET.get('user', request.user.username)

    # A01 FIX: Remove the line above and use the authenticated user.
    # username = request.user.username

    try:
        account = Account.objects.select_related('user').get(user__username=username)

        # A01 FIX: Replace the query above with the following.
        # This ensures that users can only access their own account.
        # account = Account.objects.select_related('user').get(user=request.user)

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

    # A01 Broken Access Control:
    # The sender account is determined by client-provided information.
    from_username = request.POST.get('from_user', '')
    
    # A01 FIX: Replace the line above with the following.
    # The sender must always be the authenticated user.
    # from_username = request.user.username

    to_username = request.POST.get('to', '')

    try:
        amount = int(request.POST.get('amount', ''))
    except ValueError:
        return HttpResponseBadRequest('Amount must be an integer')

    if amount <= 0 or from_username == to_username:
        return HttpResponseBadRequest('Invalid transfer')

    try:
        with transaction.atomic():

            # A01 Broken Access Control:
            # No verification that the sender owns this account.
            source = Account.objects.select_for_update().get(user__username=from_username)

            # A01 FIX: Replace the query above with the following.
            # Always use the authenticated user as the account owner.
            # source = Account.objects.select_for_update().get(user=request.user)

            destination = Account.objects.select_for_update().get(user__username=to_username)

            if source.balance < amount:
                return HttpResponseBadRequest('Insufficient funds')

            source.balance -= amount
            destination.balance += amount
            source.save(update_fields=['balance'])
            destination.save(update_fields=['balance'])

    except Account.DoesNotExist:
        return HttpResponseBadRequest('Unknown account')

    # A09 Security Logging and Monitoring Failures:
    # Deliberately NO AuditEvent for transfers or failed login attempts.
    messages.success(request, 'Transfer completed.')
    return redirect('home')



@login_required
def searchView(request):
    username = request.GET.get('username', '')
    results = []

    if username:
        # A03 Injection:
        # User input is directly inserted into the SQL query.
        # An attacker can modify the query using SQL injection.
        query = f"SELECT username FROM auth_user WHERE username = '{username}'"

        with connection.cursor() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()

        # A03 FIX: Use a parameterized query instead.
        # The database treats username as data, not as SQL code.
        #
        # query = "SELECT username FROM auth_user WHERE username = %s"
        # with connection.cursor() as cursor:
        #     cursor.execute(query, [username])
        #     results = cursor.fetchall()

    return render(
        request,
        'pages/search.html',
        {'username': username, 'results': results}
    )


@login_required
def auditView(request):
    """Admin-only access to observe audit events."""
    if not request.user.is_staff:
        return HttpResponseForbidden('Admin only')
    events = AuditEvent.objects.order_by('-created_at')[:50]
    return render(request, 'pages/audit.html', {'events': events})

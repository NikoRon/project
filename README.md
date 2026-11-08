# MOOC Cybersecurity project software - 5 flaws and their fixes

This Django-app is based on part2-13.sessionhijack -task, as it provides a good basis for the software.

### Initial adjustments:
1. Install new (enough) Python and Django (make sure they work together)
2. Unzip the file and copy the path of manage.py
3. Run the followin lines:

```Powershell
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

4. Open `http://127.0.0.1:8000/login/`.

`seed_demo` **resets** initial data and clears the log.
### Accounts

| User | Password | Amount |
| --- | --- | ---: |
| bob | squarepants | 100 € |
| alice | redqueen | 250 € |
| patrick | asteroid | 42 € |
| admin | admin | No account |

Only admin has access to event history from `/audit/`.

## Overview on the five Flaws from OWASP 2021.

| OWASP 2021 | Where? | What happens? |
| --- | --- | --- |
| **A01 Broken Access Control** | `server/pages/views.py`: `balanceView` ja `transferView` | Bob can see Alice's amount by changing the `user`-parameter. The Transfer `from_user` comes from the client without checking the permission. |
| **A02 Cryptographic Failures** | `server/pages/models.py`: `Account.card_pin` | Card PIN is stored in the database as such. One can find it from the SQLite-database. |
| **A03 Injection** | `server/pages/views.py`: `searchView` | `username` can be used to get data with SQL-Injection. |
| **A07 Identification and Authentication Failures** | `server/config/simplesession.py` | Session ID is accessible and easily iterated (`session-0`, `session-1`, etc.). The old `src/hijacksession.py` shows this issue. |
| **A09 Security Logging and Monitoring Failures** | `server/pages/views.py` and `/login/` | Event history is not working, no `AuditEvent`-logs. Admin's `/audit/` remains empty. |

### Examples for investigating vulnerabilities

- A01: Log in as Bob and open `/balance/?user=alice`.
- A01: In your browser's developer tools, change the hidden `from_user` field in Bob's transfer form to `alice`.
- A02: Run `python manage.py shell`, then execute
`from server.pages.models import Account` and
`print(list(Account.objects.values_list('user__username', 'card_pin')))`.
- A03: Enter `' OR 1=1 --` into the customer search field.
- A07: Inspect the `sessionid` cookie using your browser's developer tools.
- A09: Perform a transfer and an unsuccessful login attempt, then access `/audit/` as an administrator.

## Testing

```bash
python manage.py test server.pages.test_owasp
```

Seven tests verify the current **vulnerable baseline state** as well as the application's core functionality. As we fix the vulnerabilities one by one, we will update the corresponding OWASP test to expect secure behavior.

## What is intended to be fixed later?

During the remediation phase, A01, A02, A03, A07, and A09 will be addressed individually.
In this package, **none of these five issues have been fixed**.

### Other notes

- The transfer operation already utilizes a POST request, a CSRF token, and a database transaction, ensuring that the five vulnerabilities covered in this exercise remain distinct from one another. - User **login passwords** are in Django hash format; 
for the purpose of exercise A02, the data provided in plaintext is the **card PIN**.
- The original session hijacking script, `src/hijacksession.py`, is included.
- In the ZIP version, legacy MOOC/TMC test drivers and the old database have been
omitted. Running `migrate` and `seed_demo` will create a reproducible exercise environment.
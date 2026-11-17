# MOOC Cybersecurity project software - 5 flaws and their fixes

This Django-app is based on part2-13.sessionhijack -task, as it provides a good basis for the software. This is simple "banking"-app where one can log in to their account and transfer money to other, within their account's amount of course. The fixes for these flaws are commented out inside the code. By making these commented changes to the files, the flaws are fixed.

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

The folder `Screenshots` contains relevant screenshots. Explanations for all photos are given in this file.

## Overview on the five Flaws from OWASP 2021.

| OWASP 2021 | Where flaws? | What happens? |
| --- | --- | --- |
| **A01 Broken Access Control** | `server/pages/views.py`: `balanceView` and `transferView` | Bob can see Alice's amount by changing the `user`-parameter. The Transfer `from_user` comes from the client without checking the permission. |
| **A02 Cryptographic Failure** | `server/pages/models.py`: `Account.card_pin` | Card PIN is stored in the database as such. One can find it from the SQLite-database. |
| **A03 Injection** | `server/pages/views.py`: `searchView` | `username` can be used to get data with SQL-Injection. |
| **A07 Identification and Authentication Failures** | `server/config/simplesession.py` | Session ID is accessible and easily iterated (`session-0`, `session-1`, etc.). The old `src/hijacksession.py` shows this issue. |
| **A09 Security Logging and Monitoring Failures** | `server/pages/views.py` and `/login/` | Event history is not working, no `AuditEvent`-logs. Admin's `/audit/` remains empty. |

### Examples for demonstrating vulnerabilities

- A01: Log in as Bob and open `/balance/?user=alice`.
- A01: In your browser's developer tools, change the hidden `from_user` field in Bob's transfer form to `alice`.
- A02: Run `python manage.py shell`, then execute
`from server.pages.models import Account` and
`print(list(Account.objects.values_list('user__username', 'card_pin')))`.
- A03: Enter `' OR 1=1 --` into the customer search field.
- A07: Inspect the `sessionid` cookie using your browser's developer tools.
- A09: Perform a transfer and an unsuccessful login attempt, then access `/audit/` as an administrator.

### Flaw A01 - Broken Access Control

Sources of flaw:

Index.html:
https://github.com/NikoRon/project/blob/83feb1a0406d9f9da215698b4756490d7f552630/server/pages/templates/pages/index.html#L39

and views.py:
balanceView:
https://github.com/NikoRon/project/blob/83feb1a0406d9f9da215698b4756490d7f552630/server/pages/views.py#L14

transferView:
https://github.com/NikoRon/project/blob/83feb1a0406d9f9da215698b4756490d7f552630/server/pages/views.py#L47

Users can see other users’ bank balance by changing the user-parameter in url directly. The access control is not done on server-side. These flaws are found in index.html and views.py. 

In `index.html`, the server should determine the sender by using request.user, not the client side. Hence, the fix is to remove `from_user` -input from line 39 (in index.html). Now one cannot change the `from_user`-value via browser's developer tools. Following fixes with `transferView` is related to this. 

In `views.py`, both `balanceView`- and `transferView`-functions need fixes. First `balanceview`: By changing the line 21 with commented line 24, the user cannot see others’ balances anymore with url-hacking ( = .../balance/?=user='otheruser'). By replacing line 27 with commented line 31 the user can only access ther own account. Changes to `transferView`: The sender account it determined by client side at line 51. By replacing this with commented line 55 fixes the issue. In addition, line 72 has a flaw that doesn't ensure the account is user's own. By replacing it with commented line 76 fixes it by ensuring that only an authenticated user can access the view. After these fixes one cannot access other's balance via url or developer tools.



Relevant screenshots: "A01 Logged in as Bob" shows the initial state when Bob has signed in to his account. When logged in, Bob can type ".../balance/?user=alice" into url and get the view that is seen with screenshot "A01 Access to Alice's balance via Bob's account".

### Flaw A02 - Cryptographic Failure


### Other notes

- The transfer operation already utilizes a POST request, a CSRF token, and a database transaction, ensuring that the five vulnerabilities covered in this exercise remain distinct from one another. - User **login passwords** are in Django hash format; 
for the purpose of exercise A02, the data provided in plaintext is the **card PIN**.
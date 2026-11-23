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
| **A02 Cryptographic Failures** | `server/pages/models.py`: `Account.card_pin` | Card PIN is stored in the database as such. One can find it from the SQLite-database. |
| **A03 Injection** | `server/pages/views.py`: `searchView` | `username` can be used to get data with SQL-Injection. |
| **A07 Identification and Authentication Failures** | `server/config/simplesession.py`: `server/config/settings.py` | Session ID is accessible and easily iterated (`session-0`, `session-1`, etc.). |
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

## Flaw A01 - Broken Access Control

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

## Flaw A02 - Cryptographic Failure

Sources:

seed_demo.py:
https://github.com/NikoRon/project/blob/10177959af82b6bde6d7b636d088f42ffadd4884/server/pages/management/commands/seed_demo.py#L40
(as well as line 9!)

models.py:
https://github.com/NikoRon/project/blob/10177959af82b6bde6d7b636d088f42ffadd4884/server/pages/models.py#L5

Screenshot `A02 PIN accessed via powershell` demonstrates the initial flaw before fixes are applied.

The application stores users' four-digit card PINs directly in the database without cryptographic protection. Anyone with access to the database can read these PINs. In `models.py`, the card_pin field has a maximum length of four characters and is used to store the original PIN. In `seed_demo.py`, the PIN is inserted directly into the database using defaults={'balance': balance, 'card_pin': pin}.

In `models.py`, replacing the existing card_pin field at line 11 with the commented version at line 16 that supports longer password hashes. In `seed_demo.py`, import Django's make_password function (line 9) and replace the vulnerable database insertion (line 40) with the commented version (line 44) using make_password(pin). This ensures that PINs are hashed before storage rather than saved as plaintext. The database schema must then be migrated, and the existing plaintext PINs must be replaced.

## Flaw A03 Injection

Source:

https://github.com/NikoRon/project/blob/8b7f52363ccb457c3600f6359124e9ca91a54ea2/server/pages/views.py#L107

The customer search function uses raw SQL and inserts the user's input directly into the query string. The vulnerable code is between lines 107 and 111. Because the input is not parameterized, a user can manipulate the SQL query by entering SQL syntax into the search field. Bntering "' OR 1=1 --", one can modify the query's condition and return other usernames instead of only the requested account.

The fix is to replace these lines with commented lines from 116 to 119. The username is now passed to the database as a parameter rather than being directly concatenated into the SQL statement. This prevents the input from being interpreted as executable SQL code.

The initial vulnerability can be seen at the screenshot "A03 SQL Injection". 

## Flaw A07 Identification and Authentification Failures

Sources:

[server/config/simplesession.py](https://github.com/NikoRon/project/blob/1f3d13650ae9426ede9b27944c5653ccf510420f/server/config/simplesession.py#L7)

[server/config/settings.py](https://github.com/NikoRon/project/blob/6e55d40959f6a12216979577541f23574d1f3b39/server/config/settings.py#L57)

The application uses a custom session engine that generates predictable session identifiers such as session-0, session-1, and session-2. This is an authentication vulnerability because an attacker can easily guess another user's session ID and impersonate that user without knowing their password.

The vulnerability can be demonstrated by logging in to Bob's account with Edge and into Alice's account with Chrome. The Screenshot `A07 Predictable sessionid` shows the situation where both accounts are logged into, with developer view (F12 showing the 'application'-site). As these sessions are currently running, one can for example double click Bob's side of developer view, and change the sessionid from value 'session-0' to 'session-1'. Now, typing 'http://127.0.0.1:8000/balance/' as url, Bob can see Alice's balance. 

The fix is replace the vulnerable SESSION_ENGINE setting in `server/config/settings.py` line 57 with the commented, secure version at line 59. This line 59 is Django's standard session engine that generates unpredictable session id's instead of 0,1,2, etc. This makes guessing another user's session ID impossible.

### Other notes

- The transfer operation already utilizes a POST request, a CSRF token, and a database transaction, ensuring that the five vulnerabilities covered in this exercise remain distinct from one another. - User **login passwords** are in Django hash format; 
for the purpose of exercise A02, the data provided in plaintext is the **card PIN**.
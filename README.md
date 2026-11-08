# OWASP Top 10:2021 – tarkoituksella haavoittuva harjoituspankki

Tämä Django-sovellus perustuu Cybersecurity Base MOOCin
`part2-13.sessionhijack`-pankkiin. **Se on tarkoituksella turvaton.**
Sitä saa käyttää **vain omalla koneella**, kuvitteellisilla käyttäjillä
ja paikallisesti osoitteessa `127.0.0.1`. Älä julkaise palvelua verkkoon.

## Käynnistys

1. Asenna Python 3.10+.
2. Pura ZIP ja avaa pääte sen kansioon, jossa `manage.py` on.
3. Suorita:

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8000
```

4. Avaa `http://127.0.0.1:8000/login/`.

`seed_demo` **palauttaa** joka kerralla testikäyttäjien salasanat, saldot
ja PIN-koodit aloitusarvoihin sekä tyhjentää harjoituksen tapahtumalokin.
Tämä on tarkoitettu testidatalle, ei oikeille tiedoille.

### Tunnukset

| Käyttäjä | Salasana | Alkusaldo |
| --- | --- | ---: |
| bob | squarepants | 100 € |
| alice | redqueen | 250 € |
| patrick | asteroid | 42 € |
| admin | admin | ei omaa tiliä |

Admin voi katsoa sovelluksen tapahtumalokia osoitteessa `/audit/`.

## Viisi korjaamatonta haavoittuvuutta

| OWASP 2021 | Missä koodissa? | Miten puute näkyy? |
| --- | --- | --- |
| **A01 Broken Access Control** | `server/pages/views.py`: `balanceView` ja `transferView` | Bob voi nähdä Alicen saldon muuttamalla `user`-parametria. Tilisiirron `from_user` tulee asiakkaalta eikä omistajuutta tarkisteta. |
| **A02 Cryptographic Failures** | `server/pages/models.py`: `Account.card_pin` | Kuvitteellinen kortin PIN tallennetaan tietokantaan sellaisenaan. Esimerkkikoodin näkee SQLite-tietokannasta tai Django-shellistä. |
| **A03 Injection** | `server/pages/views.py`: `searchView` | `username` liitetään SQL-kyselyyn suoraan. Asiakashaku palauttaa muiden tilien tietoja SQL-injektiolla. |
| **A07 Identification and Authentication Failures** | `server/config/simplesession.py` | Kirjautumisistuntojen tunnukset ovat ennustettavia (`session-0`, `session-1`, jne.). Vanha `src/hijacksession.py` havainnollistaa ongelman. |
| **A09 Security Logging and Monitoring Failures** | `server/pages/views.py` ja `/login/` | Tilisiirroista ja epäonnistuneista kirjautumisista ei muodostu `AuditEvent`-merkintöjä. Adminin `/audit/` pysyy tyhjänä. |

### Esimerkkejä puutteiden tutkimiseen

- A01: Kirjaudu Bobina ja avaa `/balance/?user=alice`.
- A01: Muuta Bobin tilisiirtolomakkeen piilotettu `from_user`-kenttä
  selaimen kehittäjätyökaluissa arvoksi `alice`.
- A02: `python manage.py shell`, sitten
  `from server.pages.models import Account` ja
  `print(list(Account.objects.values_list('user__username', 'card_pin')))`.
- A03: Asiakashakuun syöte `' OR 1=1 --`.
- A07: Tutki istunnon `sessionid`-evästettä selaimen kehittäjätyökaluilla.
- A09: Tee siirto ja väärä kirjautuminen, sitten avaa adminina `/audit/`.

## Testaus

```bash
python manage.py test server.pages.test_owasp
```

Seitsemän testiä vahvistaa nykyisen **haavoittuvan lähtötilan** sekä
sovelluksen perustoiminnan. Kun korjaamme puutteet yksi kerrallaan,
vaihdamme kyseisen OWASP-testin odottamaan turvallista toimintaa.

## Mitä on tarkoitus korjata myöhemmin?

Korjauskierroksella käsitellään A01, A02, A03, A07 ja A09 erikseen.
Tässä paketissa **mitään näistä viidestä ei ole korjattu**.

### Muuta

- Siirto käyttää jo POST-pyyntöä, CSRF-tokenia ja tietokantatransaktiota,
  jotta harjoituksen viisi puutetta pysyvät erillisinä.
- Käyttäjien **kirjautumissalasanat** ovat Django-hash-muodossa;
  A02-harjoituksen tarkoituksella selväkielinen tieto on **kortin PIN**.
- Mukana on alkuperäinen istunnon tunnistusskripti `src/hijacksession.py`.
- ZIP-versiossa vanhat MOOC/TMC-testiajurit ja vanha tietokanta on jätetty
  pois. `migrate` ja `seed_demo` luovat toistettavan harjoitusympäristön.

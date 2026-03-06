import psycopg2
import os

# User's list
user_list_raw = """
Sąd Okręgowy w Białymstoku
Sąd Okręgowy w Bielsku-Białej
Sąd Okręgowy w Bydgoszczy
Sąd Okręgowy w CZęstochowie
Sąd Okręgowy w Elblągu
Sąd Okręgowy w Gdańsku
Sąd Okręgowy w Gliwicach
Sąd Okręgowy w Gorzowie Wielkopolskim
Sąd Okręgowy w Jeleniej Górze
Sąd Okręgowy w Kaliszu
Sąd Okręgowy w Katowicach
Sąd Okręgowy w Kielcach
Sąd Okręgowy w Koninie
Sąd Okręgowy w Koszalinie
Sąd Okręgowy w Krakowie
Sąd Okręgowy w Krośnie
Sąd Okręgowy w Legnicy
Sąd Okręgowy w Lublinie
Sąd Okręgowy w Łomży
Sąd Okręgowy w Łodzi
Sąd Okręgowy w Nowym Sączu
Sąd Okręgowy w Olsztynie
Sąd Okręgowy w Opolu
Sąd Okręgowy w Ostrołęce
Sąd Okręgowy w Piotrkowie Trybunalskim
Sąd Okręgowy w Płocku
Sąd Okręgowy w Poznaniu
Sąd Okręgowy w Przemyślu
Sąd Okręgowy w Radomiu
Sąd Okręgowy w Rybniku
Sąd Okręgowy w Rzeszowie
Sąd Okręgowy w Siedlcach
Sąd Okręgowy w Sieradzu
Sąd Okręgowy w Słupsku
Sąd Okręgowy w Sosnowcu
Sąd Okręgowy w Suwałkach
Sąd Okręgowy w Szczecinie
Sąd Okręgowy w Świdnicy
Sąd Okręgowy w Tarnobrzegu
Sąd Okręgowy w Tarnowie
Sąd Okręgowy w Toruniu
Sąd Okręgowy w Warszawie
Sąd Okręgowy Warszawa-Praga w Warszawie
Sąd Okręgowy we Włocławku
Sąd Okręgowy we Wrocławiu
Sąd Okręgowy w Zamościu
Sąd Okręgowy w Zielonej Górz
"""

def normalize(name):
    return name.strip()

user_set = set(normalize(line) for line in user_list_raw.strip().split('\n') if line.strip())

# DB Fetch
conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("SELECT name FROM courts.courts WHERE kind = 'district'")
db_rows = cur.fetchall()
db_set = set(row[0] for row in db_rows)

conn.close()

# Comparison
only_in_user = user_set - db_set
only_in_db = db_set - user_set

print(f"Total in User List: {len(user_set)}")
print(f"Total in Database: {len(db_set)}")

if not only_in_user and not only_in_db:
    print("\nSUCCESS: Both lists are identical.")
else:
    print("\n--- Differences Found ---")
    if only_in_user:
        print("\nPresent in User List but NOT in Database:")
        for x in sorted(only_in_user):
            print(f" - {x}")
    
    if only_in_db:
        print("\nPresent in Database but NOT in User List:")
        for x in sorted(only_in_db):
            print(f" - {x}")

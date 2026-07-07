import urllib.request
import json
import os
import sys

BEHOLD_URL = "https://feeds.behold.so/XHOEpcYGrSPvFmsL5PxR"
GITHUB_USERNAME = "statoplast"
REPO_NAME = "ig-galerija"


def run():
    if not os.path.exists('images'):
        os.makedirs('images')

    # 1. Učitaj postojeće projekte (povijest) kako ih ne bi izgubili
    postojeci_projekti = []
    if os.path.exists('projekti.json'):
        try:
            with open('projekti.json', 'r', encoding='utf-8') as f:
                postojeci_projekti = json.load(f)
        except json.JSONDecodeError:
            print("projekti.json je prazan ili neispravan, krećemo ispočetka.")

    # Napravi listu postojećih linkova da znamo što već imamo
    postojeci_linkovi = {p['permalink'] for p in postojeci_projekti}

    print("Dohvaćam podatke s Beholda...")
    req = urllib.request.Request(BEHOLD_URL, headers={'User-Agent': 'Mozilla/5.0'})

    try:
        response = urllib.request.urlopen(req)
        raw_content = response.read().decode('utf-8')
        data = json.loads(raw_content)
    except Exception as e:
        print(f"Greška pri dohvaćanju URL-a ili parsiranju JSON-a: {e}")
        sys.exit(1)

    posts_list = []
    if isinstance(data, list):
        posts_list = data
    elif isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            posts_list = data["data"]
        elif "posts" in data and isinstance(data["posts"], list):
            posts_list = data["posts"]
        else:
            sys.exit(1)

    novi_projekti_za_dodavanje = []

    for post in posts_list:
        if not isinstance(post, dict):
            continue

        permalink = post.get("permalink")
        media_url = post.get("mediaUrl") or post.get("media_url")

        if not permalink or not media_url:
            continue

        # 2. Ako ovaj post već imamo u našem JSON-u, preskoči ga!
        if permalink in postojeci_linkovi:
            continue

        post_id = permalink.rstrip('/').split('/')[-1]
        slika_ime = f"{post_id}.jpg"
        slika_putanja = f"images/{slika_ime}"

        # 3. Provjeri je li slika stvarno dostupna prije nego je dodamo u JSON.
        #    Ako slika već postoji i nije prazna, koristimo je.
        #    Inače je pokušavamo skinuti; ako skidanje ne uspije, PRESKAČEMO
        #    ovaj post (bez dodavanja u JSON), pa će se pokušati ponovno
        #    sljedeći put umjesto da ostane trajno slomljen link.
        slika_spremna = os.path.exists(slika_putanja) and os.path.getsize(slika_putanja) > 0

        if not slika_spremna:
            print(f"Skidam novu sliku: {slika_ime}")
            try:
                img_req = urllib.request.Request(media_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(img_req) as response_img, open(slika_putanja, 'wb') as out_file:
                    out_file.write(response_img.read())

                # Provjeri da datoteka nije prazna nakon skidanja
                if os.path.getsize(slika_putanja) > 0:
                    slika_spremna = True
                else:
                    raise ValueError("Skinuta datoteka je prazna.")
            except Exception as e:
                print(f"Greška pri skidanju {slika_ime}: {e} — preskačem ovaj post (pokušat ću opet sljedeći put).")
                # Očisti eventualnu djelomično skinutu / praznu datoteku
                if os.path.exists(slika_putanja):
                    try:
                        os.remove(slika_putanja)
                    except OSError:
                        pass
                continue  # Ne dodaj u JSON dok slika ne postoji

        github_slika_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/{slika_putanja}"

        novi_projekti_za_dodavanje.append({
            "permalink": permalink,
            "mediaUrl": github_slika_url
        })

    # 4. Spoji nove projekte (na vrh) i stare projekte (ispod njih)
    svi_projekti = novi_projekti_za_dodavanje + postojeci_projekti

    # 5. Spremi obogaćenu listu natrag u projekti.json
    with open('projekti.json', 'w', encoding='utf-8') as f:
        json.dump(svi_projekti, f, indent=4)

    print(f"Dodano {len(novi_projekti_za_dodavanje)} novih postova. Ukupno arhivirano: {len(svi_projekti)}.")


if __name__ == "__main__":
    run()

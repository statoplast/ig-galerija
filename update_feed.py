import urllib.request
import json
import os
import sys

BEHOLD_URL = "https://feeds.behold.so/XHOEpcYGrSPvFmsL5PxR"
GITHUB_USERNAME = "statoplast"
REPO_NAME = "ig-galerija"


def dohvati_sliku_url(post):
    """
    Vrati URL slike za post.
    - IMAGE / CAROUSEL_ALBUM -> mediaUrl (obicna slika)
    - VIDEO / REEL           -> thumbnailUrl (sličica videa, jer je mediaUrl .mp4!)
    Ako za video nema thumbnaila, vrati None (preskačemo taj post).
    """
    media_type = (post.get("mediaType") or post.get("media_type") or "").upper()
    media_url = post.get("mediaUrl") or post.get("media_url")
    thumbnail_url = post.get("thumbnailUrl") or post.get("thumbnail_url")

    if media_type in ("VIDEO", "REEL", "REELS"):
        return thumbnail_url  # može biti None -> post se preskače

    # Ako tip nije naveden, a mediaUrl izgleda kao video, koristi thumbnail
    if media_url and media_url.split("?")[0].lower().endswith((".mp4", ".mov")):
        return thumbnail_url

    return media_url


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
        if not permalink:
            continue

        # Preskoči postove koje već imamo
        if permalink in postojeci_linkovi:
            continue

        # 2. REELS FIX: za video postove koristi thumbnailUrl, ne mediaUrl (.mp4)
        slika_url = dohvati_sliku_url(post)
        if not slika_url:
            print(f"Preskačem post bez upotrebljive slike (vjerojatno reel bez thumbnaila): {permalink}")
            continue

        # 3. TIMESTAMP: spremamo datum posta da bismo mogli ispravno sortirati
        timestamp = post.get("timestamp") or post.get("createdAt") or ""

        post_id = permalink.rstrip('/').split('/')[-1]
        slika_ime = f"{post_id}.jpg"
        slika_putanja = f"images/{slika_ime}"

        slika_spremna = os.path.exists(slika_putanja) and os.path.getsize(slika_putanja) > 0

        if not slika_spremna:
            print(f"Skidam novu sliku: {slika_ime}")
            try:
                img_req = urllib.request.Request(slika_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(img_req) as response_img, open(slika_putanja, 'wb') as out_file:
                    out_file.write(response_img.read())

                if os.path.getsize(slika_putanja) > 0:
                    slika_spremna = True
                else:
                    raise ValueError("Skinuta datoteka je prazna.")
            except Exception as e:
                print(f"Greška pri skidanju {slika_ime}: {e} — preskačem (pokušat ću opet sljedeći put).")
                if os.path.exists(slika_putanja):
                    try:
                        os.remove(slika_putanja)
                    except OSError:
                        pass
                continue

        github_slika_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/{slika_putanja}"

        novi_projekti_za_dodavanje.append({
            "permalink": permalink,
            "mediaUrl": github_slika_url,
            "timestamp": timestamp,
        })

    # 4. Spoji sve postove
    svi_projekti = novi_projekti_za_dodavanje + postojeci_projekti

    # 5. SORT FIX: sortiraj po datumu, najnoviji prvi.
    #    Postovi bez timestampa idu na kraj (dobiju prazan string).
    svi_projekti.sort(key=lambda p: p.get("timestamp") or "", reverse=True)

    with open('projekti.json', 'w', encoding='utf-8') as f:
        json.dump(svi_projekti, f, indent=4, ensure_ascii=False)

    print(f"Dodano {len(novi_projekti_za_dodavanje)} novih postova. Ukupno arhivirano: {len(svi_projekti)}.")


if __name__ == "__main__":
    run()

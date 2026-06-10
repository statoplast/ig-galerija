import urllib.request
import json
import os

# 1. Tvoj Behold JSON link
BEHOLD_URL = "https://feeds.behold.so/XHOEpcYGrSPvFmsL5PxR"

# 2. Tvoj GitHub korisnički račun i repozitorij
GITHUB_USERNAME = "statoplast"
REPO_NAME = "ig-galerija"

def run():
    # Kreiraj mapu za slike ako ne postoji
    if not os.path.exists('images'):
        os.makedirs('images')

    print("Dohvaćam podatke s Beholda...")
    req = urllib.request.Request(BEHOLD_URL, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Greška s Beholdom: {e}")
        return

    novi_projekti = []
    
    # Prođi kroz sve postove koje ti Behold da
    for post in data:
        permalink = post.get("permalink")
        media_url = post.get("mediaUrl")
        
        if not permalink or not media_url:
            continue
            
        # Izvuci kod posta iz Instagram linka
        post_id = permalink.rstrip('/').split('/')[-1]
        slika_ime = f"{post_id}.jpg"
        slika_putanja = f"images/{slika_ime}"
        
        # Ako slika već ne postoji na tvom GitHubu, skini ju
        if not os.path.exists(slika_putanja):
            print(f"Skidam novu sliku s Beholda: {slika_ime}")
            try:
                img_req = urllib.request.Request(media_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(img_req) as response_img, open(slika_putanja, 'wb') as out_file:
                    out_file.write(response_img.read())
            except Exception as e:
                print(f"Greška pri skidanju {slika_ime}: {e}")
        
        # Stvori trajni javni link na tvoju sliku spremljenu na GitHubu
        github_slika_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/{slika_putanja}"
        
        # Dodaj u novi, tvoj vlastiti JSON
        novi_projekti.append({
            "permalink": permalink,
            "mediaUrl": github_slika_url
        })

    # Spremi novi projekti.json
    with open('projekti.json', 'w', encoding='utf-8') as f:
        json.dump(novi_projekti, f, indent=4)
        
    print("Ažuriranje i backup slika su uspješno završeni!")

if __name__ == "__main__":
    run()

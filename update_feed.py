import urllib.request
import json
import os
import sys

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
        raw_content = response.read().decode('utf-8')
        data = json.loads(raw_content)
    except Exception as e:
        print(f"Greška pri dohvaćanju URL-a ili parsiranju JSON-a: {e}")
        sys.exit(1)

    # Provjera formata podataka (može biti lista ili rječnik)
    posts_list = []
    if isinstance(data, list):
        posts_list = data
    elif isinstance(data, dict):
        if "data" in data and isinstance(data["data"], list):
            posts_list = data["data"]
        elif "posts" in data and isinstance(data["posts"], list):
            posts_list = data["posts"]
        else:
            print("Behold je vratio rječnik, ali ne nalazim listu postova. Ključevi:", data.keys())
            sys.exit(1)
    else:
        print(f"Neočekivan tip podataka od Beholda: {type(data)}")
        sys.exit(1)

    novi_projekti = []
    
    # Prođi kroz sve filtrirane postove
    for post in posts_list:
        if not isinstance(post, dict):
            continue
            
        permalink = post.get("permalink")
        media_url = post.get("mediaUrl") or post.get("media_url")
        
        if not permalink or not media_url:
            continue
            
        # Izvuci jedinstveni kod posta iz Instagram linka
        post_id = permalink.rstrip('/').split('/')[-1]
        slika_ime = f"{post_id}.jpg"
        slika_putanja = f"images/{slika_ime}"
        
        # Ako slika već ne postoji na tvom GitHubu, skini ju
        if not os.path.exists(slika_putanja):
            print(f"Skidam novu sliku: {slika_ime}")
            try:
                img_req = urllib.request.Request(media_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(img_req) as response_img, open(slika_putanja, 'wb') as out_file:
                    out_file.write(response_img.read())
            except Exception as e:
                print(f"Greška pri skidanju {slika_ime}: {e}")
        
        # Stvori trajni javni link na tvoju sliku spremljenu na GitHubu
        github_slika_url = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{REPO_NAME}/main/{slika_putanja}"
        
        novi_projekti.append({
            "permalink": permalink,
            "mediaUrl": github_slika_url
        })

    # Spremi novi projekti.json
    with open('projekti.json', 'w', encoding='utf-8') as f:
        json.dump(novi_projekti, f, indent=4)
        
    print(f"Uspješno sinkronizirano {len(novi_projekti)} postova u projekti.json!")

if __name__ == "__main__":
    run()

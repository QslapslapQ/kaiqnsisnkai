import requests
from bs4 import BeautifulSoup
import re

BASE = "https://animefire.io"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
    "Referer": BASE,
    "Accept-Language": "pt-BR,pt;q=0.9"
}

def _get(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r
    except Exception:
        return None

def search(query: str):
    q = query.strip().replace(" ", "-")
    url = f"{BASE}/pesquisar/{q}"
    r = _get(url)
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    for card in soup.select("article.cardUltimosEps, div.divCardUltimosEps"):
        a = card.find("a", href=True)
        img = card.find("img")
        title = card.find("h3") or card.find("h2")
        if not a:
            continue
        href = a["href"] if a["href"].startswith("http") else BASE + a["href"]
        raw_slug = href.split("/animes/")[-1].replace("-todos-os-episodios", "").strip("/")
        if raw_slug.endswith("-dublado"):
            version = "dublado"
            base_slug = raw_slug[:-len("-dublado")]
        else:
            version = "legendado"
            base_slug = raw_slug
        image_url = None
        if img:
            image_url = img.get("data-src") or img.get("src") or img.get("data-lazy-src")
        existing = next((x for x in results if x["slug"] == base_slug), None)
        if existing:
            existing["versions"].append({"version": version, "slug": raw_slug, "link": href})
        else:
            results.append({
                "slug": base_slug,
                "title": title.text.strip().replace(" (Dublado)", "").replace(" (Legendado)", "") if title else base_slug,
                "image": image_url,
                "versions": [{"version": version, "slug": raw_slug, "link": href}]
            })
    return results

def get_anime(slug: str):
    url = f"{BASE}/animes/{slug}-todos-os-episodios"
    r = _get(url)
    if not r:
        url = f"{BASE}/animes/{slug}"
        r = _get(url)
    if not r:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    def sel(*args):
        for s in args:
            el = soup.select_one(s)
            if el:
                return el
        return None
    title_el = sel("h1.animeTitle", "div.divMainNomeAnime h1", "h1")
    synopsis_el = sel("div.divSinopse")
    image_url = None
    for img in soup.select("img"):
        src = img.get("data-src") or img.get("src") or ""
        classes = img.get("class", [])
        if "imgAnimes" in classes or "cmtImg" in classes:
            continue
        if any(x in src for x in ["/img/animes/", "/capas/"]):
            image_url = src
            break
    genre_tags = soup.select("div.animeInfo a")
    genres_text = ", ".join(
        a.text.strip() for a in genre_tags
        if a.text.strip() and not re.match(r"^A[0-9]+$", a.text.strip())
    ) or None
    score_text = None
    for span in soup.select("div.animeInfo span, span"):
        t = span.text.strip()
        try:
            v = float(t)
            if 0 < v <= 10:
                score_text = t
                break
        except ValueError:
            pass
    episodes = []
    seen_eps = set()
    for ep_link in soup.select("a.lEp, a[href*='/animes/']"):
        ep_href = ep_link["href"]
        if ep_href in seen_eps:
            continue
        seen_eps.add(ep_href)
        ep_num_match = re.search(r'/([0-9]+)', ep_href)
        if not ep_num_match:
            continue
        ep_num = int(ep_num_match.group(1))
        episodes.append({"episode": ep_num, "link": ep_href if ep_href.startswith("http") else BASE + ep_href})
    episodes.sort(key=lambda x: x["episode"])
    return {
        "slug": slug,
        "title": title_el.text.strip() if title_el else slug,
        "image": image_url,
        "synopsis": synopsis_el.text.strip().replace("Sinopse: ", "").strip() if synopsis_el else None,
        "score": score_text,
        "genres": genres_text,
        "episode_count": len(episodes),
        "episodes_preview": episodes[:5]
    }

def get_episode_sources(slug: str, ep_num: int):
    import json as _json
    r = _get(f"{BASE}/animes/{slug}/{ep_num}")
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    video = soup.select_one("video[data-video-src]")
    if not video:
        return []
    video_url = video["data-video-src"]
    r2 = _get(video_url)
    if not r2:
        return []
    try:
        data = _json.loads(r2.text)
        sources = []
        for item in data.get("data", []):
            src = item.get("src", "")
            label = item.get("label", "auto")
            if src:
                sources.append({"url": src, "resolution": label, "status": "ONLINE"})
        return sources
    except Exception:
        return []

def get_trending():
    r = _get(BASE)
    if not r:
        return []
    soup = BeautifulSoup(r.text, "html.parser")
    results = []
    seen = set()
    for card in soup.select("article.cardUltimosEps")[:12]:
        a = card.find("a", href=True)
        img = card.find("img")
        title = card.find("h3") or card.find("h2")
        if not a:
            continue
        href = a["href"] if a["href"].startswith("http") else BASE + a["href"]
        slug = href.split("/animes/")[-1].replace("-todos-os-episodios", "").strip("/")
        if slug in seen:
            continue
        seen.add(slug)
        image_url = None
        if img:
            image_url = img.get("data-src") or img.get("src") or img.get("data-lazy-src")
        results.append({"slug": slug, "title": title.text.strip() if title else slug, "image": image_url})
    return results

def debug_selectors(slug: str):
    url = f"{BASE}/animes/{slug}-todos-os-episodios"
    r = _get(url)
    if not r:
        return {"error": "pagina nao encontrada"}
    soup = BeautifulSoup(r.text, "html.parser")
    tags = {}
    for tag in soup.find_all(True):
        classes = " ".join(tag.get("class", []))
        key = f"{tag.name}.{classes}".strip(".")
        if key not in tags:
            tags[key] = tag.text.strip()[:80]
    return tags

def get_all_episodes(slug: str):
    data = get_anime(slug)
    if not data:
        return []
    count = data.get("episode_count", 0)
    base = f"https://animefire.io/animes/{slug}/"
    return [{"episode": i, "link": f"{base}{i}"} for i in range(1, count + 1)]

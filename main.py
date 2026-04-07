from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from scraper.animefire import search, get_anime, get_episode_sources, get_trending

app = FastAPI(
    title="aninot",
    description="Proxy privado - MejorBerryScan",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "aninot online", "version": "1.0.0"}

@app.get("/anime/search")
def anime_search(q: str = Query(..., description="Nome do anime")):
    results = search(q)
    if not results:
        raise HTTPException(status_code=404, detail="Nenhum anime encontrado")
    return {"query": q, "results": results}

@app.get("/anime/trending")
def anime_trending():
    results = get_trending()
    return {"results": results}

@app.get("/anime/{slug}")
def anime_info(slug: str):
    data = get_anime(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Anime nao encontrado")
    return data

@app.get("/anime/{slug}/episodes")
def anime_episodes(slug: str):
    from scraper.animefire import get_all_episodes
    eps = get_all_episodes(slug)
    if not eps:
        raise HTTPException(status_code=404, detail="Nenhum episodio encontrado")
    return {"slug": slug, "total": len(eps), "episodes": eps}

@app.get("/anime/{slug}/episode/{ep_num}")
def anime_episode(slug: str, ep_num: int):
    sources = get_episode_sources(slug, ep_num)
    if not sources:
        raise HTTPException(status_code=404, detail="Episodio nao encontrado ou sem fontes")
    return {"slug": slug, "episode": ep_num, "sources": sources}

@app.get("/debug/{slug}")
def debug(slug: str):
    from scraper.animefire import debug_selectors
    return debug_selectors(slug)

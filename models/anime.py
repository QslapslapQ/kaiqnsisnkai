from pydantic import BaseModel
from typing import List, Optional

class VideoSource(BaseModel):
    url: str
    resolution: str
    status: str

class Episode(BaseModel):
    episode: int
    sources: List[VideoSource]

class Anime(BaseModel):
    slug: str
    title: str
    title_alt: Optional[str] = None
    image: Optional[str] = None
    genres: Optional[str] = None
    synopsis: Optional[str] = None
    score: Optional[str] = None
    votes: Optional[str] = None
    trailer: Optional[str] = None
    episodes: Optional[List[Episode]] = None

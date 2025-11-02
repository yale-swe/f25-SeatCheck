from pydantic import BaseModel


class Venue(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    availability: float | None = None  # 0..1 (1 = very available)

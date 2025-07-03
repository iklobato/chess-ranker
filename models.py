from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
import os
import requests

API_BASE_URL = os.environ.get("LICHESS_API_BASE_URL", "https://lichess.org/api")

class PerfType(Enum):
    CLASSICAL = 'classical'
    BLITZ = 'blitz'
    RAPID = 'rapid'

class Performance(BaseModel):
    rating: Optional[int] = None
    prog: Optional[int] = None
    prov: Optional[bool] = None

class RatingHistoryEntry(BaseModel):
    year: int
    month: int
    day: int
    rating: int

class RatingHistory(BaseModel):
    perfs: Dict[str, List[RatingHistoryEntry]]

class Player(BaseModel):
    id: str
    username: str
    perfs: Dict[str, Performance] = Field(default_factory=dict)

    @property
    def rating_history(self) -> RatingHistory:
        if self._rating_history is not None:
            return self._rating_history
        try:
            resp = requests.get(f'{API_BASE_URL}/user/{self.username}/rating-history')
            resp.raise_for_status()
            data = resp.json()
            perfs = {}
            for perf in data:
                entries = [RatingHistoryEntry(year=e[0], month=e[1], day=e[2], rating=e[3]) for e in perf['points']]
                perfs[perf['name']] = entries
            self._rating_history = RatingHistory(perfs=perfs)
            return self._rating_history
        except requests.RequestException:
            self._rating_history = RatingHistory(perfs={})
            return self._rating_history 
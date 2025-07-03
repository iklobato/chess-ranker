from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import RatingHistoryEntry, PerfType, Player, RatingHistory
import time
import os
import json
import requests
from redis_om import get_redis_connection

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = get_redis_connection(url=REDIS_URL, decode_responses=True)
API_BASE_URL = os.environ.get("LICHESS_API_BASE_URL", "https://lichess.org/api")

class RatingHistoryService:
    def get_rating_for_date(self, rating_history: List[RatingHistoryEntry], target_date: datetime):
        if not rating_history:
            return None
        best_entry = None
        for entry in rating_history:
            entry_date = datetime(entry.year, entry.month + 1, entry.day)
            if entry_date <= target_date:
                if best_entry is None:
                    best_entry = entry
                else:
                    best_date = datetime(best_entry.year, best_entry.month + 1, best_entry.day)
                    if entry_date > best_date:
                        best_entry = entry
        return best_entry.rating if best_entry else None

    def get_ratings(self, rating_history: List[RatingHistoryEntry], days: int) -> Dict[str, int]:
        today = datetime.now()
        ratings = {}
        last_known_rating = None
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            rating = self.get_rating_for_date(rating_history, date)
            if rating is not None:
                last_known_rating = rating
            elif last_known_rating is not None:
                rating = last_known_rating
            if rating is not None:
                ratings[date.strftime('%b %d')] = rating
        return ratings

    def generate_date_headers(self, days: int, date_format: str = '%Y-%m-%d'):
        today = datetime.now()
        headers = []
        for i in range(days - 1, -1, -1):
            date = today - timedelta(days=i)
            headers.append(date.strftime(date_format))
        return headers

class PlayerRatingProcessor:
    def __init__(self, api, rating_service: RatingHistoryService):
        self.api = api
        self.rating_service = rating_service

    def process_players_rating_data(self, player_histories: list[tuple[Player, RatingHistory]], perf_type: PerfType, days: int) -> list[list[Any]]:
        date_headers = self.rating_service.generate_date_headers(days)
        csv_data = []
        for i, (player, rating_histories) in enumerate(player_histories, 1):
            username = player.username
            perf_history = rating_histories.perfs.get(perf_type.name.capitalize(), [])
            row = [username]
            last_known_rating = None
            for date_header in date_headers:
                date_obj = datetime.strptime(date_header, '%Y-%m-%d')
                rating = self.rating_service.get_rating_for_date(perf_history, date_obj)
                if rating is not None:
                    last_known_rating = rating
                    row.append(rating)
                elif last_known_rating is not None:
                    row.append(last_known_rating)
                else:
                    perf = player.perfs.get(perf_type.value)
                    current_rating = perf.rating if perf else None
                    if current_rating:
                        last_known_rating = current_rating
                        row.append(current_rating)
                    else:
                        row.append('')
            csv_data.append(row)
            time.sleep(0.1)
        return csv_data

class PlayerRatingHistoryService:
    @staticmethod
    def get_rating_history(username: str) -> RatingHistory:
        key = f"rating_history:{username}"
        cached = redis.get(key)
        if cached:
            return RatingHistory.parse_obj(json.loads(cached))
        try:
            resp = requests.get(f'{API_BASE_URL}/user/{username}/rating-history')
            resp.raise_for_status()
            data = resp.json()
            perfs = {}
            for perf in data:
                entries = [RatingHistoryEntry(year=e[0], month=e[1], day=e[2], rating=e[3]) for e in perf['points']]
                perfs[perf['name']] = entries
            rh = RatingHistory(perfs=perfs)
            redis.set(key, json.dumps(rh.dict()), ex=3600)
            return rh
        except requests.RequestException:
            rh = RatingHistory(perfs={})
            redis.set(key, json.dumps(rh.dict()), ex=3600)
            return rh 
import os
import requests
from typing import List
from models import PerfType, Player, Performance

API_BASE_URL = os.environ.get("LICHESS_API_BASE_URL", "https://lichess.org/api")

class PlayerAPI:
    def get_players(self, perf_type: PerfType, quantity: int) -> List[Player]:
        try:
            resp = requests.get(f'{API_BASE_URL}/player/top/{quantity}/{perf_type.value}')
            resp.raise_for_status()
            data = resp.json()
            users = data.get('users', [])
            players = []
            for user in users:
                perfs = {k: Performance(**v) for k, v in user.get('perfs', {}).items()}
                players.append(Player(id=user['id'], username=user['username'], perfs=perfs))
            return players
        except requests.RequestException:
            return [] 
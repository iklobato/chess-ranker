from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import io
import csv
import os
import json
from api import PlayerAPI
from services import RatingHistoryService, PlayerRatingProcessor, PlayerRatingHistoryService
from models import PerfType, Player, RatingHistory
from fastapi.staticfiles import StaticFiles
from redis_om import get_redis_connection

app = FastAPI()

# Redis connection
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
redis = get_redis_connection(url=REDIS_URL, decode_responses=True)

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api = PlayerAPI()
rating_service = RatingHistoryService()
processor = PlayerRatingProcessor(api, rating_service)

# Redis cache for get_players
def cached_get_players(perf_type: str, quantity: int):
    key = f"players:{perf_type}:{quantity}"
    cached = redis.get(key)
    if cached:
        players_data = json.loads(cached)
        return [Player.parse_obj(p) for p in players_data]
    players = api.get_players(PerfType(perf_type), quantity)
    redis.set(key, json.dumps([p.dict() for p in players]), ex=3600)
    return players

@app.get("/players", response_model=List[str])
def get_top_players(top: int = Query(50, gt=0, le=100), type: str = Query("classical")):
    try:
        perf_enum = PerfType(type.lower())
    except ValueError:
        return JSONResponse({"error": f"Invalid performance type: {type}"}, status_code=400)
    players = cached_get_players(perf_enum.value, top)
    return [p.username for p in players]

@app.get("/players/ratings")
def get_top_players_ratings(top: int = Query(1, gt=0, le=100), type: str = Query("classical"), days: int = Query(30, gt=0, le=365)):
    try:
        perf_enum = PerfType(type.lower())
    except ValueError:
        return JSONResponse({"error": f"Invalid performance type: {type}"}, status_code=400)
    players = cached_get_players(perf_enum.value, top)
    if not players:
        return JSONResponse({"error": "No player found"}, status_code=404)
    result = []
    for player in players:
        rating_history = PlayerRatingHistoryService.get_rating_history(player.username)
        perf_history = rating_history.perfs.get(perf_enum.name.capitalize(), [])
        ratings = rating_service.get_ratings(perf_history, days)
        result.append({"username": player.username, "ratings": ratings})
    return result if top > 1 else result[0]

@app.get("/players/ratings/csv")
def get_top_players_ratings_csv(top: int = Query(50, gt=0, le=100), type: str = Query("classical"), days: int = Query(30, gt=0, le=365)):
    try:
        perf_enum = PerfType(type.lower())
    except ValueError:
        return JSONResponse({"error": f"Invalid performance type: {type}"}, status_code=400)
    players = cached_get_players(perf_enum.value, top)
    players = list(players)
    rating_histories = {p.username: PlayerRatingHistoryService.get_rating_history(p.username) for p in players}
    for p in players:
        p.rating_history = rating_histories[p.username]
    csv_data = processor.process_players_rating_data(players, perf_enum, days)
    date_headers = rating_service.generate_date_headers(days)
    headers = ["username"] + date_headers
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(csv_data)
    output.seek(0)
    filename = f"top_{top}_{type}_ratings_{days}days.csv"
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.get("/players/{username}/ratings")
def get_player_ratings(username: str, type: str = Query("classical"), days: int = Query(30, gt=0, le=365)):
    try:
        perf_enum = PerfType(type.lower())
    except ValueError:
        return JSONResponse({"error": f"Invalid performance type: {type}"}, status_code=400)
    rating_history = PlayerRatingHistoryService.get_rating_history(username)
    perf_history = rating_history.perfs.get(perf_enum.name.capitalize(), [])
    ratings = rating_service.get_ratings(perf_history, days)
    return {"username": username, "ratings": ratings}

@app.get("/")
def serve_index():
    return FileResponse(os.path.join("static", "index.html"))

app.mount("/static", StaticFiles(directory="static"), name="static") 
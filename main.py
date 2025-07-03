import logging
import asyncio
from api import PlayerAPI
from services import RatingHistoryService, PlayerRatingProcessor, PlayerRatingHistoryService
from output import PlayerOutput
from models import PerfType

logging.basicConfig(level=logging.INFO)

class ChessRankingApp:
    def __init__(self, api, rating_service, processor, output):
        self.api = api
        self.rating_service = rating_service
        self.processor = processor
        self.output = output

    def get_players(self, perf_type: str, quantity: int):
        try:
            perf_enum = PerfType(perf_type.lower())
        except ValueError:
            logging.error(f"Invalid performance type: {perf_type}")
            return []
        return self.api.get_players(perf_enum, quantity)

    async def get_ratings(self, player, perf_type: str, days: int):
        loop = asyncio.get_event_loop()
        rating_histories = await loop.run_in_executor(None, lambda: PlayerRatingHistoryService.get_rating_history(player.username))
        perf_history = rating_histories.perfs.get(perf_type.capitalize(), [])
        if not perf_history:
            logging.info(f"No {perf_type} rating history for {player.username}")
            return {}
        return self.rating_service.get_ratings(perf_history, days)

    async def process_players_rating_data(self, perf_type: str, quantity: int, days: int):
        players = self.get_players(perf_type, quantity)
        try:
            perf_enum = PerfType(perf_type.lower())
        except ValueError:
            logging.error(f"Invalid performance type: {perf_type}")
            return []
        # Fetch all rating histories concurrently
        loop = asyncio.get_event_loop()
        rating_histories = await asyncio.gather(*[loop.run_in_executor(None, lambda p=player: PlayerRatingHistoryService.get_rating_history(p.username)) for player in players])
        for player, rating_history in zip(players, rating_histories):
            player.rating_history = rating_history
        return self.processor.process_players_rating_data(players, perf_enum, days)

    def generate_csv(self, csv_data, headers, filename):
        self.output.save_to_csv(csv_data, headers, filename)

async def main():
    logging.info("Starting Chess Ranking App")
    api = PlayerAPI()
    rating_service = RatingHistoryService()
    processor = PlayerRatingProcessor(api, rating_service)
    output = PlayerOutput()
    app = ChessRankingApp(api, rating_service, processor, output)

    # Top 50 classical players
    players = app.get_players("classical", 50)
    app.output.print_player_usernames(players)

    # Last 30 day rating history for top player
    top_players = app.get_players("classical", 1)
    if top_players:
        player = top_players[0]
        ratings = await app.get_ratings(player, "Classical", 30)
        app.output.print_rating_history(player.username, ratings)

    # CSV for top 50 classical players
    csv_data = await app.process_players_rating_data("classical", 50, 30)
    date_headers = app.rating_service.generate_date_headers(30)
    headers = ['username'] + date_headers
    app.generate_csv(csv_data, headers, 'top_50_classical_ratings.csv')

    # Blitz and rapid players
    blitz_players = app.get_players("blitz", 5)
    app.output.print_player_usernames(blitz_players)
    rapid_players = app.get_players("rapid", 3)
    app.output.print_player_usernames(rapid_players)
    if blitz_players:
        player = blitz_players[0]
        week_ratings = await app.get_ratings(player, "Blitz", 7)
        app.output.print_rating_history(player.username, week_ratings)
    rapid_players_10 = app.get_players("rapid", 10)
    if rapid_players_10:
        csv_data = await app.process_players_rating_data("rapid", 10, 14)
        headers = ['username'] + app.rating_service.generate_date_headers(14)
        app.generate_csv(csv_data, headers, 'top_10_rapid_14days.csv')
    logging.info("Chess Ranking App finished")

if __name__ == "__main__":
    asyncio.run(main()) 
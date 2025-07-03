import csv
import logging
from typing import List, Dict, Any
from models import Player

class PlayerOutput:
    def print_player_usernames(self, players: List[Player]):
        for player in players:
            logging.info(player.username)

    def print_rating_history(self, username: str, ratings: Dict[str, int]):
        if ratings:
            ratings_str = ', '.join([f"{date}: {rating}" for date, rating in ratings.items()])
            logging.info(f"{username}, {{{ratings_str}}}")
        else:
            logging.info(f"No rating history available for {username}")

    def save_to_csv(self, csv_data: List[List[Any]], headers: List[str], filename: str):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                writer.writerows(csv_data)
            logging.info(f"CSV file '{filename}' has been created successfully!")
        except Exception as e:
            logging.error(f"Error saving CSV: {e}") 
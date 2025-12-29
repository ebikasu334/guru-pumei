#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game DAO (Data Access Object) Class
- Implements CRUD operations for games
- Provides search and filtering functionality
- Uses SQL parameters to prevent injection
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from backend.db_manager import DatabaseManager

class GameDAO:
    """Game Data Access Object class"""

    def __init__(self, db_path: str = 'db/games.db'):
        """
        Initialize the GameDAO

        Args:
            db_path: Path to SQLite database file
        """
        self.db_manager = DatabaseManager(db_path)

    def get_game_by_id(self, game_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch details of a single game by ID

        Args:
            game_id: Game ID to fetch

        Returns:
            Dictionary containing game details with all relationships, or None if not found
        """
        query = """
        SELECT
            g.game_id, g.title, g.release_date, g.description, g.rating, g.price, g.image_url,
            d.developer_id, d.name as developer_name, d.country as developer_country,
            gen.genre_id, gen.name as genre_name,
            GROUP_CONCAT(DISTINCT p.name) as platforms,
            GROUP_CONCAT(DISTINCT CASE WHEN pref.category = 'genre' THEN pref.name END) as genre_tags,
            GROUP_CONCAT(DISTINCT CASE WHEN pref.category = 'preference' THEN pref.name END) as preference_tags
        FROM games g
        JOIN developers d ON g.developer_id = d.developer_id
        JOIN genres gen ON g.genre_id = gen.genre_id
        LEFT JOIN game_platforms gp ON g.game_id = gp.game_id
        LEFT JOIN platforms p ON gp.platform_id = p.platform_id
        LEFT JOIN game_tags gt ON g.game_id = gt.game_id
        LEFT JOIN preferences pref ON gt.tag_id = pref.tag_id
        WHERE g.game_id = ?
        GROUP BY g.game_id
        """

        result = self.db_manager.execute_query(query, (game_id,))

        if not result:
            return None

        row = result[0]
        return {
            'game_id': row[0],
            'title': row[1],
            'release_date': row[2],
            'description': row[3],
            'rating': row[4],
            'price': row[5],
            'image_url': row[6],
            'developer': {
                'developer_id': row[7],
                'name': row[8],
                'country': row[9]
            },
            'genre': {
                'genre_id': row[10],
                'name': row[11]
            },
            'platforms': [p.strip() for p in row[12].split(',')] if row[12] else [],
            'genre_tags': [t.strip() for t in row[13].split(',')] if row[13] else [],
            'preference_tags': [t.strip() for t in row[14].split(',')] if row[14] else []
        }

    def search_games(self, filters: Dict[str, Any], sort_by: str = 'release_date_desc') -> List[Dict[str, Any]]:
        """
        Search games with filters and sorting

        Args:
            filters: Dictionary containing filter criteria
                    - 'platform': Platform name (string)
                    - 'genre': Genre name (string)
                    - 'preference': Preference tag name (string)
                    - 'country': Developer country (string)
            sort_by: Sort order ('release_date_desc' or 'release_date_asc')

        Returns:
            List of dictionaries containing game summaries
        """
        # Base query
        query = """
        SELECT
            g.game_id, g.title, g.release_date, g.description, g.rating, g.price, g.image_url,
            d.name as developer_name, d.country as developer_country,
            gen.name as genre_name,
            GROUP_CONCAT(DISTINCT p.name) as platforms,
            GROUP_CONCAT(DISTINCT CASE WHEN pref.category = 'preference' THEN pref.name END) as preference_tags
        FROM games g
        JOIN developers d ON g.developer_id = d.developer_id
        JOIN genres gen ON g.genre_id = gen.genre_id
        LEFT JOIN game_platforms gp ON g.game_id = gp.game_id
        LEFT JOIN platforms p ON gp.platform_id = p.platform_id
        LEFT JOIN game_tags gt ON g.game_id = gt.game_id
        LEFT JOIN preferences pref ON gt.tag_id = pref.tag_id
        WHERE g.game_id IN (
            SELECT MIN(game_id)
            FROM games
            GROUP BY title
        )
        """

        # Apply filters
        conditions = []
        params = []

        if 'platform' in filters and filters['platform']:
            conditions.append("p.name = ?")
            params.append(filters['platform'])

        if 'genre' in filters and filters['genre']:
            conditions.append("gen.name = ?")
            params.append(filters['genre'])

        if 'preference' in filters and filters['preference']:
            conditions.append("pref.name = ? AND pref.category = 'preference'")
            params.append(filters['preference'])

        if 'country' in filters and filters['country']:
            conditions.append("d.country = ?")
            params.append(filters['country'])

        if conditions:
            query += " AND " + " AND ".join(conditions)

        # Group and sort
        query += """
        GROUP BY g.game_id, g.title, g.release_date, g.description, g.rating, g.price, g.image_url, d.name, d.country, gen.name
        ORDER BY g.release_date """ + ("DESC" if sort_by == 'release_date_desc' else "ASC")

        results = self.db_manager.execute_query(query, tuple(params))

        return [{
            'game_id': row[0],
            'title': row[1],
            'release_date': row[2],
            'description': row[3],
            'rating': row[4],
            'price': row[5],
            'image_url': row[6],
            'developer': row[7],
            'country': row[8],
            'genre': row[9],
            'platforms': [p.strip() for p in row[10].split(',')] if row[10] else [],
            'preference_tags': [t.strip() for t in row[11].split(',')] if row[11] else []
        } for row in results]

    def create_game(self, game_data: Dict[str, Any]) -> int:
        """
        Create a new game with transaction

        Args:
            game_data: Dictionary containing game data
                - title, release_date, description, rating, price, image_url
                - developer (name, country)
                - genre (name)
                - platforms (list of platform names)
                - genre_tags (list of genre tag names)
                - preference_tags (list of preference tag names)

        Returns:
            ID of the created game
        """
        with self.db_manager.transaction() as cursor:
            # Get or create developer
            cursor.execute(
                "INSERT OR IGNORE INTO developers (name, country) VALUES (?, ?)",
                (game_data['developer']['name'], game_data['developer']['country'])
            )
            cursor.execute(
                "SELECT developer_id FROM developers WHERE name = ? AND country = ?",
                (game_data['developer']['name'], game_data['developer']['country'])
            )
            developer_id = cursor.fetchone()[0]

            # Get or create genre
            cursor.execute(
                "INSERT OR IGNORE INTO genres (name) VALUES (?)",
                (game_data['genre']['name'],)
            )
            cursor.execute(
                "SELECT genre_id FROM genres WHERE name = ?",
                (game_data['genre']['name'],)
            )
            genre_id = cursor.fetchone()[0]

            # Insert game
            cursor.execute(
                """INSERT INTO games
                (title, release_date, description, rating, price, developer_id, genre_id, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    game_data['title'],
                    game_data['release_date'],
                    game_data['description'],
                    game_data.get('rating'),
                    game_data.get('price'),
                    developer_id,
                    genre_id,
                    game_data.get('image_url')
                )
            )
            game_id = cursor.lastrowid

            # Insert platforms
            for platform_name in game_data.get('platforms', []):
                cursor.execute(
                    "INSERT OR IGNORE INTO platforms (name) VALUES (?)",
                    (platform_name,)
                )
                cursor.execute(
                    "SELECT platform_id FROM platforms WHERE name = ?",
                    (platform_name,)
                )
                platform_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO game_platforms (game_id, platform_id) VALUES (?, ?)",
                    (game_id, platform_id)
                )

            # Insert tags
            for tag_name in game_data.get('genre_tags', []):
                cursor.execute(
                    "INSERT OR IGNORE INTO preferences (name, category) VALUES (?, 'genre')",
                    (tag_name,)
                )
                cursor.execute(
                    "SELECT tag_id FROM preferences WHERE name = ? AND category = 'genre'",
                    (tag_name,)
                )
                tag_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                    (game_id, tag_id)
                )

            for tag_name in game_data.get('preference_tags', []):
                cursor.execute(
                    "INSERT OR IGNORE INTO preferences (name, category) VALUES (?, 'preference')",
                    (tag_name,)
                )
                cursor.execute(
                    "SELECT tag_id FROM preferences WHERE name = ? AND category = 'preference'",
                    (tag_name,)
                )
                tag_id = cursor.fetchone()[0]
                cursor.execute(
                    "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                    (game_id, tag_id)
                )

            return game_id

    def update_game(self, game_id: int, game_data: Dict[str, Any]) -> bool:
        """
        Update existing game details with transaction

        Args:
            game_id: ID of game to update
            game_data: Dictionary containing game data to update

        Returns:
            True if update was successful, False if game not found
        """
        # Check if game exists
        existing_game = self.get_game_by_id(game_id)
        if not existing_game:
            return False

        with self.db_manager.transaction() as cursor:
            # Update game basic info
            update_fields = []
            params = []

            if 'title' in game_data:
                update_fields.append("title = ?")
                params.append(game_data['title'])

            if 'release_date' in game_data:
                update_fields.append("release_date = ?")
                params.append(game_data['release_date'])

            if 'description' in game_data:
                update_fields.append("description = ?")
                params.append(game_data['description'])

            if 'rating' in game_data:
                update_fields.append("rating = ?")
                params.append(game_data['rating'])

            if 'price' in game_data:
                update_fields.append("price = ?")
                params.append(game_data['price'])

            if 'image_url' in game_data:
                update_fields.append("image_url = ?")
                params.append(game_data['image_url'])

            if update_fields:
                params.append(game_id)
                cursor.execute(
                    f"UPDATE games SET {', '.join(update_fields)} WHERE game_id = ?",
                    params
                )

            # Update developer if provided
            if 'developer' in game_data:
                cursor.execute(
                    "UPDATE developers SET name = ?, country = ? WHERE developer_id = ?",
                    (
                        game_data['developer']['name'],
                        game_data['developer']['country'],
                        existing_game['developer']['developer_id']
                    )
                )

            # Update genre if provided
            if 'genre' in game_data:
                cursor.execute(
                    "UPDATE genres SET name = ? WHERE genre_id = ?",
                    (
                        game_data['genre']['name'],
                        existing_game['genre']['genre_id']
                    )
                )

            # Update platforms if provided
            if 'platforms' in game_data:
                # Clear existing platforms
                cursor.execute("DELETE FROM game_platforms WHERE game_id = ?", (game_id,))

                # Add new platforms
                for platform_name in game_data['platforms']:
                    cursor.execute(
                        "INSERT OR IGNORE INTO platforms (name) VALUES (?)",
                        (platform_name,)
                    )
                    cursor.execute(
                        "SELECT platform_id FROM platforms WHERE name = ?",
                        (platform_name,)
                    )
                    platform_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO game_platforms (game_id, platform_id) VALUES (?, ?)",
                        (game_id, platform_id)
                    )

            # Update tags if provided
            if 'genre_tags' in game_data or 'preference_tags' in game_data:
                # Clear existing tags
                cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))

                # Add new genre tags
                for tag_name in game_data.get('genre_tags', []):
                    cursor.execute(
                        "INSERT OR IGNORE INTO preferences (name, category) VALUES (?, 'genre')",
                        (tag_name,)
                    )
                    cursor.execute(
                        "SELECT tag_id FROM preferences WHERE name = ? AND category = 'genre'",
                        (tag_name,)
                    )
                    tag_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                        (game_id, tag_id)
                    )

                # Add new preference tags
                for tag_name in game_data.get('preference_tags', []):
                    cursor.execute(
                        "INSERT OR IGNORE INTO preferences (name, category) VALUES (?, 'preference')",
                        (tag_name,)
                    )
                    cursor.execute(
                        "SELECT tag_id FROM preferences WHERE name = ? AND category = 'preference'",
                        (tag_name,)
                    )
                    tag_id = cursor.fetchone()[0]
                    cursor.execute(
                        "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                        (game_id, tag_id)
                    )

            return True

    def delete_game(self, game_id: int) -> bool:
        """
        Delete a game with transaction

        Args:
            game_id: ID of game to delete

        Returns:
            True if deletion was successful, False if game not found
        """
        # Check if game exists
        existing_game = self.get_game_by_id(game_id)
        if not existing_game:
            return False

        with self.db_manager.transaction() as cursor:
            # Delete from junction tables first (due to foreign key constraints)
            cursor.execute("DELETE FROM game_platforms WHERE game_id = ?", (game_id,))
            cursor.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))

            # Delete the game itself
            cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))

            return True

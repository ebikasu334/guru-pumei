#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game-Shiru Database Initialization Script
- Creates SQLite database with schema
- Seeds data from Japanese game dataset
- Handles transaction control for data integrity
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Set console encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Database configuration
DB_NAME = "games.db"
SCHEMA_FILE = "db/schema.sql"
GAMES_JSON_FILE = "data/games.json"

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Create and return SQLite database connection"""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    return conn

def execute_schema(conn: sqlite3.Connection, schema_file: str) -> None:
    """Execute SQL schema from file"""
    print(f"Executing schema from {schema_file}...")

    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Execute the entire schema script
        conn.executescript(sql_script)
        conn.commit()
        print("✓ Schema executed successfully")

    except Exception as e:
        print(f"✗ Error executing schema: {e}")
        conn.rollback()
        raise

def load_game_data(json_file: str) -> List[Dict[str, Any]]:
    """Load game data from JSON file"""
    print(f"Loading game data from {json_file}...")

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # The JSON is a single array of games
        if isinstance(data, list):
            games = data
        else:
            # If it's nested, flatten it
            games = []
            for game_list in data:
                if isinstance(game_list, list):
                    games.extend(game_list)

        print(f"✓ Loaded {len(games)} games")
        return games

    except Exception as e:
        print(f"✗ Error loading game data: {e}")
        raise

def get_or_create_developer(conn: sqlite3.Connection, name: str, country: str) -> int:
    """Get developer ID or create new developer"""
    cursor = conn.cursor()

    # Check if developer exists
    cursor.execute("SELECT developer_id FROM developers WHERE name = ? AND country = ?", (name, country))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new developer
    cursor.execute(
        "INSERT INTO developers (name, country, founded_year, website) VALUES (?, ?, NULL, NULL)",
        (name, country)
    )
    conn.commit()
    return cursor.lastrowid

def get_or_create_genre(conn: sqlite3.Connection, name: str) -> int:
    """Get genre ID or create new genre"""
    cursor = conn.cursor()

    # Check if genre exists
    cursor.execute("SELECT genre_id FROM genres WHERE name = ?", (name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new genre
    cursor.execute(
        "INSERT INTO genres (name, description) VALUES (?, NULL)",
        (name,)
    )
    conn.commit()
    return cursor.lastrowid

def get_or_create_platform(conn: sqlite3.Connection, name: str) -> int:
    """Get platform ID or create new platform"""
    cursor = conn.cursor()

    # Check if platform exists
    cursor.execute("SELECT platform_id FROM platforms WHERE name = ?", (name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new platform
    cursor.execute(
        "INSERT INTO platforms (name, manufacturer, release_year) VALUES (?, NULL, NULL)",
        (name,)
    )
    conn.commit()
    return cursor.lastrowid

def get_or_create_tag(conn: sqlite3.Connection, name: str, category: str) -> int:
    """Get tag ID or create new tag"""
    cursor = conn.cursor()

    # Check if tag exists (by name and category)
    cursor.execute("SELECT tag_id FROM preferences WHERE name = ? AND category = ?", (name, category))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new tag
    cursor.execute(
        "INSERT INTO preferences (name, category) VALUES (?, ?)",
        (name, category)
    )
    conn.commit()
    return cursor.lastrowid

def seed_games_data(conn: sqlite3.Connection, games: List[Dict[str, Any]]) -> None:
    """Seed games data into database with transaction control"""
    print("Seeding games data...")

    cursor = conn.cursor()

    try:
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")

        for game in games:
            # Insert game
            developer_id = get_or_create_developer(conn, game['developer'], game['country'])
            genre_id = get_or_create_genre(conn, game['genre'])

            cursor.execute(
                """INSERT INTO games
                (title, release_date, description, rating, price, developer_id, genre_id, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    game['title'],
                    game['release_date'],
                    game['description'],
                    None,  # rating not provided in this dataset
                    None,  # price not provided in this dataset
                    developer_id,
                    genre_id,
                    game['image_url']
                )
            )

            game_id = cursor.lastrowid

            # Insert platforms (Many-to-Many relationship)
            for platform_name in game['platforms']:
                platform_id = get_or_create_platform(conn, platform_name)
                cursor.execute(
                    "INSERT INTO game_platforms (game_id, platform_id) VALUES (?, ?)",
                    (game_id, platform_id)
                )

            # Insert tags (Many-to-Many relationship)
            for tag_name in game['tags']['genre']:
                tag_id = get_or_create_tag(conn, tag_name, 'genre')
                cursor.execute(
                    "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                    (game_id, tag_id)
                )

            for tag_name in game['tags']['preference']:
                tag_id = get_or_create_tag(conn, tag_name, 'preference')
                cursor.execute(
                    "INSERT INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                    (game_id, tag_id)
                )

        # Commit transaction
        conn.commit()
        print(f"✓ Successfully seeded {len(games)} games with all relationships")

    except Exception as e:
        print(f"✗ Error seeding games data: {e}")
        conn.rollback()
        raise

def verify_data_integrity(conn: sqlite3.Connection) -> None:
    """Verify data integrity and relationships"""
    print("Verifying data integrity...")

    cursor = conn.cursor()

    try:
        # Check basic counts
        cursor.execute("SELECT COUNT(*) FROM games")
        game_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM developers")
        developer_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM genres")
        genre_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM platforms")
        platform_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM preferences")
        tag_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM game_platforms")
        game_platform_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM game_tags")
        game_tag_count = cursor.fetchone()[0]

        print(f"✓ Data integrity verified:")
        print(f"  - Games: {game_count}")
        print(f"  - Developers: {developer_count}")
        print(f"  - Genres: {genre_count}")
        print(f"  - Platforms: {platform_count}")
        print(f"  - Tags: {tag_count}")
        print(f"  - Game-Platform relationships: {game_platform_count}")
        print(f"  - Game-Tag relationships: {game_tag_count}")

        # Check for orphaned records
        cursor.execute("""
            SELECT COUNT(*) FROM games
            WHERE developer_id NOT IN (SELECT developer_id FROM developers)
        """)
        orphaned_games = cursor.fetchone()[0]

        if orphaned_games > 0:
            print(f"⚠ Warning: {orphaned_games} games have invalid developer references")

        cursor.execute("""
            SELECT COUNT(*) FROM games
            WHERE genre_id NOT IN (SELECT genre_id FROM genres)
        """)
        orphaned_genres = cursor.fetchone()[0]

        if orphaned_genres > 0:
            print(f"⚠ Warning: {orphaned_genres} games have invalid genre references")

    except Exception as e:
        print(f"✗ Error verifying data integrity: {e}")
        raise

def main():
    """Main execution function"""
    print("Game-Shiru Database Initialization")
    print("=" * 40)

    # Create database directory if it doesn't exist
    os.makedirs('db', exist_ok=True)
    db_path = os.path.join('db', DB_NAME)

    try:
        # Connect to database
        conn = get_db_connection(db_path)
        print(f"✓ Connected to database: {db_path}")

        # Execute schema
        execute_schema(conn, SCHEMA_FILE)

        # Load and seed game data
        games_data = load_game_data(GAMES_JSON_FILE)
        seed_games_data(conn, games_data)

        # Verify data integrity
        verify_data_integrity(conn)

        print("\n🎮 Database initialization completed successfully!")
        print(f"Database file: {db_path}")

    except Exception as e:
        print(f"\n❌ Database initialization failed: {e}")
        return 1

    finally:
        if 'conn' in locals():
            conn.close()
            print("✓ Database connection closed")

    return 0

if __name__ == "__main__":
    exit(main())

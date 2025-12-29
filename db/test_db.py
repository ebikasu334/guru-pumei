#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script to verify the database
"""

import sqlite3
import sys

# Set console encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_database():
    """Test the database with some sample queries"""
    print("Testing Game-Shiru Database...")

    try:
        conn = sqlite3.connect('db/games.db')
        conn.execute("PRAGMA foreign_keys = ON")
        cursor = conn.cursor()

        # Test 1: Count total games
        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]
        print(f"✓ Total games: {total_games}")

        # Test 2: Count games by country
        cursor.execute("""
            SELECT d.country, COUNT(*) as game_count
            FROM games g
            JOIN developers d ON g.developer_id = d.developer_id
            GROUP BY d.country
            ORDER BY game_count DESC
            LIMIT 5
        """)
        countries = cursor.fetchall()
        print(f"✓ Top countries by game count:")
        for country, count in countries:
            print(f"  - {country}: {count} games")

        # Test 3: Count games by platform
        cursor.execute("""
            SELECT p.name, COUNT(*) as game_count
            FROM game_platforms gp
            JOIN platforms p ON gp.platform_id = p.platform_id
            GROUP BY p.name
            ORDER BY game_count DESC
            LIMIT 5
        """)
        platforms = cursor.fetchall()
        print(f"✓ Top platforms by game count:")
        for platform, count in platforms:
            print(f"  - {platform}: {count} games")

        # Test 4: Count games by genre
        cursor.execute("""
            SELECT g.name, COUNT(*) as game_count
            FROM games
            JOIN genres g ON games.genre_id = g.genre_id
            GROUP BY g.name
            ORDER BY game_count DESC
            LIMIT 5
        """)
        genres = cursor.fetchall()
        print(f"✓ Top genres by game count:")
        for genre, count in genres:
            print(f"  - {genre}: {count} games")

        # Test 5: Find games with specific tags
        cursor.execute("""
            SELECT g.title
            FROM games g
            JOIN game_tags gt ON g.game_id = gt.game_id
            JOIN preferences p ON gt.tag_id = p.tag_id
            WHERE p.name = 'ストーリー重視'
            LIMIT 5
        """)
        story_games = cursor.fetchall()
        print(f"✓ Games with 'ストーリー重視' tag:")
        for game, in story_games:
            print(f"  - {game}")

        # Test 6: Complex query - Japanese games on Nintendo platforms
        cursor.execute("""
            SELECT g.title, p.name
            FROM games g
            JOIN developers d ON g.developer_id = d.developer_id
            JOIN game_platforms gp ON g.game_id = gp.game_id
            JOIN platforms p ON gp.platform_id = p.platform_id
            WHERE d.country = '日本' AND p.name LIKE '%Nintendo%'
            LIMIT 5
        """)
        japanese_nintendo = cursor.fetchall()
        print(f"✓ Japanese games on Nintendo platforms:")
        for title, platform in japanese_nintendo:
            print(f"  - {title} ({platform})")

        print("\n🎮 All database tests passed!")

    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return 1

    finally:
        if 'conn' in locals():
            conn.close()

    return 0

if __name__ == "__main__":
    exit(test_database())

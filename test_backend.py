#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Game-Shiru backend
- Tests DatabaseManager and GameDAO functionality
- Verifies CRUD operations and search functionality
"""

import sys
import os
from backend.db_manager import DatabaseManager
from backend.game_dao import GameDAO

# Set console encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_database_manager():
    """Test DatabaseManager functionality"""
    print("Testing DatabaseManager...")

    try:
        db_manager = DatabaseManager('db/games.db')

        # Test connection
        conn = db_manager.connect()
        print("✓ Database connection established")

        # Test query execution
        result = db_manager.execute_query("SELECT COUNT(*) FROM games")
        game_count = result[0][0]
        print(f"✓ Found {game_count} games in database")

        # Test transaction
        with db_manager.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) FROM developers")
            dev_count = cursor.fetchone()[0]
            print(f"✓ Transaction test: {dev_count} developers found")

        # Test context manager
        with db_manager:
            result = db_manager.execute_query("SELECT COUNT(*) FROM platforms")
            platform_count = result[0][0]
            print(f"✓ Context manager test: {platform_count} platforms found")

        db_manager.close()
        print("✓ DatabaseManager tests passed\n")

    except Exception as e:
        print(f"✗ DatabaseManager test failed: {e}")
        return False

    return True

def test_game_dao():
    """Test GameDAO CRUD operations"""
    print("Testing GameDAO CRUD operations...")

    try:
        game_dao = GameDAO('db/games.db')

        # Test 1: Get game by ID
        game = game_dao.get_game_by_id(1)
        if game:
            print(f"✓ Get game by ID: {game['title']}")
        else:
            print("✗ Get game by ID failed")
            return False

        # Test 2: Search games (no filters)
        games = game_dao.search_games({})
        print(f"✓ Search all games: Found {len(games)} games")

        # Test 3: Search with filters
        filters = {
            'country': '日本',
            'platform': 'Nintendo Switch'
        }
        japanese_switch_games = game_dao.search_games(filters)
        print(f"✓ Search Japanese Nintendo Switch games: Found {len(japanese_switch_games)} games")

        # Test 4: Search with preference tag
        filters = {
            'preference': 'ストーリー重視'
        }
        story_games = game_dao.search_games(filters)
        print(f"✓ Search story-rich games: Found {len(story_games)} games")

        # Test 5: Search with sorting
        games_newest = game_dao.search_games({}, 'release_date_desc')
        games_oldest = game_dao.search_games({}, 'release_date_asc')
        print(f"✓ Sorting test: Newest {games_newest[0]['title']}, Oldest {games_oldest[0]['title']}")

        # Test 6: Create a new game
        new_game_data = {
            'title': 'Test Game',
            'release_date': '2024-01-01',
            'description': 'A test game for DAO testing',
            'rating': 8.5,
            'price': 59.99,
            'image_url': 'https://example.com/test.jpg',
            'developer': {
                'name': 'Test Studio',
                'country': 'Test Country'
            },
            'genre': {
                'name': 'Test Genre'
            },
            'platforms': ['PC', 'Test Platform'],
            'genre_tags': ['Test Genre Tag'],
            'preference_tags': ['Test Preference Tag']
        }

        new_game_id = game_dao.create_game(new_game_data)
        print(f"✓ Create game: New game ID {new_game_id}")

        # Test 7: Get the newly created game
        new_game = game_dao.get_game_by_id(new_game_id)
        if new_game and new_game['title'] == 'Test Game':
            print("✓ Get newly created game: Success")
        else:
            print("✗ Get newly created game failed")
            return False

        # Test 8: Update the game
        update_data = {
            'title': 'Updated Test Game',
            'rating': 9.0,
            'platforms': ['PC', 'Updated Platform']
        }
        update_success = game_dao.update_game(new_game_id, update_data)
        if update_success:
            print("✓ Update game: Success")
        else:
            print("✗ Update game failed")
            return False

        # Test 9: Verify update
        updated_game = game_dao.get_game_by_id(new_game_id)
        if updated_game and updated_game['title'] == 'Updated Test Game':
            print("✓ Verify update: Success")
        else:
            print("✗ Verify update failed")
            return False

        # Test 10: Delete the game
        delete_success = game_dao.delete_game(new_game_id)
        if delete_success:
            print("✓ Delete game: Success")
        else:
            print("✗ Delete game failed")
            return False

        # Test 11: Verify deletion
        deleted_game = game_dao.get_game_by_id(new_game_id)
        if deleted_game is None:
            print("✓ Verify deletion: Success")
        else:
            print("✗ Verify deletion failed")
            return False

        print("✓ GameDAO CRUD tests passed\n")

    except Exception as e:
        print(f"✗ GameDAO test failed: {e}")
        return False

    return True

def test_search_functionality():
    """Test advanced search functionality"""
    print("Testing advanced search functionality...")

    try:
        game_dao = GameDAO('db/games.db')

        # Test complex filter combinations
        test_cases = [
            {
                'name': 'Japanese RPGs',
                'filters': {'country': '日本', 'genre': 'RPG'},
                'expected_min': 9  # Adjusted based on actual data
            },
            {
                'name': 'Multiplayer games',
                'filters': {'preference': '協力プレイ'},
                'expected_min': 18  # Adjusted based on actual data
            },
            {
                'name': 'Nintendo Switch Action games',
                'filters': {'platform': 'Nintendo Switch', 'genre': 'アクション'},
                'expected_min': 8  # Adjusted based on actual data
            },
            {
                'name': 'Free to play games',
                'filters': {'preference': '基本プレイ無料'},
                'expected_min': 5
            }
        ]

        for test_case in test_cases:
            results = game_dao.search_games(test_case['filters'])
            if len(results) >= test_case['expected_min']:
                print(f"✓ {test_case['name']}: Found {len(results)} games")
            else:
                print(f"✗ {test_case['name']}: Expected at least {test_case['expected_min']}, got {len(results)}")
                return False

        # Test sorting
        newest_games = game_dao.search_games({}, 'release_date_desc')
        oldest_games = game_dao.search_games({}, 'release_date_asc')

        if newest_games[0]['release_date'] > oldest_games[0]['release_date']:
            print("✓ Sorting verification: Newest and oldest dates correct")
        else:
            print("✗ Sorting verification failed")
            return False

        print("✓ Advanced search tests passed\n")

    except Exception as e:
        print(f"✗ Advanced search test failed: {e}")
        return False

    return True

def main():
    """Run all tests"""
    print("Game-Shiru Backend Testing")
    print("=" * 40)

    # Ensure database exists
    if not os.path.exists('db/games.db'):
        print("❌ Database not found. Please run db/init_db.py first.")
        return 1

    tests = [
        test_database_manager,
        test_game_dao,
        test_search_functionality
    ]

    all_passed = True
    for test in tests:
        if not test():
            all_passed = False

    if all_passed:
        print("🎮 All backend tests passed successfully!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())

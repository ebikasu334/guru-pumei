-- Game-Shiru Database Schema (SQLite)
-- 3NF Normalized Design with proper relationships

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Create Developers table
CREATE TABLE IF NOT EXISTS developers (
    developer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    founded_year INTEGER,
    website TEXT
);

-- Create Genres table
CREATE TABLE IF NOT EXISTS genres (
    genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- Create Platforms table
CREATE TABLE IF NOT EXISTS platforms (
    platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    manufacturer TEXT,
    release_year INTEGER
);

-- Create Preferences (Tags) table
CREATE TABLE IF NOT EXISTS preferences (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT NOT NULL
);

-- Create Games table
CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    release_date DATE NOT NULL,
    description TEXT,
    rating REAL,
    price REAL,
    developer_id INTEGER NOT NULL,
    genre_id INTEGER NOT NULL,
    image_url TEXT,
    FOREIGN KEY (developer_id) REFERENCES developers(developer_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
);

-- Create Game_Platforms junction table (Many-to-Many)
CREATE TABLE IF NOT EXISTS game_platforms (
    game_id INTEGER NOT NULL,
    platform_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, platform_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms(platform_id) ON DELETE CASCADE
);

-- Create Game_Tags junction table (Many-to-Many)
CREATE TABLE IF NOT EXISTS game_tags (
    game_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, tag_id),
    FOREIGN KEY (game_id) REFERENCES games(game_id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES preferences(tag_id) ON DELETE CASCADE
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_games_title ON games(title);
CREATE INDEX IF NOT EXISTS idx_games_release_date ON games(release_date);
CREATE INDEX IF NOT EXISTS idx_games_rating ON games(rating);
CREATE INDEX IF NOT EXISTS idx_games_developer ON games(developer_id);
CREATE INDEX IF NOT EXISTS idx_games_genre ON games(genre_id);
CREATE INDEX IF NOT EXISTS idx_platforms_name ON platforms(name);
CREATE INDEX IF NOT EXISTS idx_genres_name ON genres(name);
CREATE INDEX IF NOT EXISTS idx_preferences_name ON preferences(name);
CREATE INDEX IF NOT EXISTS idx_game_platforms_game ON game_platforms(game_id);
CREATE INDEX IF NOT EXISTS idx_game_platforms_platform ON game_platforms(platform_id);
CREATE INDEX IF NOT EXISTS idx_game_tags_game ON game_tags(game_id);
CREATE INDEX IF NOT EXISTS idx_game_tags_tag ON game_tags(tag_id);

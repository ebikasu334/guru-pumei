<<<<<<< HEAD
# Game-Shiru (ゲムしる) - Game Recommendation App

## Overview

Game-Shiru is a web application that allows users to search, filter, and sort games based on tags, genres, and preferences. The application uses the "100 Games Master Data" to provide comprehensive game recommendations.

## Tech Stack

- **Python**: Backend programming language
- **Flask**: Web framework
- **SQLite**: Database system
- **HTML/CSS**: Frontend technologies

## Setup Instructions

### Prerequisites
- Python 3.x

### Installation
1. Install Flask:
   ```bash
   pip install flask
   ```
   Or install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Database Setup
Run the database initialization script:
```bash
python init_db.py
```

### Running the App
Start the Flask development server:
```bash
python app.py
```

### Access
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

## Features

- **Search by Tag**: Find games using specific tags and preferences
- **Filter by Country**: Filter games by developer country
- **Sort by Release Date**: Sort games chronologically (newest/oldest)
- **CRUD Operations**: Create, Read, Update, and Delete game records

## Project Structure

```
game-app/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── README.md                   # Project documentation
│
├── backend/
│   ├── db_manager.py           # Database connection manager
│   └── game_dao.py             # Game Data Access Object
│
├── db/
│   ├── games.db                # SQLite database
│   ├── init_db.py              # Database initialization script
│   └── schema.sql              # Database schema
│
├── data/
│   └── games.json              # Sample game data (100 games)
│
├── docs/
│   ├── architecture.pu         # Architecture diagram (PlantUML)
│   └── schema.pu               # Database schema diagram (PlantUML)
│
├── static/
│   └── style.css               # CSS styling
│
├── templates/
│   ├── base.html               # Base template
│   ├── index.html              # Home page with search
│   ├── detail.html             # Game detail page
│   ├── add.html                # Add game form
│   └── edit.html               # Edit game form
│
└── test_backend.py            # Backend testing script
=======

---------------------------------------------
プロジェクトメンバー
g2442009 伊比　悠幹  PM, Application Engineer
g2442036 笹川　悠互　DBA
g2442041 シンジハオ　System Architect
g2442058 出島　由基　Infra Engineer
g2442079　正岡　拳士　Business Analyst
---------------------------------------------
>>>>>>> ba7af08a32e882e21f2879a6b627f5e13ea5398a

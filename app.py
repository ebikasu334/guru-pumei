#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Game-Shiru Web Application
- Flask-based web interface for game recommendation system
- Integrates with backend DAO for data access
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from backend.game_dao import GameDAO
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'game-shiru-secret-key'

# Configure upload folder
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize GameDAO
game_dao = GameDAO('db/games.db')

# Helper function to format date for display
def format_date(date_str):
    """Format date string for display"""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%B %d, %Y')
    except:
        return date_str

# Helper function to get unique values for filters
def get_filter_options():
    """Get unique values for filter options"""
    # Get unique genres
    genres = game_dao.db_manager.execute_query("SELECT DISTINCT name FROM genres ORDER BY name")
    genre_options = [g[0] for g in genres]

    # Get unique preference tags
    preferences = game_dao.db_manager.execute_query("SELECT DISTINCT name FROM preferences WHERE category = 'preference' ORDER BY name")
    preference_options = [p[0] for p in preferences]

    # Get unique countries
    countries = game_dao.db_manager.execute_query("SELECT DISTINCT country FROM developers ORDER BY country")
    country_options = [c[0] for c in countries]

    # Get unique platforms
    platforms = game_dao.db_manager.execute_query("SELECT DISTINCT name FROM platforms ORDER BY name")
    platform_options = [p[0] for p in platforms]

    return {
        'genres': genre_options,
        'preferences': preference_options,
        'countries': country_options,
        'platforms': platform_options
    }

@app.route('/')
def index():
    """Home page - Display game list with search/filter"""
    # Get filter options
    filter_options = get_filter_options()

    # Get filter parameters from request
    selected_genres = request.args.getlist('genre')
    selected_preferences = request.args.getlist('preference')
    selected_country = request.args.get('country')
    selected_platform = request.args.get('platform')
    sort_by = request.args.get('sort', 'release_date_desc')

    # Build filters dictionary using new relevance-based search
    filters = {}
    if selected_genres:
        # Use all selected genres for OR condition
        filters['genres'] = selected_genres
    if selected_preferences:
        # Use all selected preferences for OR condition
        filters['preferences'] = selected_preferences
    if selected_country:
        filters['country'] = selected_country
    if selected_platform:
        filters['platform'] = selected_platform

    # Search games
    games = game_dao.search_games(filters, sort_by)

    # Format games for display
    formatted_games = []
    for game in games:
        formatted_games.append({
            'game_id': game['game_id'],
            'title': game['title'],
            'release_date': format_date(game['release_date']),
            'description': game['description'][:100] + '...' if len(game['description']) > 100 else game['description'],
            'rating': game['rating'],
            'price': game['price'],
            'image_url': game['image_url'],
            'developer': game['developer'],
            'country': game['country'],
            'genre': game['genre'],
            'platforms': game['platforms'],
            'preference_tags': game['preference_tags']
        })

    return render_template('index.html',
                         games=formatted_games,
                         filter_options=filter_options,
                         selected_genres=selected_genres,
                         selected_preferences=selected_preferences,
                         selected_country=selected_country,
                         selected_platform=selected_platform,
                         sort_by=sort_by)

@app.route('/game/<int:game_id>')
def game_detail(game_id):
    """Game detail page"""
    game = game_dao.get_game_by_id(game_id)

    if not game:
        flash('Game not found', 'error')
        return redirect(url_for('index'))

    # Format game for display
    formatted_game = {
        'game_id': game['game_id'],
        'title': game['title'],
        'release_date': format_date(game['release_date']),
        'description': game['description'],
        'rating': game['rating'],
        'price': game['price'],
        'image_url': game['image_url'],
        'developer': game['developer']['name'],
        'developer_country': game['developer']['country'],
        'genre': game['genre']['name'],
        'platforms': game['platforms'],
        'genre_tags': game['genre_tags'],
        'preference_tags': game['preference_tags']
    }

    return render_template('detail.html', game=formatted_game)

@app.route('/add', methods=['GET', 'POST'])
def add_game():
    """Add new game page"""
    if request.method == 'POST':
        # Process form data
        game_data = {
            'title': request.form['title'],
            'release_date': request.form['release_date'],
            'description': request.form['description'],
            'rating': float(request.form['rating']) if request.form['rating'] else None,
            'price': float(request.form['price']) if request.form['price'] else None,
            'developer': {
                'name': request.form['developer_name'],
                'country': request.form['developer_country']
            },
            'platforms': request.form.getlist('platforms'),
            'genre_tags': request.form.getlist('genre_tags'),
            'preference_tags': request.form.getlist('preference_tags')
        }

        # Handle file upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                # Extract file extension
                file_extension = os.path.splitext(file.filename)[1].lower()

                # Generate unique filename using UUID
                unique_filename = str(uuid.uuid4()) + file_extension

                # Save file with unique filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

                # Save relative path to database
                game_data['image_url'] = f"/{app.config['UPLOAD_FOLDER']}/{unique_filename}"
            else:
                # No image provided, set default image
                game_data['image_url'] = "/static/images/no_image.png"
        else:
            # No image provided, set default image
            game_data['image_url'] = "/static/images/no_image.png"

        # Create game
        game_id = game_dao.create_game(game_data)

        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {
                'success': True,
                'redirect': url_for('game_detail', game_id=game_id, _external=True)
            }
        else:
            flash('Game added successfully!', 'success')
            return redirect(url_for('game_detail', game_id=game_id))

    # GET request - show form
    filter_options = get_filter_options()

    return render_template('add.html',
                         filter_options=filter_options)

@app.route('/edit/<int:game_id>', methods=['GET', 'POST'])
def edit_game(game_id):
    """Edit game page"""
    game = game_dao.get_game_by_id(game_id)

    if not game:
        flash('Game not found', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Process form data
        update_data = {
            'title': request.form['title'],
            'release_date': request.form['release_date'],
            'description': request.form['description'],
            'rating': float(request.form['rating']) if request.form['rating'] else None,
            'price': float(request.form['price']) if request.form['price'] else None,
            'developer': {
                'name': request.form['developer_name'],
                'country': request.form['developer_country']
            },
            'platforms': request.form.getlist('platforms'),
            'genre_tags': request.form.getlist('genre_tags'),
            'preference_tags': request.form.getlist('preference_tags')
        }

        # Handle file upload
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file and file.filename != '' and allowed_file(file.filename):
                # Extract file extension
                file_extension = os.path.splitext(file.filename)[1].lower()

                # Generate unique filename using UUID
                unique_filename = str(uuid.uuid4()) + file_extension

                # Save file with unique filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))

                # Save relative path to database
                update_data['image_url'] = f"/{app.config['UPLOAD_FOLDER']}/{unique_filename}"
            # If no new file is uploaded, keep the existing image_url

        # Update game
        success = game_dao.update_game(game_id, update_data)

        if success:
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {
                    'success': True,
                    'redirect': url_for('game_detail', game_id=game_id, _external=True)
                }
            else:
                flash('Game updated successfully!', 'success')
                return redirect(url_for('game_detail', game_id=game_id))
        else:
            # Return JSON error response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {
                    'success': False,
                    'message': 'Failed to update game'
                }, 400
            else:
                flash('Failed to update game', 'error')

    # GET request - show form
    filter_options = get_filter_options()

    # Format game for form
    formatted_game = {
        'game_id': game['game_id'],
        'title': game['title'],
        'release_date': game['release_date'],
        'description': game['description'],
        'rating': game['rating'],
        'price': game['price'],
        'image_url': game['image_url'],
        'developer_name': game['developer']['name'],
        'developer_country': game['developer']['country'],
        'genre': game['genre']['name'],
        'platforms': game['platforms'],
        'genre_tags': game['genre_tags'],
        'preference_tags': game['preference_tags']
    }

    return render_template('edit.html',
                         game=formatted_game,
                         filter_options=filter_options)

@app.route('/delete/<int:game_id>', methods=['POST'])
def delete_game(game_id):
    """Delete game action"""
    success = game_dao.delete_game(game_id)

    if success:
        flash('Game deleted successfully!', 'success')
    else:
        flash('Failed to delete game', 'error')

    return redirect(url_for('index'))

def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Admin Authentication Routes
@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login route"""
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({'error': 'Password is required'}), 400

    # Check if password matches hardcoded value
    if data['password'] == 'admin123':
        session['is_admin'] = True
        return jsonify({'success': True, 'message': 'Login successful'}), 200
    else:
        return jsonify({'error': 'Invalid password'}), 401

@app.route('/admin/logout', methods=['POST', 'GET'])
def admin_logout():
    """Admin logout route"""
    session.pop('is_admin', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Create database directory if it doesn't exist
    os.makedirs('db', exist_ok=True)

    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)

from flask import Flask, render_template, request, redirect, url_for, session
import requests
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a random secret key

API_KEY = 'e1478ff1df8c5e4c8914ddd5f859ab46'

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 username TEXT UNIQUE, 
                 password TEXT)''')
    conn.commit()
    conn.close()

def get_movies(query):
    url = f"https://api.themoviedb.org/3/search/movie"
    params = {'api_key': API_KEY, 'query': query}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error fetching movies: {response.status_code}")  # Debugging statement
        return []

def get_movie_details(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {'api_key': API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_similar_movies(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/similar"
    params = {'api_key': API_KEY}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []

@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['username'] = username
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
    return render_template('register.html')

@app.route('/search', methods=['POST'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    query = request.form.get('query')
    print(f"Search query: {query}")  # Debugging statement
    movies = get_movies(query)
    print(f"Movies found: {movies}")  # Debugging statement
    return render_template('index.html', movies=movies)

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    movie_details = get_movie_details(movie_id)
    if movie_details:
        return render_template('movie.html', movie=movie_details)
    else:
        return "Movie details not found"

@app.route('/recommend/<int:movie_id>')
def recommend(movie_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    recommended_movies = get_similar_movies(movie_id)
    return render_template('recommendation.html', recommended_movies=recommended_movies)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
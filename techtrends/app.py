import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

from datetime import datetime
import logging

# Global variable to count the no of connections
connections_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connections_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    connections_count = connections_count + 1
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

def log_format_message(message):
    app.logger.info('{time} | {message}'.format(time=datetime.now().strftime("%m/%d/%Y, %H:%M:%S"), message=message))


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
#         logging.error('Article "'"%s"'" does not exist', post_id)
        log_format_message('Article "{}" does not exist'.format(post_id))
        return render_template('404.html'), 404
    else:
#         logging.info('Article "'"%s"'" retrieved!', post["title"])
        log_format_message('Article "{}" retrieved!'.format(post["title"]))
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
#     logging.info('"'"About Us"'" page retrieved')
    log_format_message('"'"About Us"'" page retrieved')
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
#             logging.info('New Article "'"%s"'" created', title) # without date
            log_format_message('New Article "{}" created'.format(title))
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')

@app.route('/healthz')
def healthcheck():
    response = ''
    try:
        connection = get_db_connection()
        connection.execute('SELECT 1 FROM posts').fetchone()
        connection.close()
        response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json')
        app.logger.info('healthcheck: ok')
    except Exception:
        response = app.response_class(
            response=json.dumps({"result":"Error - unhealthy"}),
            status=500,
            mimetype='application/json')
        app.logger.info('healthcheck: not ok')
    return response

@app.route('/metrics')
def metrics():
    """
    Total amount of posts in the database
    Total amount of connections to the database. 
    For example, accessing an article will query the database, hence will count as a connection.
    Example output: {"db_connection_count": 1, "post_count": 7}
    """
    connection = get_db_connection()
    posts_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    connection.close()
    response = app.response_class(
        response=json.dumps({"db_connection_count":connections_count,"post_count":posts_count}),
        status=200,
        mimetype='application/json')
    app.logger.info('Metrics request successful')
    return response

# start the application on port 3111
if __name__ == "__main__":
    # stream logs to a console
    logging.basicConfig(level=logging.DEBUG)
    app.run(host='0.0.0.0', port='3111')
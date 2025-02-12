import sqlite3

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys

db_connection_count = 0
logging.basicConfig(level=logging.DEBUG)


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connection_count += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',(post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'victor'


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    # app.logger.warning('Warning level log')

    return render_template('index.html', posts=posts)


@app.route('/healthz')
def health():
    healthy = True
    try:
        index()
    except:
        healthy = False

    if healthy:
        response = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    else:
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )

    app.logger.info('health Status request successfull')
    return response


@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    counts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    counts = len(counts)
    # print('\n'*10)
    # print(db_connection_count)
    # print(counts)
    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connection_count, "post_count": counts}),
        status=200,
        mimetype='application/json'
    )

    return response


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.info('non-existing article is accessed  ')
        return render_template('404.html'), 404
    else:
        app.logger.info('existing article : {}'.format(post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('"About Us" page is retrieved ')
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
            app.logger.info('new article is created, title: {}'.format(title))

            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    handler1 = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(levelname)s: %(name)s [%(asctime)s] - %(message)s")
    handler1.setFormatter(formatter)
    handler1.setLevel(logging.DEBUG)
    app.logger.addHandler(handler1)

    handler2= logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter("%(levelname)s: %(name)s [%(asctime)s] - %(message)s")
    handler2.setLevel(logging.DEBUG)
    handler2.setFormatter(formatter)
    app.logger.addHandler(handler2)

    app.run(host='0.0.0.0', port=3111, debug=True)

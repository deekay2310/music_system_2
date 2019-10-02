from flask import Flask, render_template, flash, redirect, url_for, request, session, logging
from Recommendations import popular_recommender, similar_recommender
from flask_mysqldb import MySQL
from functools import wraps
from passlib.hash import sha256_crypt

app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#Initialize MySQL
mysql = MySQL(app)

popular_songs = popular_recommender()

@app.route('/')
def intro():
    return render_template("intro.html")

@app.route('/popularity')
def popular():
    return render_template("popularity.html", popularSongs = popular_songs)

@app.route('/similarity')
def similar():
    return render_template("similarity.html")

@app.route('/similarity', methods = ["GET","POST"] )
def get_data():
    if request.method == "POST":
      song_from_form = request.form["song"]
      artist_from_form = request.form["artist"]  
      similar_songs = similar_recommender(song_from_form, artist_from_form)
    return render_template("similarity.html", similarSongs = similar_songs) 

@app.route('/register', methods = ['GET','POST'])
def register():
  if request.method == 'POST':
    name = request.form["name"]
    email = request.form["email"]
    username = request.form["username"]
    password = sha256_crypt.encrypt(str(request.form["password"]))
    #cursor obj created
    cur = mysql.connection.cursor()
    #query executed
    cur.execute("INSERT INTO users (name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))
    #commit
    mysql.connection.commit()
    #close cursor
    cur.close()
    #flash message
    flash("You are now registered and can log in.", 'success')
    return redirect(url_for('login'))
  return render_template("register.html") 

@app.route('/login', methods = ['GET','POST'])
def login():
  if request.method == 'POST':
    username = request.form["username"]
    password_login = request.form["password"]
    #cursor obj created
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM users WHERE username = %s", [username])
    if result > 0:
      data = cur.fetchone()
      password = data['password']
      if sha256_crypt.verify(password_login, password):
        session['logged_in'] = True
        session['username'] = username
        flash("Logged In Successfully!", "success")
        return redirect(url_for('library'))
      else:
        error = "Incorrect Password!"
        return render_template("login.html", error=error)
      cur.close()
    else:
        error = "User is not registered."
        return render_template("login.html", error=error)
  return render_template("login.html")

def is_logged_in(f):
  @wraps(f)
  def wrap(*args, **kwargs):
    if 'logged_in' in session:
      return f(*args, **kwargs)
    else:
      flash("Please log in to access your library!","danger")
      return redirect(url_for("login"))
  return wrap

@app.route('/logout')
@is_logged_in
def logout():
  session.clear()
  flash("Logged out successfully!","success")
  return redirect(url_for('login'))

@app.route('/add_song/<song>', methods = ['GET','POST'])
@is_logged_in
def add_song(song):
  print(song)
  print(session["username"])
  if request.method == 'POST':
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO songs (song, username) VALUES('%s', '%s')", (song, session["username"]))
    mysql.connection.commit()
    cur.close()
    flash("Song saved successfully!", "success")
    return redirect(url_for('library'))
  return render_template('library.html')

@app.route('/library')
@is_logged_in
def library():
  return render_template("library.html")

if __name__=="__main__":
    app.secret_key='secret123'
    app.run(debug=True)

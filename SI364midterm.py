###############################
####### SETUP (OVERALL) #######
###############################

## Import statements
# Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
import json, requests
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, ValidationError # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required, Length # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell

## App setup code

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.debug = True
app.use_reloader = True


## All app.config values

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string from si364'

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://localhost/movies_and_ratings"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## Statements for db setup (and manager setup if using Manager)
manager = Manager(app)
db = SQLAlchemy(app)


######################################
######## HELPER FXNS (If any) ########
######################################




##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "names"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)

class MovieList(db.Model):
    __tablename__ = "list"
    id = db.Column(db.Integer,primary_key=True)
    movie_name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.movie_name, self.id)

class Movie(db.Model):
    __tablename__ = 'movie'
    movieId = db.Column(db.Integer, primary_key=True)
    movieName = db.Column(db.String(64))
    movieRating = db.Column(db.Integer)
    userId = db.Column(db.Integer, db.ForeignKey('user.userId'))

    def __repr__(self):
        return "Movie: {} (Rating: {})".format(self.movieName, self.movieRating)


class User(db.Model):
    __tablename__ = 'user'
    userId = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    ratings = db.relationship('Movie', backref='User')

    def __repr__(self):
        return "{} (ID: {}".format(self.username, self.userId)


###################
###### FORMS ######
###################

class NameForm(FlaskForm):
    name = StringField("Please enter your name: ",validators=[Required()])
    submit = SubmitField()

class MovieListForm(FlaskForm):
    your_movies = StringField("Add a movie to your list", validators=[Required()])
    submit = SubmitField()


class MovieEntryForm(FlaskForm):
    user = StringField('Enter your name ', validators=[Required()])
    movie = StringField('Enter the name of the movie ', validators=[Required()])
    rating = RadioField('How many stars do you give this movie? ', choices=[('1', '1 star'),('2', '2 stars'),('3', '3 stars'), ('4', '4 stars'), ('5','5 stars')], validators=[Required()])
    submit = SubmitField('Submit')


class MovieForm(FlaskForm):
    movie = StringField('Enter the name of the movie ', validators=[Required()])
    submit = SubmitField('Submit')

    def validate_movie(self,field):
        form = MovieForm()
        invalid = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R','S','T','U','V','W','X','Y','Z']
        for char in field.data.split():
            if char[0] not in invalid:
                raise ValidationError('Case Sensitive!')


#######################
###### VIEW FXNS ######
#######################


@app.route('/', methods=['POST', 'GET'])
def home():
    form = NameForm() # User should be able to enter name after name and each one will be saved, even if it's a duplicate! Sends data with GET
    if form.validate_on_submit():
        name = form.name.data
        newname = Name(name = name)
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('save'))
    return render_template('base.html',form=form)

@app.route('/names')
def all_names():
    names = Name.query.all()
    return render_template('name_example.html',names=names)

@app.route('/save_movie')
def save():
    form = MovieListForm()
    return render_template('list_form.html', form=form)

@app.route('/movie_list', methods=['POST', 'GET'])
def movie_list():
    form = MovieListForm()
    if form.validate_on_submit():
        movie = form.your_movies.data
        m = MovieList(movie_name=movie)
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('all_movies'))
    return render_template('list_form.html', form=form)
    
@app.route('/all_movies')
def all_movies():
    movies = MovieList.query.all()
    return render_template('movie_list.html', movies=movies)

@app.route('/rate')
def rate():
    form = MovieEntryForm()
    return render_template('get_movie.html',form=form)


@app.route('/getmovie', methods = ['GET', 'POST'])
def get_movie():
    form = MovieEntryForm()
    if request.method == 'GET':
        user = request.args.get('user')
        movie = request.args.get('movie')
        rating = request.args.get('rating')
        # return(rating)

        reviewer = User.query.filter_by(username=user).first()
        if reviewer:
            print('user already exists', reviewer.userId)
        else:
            reviewer = User(username=user)
            db.session.add(reviewer)
            db.session.commit()

        review = Movie.query.filter_by(movieName=movie).first()
        if review:
            if User.query.filter_by(username=user):
                print('User already rated movie')
            flash('This movie has already been rated!')
            return redirect(url_for('movies_and_ratings'))

        userId = reviewer.userId
        m = Movie(movieName=movie, movieRating=rating, userId=userId)
        db.session.add(m)
        db.session.commit()
        # # flash(rating successfully)
        # flash('***MOVIE ALREADY EXISTS!***')

        flash('Movie successfully saved!')
    return render_template('get_movie.html', form=form)

    # return render_template('movie_results.html', form=form, objects=data['results'], movie=movie, rating=rating)

@app.route('/all_ratings')
def movies_and_ratings():
    # print(request.args.get('user'))
    ratings = []
    all_ratings = Movie.query.all()
    # print(all_ratings)
    # print(User.query.all())
    for rt in all_ratings:
        user_ratings = User.query.filter_by(userId=rt.userId).first()
        ratings.append((user_ratings.username, rt.movieRating, rt.movieName))
    return render_template('movies.html', ratings=ratings)

@app.route('/movie_count')
def count():
    form = MovieEntryForm()
    num_movies = len(Movie.query.all())
    return render_template('count.html', form=form, num_movies=num_movies)


@app.route('/get_review', methods=['GET','POST'])
def movie():
    form = MovieForm()
    # form = MovieEntryForm(request.form)
    if form.validate_on_submit():
        movie = form.movie.data
        api_key = '20ed2c68eb8741a781815d3945a58ef5'
        # result = request.args
        params = {}
        params['api-key'] = api_key
        params['query'] = movie
        # # params['maxResults='] = 25
        resp = requests.get('https://api.nytimes.com/svc/movies/v2/reviews/search.json?', params=params)
        data = json.loads(resp.text)

        title = data['results'][0]['display_title']
        link = data['results'][0]['link']['url']

        return render_template('movie_info.html', title=title, link=link)
    elif request.method == "GET":
        return render_template('movie_entry.html', form=form)

    else:
        flash(form.errors)
        return render_template('movie_entry.html',form=form)




@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    db.create_all()
    manager.run() # Will create any defined models when you run the application
    app.run(use_reloader=True,debug=True) # The usual

## Code to run the application...

# Put the code to do so here!
# NOTE: Make sure you include the code you need to initialize the database structure when you run the application!

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'key'
Bootstrap(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///film-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

headers = {
    "Authorization": "Bearer ***"}

API_ENDPOINT = "https://api.themoviedb.org/3"


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)


db.create_all()


class EditForm(FlaskForm):
    rating = StringField("Your rating out of 10 (ex 7.5)", validators=[DataRequired()])
    review = StringField("Your review", validators=[DataRequired()])
    submit = SubmitField('Done')


class AddForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField('Done')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = EditForm()
    index = request.args.get("id")
    movie_to_edit = Movie.query.get(index)
    if form.validate_on_submit():
        movie_to_edit.rating = form.rating.data
        movie_to_edit.review = form.review.data
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie_to_edit)


@app.route("/delete")
def delete():
    index = request.args.get("id")
    movie_to_delete = Movie.query.get(index)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddForm()
    if form.validate_on_submit():
        data = {
            "query": form.title.data,
        }
        response = requests.get(url=f"{API_ENDPOINT}/search/movie", params=data, headers=headers)
        response.raise_for_status()
        movies_data = response.json()["results"]
        return render_template("select.html", movies=movies_data)
    return render_template("add.html", form=form)


@app.route("/update")
def update():
    index = request.args.get("id")
    if index:
        response = requests.get(url=f"{API_ENDPOINT}/movie/{index}", headers=headers)
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            img_url=f"https://image.tmdb.org/t/p/w500{data['poster_path']}",
            year=data["release_date"].split("-")[0],
            description=data["overview"],
        )
        db.session.add(new_movie)
        movie = Movie.query.filter_by(title=data["title"]).first()
        db.session.commit()
        return redirect(url_for("edit", id=movie.id))
    return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)

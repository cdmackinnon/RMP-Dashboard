import json
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding
from src.scraping import ProfessorScraper
from pathlib import Path

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///rmp.db"
db = SQLAlchemy(app)


def initialize_database(app):
    with app.app_context():
        if not db.engine.dialect.has_table(
            db.engine.connect(), "schools"
        ):  # Checking if a table exists
            with open("db/schema.sql", "r") as f:
                db.session.execute(text(f.read()))
            db.session.commit()


def user_scrape_request(id: int) -> None:
    """
    Scrapes a single university and adds the parquet to the data directory
    Input: id from the SCHOOL table in the database.
    """
    pass
    # todo use the scraping file pass it in, get html, make parquet, delete html
    # Consdier returning the full html file or storing or retriveung or whatever ... SPEED


@app.route("/")
def index():
    with db.engine.connect() as connection:
        result = connection.execute(text("SELECT school_name, school_id FROM schools"))
    schools = [{"school_name": row[0], "school_id": row[1]} for row in result]
    return render_template("index.html", schools=schools)


# TODO implement a way to rescrape all the schools names
# This visits 8000 URLs to retrieve the (name, id) combos
# def get_university_names():
#     NUM_UNIVERSITIES = 8000
#     school_data = {}
#     test = ProfessorScraper()

#     for id in range(1, NUM_UNIVERSITIES):
#         name = test.fetch_school_name(id)
#         # Store only if a valid name is found
#         if name and name != "other schools":
#             school_data[id] = name

#     # Save dictionary to JSON file
#     with open("data/school_names.json", "w") as f:
#         json.dump(school_data, f, indent=4)

if __name__ == "__main__":
    initialize_database(app)
    with app.app_context():
        seeding = Seeding(db.engine.connect())
        seeding.initialize_school_names()
        seeding.seed_existing_data()
    app.run(debug=False, port=8080)

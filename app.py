import json
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding
from src.scraping import ProfessorScraper
from pathlib import Path
from src.parse_professors import parse_professors, save_to_parquet

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


def user_scrape_request(id: int, name: str) -> None:
    """
    Scrapes a single university and adds the parquet to the data directory.

    *Note: Lacks optimization for multiple threads or object persistence for consecutive requests.
    (i.e. start-up time for the webdriver on each request)*

    Input: id from the SCHOOL table in the database, Name for the parquet
    """
    url = f"https://www.ratemyprofessors.com/search/professors/{id}?q="

    scraper = ProfessorScraper()
    html_string = scraper.read_page_source(url, output_file=None)
    df = parse_professors(html_string)
    seeder = Seeding(db.engine.connect())
    seeder.seed_dataframe(df)
    data_path = Path(__file__).parent / "data/dataframes" / f"{name}.parquet"
    save_to_parquet(df, data_path)


@app.route("/")
def index():
    with db.engine.connect() as connection:
        result = connection.execute(text("SELECT school_name, school_id FROM schools"))
    schools = [{"school_name": row[0], "school_id": row[1]} for row in result]
    return render_template("index.html", schools=schools)


@app.route("/scrape")
def scrape_page():
    with db.engine.connect() as connection:
        result = connection.execute(
            text(
                """
            SELECT school_name, school_id
            FROM schools
            WHERE school_id NOT IN (
                SELECT DISTINCT school_id
                FROM instructors
            );
            """
            )
        )
        schools = [{"school_name": row[0], "school_id": row[1]} for row in result]

    return render_template("scrape.html", schools=schools)


@app.route("/scrape/<int:school_id>")
def scrape(school_id):
    with db.engine.connect() as connection:
        result = connection.execute(
            text("SELECT school_name FROM schools WHERE school_id = :school_id"),
            {"school_id": school_id},
        )
        school_name = result.fetchone()[0]

    # Call the scraping function
    user_scrape_request(school_id, school_name)

    return f"Scraped {school_name} with ID {school_id}."


if __name__ == "__main__":
    initialize_database(app)
    with app.app_context():
        seeding = Seeding(db.engine.connect())
        seeding.initialize_school_names()
        seeding.seed_existing_data()
    app.run(debug=False, port=8080)

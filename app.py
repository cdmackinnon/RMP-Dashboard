from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding

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


@app.route("/")
def index():
    with db.engine.connect() as connection:
        result = connection.execute(text("SELECT school_name, school_id FROM schools"))
    schools = [{"school_name": row[0], "school_id": row[1]} for row in result]
    return render_template("index.html", schools=schools)


if __name__ == "__main__":
    initialize_database(app)
    with app.app_context():
        seeding = Seeding(db.engine.connect())
        seeding.initialize_school_names()
        seeding.seed_existing_data()
    app.run(debug=True, port=8080)

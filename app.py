from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///rmp.db'
db = SQLAlchemy(app)

def initialize_database(app):
    with app.app_context():
        if not db.engine.dialect.has_table(db.engine.connect(), 'schools'):  # Checking if a table exists
            print("here")
            with open('db/schema.sql', 'r') as f:
                db.session.execute(text(f.read()))
            db.session.commit()

@app.route('/')
def index():
    # Query the database to get column names of the 'schools' table
    with db.engine.connect() as connection:
        result = connection.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'schools'"))
    column_names = [row[0] for row in result]

    # Pass the column names to the template
    return render_template("index.html", column_names=column_names)

if __name__ == "__main__":
    initialize_database(app)
    app.run(debug=True, port=8080)


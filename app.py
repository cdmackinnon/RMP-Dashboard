from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils
import json
from flask import request, jsonify

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


@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term", "")
    with db.engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT DISTINCT school_name FROM Schools WHERE school_name ILIKE :term LIMIT 10"
            ),
            {"term": f"%{term}%"},
        )
        names = [row[0] for row in result]
    return jsonify(names)


@app.route("/")
def index():
    return "Index"


@app.route("/departments")
def school():
    return render_template("departments.html")


@app.route("/school_plot")
def school_plot():
    # Retrieve the school name from the URL with default ""
    school_name = request.args.get("school_name", "")
    minReviews = request.args.get("min_reviews", 1000)
    metric = request.args.get("metric", "difficulty")

    if not school_name:
        return jsonify({"error": "Missing school_name parameter"}), 400

    # Query for the school's departments with their resepective difficulties and total ratings
    with db.engine.connect() as connection:
        result = connection.execute(
            text(
                f"""
                SELECT d.department_name, 
                        ROUND(SUM(i.{metric} * i.total_ratings) / SUM(i.total_ratings), 2) AS avg_metric,
                        SUM(i.total_ratings) as total_ratings
                FROM Instructors i
                JOIN Departments d ON i.department_id = d.department_id
                JOIN Schools s ON i.school_id = s.school_id
                WHERE s.school_name = :school_name
                GROUP BY d.department_name
                HAVING SUM(i.total_ratings) >= :minReviews
                ORDER BY avg_metric DESC
                """
            ),
            {
                "school_name": school_name,
                "minReviews": minReviews,
            },
        )
        data = result.fetchall()

    if not data:
        return jsonify({"error": "No data found"}), 404

    departments = [row[0] for row in data]
    avg_stat = [row[1] for row in data]
    total_ratings = [row[2] for row in data]

    bar = go.Bar(
        x=departments,
        y=avg_stat,
        text=[f"{tr} ratings" for tr in total_ratings],
        marker_color="#FF9149",
    )

    # Change the title and axis based on user selection
    if metric == "difficulty":
        title = "Average Professor Difficulty"
        ticks = [1, 2, 3, 4, 5]
        span = [1, 5]
    elif metric == "quality":
        title = "Average Professor Quality"
        ticks = [1, 2, 3, 4, 5]
        span = [1, 5]
    else:
        title = "Average Professor Retake Percent"
        ticks = [0, 25, 50, 75, 100]
        span = [0, 100]

    layout = go.Layout(
        title=f"Department Wide Averages at {school_name}",
        xaxis=dict(title="Department", tickangle=45),
        yaxis=dict(title=title, range=span, tickvals=ticks),
        height=600,
        margin=dict(b=150),
        paper_bgcolor="#FFEDDB",
    )

    fig = go.Figure(data=[bar], layout=layout)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return jsonify({"graphJSON": graph_json})


if __name__ == "__main__":
    initialize_database(app)
    # with app.app_context():
    #     seeding = Seeding(db.engine.connect())
    #     seeding.initialize_school_names()
    #     seeding.seed_existing_data()
    app.run(debug=True, port=8080)

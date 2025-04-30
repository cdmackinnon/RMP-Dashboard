import json
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils
import json
from flask import request, jsonify
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


@app.route("/autocomplete")
def autocomplete():
    term = request.args.get("term", "")
    with db.engine.connect() as conn:
        result = conn.execute(
            text(
                """
                SELECT DISTINCT school_name 
                FROM Schools 
                RIGHT JOIN Instructors
                ON Schools.school_id = Instructors.school_id
                WHERE school_name 
                ILIKE :term LIMIT 10
                """
            ),
            {"term": f"%{term}%"},
        )
        names = [row[0] for row in result]
    return jsonify(names)


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
    return render_template("index.html")


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


@app.route("/comparison")
def comparison():
    return render_template("comparison.html")


@app.route("/box_plot")
def box_plot():
    school_names = request.args.getlist("schools[]")
    department = request.args.get("department")
    metric = request.args.get("metric")

    if not school_names or not department or not metric:
        return jsonify({"error": "Missing parameters"}), 400

    box_data = []
    with db.engine.connect() as conn:
        for school in school_names:
            result = conn.execute(
                text(
                    f"""
                    SELECT i.{metric}
                    FROM Instructors i
                    JOIN Departments d ON i.department_id = d.department_id
                    JOIN Schools s ON i.school_id = s.school_id
                    WHERE s.school_name = :school AND d.department_name = :dept AND i.{metric} IS NOT NULL
                """
                ),
                {"school": school, "dept": department},
            )
            values = [row[0] for row in result]
            if values:
                box_data.append(
                    go.Box(
                        x=values,
                        name=school,
                        boxpoints="outliers",
                        marker_color="#FF9149",
                        orientation="h",
                        hoverinfo="x",
                    )
                )

    if not box_data:
        return jsonify({"error": "No data found"}), 404

    if metric != "retake_percent":
        ticks = [1, 2, 3, 4, 5]
        span = [1, 5]
    else:
        ticks = [0, 25, 50, 75, 100]
        span = [0, 100]

    metric = metric.replace("_", " ").title()

    layout = go.Layout(
        title=f"{metric} Distribution in {department} Across Schools",
        xaxis=dict(title=metric, range=span, tickvals=ticks),
        paper_bgcolor="#FFEDDB",
        height=600,
    )

    fig = go.Figure(data=box_data, layout=layout)
    return jsonify({"graphJSON": json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)})


@app.route("/departments_for_schools")
def departments_for_schools():
    schools = request.args.getlist("schools[]")
    if not schools:
        return jsonify([])

    with db.engine.connect() as conn:
        result = conn.execute(
            # Finding the departments shared across all schools
            text(
                """
                SELECT department_name
                FROM Departments
                JOIN Instructors ON Instructors.department_id = Departments.department_id
                JOIN Schools ON Schools.school_id = Instructors.school_id
                WHERE Schools.school_name = ANY(:schools)
                GROUP BY department_name
                HAVING COUNT(DISTINCT Schools.school_name) = :num_schools
                """
            ),
            {"schools": schools, "num_schools": len(schools)},
        )
        departments = sorted({row[0] for row in result})
    return jsonify(departments)


if __name__ == "__main__":
    initialize_database(app)
    # with app.app_context():
    #     seeding = Seeding(db.engine.connect())
    #     seeding.initialize_school_names()
    #     seeding.seed_existing_data()
    app.run(debug=True, port=8080)

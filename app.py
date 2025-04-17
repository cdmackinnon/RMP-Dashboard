from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
from src.seeding import Seeding
import plotly.graph_objs as go
import plotly.io as pio
import plotly.utils
import json

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


from flask import request, jsonify


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
    return render_template("index.html")


@app.route("/school_plot")
def school_plot():
    school_name = request.args.get("school_name", "")
    if not school_name:
        return jsonify({"error": "Missing school_name parameter"}), 400

    with db.engine.connect() as connection:
        result = connection.execute(
            text(
                """
                SELECT
                    d.department_name,
                    ROUND(SUM(i.difficulty * i.total_ratings) / SUM(i.total_ratings), 2) AS avg_difficulty,
                    SUM(i.total_ratings) as total_ratings
                FROM
                    Instructors i
                JOIN
                    Departments d ON i.department_id = d.department_id
                JOIN
                    Schools s ON i.school_id = s.school_id
                WHERE
                    s.school_name = :school_name
                GROUP BY
                    d.department_name
                HAVING
                    SUM(i.total_ratings) > 10
                ORDER BY
                    avg_difficulty DESC
                """
            ),
            {"school_name": school_name},
        )

        data = result.fetchall()

    if not data:
        return jsonify({"error": "No data found"}), 404

    departments = [row[0] for row in data]
    avg_difficulties = [row[1] for row in data]
    total_ratings = [row[2] for row in data]

    bar = go.Bar(
        x=departments,
        y=avg_difficulties,
        text=[f"{tr} ratings" for tr in total_ratings],
        marker_color="indianred",
    )

    layout = go.Layout(
        title=f"Average Difficulty per Department at {school_name}",
        xaxis=dict(title="Department", tickangle=45),
        yaxis=dict(title="Avg Difficulty"),
        height=600,
        margin=dict(b=150),
    )

    fig = go.Figure(data=[bar], layout=layout)
    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return jsonify({"graphJSON": graph_json})


# @app.route("/")
# def index():
#     with db.engine.connect() as connection:
#         result = connection.execute(
#             text(
#                 """
#             SELECT
#                 s.school_name,
#                 s.school_id,
#                 ROUND(SUM(i.quality * i.total_ratings) / SUM(i.total_ratings), 2) AS avg_quality,
#                 ROUND(SUM(i.difficulty * i.total_ratings) / SUM(i.total_ratings), 2) AS avg_difficulty
#             FROM
#                 Schools s
#             JOIN
#                 Instructors i ON s.school_id = i.school_id
#             GROUP BY
#                 s.school_id, s.school_name
#             HAVING
#                 SUM(i.total_ratings) > 100;

#         """
#             )
#         )

#         data = result.fetchall()
#     school_names = [row[0] for row in data]
#     avg_qualities = [row[2] for row in data]
#     avg_difficulties = [row[3] for row in data]

#     scatter = go.Scatter(
#         x=avg_difficulties,
#         y=avg_qualities,
#         mode="markers+text",
#         hovertext=school_names,
#         # text= school_names,
#         textposition="top center",
#         marker=dict(size=12, color="skyblue"),
#     )

#     layout = go.Layout(
#         title="Average Quality vs Difficulty per School",
#         xaxis=dict(title="Average Difficulty"),
#         yaxis=dict(title="Average Quality"),
#         height=600,
#     )

#     fig = go.Figure(data=[scatter], layout=layout)
#     graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
#     return render_template("index.html", graphJSON=graph_json)


if __name__ == "__main__":
    initialize_database(app)
    # with app.app_context():
    #     seeding = Seeding(db.engine.connect())
    #     seeding.initialize_school_names()
    #     seeding.seed_existing_data()
    app.run(debug=True, port=8080)

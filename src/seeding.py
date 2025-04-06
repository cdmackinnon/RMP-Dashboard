import json
from pathlib import Path
from sqlalchemy.sql import text
from bs4 import BeautifulSoup
import tqdm
import polars as pl

# SCHOOLS_PATH = os.path.join(os.path.dirname(__file__), "../data/dataframes")


class Seeding:
    def __init__(self, db_connection: str):
        self.db_connection = db_connection

    def initialize_school_names(self):
        # names = os.path.join(os.path.dirname(__file__), "../data/school_names.json")
        school_names_path = Path(__file__).parent.parent / "data/school_names.json"
        with open(school_names_path, "r") as file:
            school_data = json.load(file)

        # Schools with scraped data
        # files = os.listdir(os.path.join(os.path.dirname(__file__), "../data/schools"))
        school_html_path = Path(__file__).parent.parent / "data/schools"
        files = [f.name for f in school_html_path.iterdir() if f.is_file()]

        with self.db_connection.begin():
            for school_id, name in school_data.items():
                # if the school has data add it to the database
                if name in files:
                    self.db_connection.execute(
                        text(
                            """
                            INSERT INTO Schools (school_id, school_name)
                            VALUES (:school_id, :school_name)
                            ON CONFLICT (school_id) DO NOTHING
                            """
                        ),
                        {"school_id": int(school_id), "school_name": name},
                    )

    def seed_existing_data(self):
        # SCHOOLS_PATH = "/Users/connormackinnon/Desktop/Automations and workflows/RMP/RMP-Dashboard/data/dataframes"
        dataframes_path = Path(__file__).parent.parent / "data/dataframes"
        files = [f for f in dataframes_path.iterdir() if f.is_file()]
        # files = os.listdir(dataframes_path)
        for file in tqdm.tqdm(files, desc="Seeding files into database"):
            if not file.suffix == ".parquet":
                continue

            # dataframes_path
            # os.path.join(SCHOOLS_PATH, file)
            df = pl.read_parquet(file)

            with self.db_connection.begin():
                for row in df.iter_rows(named=True):
                    department = row["Department"]
                    school = row["School"]

                    # Insert department if not exists, or get existing id
                    department_id = self.db_connection.execute(
                        text(
                            """
                            INSERT INTO Departments (department_name)
                            VALUES (:department_name)
                            ON CONFLICT (department_name) DO NOTHING
                            RETURNING department_id
                        """
                        ),
                        {"department_name": department},
                    ).scalar()

                    if department_id is None:
                        department_id = self.db_connection.execute(
                            text(
                                """
                                SELECT department_id
                                FROM Departments
                                WHERE department_name = :department_name
                            """
                            ),
                            {"department_name": department},
                        ).scalar()

                    # Get school ID
                    school_id = self.db_connection.execute(
                        text(
                            """
                            SELECT school_id
                            FROM Schools
                            WHERE school_name = :school_name
                        """
                        ),
                        {"school_name": school},
                    ).scalar()

                    if school_id is not None:
                        self.db_connection.execute(
                            text(
                                """
                                INSERT INTO Instructors (
                                    instructor_name,
                                    department_id,
                                    school_id,
                                    quality,
                                    total_ratings,
                                    retake_percent,
                                    difficulty
                                ) VALUES (
                                    :instructor_name,
                                    :department_id,
                                    :school_id,
                                    :quality,
                                    :total_ratings,
                                    :retake_percent,
                                    :difficulty
                                )
                            """
                            ),
                            {
                                "instructor_name": row["Name"],
                                "department_id": department_id,
                                "school_id": school_id,
                                "quality": row["Quality"],
                                "total_ratings": row["# of Ratings"],
                                "retake_percent": row["Would Take Again (%)"],
                                "difficulty": row["Difficulty"],
                            },
                        )
                    else:
                        print(
                            f"Warning: Skipping instructor {row['Name']} because "
                            f"school '{row['School']}' does not exist."
                        )

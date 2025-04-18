import json
from pathlib import Path
from sqlalchemy.sql import text
from bs4 import BeautifulSoup
import tqdm
import polars as pl


class Seeding:
    """
    Class for loading any information into the database.
    Instantiated with a database connection.
    """

    def __init__(self, db_connection: str):
        self.db_connection = db_connection

    # Why not include every school then search bar can query unique instructors?
    # Advantageous for rescraping, initial scraping
    # Disadvantageous for all school queries (need unique school instructor 🤷)
    def initialize_school_names(self):
        """
        Initializes university names and ids.
        Uses a JSON file containing this prescrapped information.
        """
        # Open the JSON file of all RMP university names
        # Contains names and ids between 1 and 8000 from rate my professor URLs
        # I.e. "https://www.ratemyprofessors.com/search/professors/{SCHOOL_ID_NUMBER}?q="
        school_names_path = Path(__file__).parent.parent / "data/school_names.json"
        with open(school_names_path, "r") as file:
            school_data = json.load(file)

        with self.db_connection.begin():
            for school_id, name in school_data.items():
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
        """
        Opens the "data/dataframes" folder and seeds all existing dataframes.
        Skips files without the .parquet "ending"
        """
        # Open the directory of all dataframes
        dataframes_path = Path(__file__).parent.parent / "data/dataframes"
        files = [f for f in dataframes_path.iterdir() if f.is_file()]
        for file in tqdm.tqdm(files, desc="Seeding files into database"):
            # Skip erroneous files
            if not file.suffix == ".parquet":
                continue
            # TODO check runtime for these extra function calls
            self.seed_file(file)

    # TODO Type hint the parquet file
    def seed_file(self, file):
        """
        Seed a file into the database.
        Fails if the university name is not recognized

        Input: parquet file
        """
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

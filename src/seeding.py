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

    def initialize_school_names(self) -> None:
        """
        Initializes university names and IDs in the database.
        Uses a JSON file containing this prescrapped information.
        """
        school_data = self.get_school_names()

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

    def get_school_names(self) -> dict:
        """
        Returns a dictionary of all Rate My Professor school IDs and their names
        """
        # Open the JSON file of all RMP university names
        # Contains names and IDs between 1 and 8000 from rate my professor URLs
        # I.e. "https://www.ratemyprofessors.com/search/professors/{SCHOOL_ID_NUMBER}?q="
        school_names_path = Path(__file__).parent.parent / "data/school_names.json"
        with open(school_names_path, "r", encoding="UTF-8") as file:
            school_data = json.load(file)
        return school_data

    def seed_existing_data(self) -> None:
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

    def seed_file(self, file: Path) -> None:
        """
        Converts a file path to a Polars DataFrame and seeds it into the database.
        """
        return self.seed_dataframe(pl.read_parquet(file))

    def seed_dataframe(self, df: pl.DataFrame) -> None:
        """
        Seed a Polars Dataframe into the database.
        Fails if the university name is not recognized
        """

        # Retrieving schools id's and their corresponding names
        school_names = self.get_school_names()
        # Flipping the id name mapping
        school_id_mapping = {val: int(key) for key, val in school_names.items()}

        # Storing the department IDs to avoid duplicate inserts and faster retrieval
        department_cache = {}
        # Storing the instructors to be inserted for bulk insert
        pending_instructors = []

        for row in df.iter_rows(named=True):
            department_name = row["Department"]
            school_name = row["School"]

            # Check the new school name matches a name in the schools table
            school_id = school_id_mapping.get(school_name)
            if not school_id:
                print(
                    f"Skipping instructor {row['Name']} — unknown school: {school_name}"
                )
                continue

            # Adding or retrieving the department name and department ID
            if department_name not in department_cache:
                # Equals 0 if the department already exists
                department_id = self.db_connection.execute(
                    text(
                        """
                        INSERT INTO Departments (department_name)
                        VALUES (:name)
                        ON CONFLICT (department_name) DO NOTHING
                        RETURNING department_id
                    """
                    ),
                    {"name": department_name},
                ).scalar()

                # If the department already exists, then retrieve its ID
                if department_id is None:
                    department_id = self.db_connection.execute(
                        text(
                            """
                            SELECT department_id
                            FROM Departments
                            WHERE department_name = :name
                        """
                        ),
                        {"name": department_name},
                    ).scalar()

                # Store the department ID in the cache for faster access later
                department_cache[department_name] = department_id

            department_id = department_cache[department_name]

            # Prep instructors to be added to the database with a dictionary
            # Dictionaries allow for bulk insertions for efficiency
            pending_instructors.append(
                {
                    "instructor_name": row["Name"],
                    "department_id": department_id,
                    "school_id": school_id,
                    "quality": row["Quality"],
                    "total_ratings": row["# of Ratings"],
                    "retake_percent": row["Would Take Again (%)"],
                    "difficulty": row["Difficulty"],
                }
            )

        # Bulk insert using an insert statement and dictionary
        if pending_instructors:
            insert_statement = text(
                """
                INSERT INTO Instructors (
                    instructor_name, department_id, school_id,
                    quality, total_ratings, retake_percent, difficulty
                ) VALUES (
                    :instructor_name, :department_id, :school_id,
                    :quality, :total_ratings, :retake_percent, :difficulty
                )
            """
            )
            self.db_connection.execute(insert_statement, pending_instructors)
            self.db_connection.commit()

import json
import os
from sqlalchemy.sql import text
from bs4 import BeautifulSoup
import pandas as pd

SCHOOLS_PATH = os.path.join(os.path.dirname(__file__), "../data/schools")


class Seeding:
    def __init__(self, db_connection: str):
        self.db_connection = db_connection

    def parse_professors(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        professors = []

        # identify every professor card, extract data, and append it to the list of professors
        for card in soup.find_all("div", class_="TeacherCard__CardInfo-syjs0d-1"):
            try:
                name = card.find("div", class_="CardName__StyledCardName-sc-1gyrgim-0")
                name = name.text if name else "N/A"

                department = card.find(
                    "div", class_="CardSchool__Department-sc-19lmz2k-0"
                )
                department = department.text if department else "N/A"

                school = card.find("div", class_="CardSchool__School-sc-19lmz2k-1")
                school = school.text if school else "N/A"

                quality = card.find_next(
                    "div", class_="CardNumRating__CardNumRatingNumber-sc-17t4b9u-2"
                )
                quality = quality.text if quality else "N/A"

                num_ratings = card.find_next(
                    "div", class_="CardNumRating__CardNumRatingCount-sc-17t4b9u-3"
                )
                num_ratings = num_ratings.text.split()[0] if num_ratings else "0"

                would_take_again = card.find(
                    "div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2"
                )
                would_take_again = (
                    would_take_again.text.strip("%") if would_take_again else "N/A"
                )

                difficulty = card.find_all(
                    "div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2"
                )
                difficulty = difficulty[1].text if len(difficulty) > 1 else "N/A"

                professors.append(
                    [
                        name,
                        department,
                        school,
                        quality,
                        num_ratings,
                        would_take_again,
                        difficulty,
                    ]
                )

            except AttributeError as e:
                print(f"Error reading teacher card: {e}")
                continue

        df = pd.DataFrame(
            professors,
            columns=[
                "Name",
                "Department",
                "School",
                "Quality",
                "# of Ratings",
                "Would Take Again (%)",
                "Difficulty",
            ],
        )
        return df

    def initialize_school_names(self):
        names = os.path.join(os.path.dirname(__file__), "../data/school_names.json")
        with open(names, "r") as file:
            school_data = json.load(file)

        # Schools with scraped data
        files = os.listdir(SCHOOLS_PATH)

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
        # glob to get all the files in the directory
        files = os.listdir(SCHOOLS_PATH)
        for file in files:
            if file == ".DS_Store":
                continue
            df = self.parse_professors(os.path.join(SCHOOLS_PATH, file))

            # insert into the database
            with self.db_connection.begin():
                df.replace("N/A", None, inplace=True)
                for index, row in df.iterrows():
                    # Insert department if not exists and return department_id
                    department_id = self.db_connection.execute(
                        text(
                            """
                            INSERT INTO Departments (department_name)
                            VALUES (:department_name)
                            ON CONFLICT (department_name) DO NOTHING
                            RETURNING department_id
                            """
                        ),
                        {"department_name": row["Department"]},
                    ).scalar()

                    # If department_id is None, fetch existing department_id
                    if department_id is None:
                        department_id = self.db_connection.execute(
                            text(
                                """
                                SELECT department_id
                                FROM Departments
                                WHERE department_name = :department_name
                                """
                            ),
                            {"department_name": row["Department"]},
                        ).scalar()

                    # Retrieve school ID from Schools
                    school_id = self.db_connection.execute(
                        text(
                            """
                            SELECT school_id
                            FROM Schools
                            WHERE school_name = :school_name
                            """
                        ),
                        {"school_name": row["School"]},
                    ).scalar()

                    # Ensure school_id is valid then insert the instructor
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

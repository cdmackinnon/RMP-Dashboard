import json
from sqlalchemy.sql import text
import os
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np


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
                name = card.find(
                    "div", class_="CardName__StyledCardName-sc-1gyrgim-0"
                ).text
                department = card.find(
                    "div", class_="CardSchool__Department-sc-19lmz2k-0"
                ).text
                school = card.find("div", class_="CardSchool__School-sc-19lmz2k-1").text
                quality = card.find_next(
                    "div", class_="CardNumRating__CardNumRatingNumber-sc-17t4b9u-2"
                ).text
                num_ratings = card.find_next(
                    "div", class_="CardNumRating__CardNumRatingCount-sc-17t4b9u-3"
                ).text.split()[0]
                would_take_again = card.find(
                    "div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2"
                ).text.strip("%")
                difficulty = card.find_all(
                    "div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2"
                )[1].text

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
                print(f"Skipping a professor card due to missing data: {e}")
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

        with self.db_connection.begin():
            for id, name in school_data.items():
                self.db_connection.execute(
                    text(
                        """INSERT INTO Schools (school_id, school_name)
                        VALUES (:school_id, :school_name)
                        ON CONFLICT (school_id) DO NOTHING"""
                    ),
                    {"school_id": int(id), "school_name": name},
                )
                

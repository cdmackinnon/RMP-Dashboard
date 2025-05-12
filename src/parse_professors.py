import os
from bs4 import BeautifulSoup
import polars as pl
from pathlib import Path


def parse_professors_from_path(path: Path) -> pl.DataFrame:
    """
    Takes the path of an html file and parses it.
    Returns a polars dataframe from the parse_professors function.
    """
    html_content = path.read_text(encoding="utf-8")
    return parse_professors(html_content)


def parse_professors(html_content: str) -> pl.DataFrame:
    """
    Takes the html content of a page and parses it into a polars dataframe.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    # Initialize the column-wise lists for a faster polars dataframe
    names, departments, schools = [], [], []
    qualities, num_ratings, would_take_agains, difficulties = [], [], [], []

    for card in soup.find_all("div", class_="TeacherCard__CardInfo-syjs0d-1"):
        try:
            name = card.find("div", class_="CardName__StyledCardName-sc-1gyrgim-0")
            department = card.find("div", class_="CardSchool__Department-sc-19lmz2k-0")
            school = card.find("div", class_="CardSchool__School-sc-19lmz2k-1")
            quality = card.find_next(
                "div", class_="CardNumRating__CardNumRatingNumber-sc-17t4b9u-2"
            )
            num = card.find_next(
                "div", class_="CardNumRating__CardNumRatingCount-sc-17t4b9u-3"
            )
            again = card.find("div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2")
            diff = card.find_all(
                "div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2"
            )

            names.append(name.text if name else None)
            departments.append(department.text if department else None)
            schools.append(school.text if school else None)
            qualities.append(quality.text if quality else None)
            num_ratings.append(num.text.split()[0] if num else "0")
            # Some of the professors don't have a would take again percentage
            # They are marked as N/A and need to be converted to None
            if again:
                text = again.text.strip("%")
                would_take_agains.append(None if text == "N/A" else text)
            else:
                would_take_agains.append(None)
            difficulties.append(diff[1].text if len(diff) > 1 else None)

        except AttributeError:
            # TODO we can't just continue, but also we can't afford to not continue
            continue

    # Create Polars DataFrame
    return pl.DataFrame(
        {
            "Name": names,
            "Department": departments,
            "School": schools,
            "Quality": qualities,
            "# of Ratings": num_ratings,
            "Would Take Again (%)": would_take_agains,
            "Difficulty": difficulties,
        }
    )


def save_to_parquet(df, output_file):
    """
    Takes a polars dataframe and saves it to a parquet file.
    This allows for faster loading and saving of dataframes in smaller file sizes.
    """
    df.write_parquet(output_file)


def parse_all(file_path):
    """
    Takes the file path of the directory containing html files
    Parses all the files and saves them to parquet files.
    """
    # glob to get all the files in the directory
    files = [file.name for file in Path(file_path).iterdir()]
    for file in files:
        if file == ".DS_Store":
            continue

        df = parse_professors_from_path(Path(file_path) / file)
        save_to_parquet(df, Path("data", "dataframes", file + ".parquet"))

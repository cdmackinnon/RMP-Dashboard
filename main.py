from src.scraping import ProfessorScraper
from src.parse_professors import parse_all
import json


def main():
    # Test Scrape
    # test = ProfessorScraper()
    # url = "https://www.ratemyprofessors.com/search/professors/1095?q="
    # test.read_page_source(url, "University of Denver")

    # get_university_names()
    # parse_all("data/schools/new")


def get_university_names():
    NUM_UNIVERSITIES = 8000
    school_data = {}
    test = ProfessorScraper()

    for id in range(1, NUM_UNIVERSITIES):
        name = test.fetch_school_name(id)
        # Store only if a valid name is found
        if name and name != "other schools":
            school_data[id] = name

    # Save dictionary to JSON file
    with open("data/school_names.json", "w") as f:
        json.dump(school_data, f, indent=4)


if __name__ == "__main__":
    main()

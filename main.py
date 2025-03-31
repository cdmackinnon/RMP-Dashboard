from src.scraping import ProfessorScraper
import json

def main():
    NUM_UNIVERSITIES = 8000
    school_data = {}

    for id in range(1, NUM_UNIVERSITIES):
        name = test.fetch_school_name(id)
        # Store only if a valid name is found
        if name and name != "other schools":
            school_data[id] = name

    # Save dictionary to JSON file
    with open("data/school_data.json", "w") as f:
        json.dump(school_data, f, indent=4)


    # url = "https://www.ratemyprofessors.com/search/professors/{insert_school_id}?q="
    # Test scraping
    test = ProfessorScraper()
    id  = 5000
    school_name = test.fetch_school_name(id)
    test.read_page_source(f"https://www.ratemyprofessors.com/search/professors/{id}?q=*", school_name)
    test.quit()

    # Test parsing
    test.parse_professors(school_name)

if __name__ == "__main__":
    main()

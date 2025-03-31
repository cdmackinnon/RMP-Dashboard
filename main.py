from src.scraping import ProfessorScraper
import json

def main():
    # url = "https://www.ratemyprofessors.com/search/professors/{insert_school_id}?q="
    # Test scraping
    test = ProfessorScraper()
    i  = 5000
    school_name = test.fetch_school_name(i)
    test.read_page_source(f"https://www.ratemyprofessors.com/search/professors/{i}?q=*", school_name)
    test.quit()

    # Test parsing
    test.parse_professors(school_name)


if __name__ == "__main__":
    main()

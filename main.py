from src.scraping import ProfessorScraper
import json

def main():
    # url = "https://www.ratemyprofessors.com/search/professors/{insert_school_id}?q="

    test = ProfessorScraper()
    i  = 5000
    test.read_page_source(f"https://www.ratemyprofessors.com/search/professors/{i}?q=*", test.fetch_school_name(i))
    test.quit()


if __name__ == "__main__":
    main()

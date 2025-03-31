from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import Options
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


class ProfessorScraper:
    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def get_total_professors(self):
        """Extracts the total number of professors from the page."""
        try:
            header = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//h1[@data-testid='pagination-header-main-results']"))
            ).text
            return int(header.split()[0])
        except Exception as e:
            print(self.driver.page_source)
            print(f"Failed to extract total professors: {e}")
            return 0

    def load_all_professors(self, total_professors):
        """Clicks 'Show More' until all professors are loaded."""
        total_clicks = (total_professors + 7) // 8
        for _ in tqdm(range(total_clicks), desc="Loading professors"):
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Show More')]"))
                )
                button.click()
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'ProfessorCard')]"))
                )
            except Exception:
                break

    def read_page_source(self, url, output_file):
        """Main function to scrape professor data from a school page."""
        self.driver.get(url)
        total_professors = self.get_total_professors()
        print(f"Total professors: {total_professors}")
        self.load_all_professors(total_professors)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)

        print(f"Page source saved to {output_file}")
    
    def fetch_school_name(self, id) -> str:
        """
        Fetches a school's name from a given page. Takes a page id as an input.
        """
        url = f"https://www.ratemyprofessors.com/search/professors/{id}?q=*"
        try:
            self.driver.get(url)
        except:
            return None
        try:
            header = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//h1[@data-testid='pagination-header-main-results']"))
            )
            # The 3rd word and onwards are the college's name
            return ' '.join(header.text.split()[3:])
        except:
            return None

    def quit(self):
        """Closes the WebDriver."""
        self.driver.quit()

    @staticmethod
    def parse_professors(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")
        professors = []

        for card in soup.find_all("div", class_="TeacherCard__CardInfo-syjs0d-1"):
            try:
                name = card.find("div", class_="CardName__StyledCardName-sc-1gyrgim-0").text
                department = card.find("div", class_="CardSchool__Department-sc-19lmz2k-0").text
                school = card.find("div", class_="CardSchool__School-sc-19lmz2k-1").text
                quality = card.find_next("div", class_="CardNumRating__CardNumRatingNumber-sc-17t4b9u-2").text
                num_ratings = card.find_next("div", class_="CardNumRating__CardNumRatingCount-sc-17t4b9u-3").text.split()[0]
                would_take_again = card.find("div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2").text.strip('%')
                difficulty = card.find_all("div", class_="CardFeedback__CardFeedbackNumber-lq6nix-2")[1].text

                professors.append([name, department, school, quality, num_ratings, would_take_again, difficulty])
            except AttributeError:
                continue

        df = pd.DataFrame(professors, columns=["Name", "Department", "School", "Quality", "# of Ratings", "Would Take Again (%)", "Difficulty"])
        return df

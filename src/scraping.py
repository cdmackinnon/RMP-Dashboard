import json
from pathlib import Path
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.webdriver import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


class ProfessorScraper:
    """
    This class scrapes professor data from Rate My Professors using Selenium.
    It loads the page, clicks the "Show More" button to load all professors,
    extracts the total number of professors, and returns page source code.
    It also provides a method to fetch school names based on their IDs.
    """

    def __init__(self, headless=True):
        options = Options()
        if headless:
            options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=options)

    def get_total_professors(self) -> int:
        """
        Extracts the total number of professors from the page.
        """
        try:
            header = (
                WebDriverWait(self.driver, 15)
                .until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//h1[@data-testid='pagination-header-main-results']",
                        )
                    )
                )
                .get_attribute("textContent")
            )
            return int(header.split()[0])
        except Exception as e:
            print(self.driver.page_source)
            print(f"Failed to extract total professors: {e}")
            return 0

    def load_all_professors(self, total_professors: int) -> None:
        """
        Clicks the 'Show More' button on the webpage until all professors are loaded.
        Each button click loads 8 professors.
        The total number of clicks needed is calculated by dividing the total number of professors by 8.
        """
        # add 7 to the total professors to round up to the nearest multiple of 8
        total_clicks = (total_professors + 7) // 8
        for _ in tqdm(range(total_clicks), desc="Loading professors"):
            try:
                button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'Show More')]")
                    )
                )
                self.driver.execute_script("arguments[0].click();", button)
            except Exception:
                break

    def read_page_source(self, url: str, output_file: str = None) -> str:
        """
        Main function to scrape professor data from a school page.

        Input: URL of the school page and an optional output file name.
        Output: Returns the page source as a string.
        """
        self.driver.get(url)
        # Wait for the page to load and print how many professors the college has
        total_professors = self.get_total_professors()
        print(f"Total professors: {total_professors}")
        self.load_all_professors(total_professors)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                print(f"Page source saved to {output_file}")

        # Store the page source code and quit the driver
        page_source = self.driver.page_source
        self.quit()
        return page_source

    def fetch_school_name(self, id: str) -> str:
        """
        Fetches a school's name from a given webpage. Takes a page ID as an input.
        """
        url = f"https://www.ratemyprofessors.com/search/professors/{id}?q=*"
        try:
            self.driver.get(url)
            header = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//h1[@data-testid='pagination-header-main-results']")
                )
            )
            # The 3rd word onwards are the college's name
            return " ".join(header.text.split()[3:])
        # If the page doesn't load or contain the header then return None
        except (TimeoutException, WebDriverException):
            return None

    def fetch_all_school_names(self) -> None:
        """
        Fetches all school names and their IDs from Rate My Professors.
        Stores the data in a JSON file.

        Note:
        - Most school IDs are densely packed between 1 and 6000.
        - Beyond 6000, IDs become increasingly sparse, with the majority unused.
        - This function is not integrated in the app. The IDs are statically stored in a JSON file.
        """
        # Checking the first 8000 IDs for reasonable coverage
        NUM_UNIVERSITIES = 8000
        school_data = {}

        for id in range(1, NUM_UNIVERSITIES + 1):
            name = self.fetch_school_name(id)
            # Store only if a valid name is found
            # IDs not corresponding to a university will return None or "other schools"
            if name and name != "other schools":
                school_data[id] = name

        # Save dictionary to JSON file
        json_path = Path(__file__).parent.parent / "data/school_names.json"
        with open(json_path, "w") as f:
            json.dump(school_data, f, indent=4)

    def quit(self):
        """Closes the WebDriver."""
        self.driver.quit()

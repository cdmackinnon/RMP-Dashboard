# RateMyProfessors Dashboard

This project allows users to scrape and visualize professor ratings data from **RateMyProfessors** (RMP) for various universities. It uses **Flask** for the web app, **Selenium** for web scraping, **Plotly** for visualizations, **Polars** for data processing, and **PostgreSQL** for storing the data.

## Features

- **Scrape University Data**: Select a university and scrape professor data from RMP.
- **Store Data in PostgreSQL**: The data is stored in a PostgreSQL database for fast queries and adding additional information.
- **Data Visualization**: View department-wide ratings, difficulty, and other statistics through interactive charts.
- **Autocomplete Search**: Efficient search and selection through university names

## Installation

### Prerequisites

- Python 3.12.x
- PostgreSQL database
- ChromeDriver (or another WebDriver for Selenium)

### Quick Start

```bash
git clone https://github.com/cdmackinnon/RMP-Dashboard.git
cd RMP-Dashboard
uv run app.py
```

## Pages

### Index
<img src="/images/Index.jpeg" alt="Index Page" width="800"/>

### Individual University Departments
<img src="/images/Individual University Departments.jpeg" alt="Individual University Departments" width="800"/>

- View the metrics of each department at a single university.
- Filter by the number of reviews a department has.
- Select which metric to sort by (Quality, Difficulty, Percent of students who said they would retake the class)

### Compare University Departments
<img src="/images/Compare University Departments.jpeg" alt="Compare University Departments" width="800"/>

- Enter several universities to compare.
- View the metrics for a shared department. Filters departments by the ones existing at all the selected universities.
- Select which metric to sort by (Quality, Difficulty, Percent of students who said they would retake the class)
- Refresh to clear selections

### Download Additional Universities
<img src="/images/Download Additional Universities.jpeg" alt="Download Additional Universities" width="800"/>

1. **Select University**: The user enters a university name in the input field on the dashboard.
2. **Trigger Scrape**: Upon pressing submit, the app uses Selenium and the Chrome webdriver to scrape professor data from RateMyProfessor.
3. **Store Data**: The scraped data is then processed using Polars and inserted into a PostgreSQL database.
4. **Visualize**: Interactive data visualizations of professor ratings, quality, difficulty, etc., are shown on the dashboards using Plotly.

## Database

### Database Initialization
When the app is started with `uv run app.py`
1. The database and tables are automatically created if they do not already exist.
2. **Seeding**: The app seeds the database with the existing universities and ratings stored in Parquet files.

### Database Schema
The database consists of three main tables:
- **Schools**: Contains information about universities.
- **Departments**: Contains departments offered by the universities.
- **Instructors**: Contains the average metric ratings for each instructor and their total ratings



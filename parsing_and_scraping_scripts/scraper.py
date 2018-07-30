from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import requests
import shutil
import sys
import os

ARCHIVE_URL = "https://www.minneapolisfed.org/news-and-events/beige-book-archive"
WEBDRIVER_PATH = "./webdriver/chromedriver.exe"

SEARCH_BUTTON_XPATH = '//*[@id="bb_search"]/input'  # For easy access to XPATH
SELECT_ID = "bb_year"  # For easy access to the select ID
HTML_LINK_XPATH = "//a[@href]"  # For easy access to html XPATH

URL_IDENTIFIER = "https://www.minneapolisfed.org/news-and-events/beige-book-archive/"
CURRENT_YEAR = 2018  # Current year of scraping
MAX_YEAR = CURRENT_YEAR + 1
END_YEAR = 1970  # First year of archive

SCRAPING_DIRECTORY = "./scraped_files/"  # Save all htmls to here

PRINT_STATUS = False  # If true, prints out status messages as the program runs
# WARNING: Setting PRINT_STATUS to True uses up GIGABYTES of memory.


def main():
    """ Main call for all scraping. Returns nothing and no errors (should) be thrown. """
    err_print("Booting up web driver...")
    beige_books = webdriver.Chrome(WEBDRIVER_PATH)  # Webdriver loaded from folder in case PATH not configured
    err_print("Loading main archive page...", status=True)
    beige_books.get(ARCHIVE_URL)
    err_print("Loading XPATH and ID identifiers...", status=True)
    search_button = beige_books.find_element_by_xpath(SEARCH_BUTTON_XPATH)  # Easy button pressing
    selects = Select(beige_books.find_element_by_name(SELECT_ID)).options  # Grab all available options
    err_print("Selecting all possible years...\n", status=True)
    reports = []
    curr_year = CURRENT_YEAR

    while curr_year >= END_YEAR:  # While loop used because 'selects' change on every iteration and useful for indexing
        year = selects[index_from_year(curr_year)]  # Loads the year into memory
        err_print("Grabbing all reports for " + str(curr_year) + "...")
        year.click()
        search_button.click()
        links = beige_books.find_elements_by_xpath(HTML_LINK_XPATH)  # Grabs all hyperlinks

        for link in links:
            link_html = link.get_attribute("href")  # Converts Selenium object to string URLs
            if contains(URL_IDENTIFIER + str(curr_year), link_html) and link_html not in reports:  # Checks for dupes
                err_print("Grabbed " + link_html + "!")
                reports.append(link_html)

        err_print("Finished " + str(curr_year) + "!")
        curr_year -= 1  # Since the current year is the first item on the select, deincrement after every loop
        err_print("Refreshing parameters for " + str(curr_year) + "...\n")
        search_button = beige_books.find_element_by_xpath(SEARCH_BUTTON_XPATH)  # Refresh needed because site changed
        selects = Select(beige_books.find_element_by_name(SELECT_ID)).options

    err_print("Closing web driver...", status=True)
    beige_books.close()  # Exits out of the website
    err_print("Clearing old files...", status=True)
    delete_directory(SCRAPING_DIRECTORY)  # As not to accumulate too many files
    err_print("Saving reports to directory...", status=True)
    for report in reports:
        save(report)
    err_print("Scraping complete!", status=True)


def soupify(url):
    """ Helper function to convert a string URL to a bs4 object """
    raw_html = requests.get(url).content
    return bs(raw_html, 'html.parser')


def contains(pre_str, full_str):
    """ Using a function looks nicer than using the below code """
    return pre_str in full_str


def index_from_year(year):
    """ Converts a year to the specified index in the select """
    return -year + MAX_YEAR


def save(report_html):
    """ Helper function for saving a website into an actual html file """
    contents = soupify(report_html).prettify()
    name = report_html.split("/")[-1]
    err_print("Saving " + report_html + " as " + name + ".html...")
    new_file = open(SCRAPING_DIRECTORY + name + '.html', 'w', encoding="utf-8")
    new_file.write(contents)
    new_file.close()


def delete_directory(directory):
    """ Helper function to clear the scraping directory """
    try:
        shutil.rmtree(directory)
    except FileNotFoundError:
        err_print("Creating new directory...")
    finally:
        os.makedirs(directory)


def err_print(*args, status=PRINT_STATUS, **kwargs):
    """ Helper function for easy prints to std err """
    if status:
        try:
            print(*args, file=sys.stderr, **kwargs)
        except UnicodeEncodeError:
            print("Invalid unicode character", file=sys.stderr)

if __name__ == "__main__":  # Because this is good practice apparently
    main()

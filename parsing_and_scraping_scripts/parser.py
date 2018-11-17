from bs4 import BeautifulSoup as bs
import datascience as ds
#import pandas as pd
import sys
import os
import re

SCRAPING_DIRECTORY = "./scraped_files/"
TABLE_FILE_NAME = "beige_books.csv"

START_FLAGS = ["Beige Book Report: ", "Beige Book: "]  # List of flags to start parsing data
END_FLAGS = ["Latest Content from the Minneapolis Fed", "For more information about "]  # List of flags to stop parse

MAX_TOPIC_LENGTH = 50  # To delimit between text and topic
GLOBAL_ID = 15822  # Counter for section IDs

# The following gives us easy conversion from string month to numerical month
DATE_DICTIONARY = {"January": '1', "February": '2', "March": '3', "April": '4', "May": '5', "June": '6', "July": '7'}
DATE_DICTIONARY.update({"August": '8', "September": '9', "October": '10', "November": '11', "December": '12'})

PRINT_STATUS = False  # If true, prints out status messages as the program runs
# WARNING: Setting PRINT_STATUS to True uses up GIGABYTES of memory.


def main():
    """ Main call for all parsing. Returns nothing and no errors (should) be thrown. """
    err_print("Listing all files from scraping directory...", status=True)
    raw_files = os.listdir(SCRAPING_DIRECTORY)  # Lists all the files that were scraped
    err_print("Instantiating new data table...\n", status=True)
    final_table = new_table()  # Creates a new table to store data
    for w in raw_files:  # Reads the 'text content' of all the scraped files and parses them into the final table
        err_print("Extracting data from " + w + "...")
        site = load(w)
        final_table = parse(site, final_table)
    err_print("Saving the final table as .csv...", status=True)
    save(final_table)  # Saves the table into a CSV
    err_print("Parsing complete!", status=True)


def new_table():
    """
    Creates an empty table with the following columns: ID to enumerate all possible
    heading - text pairs, Date to store the date of every beige book published, District
    to store the name of the district, Sector Heading to give the associated text a
    broad topic description, and Sector Text to contain the actual text of interest.
    """
    new = ds.Table()
    new = new.with_column("ID", []).with_column("Date", []).with_column("District", [])
    new = new.with_column("Sector Heading", []).with_column("Sector Text", [])
    return new


def load(file_name):
    """
    Helper function to load an html file called 'file_name' into memory. This returns a
    'soupified' version of the html file that can be worked with through BS4.
    """
    file = open(SCRAPING_DIRECTORY + file_name, 'r', encoding="utf-8")  # Encoding to handle 'strange' characters
    file_contents = ""
    for line in file:
        file_contents += line
    file.close()
    website = bs(file_contents, 'html.parser')
    return website


def parse(site, table):
    """
    Where all of the magic / parsing happens. Takes a website and extracts all relevant
    information from the website and stores said information into a table.s

    :param site: 'Soupified' website
    :param table: Final output table that stores all data
    :return: The inputted table but mutated to include new data
    """
    global GLOBAL_ID  # Loads the unique IDs from Global frame to current frame

    # Instantiates empty fields for data of interest
    Date = ""
    District = ""
    Heading = ""
    Text = ""

    # Instantiates parsing flags for easy parsing control flow
    text_flag = False
    date_start = False
    first_topic = False
    pre_date = ""

    text = site.find_all(text=True)  # Extracts all non-html text from the website
    for t in text:
        # The following formats all text to remove extraneous whitespace
        filtered_text = re.sub('\s+', ' ', t).strip().replace("\n", " ")
        if filtered_text == "":  # Skip empty strings
            continue
        elif contains(filtered_text, START_FLAGS) and not text_flag:  # Start flag for data retrieval!
            District = filtered_text.split(":")[1].strip()
            date_start = True  # Next line should be the date
            if District == "National Summary":  # Ignore National Summaries for now until we fix all bugs
                date_start = False
                err_print("Ignoring Nation Summaries for now.")
        elif date_start:  # Extracts the date from the website
            if pre_date == "":
                try:
                    Date = numeric_date(filtered_text)
                    date_start = False
                    text_flag = True  # Next lines should be the textual data
                    first_topic = True  # Next line should be the first topic
                except KeyError:
                    pre_date = filtered_text
            else:  # Special Edge case for Minneapolis November 1st, 1995
                Date = numeric_date(pre_date + filtered_text)
                date_start = False
                text_flag = True
                first_topic = True
                pre_date = ""
        elif text_flag:
            if contains(filtered_text, END_FLAGS):  # End flag for data retrieval
                table = add_data(table, [str(GLOBAL_ID), Date, District, Heading, Text])  # Save final blobs
                GLOBAL_ID += 1  # Increment Global ID by one for next website pass through
                break
            elif len(filtered_text) > MAX_TOPIC_LENGTH and first_topic:
                Heading = "Summary of Economic Activity"  # Lack of topic means following text is a summary
                Text += filtered_text
                first_topic = False
            elif len(filtered_text) < MAX_TOPIC_LENGTH and first_topic:
                Heading = filtered_text  # Continue as normal
                first_topic = False
            elif len(filtered_text) < MAX_TOPIC_LENGTH and not first_topic:
                table = add_data(table, [str(GLOBAL_ID), Date, District, Heading, Text])  # Conclusion of a topic
                Text = ""
                Heading = filtered_text
                GLOBAL_ID += 1
            elif len(filtered_text) > MAX_TOPIC_LENGTH and not first_topic:  # Multi-paragraph text handling
                Text += filtered_text
    return table


def contains(string, str_arr):
    """ Helper function to check is a certain string is a flag """
    for s in str_arr:
        if s in string:
            return True
    return False


def numeric_date(date_str):
    """ Helper function to convert string date to numeric date """
    final_date = ""
    date = date_str.split(" ")
    final_date += DATE_DICTIONARY[date[0]] + "-"
    final_date += date[1][:-1] + "-"
    final_date += date[2]
    return final_date


def add_data(table, row):
    """ Helper function to add data to table """
    err_print("ID: " + row[0])
    err_print("Date: " + row[1])
    err_print("District: " + row[2])
    err_print("Heading: " + row[3])
    err_print("Text: " + row[4])
    table = table.with_row(row)
    return table


def save(table):
    """
    Saves new table into a .csv file with all data collected for future use.
    """
    if os.path.isfile(TABLE_FILE_NAME):
        os.remove(TABLE_FILE_NAME)
    table.to_csv(TABLE_FILE_NAME)


def err_print(*args, status=PRINT_STATUS, **kwargs):
    """ Helper function for easy prints to std err """
    if status:
        try:
            print(*args, file=sys.stderr, **kwargs)
        except UnicodeEncodeError:
            print("Invalid unicode character", file=sys.stderr)

if __name__ == "__main__":  # Because this is good practice apparently
    main()

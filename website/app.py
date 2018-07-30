#!/usr/bin/env python

import flask
from flask import request, send_file

import sqlite3
import csv

import datascience
import numpy

# Create the application.
app = flask.Flask(__name__)
app.static_folder = 'static'


@app.route('/')
def index():
    return flask.render_template('index.html')


@app.route('/index.html')
def index2():
    return index()


@app.route('/about.html')
def about():
    return flask.render_template('about.html')


@app.route('/analysis.html')
def analysis():
    return flask.render_template('analysis.html')


@app.route('/team.html')
def team():
    return flask.render_template('team.html')


@app.route('/code.html')
def code():
    return flask.render_template('code.html')


#Things to show: Date, Distctict, Sector Heading, Sector Text, First Keyword
@app.route('/query.html')
def query():
    format_ = request.args.get("format", None)
    keyword = request.args.get("name", "")
    year = request.args.get("year", "")

    connection = sqlite3.connect("beigedb.sqlite")
    connection.row_factory = dictionary_factory
    cursor = connection.cursor()

    # Query that gets the records that match the query
    all_records_query = "SELECT Date as date, District as district,\
                        Heading as heading, Text as text,\
                        First as first FROM BeigeDB %s %s;"

    where_clause = ""
    if keyword or year:
        where_clause = "WHERE "
        if keyword:
            where_clause += " first = ? " if keyword else ""
        if year and keyword:
            where_clause += " and "
        if year:
            where_clause += " date like ? " if len(year) > 2 else ""
    limit_statement = "limit 8" if format_ != "csv" else ""

    all_records_query = all_records_query % (where_clause, limit_statement)

    if keyword and year:
        cursor.execute(all_records_query, (keyword.lower(), "%" + year))
    elif keyword:
        cursor.execute(all_records_query, (keyword.lower(),))
    elif year:
        cursor.execute(all_records_query, ("%" + year,))
    else:
        cursor.execute(all_records_query)
    records = cursor.fetchall()

    # Query to count the number of records
    count_query = "SELECT count(*) as count FROM BeigeDB %s;"
    count_query = count_query % where_clause
    if keyword and year:
        cursor.execute(count_query, (keyword.lower(), "%" + year))
    elif year:
        cursor.execute(count_query, ("%" + year,))
    elif keyword:
        cursor.execute(count_query, (keyword.lower(),))
    else:
        cursor.execute(count_query)
    # There's a lot of if else going on here but I will send a better solution for you guys to work with
    no_of_records = cursor.fetchall()
    connection.close()

    # Send the information back to the view
    # if the user specified csv send the data as a file for download else visualize the data on the web page
    if format_ == "csv":
        return download_csv(keyword, year)
    else:
        years = [x for x in range(2018, 1969, -1)]
        selected_year = int(year) if year else None
        return flask.render_template('query.html', records=records, no_of_records=no_of_records[0]['count'],
                                     keyword=keyword, years=years, selected_year=selected_year)


########################################################################
# The following are helper functions. They do not have a @app.route decorator
########################################################################
def dictionary_factory(cursor, row):
    """
    This function converts what we get back from the database to a dictionary
    """
    d = {}
    for index, col in enumerate(cursor.description):
        d[col[0]] = row[index]
    return d


def download_csv(keyword, year):
    """
    Pass into this function, the data dictionary and the name of the file and it will create the csv file and send it to the view
    """
    filename = "beige_db.csv"

    beige_table = datascience.Table().read_table("beigedb.csv")

    if year:
        beige_table = beige_table.where("Date", lambda x: year in x)
    if keyword:
        beige_table = beige_table.where("First", keyword.lower())

    header = beige_table.labels

    f = open(filename, "w+", encoding='utf8')

    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    writer.writerow(header)

    for i in range(beige_table.num_rows):
        new_row = list(beige_table.row(i))

        writer.writerow(new_row)

    # Push the file to the view
    return send_file(filename,
                     mimetype='text/csv',
                     attachment_filename=filename,
                     as_attachment=True)


if __name__ == '__main__':
    app.debug = True
    app.run()

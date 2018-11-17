import pandas as pd
import numpy as np
import warnings

#dropping empty sector texts
print('Starting Cleaning Process...')
beige_books = pd.read_csv('./beige_books.csv')
empty_records = beige_books[beige_books['Sector Text'].isna()]['Date']
print('Number of faulty texts to drop: ', len(empty_records))
beige_books = beige_books.dropna(axis=0,subset=['Sector Text'])

# Checking Sector heading
strange_headings_ids = beige_books[beige_books.apply(lambda s: len(s) < 5 and s != "Coal" and s != "Fuel", axis=1)]['ID']
print('Number of faulty sector headings to drop: ', len(strange_headings_ids))
beige_books = beige_books[~beige_books['ID'].isin(strange_headings_ids)]

# Checking dates
beige_books['Date'] = pd.to_datetime(beige_books['Date'], errors='coerce')
bad_dates_ids = beige_books[beige_books['Date'].isna()]['ID']
beige_books = beige_books[~beige_books['ID'].isin(bad_dates_ids)]

print('Done Cleaning!')
beige_books.to_csv('./cleaned_bbd.csv', index = False)

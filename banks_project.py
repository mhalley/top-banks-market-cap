# Code for ETL operations on Country-GDP data

# Importing the required libraries
from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime

url = 'https://web.archive.org/web/20230908091635/https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attribs = ["Name", "MC_USD_Billion"]
csv_path = 'exchange_rate.csv'
output_path = './Largest_banks_data.csv'
db_name = 'Banks.db'
table_name = 'Largest_banks'

def log_progress(message):
    ''' This function logs the mentioned message of a given stage of the
    code execution to a log file. Function returns nothing'''
    timestamp_format = '%Y-%h-%d-%H:%M:%S' # Year-Monthname-Day-Hour-Minute-Second 
    now = datetime.now() # get current timestamp 
    timestamp = now.strftime(timestamp_format) 
    with open("./code_log.txt","a") as f: 
        f.write(timestamp + ' : ' + message + '\n')

def extract(url, table_attribs):
    ''' This function aims to extract the required
    information from the website and save it to a data frame. The
    function returns the data frame for further processing. '''
    page = requests.get(url).text
    data = BeautifulSoup(page,'html.parser')
    df = pd.DataFrame(columns = table_attribs)
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')
    for row in rows:
        if row.find('td') is not None:
            col = row.find_all('td')
            data_dict = {"Name" : col[1].find_all('a')[1]['title'],
                        "MC_USD_Billion" : float(col[2].contents[0][:-1])}
            df1 = pd.DataFrame(data_dict, index=[0])
            df = pd.concat([df,df1], ignore_index=True)
    return df

def transform(df, csv_path):
    ''' This function accesses the CSV file for exchange rate
    information, and adds three columns to the data frame, each
    containing the transformed version of Market Cap column to
    respective currencies'''
    # Read exchange rates from CSV file
    exchange_rate_df = pd.read_csv(csv_path)
    
    # Convert the exchange rates DataFrame to a dictionary using the specified syntax
    exchange_rate = exchange_rate_df.set_index('Currency').to_dict()['Rate']
    
    # Add new columns to the dataframe converting Market Cap from USD to GBP, EUR, and INR
    df['MC_GBP_Billion'] = [np.round(x * exchange_rate['GBP'], 2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x * exchange_rate['EUR'], 2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x * exchange_rate['INR'], 2) for x in df['MC_USD_Billion']]
    
    return df

def load_to_csv(df, output_path):
    ''' This function saves the final data frame as a CSV file in
    the provided path. Function returns nothing.'''
    df.to_csv(output_path)

def load_to_db(df, sql_connection, table_name):
    ''' This function saves the final data frame to a database
    table with the provided name. Function returns nothing.'''
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    ''' This function runs the query on the database table and
    prints the output on the terminal. Function returns nothing. '''
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

''' Here, you define the required entities and call the relevant
functions in the correct order to complete the project. Note that this
portion is not inside any function.'''

# Log the initialization of the ETL process 
log_progress("Preliminaries complete. Initiating ETL process") 

df = extract(url, table_attribs)

# Log the completion of the Extraction process 
log_progress("Data extraction complete. Initiating Transformation process") 
 
df = transform(df, csv_path)
print(df)
print(df['MC_EUR_Billion'][4])

# Log the completion of the Transformation process 
log_progress("Data transformation complete. Initiating Loading process") 

load_to_csv(df, output_path)

# Log saved to CSV 
log_progress("Data saved to CSV file") 

sql_connection = sqlite3.connect(db_name)

# Log connected to database 
log_progress("SQL Connection initiated") 

load_to_db(df, sql_connection, table_name)

# Log loaded data to database 
log_progress("Data loaded to Database as a table, Executing queries")

query_statement = f"SELECT * from {table_name}"
run_query(query_statement, sql_connection)

query_statement = f"SELECT AVG(MC_GBP_Billion) from {table_name}"
run_query(query_statement, sql_connection)

query_statement = f"SELECT Name from {table_name}  LIMIT 5"
run_query(query_statement, sql_connection)

# Log completion of running queries
log_progress("Process Complete")

sql_connection.close()

# Log disconnect from server
log_progress("Server Connection closed")

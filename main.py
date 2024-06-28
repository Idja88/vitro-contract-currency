import json
import os
import urllib
from datetime import datetime, timedelta
import openpyxl
import pandas as pd
import requests
import sqlalchemy as sa


def connect_to_db(connection_string):
    connection_uri = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
    engine = sa.create_engine(connection_uri, fast_executemany=True, echo=True)
    return engine

def main(rates, currencies, connection_string):
    end_date = datetime.now()
    begin_date = end_date - timedelta(days=0)
    end_date_str = end_date.strftime('%d.%m.%Y')
    begin_date_str = begin_date.strftime('%d.%m.%Y')

    url = 'https://nationalbank.kz/ru/exchangerates/ezhednevnye-oficialnye-rynochnye-kursy-valyut/excel'
    params = {
        'beginDate': begin_date_str,
        'endDate': end_date_str,
        'rates[]': rates
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        filename = 'exchange_rates.xlsx'
        file_path = f'C:\\Windows\\Temp\\{filename}'
        
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print(f'File saved as {file_path}')

        df = pd.read_excel(file_path, engine='openpyxl')
        df_melted = df.melt(id_vars=['Date'], value_vars=currencies, var_name='CurrencyCode', value_name='CurrencyValue')
        df_melted.columns = ['DATE', 'CurrencyCode', 'CurrencyValue']
        df_melted['DATE'] = pd.to_datetime(df_melted['DATE'], infer_datetime_format=True)

        try:
            engine = connect_to_db(connection_string)
            df_melted.to_sql('currency_history', engine, if_exists='append', index=False)
            print("Data has been inserted successfully.")
        finally:
            engine.raw_connection().close()
            
    else:
        print(f'Failed to download file. Status code: {response.status_code}')

if __name__ == "__main__":
    config_path = os.path.join(os.getcwd(), 'config.json')
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        connection_string = config['connection_string']
        currencies = list(config['currency_code'].keys())
        rates = list(config['currency_code'].values())
    main(rates=rates, currencies=currencies, connection_string=connection_string)
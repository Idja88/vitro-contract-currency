import json
import os
import urllib
from datetime import datetime, timedelta
import pandas as pd
import requests
import sqlalchemy as sa
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_exchange_rates(rates, begin_date):
    end_date = datetime.now()
    end_date_str = end_date.strftime('%d.%m.%Y')
    if begin_date == "":
        begin_date = end_date - timedelta(days=0)
        begin_date_str = begin_date.strftime('%d.%m.%Y')
    else: 
        begin_date_str = begin_date
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
    return file_path

def transform_data(file_path, currencies):
    df = pd.read_excel(file_path, engine='openpyxl')
    for currency in currencies:
        quant_column = f"{currency}_quant"
        df[currency] = df[currency] / df[quant_column]
    df_melted = df.melt(id_vars=['Date'], value_vars=currencies, var_name='CurrencyCode', value_name='CurrencyValue')
    df_melted.columns = ['DATE', 'CurrencyCode', 'CurrencyValue']
    df_melted['DATE'] = pd.to_datetime(df_melted['DATE'], format='%d.%m.%Y', errors='coerce')
    return df_melted

def connect_to_db(connection_string):
    connection_uri = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}"
    engine = sa.create_engine(connection_uri, fast_executemany=True, echo=False)
    return engine

def load_data(df, connection_string):
    try:
        engine = connect_to_db(connection_string)
        with engine.connect() as connection:
            df.to_sql('currency_history', connection, if_exists='append', index=False)
            print("Data has been inserted successfully.")
    finally:
        engine.dispose()

def send_email(subject, message, from_email, to_emails, smtp_server, smtp_port):
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        for to_email in to_emails:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))
            server.send_message(msg)
    except Exception as e:
        print("Error sending email:", str(e))
    finally:
        server.quit()

def main(rates, currencies, connection_string, begin_date):
    file_path = get_exchange_rates(rates=rates, begin_date=begin_date)
    transformed_df = transform_data(file_path=file_path, currencies=currencies)
    load_data(transformed_df, connection_string=connection_string)

if __name__ == "__main__":
    config_path = os.path.join(os.getcwd(), 'config.json')
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        begin_date = config['begin_date']
        currencies = list(config['currency_code'].keys())
        rates = list(config['currency_code'].values())
        connection_string = config['connection_string']
        from_email = config['mail_message']['from_email']
        to_emails = config['mail_message']['to_emails']
        smtp_server = config['mail_message']['smtp_server']
        smtp_port = config['mail_message']['smtp_port']

    try:
        main(rates=rates, currencies=currencies, connection_string=connection_string, begin_date=begin_date)
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        send_email("Error in ETL process", error_message, from_email, to_emails, smtp_server, smtp_port)
        raise SystemExit(1)
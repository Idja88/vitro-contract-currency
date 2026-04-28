import json
import os
from datetime import datetime, timedelta
import pandas as pd
import requests
import sqlalchemy as sa
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DateValidationError(Exception):
    pass

class DateLogicError(Exception):
    pass

def validate_date(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, '%d.%m.%Y')
        return True
    except ValueError:
         raise DateValidationError(f"Invalid date format: {date_string}")

def get_exchange_rates(url: str, temp_path: str, rates: list, begin_date: str, end_date: str) -> str:
    if end_date == "":
        end_date = datetime.now()
        end_date_str = end_date.strftime('%d.%m.%Y')
    elif validate_date(end_date) == True:
        end_date_str = end_date

    if begin_date == "":
        begin_date = end_date - timedelta(days=0)
        begin_date_str = begin_date.strftime('%d.%m.%Y')
    elif validate_date(begin_date) == True:
        begin_date_str = begin_date

    if begin_date > end_date:
        raise DateLogicError(f"{begin_date} cannot be later than {end_date}.")

    params = {
        'beginDate': begin_date_str,
        'endDate': end_date_str,
        'rates[]': rates
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        filename = 'exchange_rates.xlsx'
        file_path = os.path.join(temp_path, filename)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        return file_path
    else:
        raise requests.exceptions.HTTPError(f"Failed to download file. Status code: {response.status_code}")

def transform_data(file_path: str, currencies: list) -> pd.DataFrame:
    df = pd.read_excel(file_path, engine='openpyxl')
    for currency in currencies:
        quant_column = f"{currency}_quant"
        df[currency] = df[currency] / df[quant_column]
    df_melted = df.melt(id_vars=['Date'], value_vars=currencies, var_name='currency_code', value_name='currency_value')
    df_melted.columns = ['date', 'currency_code', 'currency_value']
    df_melted['date'] = pd.to_datetime(df_melted['date'], format='%d.%m.%Y', errors='coerce')
    return df_melted

def connect_to_db(connection_string: str) -> sa.engine.base.Engine:
    parts = {}
    for param in connection_string.split(';'):
        if '=' in param:
            key, value = param.split('=', 1)
            parts[key.strip()] = value.strip().strip('{}')
    
    driver = parts.get('Driver') or parts.get('DRIVER')
    host = parts.get('Server') or parts.get('SERVER')
    port = parts.get('Port') or parts.get('PORT')
    database = parts.get('Database') or parts.get('DATABASE')
    user = parts.get('Uid') or parts.get('UID')
    password = parts.get('Pwd') or parts.get('PWD')
        
    # Определяем тип БД на основе driver в строке подключения
    if "postgresql" in driver.lower():
        connection_url = sa.URL.create(
            drivername="postgresql+psycopg2",
            username=user,
            password=password,
            host=host,
            port=port if port else 5432,
            database=database
        )
        engine = sa.create_engine(connection_url)
        
    elif "sql server" in driver.lower():
        connection_url = sa.URL.create(
            drivername="mssql+pyodbc",
            username=user,
            password=password,
            host=host,
            port=port if port else 1433,
            database=database,
            query={"driver": driver}
        )
        engine = sa.create_engine(connection_url, fast_executemany=True)
    
    else:
        raise ValueError(f"Unknown database driver: {driver}")
    
    return engine

def load_data(df: pd.DataFrame, connection_string: str, table_name: str, table_schema: str):
    try:
        engine = connect_to_db(connection_string)
        with engine.connect() as connection:
            df.to_sql(name=table_name, con=connection, schema=table_schema, if_exists='append', index=False)
            print("Data has been inserted successfully.")
    finally:
        engine.dispose()

def send_email(
        subject: str,
        message: str,
        from_email: str,
        to_emails: list,
        smtp_server: str,
        smtp_port: int,
        smtp_login: str,
        smtp_password: str
) -> None:
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_login, smtp_password)
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

def main(
    url: str,
    temp_path: str,
    table_name: str,
    table_schema: str,
    rates: list,
    currencies: list,
    connection_string: str,
    begin_date: str,
    end_date: str
) -> None:
    file_path = get_exchange_rates(url=url, temp_path=temp_path, rates=rates, begin_date=begin_date, end_date=end_date)
    transformed_df = transform_data(file_path=file_path, currencies=currencies)
    load_data(df=transformed_df, connection_string=connection_string, table_name=table_name, table_schema=table_schema)

if __name__ == "__main__":
    config_path = os.path.join(os.getcwd(), 'config.json')
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
        url = config['url']
        temp_path = config['temp_path']
        table_name = config['table_name'] if config['table_name'] else "currency_history"
        table_schema = config['table_schema'] if config['table_schema'] else None
        begin_date = config['begin_date']
        end_date = config['end_date']
        currencies = list(config['currency_code'].keys())
        rates = list(config['currency_code'].values())
        connection_string = config['connection_string']
        from_email = config['mail_message']['from_email']
        to_emails = config['mail_message']['to_emails']
        smtp_server = config['mail_message']['smtp_server']
        smtp_port = config['mail_message']['smtp_port']
        smtp_login = config['mail_message']['smtp_login']
        smtp_password = config['mail_message']['smtp_password']

    try:
        main(
        url=url,
        temp_path=temp_path,
        table_name=table_name,
        table_schema=table_schema,
        rates=rates,
        currencies=currencies,
        connection_string=connection_string,
        begin_date=begin_date,
        end_date=end_date
        )
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        send_email("Error in ETL process", error_message, from_email, to_emails, smtp_server, smtp_port, smtp_login, smtp_password)
        raise SystemExit(1)
import pandas as pd
import datetime
import os
from sqlalchemy import create_engine
from garminconnect import Garmin

def get_cockroachdb_conn():

    os.system('curl --create-dirs -o ~/.postgresql/root.crt -O https://cockroachlabs.cloud/clusters/b41c3959-f129-4644-acbf-06ec2ac22b22/cert')

    # Init connection to CockroachDB
    connection_string = os.environ.get('cockroachdb')
    connection_string = connection_string.replace('database_name', 'garmin')

    engine = create_engine(connection_string)
    conn = engine.connect()
    return engine, conn 

def get_garmin_api():
    api = Garmin('hugo.le-moine@outlook.fr', os.environ.get("garmin-password"))
    api.login()
    return api

def get_latest_data_point(conn, table):
    date_latest_point = conn.execute(
        f"""
        SELECT *
        FROM {table}
        ORDER BY date DESC
        LIMIT 1
        """
    ).fetchone()
    
    if date_latest_point:
        return date_latest_point[0]
    return []
        
def create_list_missing_dates(conn, table):
    
    date_latest_point = get_latest_data_point(conn, table)
    
    if not date_latest_point:
        date_latest_point = datetime.date(2022, 8, 26) # First day of Garmin Venu 2 Plus watch
    elif type(date_latest_point) != datetime.date:
        date_latest_point = date_latest_point.date()
            
    dates = pd.date_range(
        start=date_latest_point + datetime.timedelta(days=1), # day after latest point
        end=datetime.datetime.today().date() - datetime.timedelta(days=1), # day before today
        freq='d'
    )
    return dates

def collect_stress_data(garmin_api, conn):
    missing_dates = create_list_missing_dates(conn, 'stress')
    if not missing_dates.empty:
        df = pd.concat([
            pd.DataFrame(garmin_api.get_stress_data(date.date())['stressValuesArray'], columns=['date', 'stress'])
            for date in missing_dates
        ])
        
        df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
        df['stress'] = df.stress.astype(int)
        df = df.sort_values(by='date')

        df.to_sql(
            'stress',
            conn,
            if_exists='append',
            index=False
        )
        print(f'Stress data: {len(missing_dates)} new days added.')
    else:
        print('Stress data: already up to date!')

def collect_hydration_data(garmin_api, conn):
    missing_dates = create_list_missing_dates(conn, 'hydration')
    if not missing_dates.empty:
        df = pd.DataFrame([
            garmin_api.get_hydration_data(date.date())
            for date in missing_dates
        ])
        
        df = df[['calendarDate', 'valueInML', 'goalInML', 'sweatLossInML']]
        df.columns = ['date', 'value_in_ml', 'goal_in_ml', 'sweat_loss_in_ml']
        df.to_sql(
            'hydration',
            conn,
            if_exists='append',
            index=False
        )
        print(f'Hydration data: {len(missing_dates)} new days added.')
    else:
        print('Hydration data: already up to date!')

def collect_all(event, context):
    # Get cockroachdb
    engine, conn = get_cockroachdb_conn()    

    # Log to garmin API
    garmin_api = get_garmin_api()

    # Run collectors
    collect_stress_data(garmin_api, conn)
    collect_hydration_data(garmin_api, conn)

    # close connection
    conn.close()
    engine.dispose()
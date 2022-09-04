import pandas as pd
import datetime
from sqlalchemy import create_engine

from prefect import flow, task, get_run_logger
from prefect.blocks.system import Secret

from garminconnect import (
    Garmin,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
    GarminConnectAuthenticationError,
)

@task
def get_garmin_api():
    api = Garmin(Secret.load("garmin-login").get(), Secret.load("garmin-password").get())
    api.login()
    return api

@task
def get_latest_data_point(conn, table):
    return conn.execute(
        f"""
        SELECT *
        FROM {table}
        ORDER BY date DESC
        LIMIT 1
        """
    ).fetchone()

@task
def get_list_missing_dates(date_latest_point):
    try:
        if type(date_latest_point) != datetime.date:
            date_latest_point = date_latest_point.date()
    except:
        date_latest_point = datetime.date(2022, 8, 26) # First day of Garmin Venu 2 Plus watch
    dates = pd.date_range(
        start=date_latest_point + datetime.timedelta(days=1), # day after latest point
        end=datetime.datetime.today().date() - datetime.timedelta(days=1), # day before today
        freq='d'
    )
    return dates

@flow
def collect_stress_data(garmin_api, conn):
    date_latest_point = get_latest_data_point(conn, 'stress')[0]
    missing_dates = get_list_missing_dates(date_latest_point)
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
        get_run_logger().info(f'Stress data: {len(missing_dates)} new days added.')
    else:
        get_run_logger().info('Stress data: already up to date!')

@flow
def collect_hydration_data(garmin_api, conn):
    date_latest_point = get_latest_data_point(conn, 'hydration')[0]
    missing_dates = get_list_missing_dates(date_latest_point)
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
        get_run_logger().info(f'Hydration data: {len(missing_dates)} new days added.')
    else:
        get_run_logger().info('Stress data: already up to date!')


@flow(
    name="garmin-flow",
    description="Collect all garmin data: sress, hydration etc.",
)
def collect_all():
    # Init connection to CockroachDB
    connection_string = Secret.load('cockroachdb').get()
    connection_string = connection_string.replace('database_name', 'garmin')

    engine = create_engine(connection_string)
    conn = engine.connect()

    # Log to garmin API
    garmin_api = get_garmin_api()

    # Run collectors
    collect_stress_data(garmin_api, conn)
    collect_hydration_data(garmin_api, conn)

if __name__ == "__main__":
    collect_all()
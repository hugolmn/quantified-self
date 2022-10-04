import os

from sqlalchemy import create_engine
from garminconnect import Garmin

from garmin_collectors import *

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

def collect_all(event, context):
    # Get cockroachdb
    engine, conn = get_cockroachdb_conn()    

    # Log to garmin API
    garmin_api = get_garmin_api()

    # Run collectors
    StatsCollector(garmin_api, conn).insert_new_data()
    StepsCollector(garmin_api, conn).insert_new_data()
    HeartRateCollector(garmin_api, conn).insert_new_data()
    StressCollector(garmin_api, conn).insert_new_data()
    HydrationCollector(garmin_api, conn).insert_new_data()
    SleepCollector(garmin_api, conn).insert_new_data()

    # close connection
    conn.close()
    engine.dispose()
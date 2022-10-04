from abc import ABC, abstractclassmethod
import datetime
import pandas as pd

class GarminCollector(ABC):

    def __init__(self, garmin_api, conn, table):
        self.garmin_api = garmin_api
        self.conn = conn
        self.table = table

    @staticmethod
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

    def create_list_missing_dates(self):
        date_latest_point = self.get_latest_data_point(self.conn, self.table)
        
        if (not date_latest_point):
            date_latest_point = datetime.date(2022, 8, 26) # First day of Garmin Venu 2 Plus watch
        elif type(date_latest_point) != datetime.date:
            date_latest_point = date_latest_point.date()
        
        if date_latest_point < datetime.date(2022, 8, 26):
            date_latest_point = datetime.date(2022, 8, 26)

        dates = pd.date_range(
            start=date_latest_point + datetime.timedelta(days=1), # day after latest point
            end=datetime.datetime.today().date() - datetime.timedelta(days=3), # 3 days before today
            freq='d'
        )
        return dates

    def insert_new_data(self):
        missing_dates = self.create_list_missing_dates()
        if not missing_dates.empty:
            df = self.collect_data(missing_dates)
            df.to_sql(
                self.table,
                self.conn,
                if_exists='append',
                index=False
            )
            print(f'{self.table}: {len(missing_dates)} new days added.')
        else:
            print(f'{self.table}: already up to date!')

    @abstractclassmethod
    def collect_data(self, missing_dates):
        pass


class StatsCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'stats')

    def collect_data(self, dates):
        df = pd.DataFrame.from_dict([
            self.garmin_api.get_stats(date)
            for date in dates
        ])

        df = df[[
            # Date
            'calendarDate',
            # Calories
            'totalKilocalories', 'activeKilocalories', 'bmrKilocalories',
            # Steps
            'totalSteps', 'totalDistanceMeters',
            # Activity level
            'highlyActiveSeconds', 'activeSeconds', 'sedentarySeconds', 'sleepingSeconds',
            # Intense minutes
            'moderateIntensityMinutes', 'vigorousIntensityMinutes',
            # Elevation
            'floorsAscendedInMeters', 'floorsDescendedInMeters',
            # HR
            'minHeartRate', 'maxHeartRate', 'restingHeartRate', 'lastSevenDaysAvgRestingHeartRate',
            # Stress
            'averageStressLevel', 'maxStressLevel', 'stressDuration', 'restStressDuration', 'activityStressDuration',
            'uncategorizedStressDuration', 'totalStressDuration', 'lowStressDuration', 'mediumStressDuration', 'highStressDuration',
            # Awake / Asleep
            'measurableAwakeDuration', 'measurableAsleepDuration',
            # Body battery
            'bodyBatteryChargedValue', 'bodyBatteryDrainedValue', 'bodyBatteryHighestValue', 'bodyBatteryLowestValue',
            # SPO2
            'averageSpo2', 'lowestSpo2',
            # Breathing
            'avgWakingRespirationValue', 'highestRespirationValue',
        ]]
        
        df = df.rename(columns={'calendarDate': 'date'})
        df = df.assign(date=pd.to_datetime(df['date']).dt.date)

        # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
        df.columns = df.columns.str.replace(r'(?<!^)(?=[A-Z])', '_', regex=True).str.lower()
        
        df = pd.concat([
            df['date'],
            df.iloc[:, 1:].fillna(0).astype(int)
        ], axis=1)
        df = df.sort_values('date')
        return df


class StepsCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'steps')

    def collect_data(self, dates):
        df = pd.concat([
            pd.DataFrame(self.garmin_api.get_steps_data(date.date()))
            for date in dates
        ])
        
        df = df[['startGMT', 'steps', 'primaryActivityLevel']]
        df.columns = ['date', 'steps', 'activity_level']

        df['date'] = pd.to_datetime(df.date, utc=True).dt.tz_convert('Europe/Paris')

        df = df.assign(steps=df.steps.astype(int).fillna(0))
        df = df.sort_values(by='date')
        return df


class HeartRateCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'heart_rate')

    def collect_data(self, dates):
        df = pd.concat([
            pd.DataFrame(
                self.garmin_api.get_heart_rates(date.date())['heartRateValues'],
                columns=['date', 'hr']
            )
            for date in dates
        ])
        
        df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
        df['hr'] = df.hr.fillna(-1).astype(int)
        df = df.sort_values(by='date')
        return df


class StressCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'stress')

    def collect_data(self, dates):
        df = pd.concat([
            pd.DataFrame(
                self.garmin_api.get_stress_data(date.date())['stressValuesArray'],
                columns=['date', 'stress']
            )
            for date in dates
        ])
        
        df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
        df['stress'] = df.stress.astype(int)
        df = df.sort_values(by='date')
        return df


class HydrationCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'hydration')

    def collect_data(self, dates):
        df = pd.DataFrame([
            self.garmin_api.get_hydration_data(date.date())
            for date in dates
        ])
        
        df = df[['calendarDate', 'valueInML', 'goalInML', 'sweatLossInML']]
        df.columns = ['date', 'value_in_ml', 'goal_in_ml', 'sweat_loss_in_ml']
        return df

class SleepCollector(GarminCollector):

    def __init__(self, garmin_api, conn):
        super().__init__(garmin_api, conn, 'sleep')

    def collect_data(self, dates):
        df = pd.DataFrame([
            self.garmin_api.get_sleep_data(date.date())['dailySleepDTO']
            for date in dates
        ])
        
        df = df[[
            'calendarDate',
            'sleepStartTimestampGMT',
            'sleepEndTimestampGMT',
            'sleepTimeSeconds',
            'deepSleepSeconds',
            'lightSleepSeconds',
            'remSleepSeconds',
            'awakeSleepSeconds',
            'averageSpO2Value',
            'lowestSpO2Value',
            'highestSpO2Value',
            'averageSpO2HRSleep',
            'averageRespirationValue',
            'lowestRespirationValue',
            'highestRespirationValue',
            'awakeCount',
            'avgSleepStress',
        ]]

        df.columns = [
            'date',
            'sleep_start',
            'sleep_end',
            'sleep_time_seconds',
            'deep_sleep_seconds',
            'light_sleep_seconds',
            'rem_sleep_seconds',
            'awake_sleep_seconds',
            'average_spo2',
            'lowest_spo2',
            'highest_spo2',
            'average_hr_sleep',
            'average_respiration',
            'lowest_respiration',
            'highest_respiration',
            'awake_count',
            'avg_sleep_stress',
        ]

        df['date'] = pd.to_datetime(df['date'], unit='ms', utc=True).dt.tz_convert('Europe/Paris')
        return df

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import io
import zipfile
from utils import find_file_id, download_file, load_gsheet


def load_car_data() -> pd.DataFrame:
    vehicle_df_list = []
    for vehicle in ["vehicle-1", "vehicle-2"]:
        file_id = find_file_id(f"name contains '{vehicle}'")[0]["id"]

        # Download zip archive from google drive
        zip_archive = download_file(file_id)
        # Create zipfile object using zipfile library for zip file handling
        zipfile_object = zipfile.ZipFile(zip_archive)
        # Open first file found in zip archive
        csv = zipfile_object.read(zipfile_object.filelist[0])

        df = pd.read_csv(io.StringIO(csv.decode("utf-8")), skiprows=4)
        df = df.loc[: df[df.Data.str.startswith("## CostCategories")].index[0] - 1]
        df = df[["Data", "Odo (km)", "Fuel (litres)", "Full"]]
        df.columns = ["Date", "Odo", "Fuel", "Full"]

        df = df.assign(
            Date=pd.to_datetime(df.Date),
            Odo=df.Odo.astype(float),
            Fuel=df.Fuel.astype(float),
            Full=df.Full.astype("category"),
        )
        df = df.sort_values("Date")
        df = df.assign(Distance=df["Odo"].astype(float).diff())
        df = df.reset_index(drop=True)

        df["Fuel Level"] = np.where(df.Full == "1", 50, df.Fuel)
        df["Fuel Burn"] = df.Fuel - (df["Fuel Level"] - df["Fuel Level"].shift())

        df["Efficiency"] = df["Fuel Burn"] / (
            df.Distance / 100
        )  # Fuel consumption per 100km
        df["Carbon_Footprint"] = (
            df["Fuel Burn"] * 2.28 / 2
        )  # One liter of gasoline yields 2.28kg of CO2, divided by 2 for load factor

        df = df.iloc[1:]  # Dropping first row: initial fuel level

        vehicle_df_list.append(df)

    vehicle_df = pd.concat(vehicle_df_list)
    return vehicle_df


def load_transport(transport_name: str) -> pd.DataFrame:
    if transport_name == "Car":
        df = load_car_data()
    else:
        file_id = find_file_id(f"name contains '{transport_name}'")[0]["id"]
        df = load_gsheet(file_id, transport_name)

    df = df[["Date", "Distance", "Carbon_Footprint"]]
    df = df.assign(
        Date=pd.to_datetime(df.Date),
        Distance=df.Distance.astype(float).round(),
        Carbon_Footprint=df.Carbon_Footprint.astype(float).round(),
    )
    return df.assign(Transport=transport_name)


car = load_transport("Car")
train = load_transport("Train")
plane = load_transport("Plane")

df = pd.concat([car, train, plane])
df = df[df.Date < pd.Timestamp.now()]

chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("year(Date):T", title="Year"),
        y=alt.Y("sum(Carbon_Footprint):Q", title="Carbon Footprint (kg CO2)"),
        color=alt.Color("Transport:N"),
    )
)

st.title("Carbon Footprint")

st.altair_chart(chart, use_container_width=True, theme="streamlit")

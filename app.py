import os
import time
import streamlit as st
import influxdb_client
from influxdb_client import InfluxDBClient
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("INFLUXDB_TOKEN")
org = "eafit"
url = "https://influx.dis.eafit.edu.co"

query = """
from(bucket: "influxdb")
  |> range(start: -10m, stop: now())
  |> filter(fn: (r) => r["device"] == "esp32_dv")
  |> filter(fn: (r) => r["_field"] == "si1145_ir" or r["_field"] == "si1145_uv" or r["_field"] == "si1145_vis")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> keep(columns: ["_time", "si1145_ir", "si1145_uv", "si1145_vis"]) 
"""

client = InfluxDBClient(url=url, token=token, org=org, debug=False)


def load_data(query):
    df = client.query_api().query_data_frame(query)
    df = df.drop(columns=["result", "table"])
    df = df.rename(
        columns={
            "_time": "Time",
            "si1145_ir": "IR",
            "si1145_uv": "UV",
            "si1145_vis": "Visible",
        }
    )
    df["Time"] = pd.to_datetime(df["Time"], utc=True)
    df["Time"] = df["Time"].dt.tz_convert("America/Bogota")
    df = df.set_index("Time")
    return df


num_data_slider = st.sidebar.slider("Select the range of data", 0, 100, 10)
data_load_state = st.text("Loading data...")
start = time.time()
df = load_data(query)
total = time.time() - start
df = df.tail(num_data_slider)
data_load_state.text(f"Loading data...done in {total:.2f} seconds.")

st.title("SI1145 Sensor Data")
if st.checkbox("Show raw data"):
    st.subheader("Raw data")
    st.write(df)

selected_vars = st.sidebar.multiselect(
    "Select variables", df.columns, default=list(df.columns)
)

st.subheader("Graph")
st.line_chart(df[selected_vars])

st.subheader("Plotly Graph")
fig = px.line(df, x=df.index, y=selected_vars, title="SI1145 Sensor Data")
st.plotly_chart(fig)

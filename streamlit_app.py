import streamlit as st
from streamlit_folium import folium_static

from pycaret.classification import *

from folium.plugins import HeatMapWithTime
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import folium

import numpy as np
import pandas as pd

from PIL import Image


@st.cache
def load_data():
    df = pd.read_csv("data/aus_clean_data.csv")
    return df


@st.cache
def load_map_data():
    df = pd.read_csv("data/aus_clean_map_data.csv")
    return df


def get_corr_heatmap(df):
    corr = df.corr()
    mask = np.triu(np.ones_like(corr, dtype=bool))
    f, ax = plt.subplots(figsize=(11, 9))
    cmap = sns.diverging_palette(230, 20, as_cmap=True)
    sns.heatmap(corr,
                mask=mask,
                cmap=cmap,
                vmax=.3,
                center=0,
                square=True,
                linewidths=.5,
                cbar_kws={"shrink": .5})
    return plt


def get_max_temp_bar_chart(df):
    loc_max_temp = df[["Location", "MaxTemp"]].groupby("Location").mean()
    loc_max_temp.sort_values(by="MaxTemp", inplace=True)
    labels = {"MaxTemp": "Maximum Temperature °C", "Location": "Location Names"}
    fig = px.bar(loc_max_temp,
                 labels=labels,
                 color_discrete_sequence=["lightcoral"])
    return fig


def get_min_temp_bar_chart(df):
    loc_min_temp = df[["Location", "MinTemp"]].groupby("Location").mean()
    loc_min_temp.sort_values(by="MinTemp", inplace=True)
    labels = {"MinTemp": "Minumum Temperature °C", "Location": "Location Names"}
    fig = px.bar(loc_min_temp,
                 labels=labels,
                 color_discrete_sequence=["lightslategray"])
    return fig


def get_rain_bar_chart(df):
    loc_rain = df[["Location", "Rainfall"]].groupby("Location").mean()
    loc_rain.sort_values(by="Rainfall", inplace=True)
    labels = {"Rainfall": "Amount of Rainfall", "Location": "Location Names"}
    fig = px.bar(loc_rain, labels=labels, color_discrete_sequence=["skyblue"])
    return fig


def get_weather_map(map_data):
    date = map_data["Date"]
    date_choice = st.selectbox("Select date:", date)
    date_df = map_data.loc[map_data.Date == date_choice]
    cols = ["MinTemp", "MaxTemp", "Rainfall", "Evaporation", "Sunshine", "WindGustSpeed",
            "WindSpeed9am", "Humidity9am", "Pressure9am", "Cloud9am", "Temp9am"]
    col_option = st.multiselect("Select Features", cols, cols[0])
    aus_plot = folium.Map(location=[-28.0, 135],
                          control_scale=True,
                          zoom_start=4.3,
                          tiles="CartoDB positron")
    for i in range(0, len(date_df)):
        tool_tip = ""
        if "MinTemp" in col_option:
            tool_tip += f"MinTemp: {date_df.iloc[i]['MinTemp']}<br/>"
        if "MaxTemp" in col_option:
            tool_tip += f"MaxTemp: {date_df.iloc[i]['MaxTemp']}<br/>"
        if "Rainfall" in col_option:
            tool_tip += f"Rainfall: {date_df.iloc[i]['Rainfall']}<br/>"
        if "Evaporation" in col_option:
            tool_tip += f"Evaporation: {date_df.iloc[i]['Evaporation']}<br/>"
        if "Sunshine" in col_option:
            tool_tip += f"Sunshine: {date_df.iloc[i]['Sunshine']}<br/>"
        if "WindGustSpeed" in col_option:
            tool_tip += f"WindGustSpeed: {date_df.iloc[i]['WindGustSpeed']}<br/>"
        if "WindSpeed9am" in col_option:
            tool_tip += f"WindSpeed9am: {date_df.iloc[i]['WindSpeed9am']}<br/>"
        if "Humidity9am" in col_option:
            tool_tip += f"Humidity9am: {date_df.iloc[i]['Humidity9am']}<br/>"
        if "Pressure9am" in col_option:
            tool_tip += f"Pressure9am: {date_df.iloc[i]['Pressure9am']}<br/>"
        if "Cloud9am" in col_option:
            tool_tip += f"Cloud9am: {date_df.iloc[i]['Cloud9am']}<br/>"
        if "Temp9am" in col_option:
            tool_tip += f"Temp9am: {date_df.iloc[i]['Temp9am']}<br/>"
        # "MinTemp: " + str(date_df.iloc[i]["MinTemp"]) +
        #             "<br/> MaxTemp: " + str(date_df.iloc[i]["MaxTemp"])
        folium.Marker(
            location=[date_df.iloc[i]["lat"], date_df.iloc[i]["lng"]],
            tooltip=tool_tip,
            icon=folium.Icon(color="blue",
                             prefix="fa fas fa-cloud")).add_to(aus_plot)
    return aus_plot


def get_rainfall_timeseries_map(map_df):
    dfmap = map_df[['Date', 'lat', 'lng', 'Rainfall']]
    df_day_list = []

    for day in dfmap["Date"].sort_values().unique():
        data = dfmap.loc[
            dfmap["Date"] == day,
            ['Date', 'lat', 'lng', 'Rainfall']].groupby(
            ['lat', 'lng']).sum().reset_index().values.tolist()
        df_day_list.append(data)

    ts_rain_map = folium.Map([-28.0, 135],
                             zoom_start=4.3,
                             tiles='CartoDB positron')
    HeatMapWithTime(df_day_list,
                    index=list(dfmap["Date"].sort_values().unique()),
                    auto_play=False,
                    radius=10,
                    gradient={
                        0.2: 'lightskyblue',
                        0.4: 'skyblue',
                        0.6: 'steelblue',
                        1.0: 'darkcyan'
                    },
                    min_opacity=0.5,
                    max_opacity=0.8,
                    use_local_extrema=True).add_to(ts_rain_map)
    return ts_rain_map


def get_predictions():
    saved_model = load_model('rf_model')
    st.write("## Predict Rainfall")
    st.write("Predictions Based on Trained Random Forest Classifer Model")
    input_cols = ['Location_cat', 'MinTemp', 'MaxTemp', 'Rainfall',
                  'Evaporation', 'Sunshine', 'WindGustDir_cat',
                  'WindGustSpeed', 'Humidity9am', 'Humidity3pm',
                  'Pressure9am', 'Pressure3pm', 'Cloud9am', 'Cloud3pm',
                  'Temp9am', 'Temp3pm', 'RainToday_cat']
    # input_data = [[3, 13, 22, 0.6, 5.4, 7.6, 13, 44, 70, 22,
    #                1007.2, 1007.1, 8.0, 21.8, 16.2, 21.7, 0]]
    Location_cat = st.text_input("Location_cat", 3)
    MinTemp = st.text_input("MinTemp", 13)
    MaxTemp = st.text_input("MaxTemp", 22)
    Rainfall = st.text_input("Rainfall", 0.6)
    Evaporation = st.text_input("Evaporation", 5.4)
    Sunshine = st.text_input("Sunshine", 7.6)
    WindGustDir_cat = st.text_input("WindGustDir_cat", 13)
    WindGustSpeed = st.text_input("WindGustSpeed", 44)
    Humidity9am = st.text_input("Humidity9am", 70)
    Humidity3pm = st.text_input("Humidity3pm", 22)
    Pressure9am = st.text_input("Pressure9am", 1007)
    Pressure3pm = st.text_input("Pressure3pm", 1007)
    Cloud9am = st.text_input("Cloud9am", 8.0)
    Cloud3pm = st.text_input("Cloud3pm", 21.5)
    Temp9am = st.text_input("Temp9am", 16.5)
    Temp3pm = st.text_input("Temp3pm", 21.0)
    RainToday_cat = st.text_input("RainToday_cat", 0)
    input_data = [[Location_cat, MinTemp, MaxTemp, Rainfall, Evaporation, Sunshine,
                   WindGustDir_cat, WindGustSpeed, Humidity9am, Humidity3pm,
                   Pressure9am, Pressure3pm, Cloud9am, Cloud3pm, Temp9am, Temp3pm,
                   RainToday_cat]]
    input_df = pd.DataFrame(input_data, columns=input_cols)
    st.write(input_df)
    predictions = predict_model(saved_model, data=input_df)
    rain_tomorrow = int(predictions["Label"])
    return rain_tomorrow


# Main
st.title("Australia Rain Prediction")
image = Image.open("data/aus_climate.jpg")
placeholder = st.image(image)

data = load_data()
map_data = load_map_data()

st.sidebar.header("Dataset:")
if st.sidebar.checkbox("Show Data"):
    placeholder.empty()
    st.write("## Dataset:")
    st.write(data.head())
if st.sidebar.checkbox("Show Feature Correlations"):
    placeholder.empty()
    st.write("## Features Correlation:")
    st.pyplot(get_corr_heatmap(data))
st.sidebar.header("Features:")
if st.sidebar.checkbox("Show Max Tempreature"):
    placeholder.empty()
    st.write("## Cities with High Tempreature:")
    st.plotly_chart(get_max_temp_bar_chart(data))
if st.sidebar.checkbox("Show Min Tempreature"):
    placeholder.empty()
    st.write("## Cities with Minimum Tempreature:")
    st.plotly_chart(get_min_temp_bar_chart(data))
if st.sidebar.checkbox("Show Rainfall"):
    placeholder.empty()
    st.write("## Cities with Rainfall:")
    st.plotly_chart(get_rain_bar_chart(data))
st.sidebar.header("Maps:")
if st.sidebar.checkbox("Show Temp Map"):
    placeholder.empty()
    st.write("## Cities Map with Weather Markers:")
    aus_plot = get_weather_map(map_data)
    folium_static(aus_plot)
if st.sidebar.checkbox("Show Rainfall Timeseries Map"):
    placeholder.empty()
    st.write("## Rainfall Timeseries:")
    timeseries_plot = get_rainfall_timeseries_map(map_data)
    folium_static(timeseries_plot)
st.sidebar.header("Rainfall Prediction:")
if st.sidebar.checkbox("Predict"):
    placeholder.empty()
    rain_tomorrow = get_predictions()
    if int(rain_tomorrow) == 0:
        st.write("## It will not rain tomorrow!")
    else:
        st.write("## It will rain tomorrow!")

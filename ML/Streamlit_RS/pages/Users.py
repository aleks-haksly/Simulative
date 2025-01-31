import streamlit as st
from helpers.functions import *

#---Constants---------
LOGO_PATH_2 = "static/hiclipart.com_2.png"
USER_NAMES_PATH = "datasets/user_names.csv"
#---Logo----------------
st.logo(
    LOGO_PATH_2,
    icon_image=LOGO_PATH_2
)

#---Loading data---------
loading_data = st.text("Loading datasets...")
user_names_df = get_csv_data(USER_NAMES_PATH)
loading_data.text("")

#---Page header---------
col1, col2 = st.columns([1, 8])
with col1:
    st.image(LOGO_PATH_2, width=100)
with col2:
    st.title("Movie ratings analytics")


st.dataframe(user_names_df)
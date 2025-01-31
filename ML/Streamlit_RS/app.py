import streamlit as st
import pandas as pd
import numpy as np

@st.cache_data
def get_user_data_df():
    return pd.read_csv("./datasets/user_data.csv", compression='gzip', index_col='userId')
@st.cache_data
def get_movies_df():
    return pd.read_csv("./datasets/movies_df.csv", compression='gzip')
@st.cache_data
def get_ratings_df():
    return pd.read_csv("./datasets/ratings_df.csv", compression='gzip')


ratings_df = get_ratings_df()
user_data_df = get_user_data_df()
movies_df = get_movies_df()

st.write(user_data_df)
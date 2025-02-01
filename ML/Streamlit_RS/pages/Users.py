from random import randint
import streamlit as st
from helpers.functions import get_csv_data

# ---Constants---------
LOGO_PATH_2 = "static/hiclipart.com_2.png"
USER_NAMES_PATH = "datasets/user_names.csv"
USER_DATA_DF_PATH = "./datasets/user_data.csv"
# ---Logo----------------
st.logo(LOGO_PATH_2, icon_image=LOGO_PATH_2)

# ---Loading data---------
loading_data = st.text("Loading datasets...")
user_names_df = get_csv_data(USER_NAMES_PATH, index_col="Unnamed: 0")
user_data_df = get_csv_data(USER_DATA_DF_PATH)
loading_data.text("")
if "UserId" not in st.session_state:
    st.session_state["UserId"] = randint(1, 1200)

userId = st.session_state["UserId"]

# ---Page header---------
col1, col2, col3, col4 = st.columns([1, 5, 2, 2,])
with col1:
    st.image(LOGO_PATH_2, width=100)
with col2:
    st.markdown(
        f"""<H2>{user_names_df.iloc[st.session_state['UserId']].user_name}</H1><b>Last seen:</b>
                {user_data_df.get('last_seen').iloc[userId][:-3]}""",
        unsafe_allow_html=True,
    )
# ---Indictors----------------------------
col3.metric(
    "Movies watched",
    f"{user_data_df.get('movies_watched').iloc[userId]: ,}",
    f"""{user_data_df.get('movies_watched').iloc[userId] -
         user_data_df.get('previous_watched').iloc[userId]: .0f} to prev. mo""",
    border=False,
)
col4.metric(
    "User ranking",
    f"{user_data_df.get('current_rank').iloc[userId]: .0f}",
    f"""{user_data_df.get('current_rank').iloc[userId] -
         user_data_df.get('previous_rank').iloc[userId]: .0f} to prev. mo""",
    delta_color="inverse",
)
# col5.metric("User mean rating", f"{user_data_df.get("mean_rating").iloc[userId]: .0f}")


st.dataframe(user_data_df)

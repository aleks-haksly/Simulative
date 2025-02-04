import pandas as pd
import streamlit as st
from random import randint
from helpers.cls import CustomTransformer
from helpers.functions import (
    get_csv_data, get_image, get_recommended_movies,
    get_user_last_movies, model_load
)

# --- Constants ---
RATINGS_DF_PATH = "./datasets/ratings_df.csv"
MOVIES_DF_PATH = "./datasets/movies_df.csv"
AVATAR_PATH = "https://i.pravatar.cc/100"
USER_NAMES_PATH = "datasets/user_names.csv"
USER_DATA_DF_PATH = "./datasets/user_data.csv"
USER_DATA_DF_PATH_JSON = "./datasets/user_data.json"
MODEL_PATH = "./model/best_model.pkl.gz"

# --- Load Datasets ---
loading_datasets = st.text("Loading datasets...")
ratings_df = get_csv_data(RATINGS_DF_PATH)
movies_df = get_csv_data(MOVIES_DF_PATH)
user_names_df = get_csv_data(USER_NAMES_PATH, index_col="Unnamed: 0")
user_data_df = pd.read_json(USER_DATA_DF_PATH_JSON, compression='gzip')


loading_datasets.text("")


# --- User Session Handling ---
def update_user_id():
    """Updates the UserId in session state and resets avatar."""
    st.session_state["UserId"] = st.session_state["new_user_id"]
    st.session_state.pop("avatar", None)


# Initialize session state variables
if "UserId" not in st.session_state:
    st.session_state["UserId"] = randint(1, 1199)
if "avatar" not in st.session_state:
    st.session_state["avatar"] = get_image(AVATAR_PATH)

userId = st.session_state["UserId"]
avatar = st.session_state["avatar"]


rating_distribution = user_data_df.loc[userId, "rating_distribution"]
rating_df = pd.DataFrame.from_dict(rating_distribution, orient="index").reset_index()
rating_df.rename(columns={"index": "rating", 0: "values"}, inplace=True)


# --- Sidebar (User Selection) ---
with st.sidebar:
    st.markdown(f"**User name:** {user_names_df.iloc[userId].user_name}")

    # User ID input
    col1, col2 = st.columns([1, 8])
    with col1:
        st.markdown('<div style="padding-top: 6px;"><b>ID:</b></div>', unsafe_allow_html=True)
    with col2:
        st.number_input(
            "UserId", min_value=1, max_value=1200,
            value=userId, step=1,
            label_visibility="collapsed",
            key="new_user_id", on_change=update_user_id
        )

    # Random user button
    if st.button("Random user"):
        st.session_state.pop("UserId", None)
        st.session_state.pop("avatar", None)
        st.rerun()

# --- User Profile Header ---
col1, col2, col3, col4 = st.columns([1, 5, 2, 2])
with col1:
    st.image(avatar, width=100)
with col2:
    last_seen = pd.to_datetime(user_data_df.loc[userId, "last_seen"], unit="ms").strftime("%Y-%m-%d %H:%M")
    st.markdown(f"<H2>{user_names_df.iloc[userId].user_name}</H2><b>Last seen:</b> {last_seen}", unsafe_allow_html=True)

# --- User Metrics ---
col3.metric(
    "Movies watched",
    f"{user_data_df.loc[userId, 'movies_watched']: ,}",
    f"{user_data_df.loc[userId, 'movies_watched'] - user_data_df.loc[userId, 'previous_watched']: .0f} vs prev mth",
    border=False,
)
col4.metric(
    "User ranking",
    f"{user_data_df.loc[userId, 'current_rank']: .0f}",
    f"{user_data_df.loc[userId, 'current_rank'] - user_data_df.loc[userId, 'previous_rank']: .0f} vs prev mth",
    delta_color="inverse",
    help="Rank by movies watched number",
)

# --- Recommended Movies ---
loading_recommended = st.text("Loading recommended movies...")
model = model_load(MODEL_PATH)
recommended_movies = get_recommended_movies(userId, ratings_df, movies_df, model, limit=5)
loading_recommended.text("")

TITLE_HEIGHT, GENRES_HEIGHT, RATING_HEIGHT = 100, 80, 20
st.markdown("### Recommended Movies", help='Recommendation made with XGBoost model')
cols = st.columns(len(recommended_movies))
for col, (_, row) in zip(cols, recommended_movies.iterrows()):
    with col:
        st.image(row["urls"], width=150)
        st.markdown(
            f'<div style="height:{TITLE_HEIGHT}px; text-align: center; font-weight: bold;">{row["title"]}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div style="height:{GENRES_HEIGHT}px; text-align: center; font-style: italic;">{", ".join(row["genres"].split("|")[:3])}</div>',
            unsafe_allow_html=True)
        st.markdown(f'<div style="height:{RATING_HEIGHT}px; text-align: center;">⭐ {row["predicted_rating"]}</div>',
                    unsafe_allow_html=True)

# --- Watched Movies ---
loading_last_movies = st.text("Loading last watched movies...")
user_last_movies = get_user_last_movies(userId, ratings_df, movies_df, model, limit=5)
loading_last_movies.text("")


col1, col2 = st.columns([2, 3])
with col1:
    st.markdown("### Prefered genres")
    st.data_editor(
        pd.DataFrame.from_dict(user_data_df.loc[userId, "Top 3 genres"], orient='index'),
        column_config={
            "0": st.column_config.ProgressColumn(
                "Prefered genres",
                help="User's 3 prefered genres",
                format="%.1f",
                min_value=0,
                max_value=5,
            ),
        },
        hide_index=False, )
with col2:
    st.markdown("### User ratings distribution")
    st.bar_chart(
        rating_df,
        x="rating", y="values",
        height=220, y_label="Ratings count", x_label="Movie Rating",
        color="#FDB462",
    )


st.markdown("### Last Watched Movies")
st.data_editor(
    user_last_movies,
    column_config={
        "Title": st.column_config.TextColumn(),
        "Cover": st.column_config.ImageColumn(),
        "User/Movie rating": st.column_config.TextColumn(label="Rating", help="User rating/Movie mean rating",
                                                         width="small"),
        "Genres": st.column_config.TextColumn(width="medium"),
    },
    use_container_width=True,
    hide_index=True,
)








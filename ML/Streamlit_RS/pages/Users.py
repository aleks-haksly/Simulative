from random import randint
import ast
import streamlit as st
from helpers.functions import get_csv_data, model_load, get_user_last_movies, get_image, get_recommended_movies
from Dashboard import ratings_df, movies_df
import pandas as pd
from helpers.cls import CustomTransformer

# ---Constants---------
AVATAR_PATH = "https://i.pravatar.cc/100"
USER_NAMES_PATH = "datasets/user_names.csv"
USER_DATA_DF_PATH = "./datasets/user_data.csv"
MODEL_PATH = "./model/best_model.pkl.gz"
# ---Logo----------------
#st.logo(LOGO_PATH_2, icon_image=LOGO_PATH_2)

# ---Loading data---------
loading_data = st.text("Loading datasets...")
user_names_df = get_csv_data(USER_NAMES_PATH, index_col="Unnamed: 0")
user_data_df = get_csv_data(USER_DATA_DF_PATH)
loading_data.text("")

if "UserId" not in st.session_state:
    st.session_state["UserId"] = randint(1, 1200)
userId = st.session_state["UserId"]

if "avatar" not in st.session_state:
    st.session_state["avatar"] = get_image(AVATAR_PATH)
avatar = st.session_state["avatar"]

# ---Sidebar-----------------------------
with st.sidebar:
    st.markdown(f"""**User name:** {user_names_df.iloc[st.session_state['UserId']].user_name}<br>**ID:** {st.session_state['UserId']}""",
                unsafe_allow_html=True)

# ---Page header---------
col1, col2, col3, col4 = st.columns([1, 5, 2, 2,])
with col1:
    st.image(avatar, width=100)
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
         user_data_df.get('previous_watched').iloc[userId]: .0f} vs prev mth""",
    border=False,
)
col4.metric(
    "User ranking",
    f"{user_data_df.get('current_rank').iloc[userId]: .0f}",
    f"""{user_data_df.get('current_rank').iloc[userId] -
         user_data_df.get('previous_rank').iloc[userId]: .0f} vs prev mth""",
    delta_color="inverse",
    help="Rank by movies watched number"
)

# ---Watched movies-------------------------
loading_model = st.text("Loading model...")
model = model_load(MODEL_PATH)
loading_model.text(f"Loading {user_names_df.iloc[st.session_state['UserId']].user_name} last watched movies...")
user_last_movies = get_user_last_movies(userId=st.session_state['UserId'], ratings=ratings_df, movies=movies_df, _model=model, limit=5)
loading_model.text("")

st.markdown(f"### Last watched movies")
st.data_editor(
    user_last_movies,
    column_config={
        "Title": st.column_config.TextColumn(),
        "Cover": st.column_config.ImageColumn(),
        "User/Movie rating": st.column_config.TextColumn(label="Rating", help="User rating/Movie mean rating", width='small'),
        "Genres": st.column_config.TextColumn(width="medium")
    },
    use_container_width=True,
    hide_index=True,
)

st.bar_chart(
    pd.DataFrame.from_dict(ast.literal_eval(user_data_df
                                            .iloc[st.session_state['UserId']]
                                            .get("rating_distribution")),
                           orient='index')
                .reset_index()\
                .rename({"index": "rating", 0:"values"}, axis=1),
    x="rating",
    y="values",
    height=280,
    y_label="Ratings count",
    x_label="Movie Rating",
    color="#FDB462",)

recommended_movies_loading = st.text(f"Loading {user_names_df.iloc[st.session_state['UserId']].user_name} recommended movies...")
recommended_movies = get_recommended_movies(userId=st.session_state['UserId'], ratings=ratings_df, movies=movies_df, _model=model, limit=5)
recommended_movies_loading.text("")


TITLE_HEIGHT = 100
GENRES_HEIGHT = 80
RATING_HEIGHT = 20

cols = st.columns(len(recommended_movies))
for col, (_, row) in zip(cols, recommended_movies.iterrows()):
    with col:
        st.image(row["urls"], width=150 )

        # Use Markdown with CSS for fixed height
        st.markdown(
            f'<div style="height:{TITLE_HEIGHT}px; text-align: center; font-weight: bold;">{row["title"]}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="height:{GENRES_HEIGHT}px; text-align: center; font-style: italic;">{", ".join(row["genres"].split("|"))}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="height:{RATING_HEIGHT}px; text-align: center;">⭐ {row["predicted_rating"]}</div>',
            unsafe_allow_html=True,
        )




#model_load.clear()
#st.cache_data.clear()

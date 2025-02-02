import streamlit as st
from helpers.functions import (get_csv_data, get_movies_statistics,
                               get_top_movies, pie_chart, preserve_sorting_df,
                               user_activity_hist)

# ---Constants---------
RATINGS_DF_PATH = "./datasets/ratings_df.csv"
MOVIES_DF_PATH = "./datasets/movies_df.csv"
LOGO_PATH = "static/hiclipart.com.png"
WATCH_LIMIT=50
# ---Logo----------------
st.logo(LOGO_PATH, link="https://streamlit.io/gallery", icon_image=LOGO_PATH)

# ---Page header---------
col1, col2 = st.columns([1, 8])
with col1:
    st.image(LOGO_PATH, width=100)
with col2:
    st.title("Movies ratings analytics")

# ---Loading data---------
loading_data = st.text("Loading datasets...")
ratings_df = get_csv_data(RATINGS_DF_PATH)

movies_df = get_csv_data(MOVIES_DF_PATH) # index_col="movieId")

# ---Calculating movies statistics---------
loading_data.text("Calculating statistics...")
movies_statistics = get_movies_statistics(movies_df, ratings_df)
loading_data.text("")

# ---Indictors----------------------------
col1, col2, col3 = st.columns(3)
col1.metric("Movies count", f"{movies_statistics.get('movies_count'): ,}")
col2.metric(
    "Active users",
    f"{movies_statistics.get('users_ratings').get('now').loc['nunique'].values[0]: ,}",
    f"{movies_statistics.get('users_ratings').get('delta_previous_month').loc['nunique'].values[0]: ,} vs prev mth",
)

col3.metric(
    "User rating count",
    f"{movies_statistics.get('users_ratings').get('now').loc['count'].values[0]: ,}",
    f"{movies_statistics.get('users_ratings').get('delta_previous_month').loc['count'].values[0]: ,} vs prev mth",
)

# ---Bar Charts ---------------------
with st.container():
    col3, col4 = st.columns([1, 1])
    with col3:
        st.markdown("### Movies watched by genre")
        st.bar_chart(
            preserve_sorting_df(movies_statistics.get("watching_counts"), cat_column="genre"),
            x="genre",
            y="count",
            height=320,
            y_label="Movies count",
            x_label="Genre",
            color="#BC80BD",
        )

    with col4:
        st.markdown("### Movies count by genre")
        st.plotly_chart(
            pie_chart(movies_statistics.get("genres_count"), category="genre", value="count"),
            use_container_width=True,
        )

with st.container():
    col5, col6 = st.columns([1, 1])
    with col5:
        st.markdown("### Movies ratings distribution")
        st.bar_chart(
            movies_statistics.get("movies_ratings_distribution"),
            x="rating",
            y="count",
            height=280,
            y_label="Rating count",
            x_label="Movie Rating",
            color="#FDB462",
        )
    with col6:
        st.markdown("### Users activity distribution")
        st.plotly_chart(
            user_activity_hist(movies_statistics.get("user_activity")), use_container_width=True
        )

loading_data = st.text("Loading top movies...")
top_movies_df = get_top_movies(movies_df, ratings_df, n_top=10, watch_limit=WATCH_LIMIT)
# top_movies_df = top_movies_df.style.set_properties(**{'line-height': '100px'})
loading_data.text("")

st.markdown(f"### Top-{top_movies_df.shape[0]} movies by mean rating",
            help=f"Movies with at least {WATCH_LIMIT} ratings")
st.data_editor(
    top_movies_df,
    column_config={
        "Cover": st.column_config.ImageColumn(),
        "Mean rating": st.column_config.NumberColumn(format="%.2f"),
    },
    use_container_width=True,
    hide_index=True,
)

# st.cache_data.clear()
# st.json(user_data_df)
#st.cache_data.clear()
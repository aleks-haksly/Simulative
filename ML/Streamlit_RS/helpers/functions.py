import gzip
from io import BytesIO
from time import sleep

import joblib
import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent
from requests import Session
from sklearn.preprocessing import MultiLabelBinarizer


@st.cache_data
def get_csv_data(filepath_or_buffer, compression="gzip", index_col=None):
    return pd.read_csv(filepath_or_buffer, compression="gzip", index_col=index_col)


@st.cache_data
def get_movies_statistics(movies, ratings):
    movies = movies.copy()
    movies.set_index(movies.movieId, inplace=True)
    result = dict()
    result["movies_count"] = movies.shape[0]
    result["movies_ratings_distribution"] = ratings.rating.value_counts().reset_index()

    mlb_genres = MultiLabelBinarizer()
    mlb_genres.fit(movies.genres.apply(lambda x: x.split("|")))
    result["genres_count"] = (
        pd.DataFrame(
            mlb_genres.transform(movies.genres.apply(lambda x: x.split("|"))),
            columns=mlb_genres.classes_,
            index=movies.index,
        )
        .sum()
        .reset_index()
        .rename({"index": "genre", 0: "count"}, axis=1)
        .sort_values(by="count", ascending=False)
    )

    user_activity = ratings["userId"].value_counts()
    result["user_activity"] = user_activity[user_activity <= 1000]
    genres = ratings.movieId.map(movies.genres)
    genres = pd.DataFrame(
        mlb_genres.transform(genres.apply(lambda x: x.split("|"))),
        columns=mlb_genres.classes_,
        index=genres.index,
    )
    result["watching_counts"] = (
        genres.sum()
        .reset_index()
        .rename({"index": "genre", 0: "count"}, axis=1)
        .sort_values(by="count", ascending=False)
    )
    genres = genres.mul(ratings.rating, axis=0)
    result["genres_rating_distribution"] = {
        col: genres[col][genres[col] != 0].value_counts().to_dict() for col in genres.columns
    }
    ratings["datetime"] = pd.to_datetime(ratings.timestamp, unit="s")
    users_ratings = ratings.agg({"userId": ["nunique", "count"]})
    result["users_ratings"] = {
        "now": users_ratings,
        "delta_previous_month": users_ratings
        - ratings[ratings.datetime < ratings.datetime.max() - pd.DateOffset(months=1)].agg(
            {"userId": ["nunique", "count"]}
        ),
    }
    result["movie_rating"] = ratings.groupby("movieId").agg({"rating": ["count", "mean"]})
    return result


def preserve_sorting_df(df: pd.DataFrame, cat_column) -> pd.DataFrame:
    df_sorted = df.copy()
    df_sorted[cat_column] = pd.CategoricalIndex(
        df_sorted[cat_column], categories=df_sorted[cat_column], ordered=True
    )
    return df_sorted


@st.cache_data
def get_img_urls(titles_list):
    url_list = []
    ua = UserAgent()  # =1.3 если сипользовать только поулярные user_agents
    session = Session()
    session.headers.update({"User-Agent": ua.random})
    for t in titles_list:
        try:
            response = session.get(f"https://www.imdb.com/find/?q={requests.utils.quote(t)}")
            if response.status_code == 200:
                url_list.append(
                    bs(response.text, features="html.parser")
                    .select_one("div.ipc-media img")
                    .get("src")
                )
        except Exception as e:
            return f"Произошла ошибка: {e}"
    return url_list


@st.cache_data
def get_img_urls_big(titles_list):
    url_list = []
    ua = UserAgent()
    session = Session()
    session.headers.update({"User-Agent": ua.random})
    if isinstance(titles_list, str):
        titles_list = [titles_list]
    for t in titles_list:
        try:
            response = session.get(f"https://www.imdb.com/find/?q={requests.utils.quote(t)}")
            if response.status_code == 200:
                movie_card = "https://www.imdb.com/" + \
                             bs(response.text, features="html.parser").select_one(
                                 ".ipc-metadata-list-summary-item__t").get("href")
                response = session.get(movie_card)
                if response.status_code == 200:
                    url_list.append(
                        bs(response.text, features="html.parser").select_one("div.ipc-media img").get("src"))

        except Exception as e:
            url_list.append(None)
        sleep(0.2)
    if url_list:
        return url_list if len(url_list) > 1 else url_list[0]


@st.cache_data
def get_top_movies(movies, ratings, n_top=10, watch_limit=30):
    df = ratings.groupby("movieId", as_index=False).agg({"rating": ["count", "mean"]})
    df.columns = ["movieId", "count", "mean"]
    df = (
        df.sort_values(by="mean", ascending=False)
        .query("count >= @watch_limit")
        .head(n_top)
        .merge(movies, on="movieId")
    )
    df["urls"] = get_img_urls(df.title.to_list())
    df = df[["title", "mean", "count", "urls"]]
    df.columns = ["Movie title", "Mean rating", "Number of ratings", "Cover"]
    return df


def user_activity_hist(df: pd.Series):
    fig = px.histogram(df, x="count", nbins=30)
    fig.update_traces(marker_color="#80B1D3")  # Установка цвета столбцов
    fig.update_xaxes(title_text="Number of movies rated")  # Подпись оси X
    fig.update_yaxes(title_text="Users count")  # Подпись оси Y
    fig.update_layout(
        height=250,  # Высота графика
        margin=dict(
            t=0, b=0, l=0, r=0  # Верхний отступ  # Нижний отступ  # Левый отступ  # Правый отступ
        ),
    )
    return fig


def pie_chart(df: pd.DataFrame, category: str, value: str):
    # Строим pie chart с использованием Plotly
    fig = px.pie(
        df,
        names=category,
        values=value,
        color=category,
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    # Сортировка значений по убыванию
    fig.update_traces(sort=False)
    fig.update_layout(
        height=230,  # Высота графика
        margin=dict(
            t=0, b=0, l=0, r=0  # Верхний отступ  # Нижний отступ  # Левый отступ  # Правый отступ
        ),
    )
    return fig


# ---Model -----------------------------
@st.cache_resource
def model_load(path):
    with gzip.open(path, "rb") as f:
        loaded_model = joblib.load(f)
    return loaded_model


@st.cache_data
def get_user_last_movies(userId, ratings, movies, _model, limit=3):
    watched_movies = (
        ratings.loc[ratings["userId"] == userId]
        .sort_values(by="timestamp", ascending=False)
        .head(limit)
    )
    watched_movies = watched_movies.merge(movies, how="left", on="movieId")
    rating_movie_mean = _model.named_steps.Custom_transf.rating_movie_mean
    watched_movies["mean_raing"] = watched_movies.movieId.map(rating_movie_mean)
    watched_movies["user_rating / movie_rating"] = (
        watched_movies["rating"].astype("str")
        + " / "
        + watched_movies["mean_raing"].apply(lambda x: str(round(x, 1)))
    )
    watched_movies.drop(columns=["userId", "timestamp", "movieId"], inplace=True)
    watched_movies = watched_movies[["title", "user_rating / movie_rating", "genres"]]
    watched_movies["genres"] = watched_movies["genres"].apply(
        lambda x: ", ".join(x.split("|")[:2])
    )
    watched_movies["urls"] = get_img_urls(watched_movies.title.to_list())
    watched_movies.columns = ["Title", "User/Movie rating", "Genres", "Cover"]
    return watched_movies


@st.cache_data
def get_recommended_movies(userId, ratings, movies, _model, limit=5):
    watched_movies = ratings.loc[ratings["userId"] == userId].movieId
    unwatched_movies = set(movies.movieId).difference(watched_movies)
    recommended_movies = pd.DataFrame(unwatched_movies, columns=["movieId"])
    recommended_movies["userId"] = userId
    recommended_movies["timestamp"] = ratings.timestamp.max()
    recommended_movies["predicted_rating"] = _model.predict(recommended_movies)
    recommended_movies = recommended_movies.sort_values(
        by="predicted_rating", ascending=False
    ).head(limit)
    recommended_movies = recommended_movies.merge(movies, how="left", on="movieId")
    recommended_movies["predicted_rating"] = recommended_movies.predicted_rating.apply(
        lambda x: round(x, 1)
    )
    recommended_movies["urls"] = get_img_urls_big(recommended_movies.title.to_list())

    return recommended_movies[["title", "genres", "predicted_rating", "urls"]]


def get_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content)  # Возвращаем объект байтов
        else:
            return None  # Если ошибка, вернём None
    except Exception as e:
        st.error(f"Ошибка загрузки изображения: {e}")
        return None

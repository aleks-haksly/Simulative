import pandas as pd
import streamlit as st
import plotly.express as px
import requests
from requests import Session
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
from sklearn.preprocessing import MultiLabelBinarizer


@st.cache_data
def get_csv_data(filepath_or_buffer, compression='gzip', index_col=None):
    return pd.read_csv(filepath_or_buffer, compression='gzip', index_col=index_col)




@st.cache_data
def get_movies_statistics(movies, ratings):
    result = dict()
    result['movies_count'] = movies.shape[0]
    result["movies_ratings_distribution"] = ratings.rating.value_counts().reset_index()

    mlb_genres = MultiLabelBinarizer()
    mlb_genres.fit(movies.genres.apply(lambda x: x.split('|')))
    result["genres_count"] = pd.DataFrame(mlb_genres.transform(movies.genres.apply(lambda x: x.split('|'))),
                                          columns=mlb_genres.classes_, index=movies.index) \
                                          .sum() \
                                          .reset_index() \
                                          .rename({'index': 'genre', 0: 'count'}, axis=1)\
                                          .sort_values(by='count', ascending=False)

    user_activity = ratings['userId'].value_counts()
    result["user_activity"] = user_activity[user_activity <= 1000]
    genres = ratings.movieId.map(movies.genres)
    genres = (pd.DataFrame(mlb_genres.transform(genres.apply(lambda x: x.split('|'))), columns=mlb_genres.classes_,
                          index=genres.index))
    result["watching_counts"] = genres.sum()\
                                      .reset_index()\
                                      .rename({'index': 'genre', 0: 'count'}, axis=1)\
                                      .sort_values(by='count', ascending=False)
    genres = genres.mul(ratings.rating, axis=0)
    #result['genres_mean_ratings'] = genres.apply(lambda x: round(np.mean([_ for _ in x if _ > 0]), 2))
    result['genres_rating_distribution'] = {col: genres[col][genres[col] != 0].value_counts().to_dict() for col in
                                            genres.columns}
    ratings['datetime'] = pd.to_datetime(ratings.timestamp, unit='s')
    users_ratings = ratings.agg({"userId": ["nunique", "count"]})
    result['users_ratings'] = {"now": users_ratings, 'delta_previous_month': users_ratings - ratings[
        ratings.datetime < ratings.datetime.max() - pd.DateOffset(months=1)].agg({"userId": ["nunique", "count"]})}
    result['movie_rating'] = ratings.groupby('movieId').agg({'rating': ['count', 'mean']})
    return result

def preserve_sorting_df(df:pd.DataFrame, cat_column)->pd.DataFrame:
    df_sorted = df.copy()
    df_sorted[cat_column] = pd.CategoricalIndex(df_sorted[cat_column], categories=df_sorted[cat_column], ordered=True)
    return df_sorted

def get_img_urls(titles_list):
  url_list = []
  ua = UserAgent() # =1.3 если сипользовать только поулярные user_agents
  session = Session()
  session.headers.update({'User-Agent': ua.random})
  for t in titles_list:
    try:
      response = session.get(f"https://www.imdb.com/find/?q={requests.utils.quote(t)}")
      if response.status_code == 200:
        url_list.append(bs(response.text, features="html.parser").select_one("div.ipc-media img").get("src"))
    except Exception as e:
        return f"Произошла ошибка: {e}"
  return url_list

@st.cache_data
def get_top_movies(movies, ratings, n_top=10, watch_limit=30):
    df = ratings.groupby('movieId', as_index=False).agg({'rating': ['count', 'mean']})
    df.columns = ['movieId', 'count', 	'mean']
    df = df.sort_values(by='mean', ascending=False).query("count >= @watch_limit").head(n_top).merge(movies, on='movieId')
    df["urls"] = get_img_urls(df.title.to_list())
    df = df[['title', 'mean', 'count', 'urls']]
    df.columns = ['Movie title', 'Mean rating', 'Number of ratings', "Preview Image"]
    return df



def user_activity_hist(df: pd.Series):
    fig = px.histogram(df, x='count', nbins=30)
    fig.update_layout(
        height=250,  # Высота графика
        margin=dict(
            t=0,  # Верхний отступ
            b=0,  # Нижний отступ
            l=0,  # Левый отступ
            r=0  # Правый отступ
        )
    )
    return fig


def pie_chart(df: pd.DataFrame, category: str, value: str):
    # Строим pie chart с использованием Plotly
    fig = px.pie(df, names=category, values=value,
                 color=category, color_discrete_sequence=px.colors.qualitative.Set3)
    # Сортировка значений по убыванию
    fig.update_traces(sort=False)
    fig.update_layout(
        height=230,  # Высота графика
        margin=dict(
            t=0,  # Верхний отступ
            b=0,  # Нижний отступ
            l=0,  # Левый отступ
            r=0  # Правый отступ
        )
    )
    return fig
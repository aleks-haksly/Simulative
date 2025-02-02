import requests
from requests import Session
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as bs
import pandas as pd
from pathlib import Path
from time import sleep
import sqlite3
from tqdm import tqdm


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
        if url_list:
          return url_list if len(url_list) > 1 else url_list[0]

def save_movie_cover(movie_id: int, title: str, db_path: str = "movies.db"):
    """
                Получает URL обложки фильма по названию и сохраняет его в SQLite БД.

                :param movie_id: ID фильма.
                :param title: Название фильма.
                :param db_path: Путь к файлу базы данных (по умолчанию "movies.db").
                """
    url = get_img_urls_big(title)
    if not url:
        print(f"no url for {movie_id}")
        return

    # Подключаемся к БД (создаётся, если отсутствует)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Создаём таблицу, если её нет
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS movie_covers (
                            movieId INTEGER PRIMARY KEY,
                            url TEXT NOT NULL
                        )
                    """)

        # Вставляем или обновляем URL обложки для данного movieId
        cursor.execute("""
                        INSERT INTO movie_covers (movieId, url) 
                        VALUES (?, ?) 
                        ON CONFLICT(movieId) 
                        DO UPDATE SET url = excluded.url
                    """, (movie_id, url))

        conn.commit()


path = Path(__file__).parents[1] / "datasets/movies_df.csv"
movies = pd.read_csv(path, compression='gzip')

for row in tqdm(movies[["movieId", "title"]].iloc[6569:].itertuples(index=False, name=None)):
  save_movie_cover(*row)


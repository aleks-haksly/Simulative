import asyncio
import sqlite3
from pathlib import Path
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup as bs
from fake_useragent import UserAgent

SEM_LIMIT = 8  # Ограничение на количество одновременных запросов

# Функция для получения URL изображения
async def get_img_url_big(
    session, movie_id: int, title: str, sem: asyncio.Semaphore
):
    url = None
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
    search_url = f"https://www.imdb.com/find/?q={title}"
    try:
        async with sem:
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    soup = bs(await response.text(), features="html.parser")
                    movie_card = soup.select_one(".ipc-metadata-list-summary-item__t")
                    if movie_card:
                        movie_card_url = "https://www.imdb.com/" + movie_card.get("href")
                        async with session.get(movie_card_url, headers=headers) as movie_response:
                            if movie_response.status == 200:
                                soup = bs(await movie_response.text(), features="html.parser")
                                img_tag = soup.select_one("div.ipc-media img")
                                if img_tag:
                                    url = img_tag.get("src")
        return movie_id, url
    except Exception as e:
        print(f"Error processing movie {movie_id} ({title}): {e}")
        return movie_id, None  # Возвращаем None, если произошла ошибка

# Функция для сохранения данных в базу данных
async def save_urls_to_db(urls: list, db_path: str):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS movie_covers (
                movieId INTEGER PRIMARY KEY,
                url TEXT NOT NULL
            )
            """
        )
        for movie_id, url in urls:
            if url:  # Запись только в случае наличия URL
                cursor.execute(
                    """
                    INSERT INTO movie_covers (movieId, url)
                    VALUES (?, ?)
                    ON CONFLICT(movieId)
                    DO UPDATE SET url = excluded.url
                    """,
                    (movie_id, url),
                )
        conn.commit()

# Основная функция парсера
async def parser(movies: list):
    sem = asyncio.Semaphore(SEM_LIMIT)
    async with aiohttp.ClientSession() as session:
        tasks = [
            get_img_url_big(session, movie_id, movie_title, sem)
            for movie_id, movie_title in movies
        ]
        # Собираем все результаты
        results = await asyncio.gather(*tasks)
        # Сохраняем результаты в базу данных
        await save_urls_to_db(results, "movies.db")

# Главная часть скрипта
if __name__ == "__main__":
    path = Path(__file__).parents[1] / "datasets/movies_df.csv"
    movies = pd.read_csv(path, compression="gzip")
    try:
        with sqlite3.connect("movies.db") as conn:
            cursor = conn.cursor()
            mx = cursor.execute("SELECT max(movieId) FROM movie_covers")
            result = mx.fetchone()[0]
            print(result)
        idx = movies.query("movieId == @result").index[0] + 1
    except sqlite3.OperationalError:
        idx = 0
    while idx < movies.shape[0]+1000:
        movies_list = movies[["movieId", "title"]].iloc[idx:][["movieId", "title"]].to_numpy()[:1000]
        asyncio.run(parser(movies_list))
        with sqlite3.connect("movies.db") as conn:
            cursor = conn.cursor()
            mx = cursor.execute("SELECT max(movieId) FROM movie_covers")
            result = mx.fetchone()[0]
            print(result)
        idx = movies.query("movieId == @result").index[0] + 1
    print("Parsing done")

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class CustomTransformer(BaseEstimator, TransformerMixin):
    def __init__(
        self,
        mlb_genres,
        movies_data,  # база данных всех фильмов
        avg=np.mean,  # для дальнейшей проверки в GridSearchCV
    ):

        self.mlb = mlb_genres
        self.movies_data = movies_data
        self.avg = avg

    def fit(self, X, y):

        X_train_copy = X.copy()
        X_train_copy = pd.concat([X_train_copy, y], axis=1)
        X_train_copy = X_train_copy.merge(
            self.movies_data[["movieId", "genres"]], on="movieId", how="left"
        )

        #  Для каждого user в train рассчитаем среднюю оценку, которую он ставит фильмам
        self.rating_user_mean = (
            X_train_copy.groupby("userId").rating.apply(self.avg).rename("rating_user_mean")
        )

        #  Для каждого movie в train рассчитаем среднюю оценку, которую он получает от пользователь
        self.rating_movie_mean = (
            X_train_copy.groupby("movieId").rating.apply(self.avg).rename("rating_movie_mean")
        )

        # Для каждого пользователя рассчитаем среднюю оценку,
        # которую он ставит в каждом жанре фильма
        self.mlb_encoded_genres = pd.concat(
            [
                X_train_copy.userId,
                pd.DataFrame(
                    self.mlb.transform(X_train_copy.genres.apply(lambda x: x.split("|"))),
                    columns=self.mlb.classes_,
                    index=X_train_copy.index,
                ).mul(X_train_copy.rating, axis=0),
            ],
            axis=1,
        )
        # А затем сгуппируем по пользователям и усредним
        self.mean_genres_by_users = self.mlb_encoded_genres.groupby(
            "userId"
        ).mean()  # .rename("mean_genres_by_users")
        self.mean_rating = y.pipe(self.avg)  # средний рейтинг всех фильмов train
        # для заполнения пропусков в дальнейшем при трансформации X_test
        return self

    def transform(self, X: pd.DataFrame):

        X_copy = X.copy()
        # Добавим к X_test иформацию их X_train о средних для фильма и средних
        # для пользователя рейтингах. Пропуски заполним средним рейтингом всех фильмов.
        X_copy = (
            X_copy.merge(self.movies_data[["movieId", "genres"]], on="movieId", how="left")
            .merge(self.rating_user_mean, left_on="userId", right_index=True, how="left")
            .merge(self.rating_movie_mean, left_on="movieId", right_index=True, how="left")
            .fillna(self.mean_rating)
        )

        datetime_ = pd.to_datetime(X_copy.timestamp, unit="s")

        X_copy["year_2019"] = datetime_.dt.year.apply(lambda x: int(x == 2019))
        X_copy["weekend"] = datetime_.dt.day_of_week.apply(lambda x: int(x in [5, 6]))

        # добавим к X_train колонки, кодирующие признак, к какому жанру принадлежит текущий фильм
        X_copy = pd.concat(
            [
                X_copy,
                pd.DataFrame(
                    self.mlb.transform(X_copy.genres.apply(lambda x: x.split("|"))),
                    columns=self.mlb.classes_,
                ),
            ],
            axis=1,
        )
        # добавим к X_train колонки с информацией о том,
        # какие в среднем оценки получает каждый жанр от текущего пользователя
        X_copy = X_copy.merge(
            self.mean_genres_by_users,
            how="left",
            left_on="userId",
            right_index=True,
            suffixes=("", "_mean"),
        )
        # дропнем кололнки, которые мы используем трансформированными и те,
        # что нам точно не пригодятся для предсказания рейтинга фильма
        X_copy.drop(
            columns=[
                "timestamp",
                "genres",
                "userId",
                "movieId",
            ],
            inplace=True,
        )
        return X_copy.set_index(X.index)  # для надежности вернем первоначальный индекс, в X_test

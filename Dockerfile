FROM python:3.11-slim

WORKDIR /app

# SQLite3をアップデートするための依存関係をインストール
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# SQLite3の最新版をソースからビルド
RUN wget https://www.sqlite.org/2023/sqlite-autoconf-3430200.tar.gz \
    && tar xzf sqlite-autoconf-3430200.tar.gz \
    && cd sqlite-autoconf-3430200 \
    && ./configure --prefix=/usr/local \
    && make \
    && make install \
    && cd .. \
    && rm -rf sqlite-autoconf-3430200*

# 環境変数を設定してPythonが新しいSQLite3を使用するようにする
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "engineers_discussion.py", "werewolf_game_open_mode.py", "werewolf_game_anonymous_mode.py"] 
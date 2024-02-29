import logging
import os
import time

import requests
import schedule
import uvicorn
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

# スクリプトのあるディレクトリを取得
dir_path = os.path.dirname(os.path.realpath(__file__))
# logconf.iniの絶対パスを作成
logconf_path = os.path.join(dir_path, "../logconf.ini")

# ログ設定を読み込む
logging.config.fileConfig(logconf_path)
logger = logging.getLogger("waap")

seconds_index = 0
in_progress = False
request_path = ""
transaction_id = ""
response_data = ""

# 環境変数を取得
concierge_uri: str = os.getenv("CONCIERGE_URI")
concierge_check_uri: str = os.getenv("CONCIERGE_CHECK_URI")


def set_request_path(path: str):
    global request_path
    request_path = path


def set_transaction_id(id: str):
    global transaction_id
    transaction_id = id


def set_response_data(data: str):
    global response_data
    response_data = data


def get_request_path() -> str:
    return request_path


def get_transaction_id() -> str:
    return transaction_id


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/service/")
async def start_service(request: Request, path: str, server_id: str):
    global concierge_uri
    connect_uri = concierge_uri + path
    set_request_path(connect_uri)
    result = request_handler(request.method, path, server_id)
    return result


@app.api_route(
    "/service/",
    methods=["POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    status_code=201,
)
async def create_service(request: Request, path: str, server_id: str):
    global concierge_uri
    connect_uri = concierge_uri + path
    set_request_path(connect_uri)
    result = request_handler(request.method, path, server_id)
    return result


def check_request():
    global concierge_check_uri, in_progress, seconds_index
    response = requests.get(
        concierge_check_uri + get_transaction_id(),
        headers={"Content-Type": "application/json"},
    )
    data = response.json()
    if data["status"] == "FINISHED":
        print(f"timer finished : {data}")
        in_progress = False
        schedule.clear()
        seconds_index = 0
        set_response_data(data["response"])
        return data

    print(f"next timer set : {data}")
    # 実行する秒数のリスト
    seconds = [2, 4, 8, 16, 32, 64, 128, 256]

    if seconds_index < len(seconds):
        schedule.clear()
        schedule.every(seconds[seconds_index]).seconds.do(check_request)
        print(f"request for concierge timer set : {seconds[seconds_index]}")
        seconds_index += 1
    else:
        in_progress = False
        schedule.clear()
        seconds_index = 0
        raise HTTPException(status_code=408, detail="Request timed out")


def request_handler(method: str, path: str, server_id: str) -> bool:
    logger.debug(
        f"request_handler path: {path}, server_id: {server_id}, concierge_uri: {concierge_uri}"
    )
    global in_progress, response_data
    in_progress = True
    response = requests.request(
        method,
        get_request_path(),
        headers={"Content-Type": "application/json", "x-server-id": server_id},
        json={"original_path": path},
    )
    data = response.json()
    set_transaction_id(data["transaction_id"])

    schedule.every(1).seconds.do(check_request).tag("default")
    while True:
        if not in_progress:
            break
        schedule.run_pending()
        time.sleep(1)
    return response_data


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8008)

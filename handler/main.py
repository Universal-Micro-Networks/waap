import os
import time

import requests
import schedule
import uvicorn
from fastapi import FastAPI

app = FastAPI()
interval = 1  # 初期の実行間隔
is_request = False
request_path = ""
transaction_id = ""

# 環境変数を取得
concierge_uri: str = os.getenv("CONCIERGE_URI")
concierge_check_uri: str = os.getenv("CONCIERGE_CHECK_URI")


def set_request_path(path: str):
    global request_path
    request_path = path


def set_transaction_id(id: str):
    global transaction_id
    transaction_id = id


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
async def start_request(path: str):
    global concierge_uri
    concierge_uri = str(concierge_uri) + path
    set_request_path(concierge_uri)
    request_handler()
    return {"message": "get response from concierge"}


def request():
    global interval, concierge_check_uri, is_request
    response = requests.get(
        concierge_check_uri + get_transaction_id(),
        headers={"Content-Type": "application/json"},
    )
    data = response.json()
    if data["status"] == "FINISHED":
        print(f"timer finished : {data}")
        is_request = False
        interval = 1
        schedule.clear()
        return True

    print(f"next timer set : {data}")

    if interval < 40:
        interval += 10  # 実行間隔を10秒増やす
        schedule.clear()
        schedule.every(interval).seconds.do(request)
        print(f"request for concierge : {interval}")
    else:
        interval += 5
        schedule.clear()


def request_handler() -> bool:
    global interval, is_request
    print(f"I'm working start...{interval}")
    is_request = True
    response = requests.post(
        get_request_path(),
        headers={"Content-Type": "application/json", "x-server-id": "server_id3"},
        json={"original_path": "admin"},
    )
    data = response.json()
    set_transaction_id(data["transaction_id"])
    print(data["transaction_id"])

    schedule.every(interval).seconds.do(request).tag("default")
    while True:
        if not is_request:
            break
        schedule.run_pending()
        time.sleep(1)
    return True


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8008)

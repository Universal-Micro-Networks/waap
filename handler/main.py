import os
import time

import requests
import schedule
import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI()
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
async def start_request(path: str):
    global concierge_uri
    concierge_uri = str(concierge_uri) + path
    set_request_path(concierge_uri)
    result = request_handler()
    return result


def request():
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
        schedule.every(seconds[seconds_index]).seconds.do(request)
        print(f"request for concierge timer set : {seconds[seconds_index]}")
        seconds_index += 1
    else:
        in_progress = False
        schedule.clear()
        raise HTTPException(status_code=408, detail="Request timed out")


def request_handler() -> bool:
    global in_progress, response_data
    in_progress = True
    response = requests.post(
        get_request_path(),
        headers={"Content-Type": "application/json", "x-server-id": "server_id3"},
        json={"original_path": "admin"},
    )
    data = response.json()
    set_transaction_id(data["transaction_id"])
    print(data["transaction_id"])

    schedule.every(1).seconds.do(request).tag("default")
    while True:
        if not in_progress:
            break
        schedule.run_pending()
        time.sleep(1)
    return response_data


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8008)

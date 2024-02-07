from fastapi import FastAPI
import uvicorn
import schedule
import time

app = FastAPI()
interval = 10  # 初期の実行間隔


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/service/")
async def start_request():
    request_timer()
    return {"message": "get response from concierge"}


def request():
    global interval
    if interval < 40:
        interval += 10  # 実行間隔を10秒増やす
        schedule.clear()
        schedule.every(interval).seconds.do(request)
        print(f"request for concierge : {interval}")
    else:
        interval += 5
        schedule.clear()


def request_timer() -> bool:
    global interval
    print(f"I'm working start...{interval}")

    schedule.every(interval).seconds.do(request).tag('default')
    while True:
        if interval > 40:
            break
        schedule.run_pending()
        time.sleep(1)
    return True


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8008)

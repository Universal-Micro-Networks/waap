# WAAP
Web Application API Proxy

## 概要
WAAPはターンアラウンドタイムに対してルーズなレガシーWeb Applicationの前で稼働させることで、モダンなクラウドインフラで稼働するAPI Gateway等の制約を回避するProxyサービスです。
クラウドアプリケーションはその可用性や自立性を担保するためにターンアラウンドタイムを短く設計・実装されます。その一方でレガシーWebアプリケーションはその限りではありません。そのためレガシーWebアプリケーションの前にAPI Gateway等をおいてしまうと、タイムアウト（HTTP Status Code: 504）となってしまうことがしばしばです。
WAAPはこの問題を解決するために開発されました。

## 解決する課題
クラウドインフラのタイムアウト要件に合わないレガシーWebアプリケーションを、前段に配置されるAPI Gatewayをラッピングする形でタイムアウトを回避します。

## 構成
WAAPは二つのプロセス（ConciergeとHandler＆BackgroundTask）と一つのDBによって構成されます。

|No.|Sub No.|Name|Role|
|---:|---:|---|---|
|1.|-|Concierge|Receives an API request from UI and toss it to API Gateway|
|2.|1.|Handler|Receives an API request from the API Gateway and spaun background tasks|
|2.|2.|Background Task|manages slow requests/responses with a legacy web application|
|3.|-|DB|record request statuses of the requests to the legacy web applications|
### Concierge & Handler

Fast API Application

### DB

Key Value Database
Now we assume it should be DynamoDB and we will add more DBs in the future.

### 正常系シーケンス図
```mermaid
sequenceDiagram
    autonumber
    actor UI as UI
    participant WAAPC as WAAP Concierge
    actor AG as API Gateway
    participant WAAPH as WAAP Handler
    participant WAAPB as WAAP Background Task
    participant WAAPD as WAAP DB
    actor WA as Legacy Web App
    UI ->>+ WAAPC : REST Req
    WAAPC ->>+ AG : REST Req
    Note over WAAPC: Web Appからの返事を待つ
    AG ->>+ WAAPH : REST Req
    WAAPH -) WAAPB : Initiate
    WAAPB ->> WAAPD : CREATE
    WAAPB ->>+ WA : REST Req
    Note over WAAPH: 即座にAPI Gatewayにレスポンスを返す。
    WAAPH -->>- AG : Response 201 with Req ID
    AG -->>- WAAPC : Response 201 with Req ID
    loop Web Appからレスポンスが返るまで
        WAAPC->>WAAPC: Wait for a moment
        alt Web Appからのレスポンスなし
            WAAPC ->> WAAPD : GET with Req ID (W/O Update)
        else Web Appからのレスポンスあり
            WA -->>- WAAPB: Response 200/4xx/5xx
            WAAPB ->> WAAPD: UPDATE

            WAAPC ->> WAAPD : GET with Req ID (W/T Update)
            WAAPC -->>- UI : Response 200/4xx/5xx
        end
    end
```

## Quick Start

### Download

```Shell
# gh repo clone Universal-Micro-Networks/waap
```
### Run
```Shell
# docker-compose up
```

## テスト方法
Docker Compose起動後
```Shell
# pytest
```

## その他Tips

### Bump upについて
Bump upは、プラグインを入れると以下コマンドで一括アップデートできるのでおすすめです。
```
# poetry up --latest
```
https://github.com/MousaZeidBaker/poetry-plugin-up

import json
from datetime import datetime, timedelta

import urllib3
from cachetools.func import TTLCache, ttl_cache

TIME_DELTA_CLIENT = timedelta(minutes=5)
TIME_DELTA_TICKER = timedelta(minutes=5)
MAX_TICKERS = 9
MAX_SIZE_CLIENT_CACHE = 100
MAX_SIZE_TICKER_CACHE = MAX_SIZE_CLIENT_CACHE * MAX_TICKERS
API_KEY = "7fc86eb53efdbebe53aedf3b4ddf08bf"


@ttl_cache(ttl=TIME_DELTA_TICKER, timer=datetime.now, maxsize=MAX_SIZE_TICKER_CACHE)
def get_ticker(ticker):
    http = urllib3.PoolManager()
    return json.loads(
        http.request(
            "GET",
            f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}",
        ).data.decode("utf8")
    )[0]


def get_clientip(
    clientip,
    tickers,
    cache=TTLCache(
        ttl=TIME_DELTA_CLIENT, timer=datetime.now, maxsize=MAX_SIZE_CLIENT_CACHE
    ),
):
    if clientip in cache:
        return cache[clientip]
    cache[clientip] = [get_ticker(ticker) for ticker in tickers[:MAX_TICKERS]]
    return cache[clientip]


def lambda_handler(event, context):
    tickers = [
        ticker.upper().strip()
        for ticker in (event or {})
        .get("queryStringParameters", {})
        .get("tickers", "")
        .split(",")
        if ticker
    ]
    clientip = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
    message = get_clientip(clientip, tickers)
    return {
        "headers": {
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(message),
    }

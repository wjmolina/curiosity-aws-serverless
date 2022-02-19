import json
import os
from datetime import datetime, timedelta

import urllib3
from cachetools.func import TTLCache, ttl_cache

TIME_DELTA_CLIENT = timedelta(seconds=5)
TIME_DELTA_TICKER = timedelta(seconds=5)
MAX_TICKERS = 9
MAX_SIZE_CLIENT_CACHE = 100
MAX_SIZE_TICKER_CACHE = MAX_SIZE_CLIENT_CACHE * MAX_TICKERS
API_KEY = os.environ.get("API_KEY")


@ttl_cache(ttl=TIME_DELTA_TICKER, timer=datetime.now, maxsize=MAX_SIZE_TICKER_CACHE)
def get_ticker(ticker):
    http = urllib3.PoolManager()
    response = json.loads(
        http.request(
            "GET",
            f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}",
        ).data.decode("utf8")
    )
    return response[0] if response else {}


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


def lambda_handler(event, _):
    tickers = [
        ticker.upper().strip()
        for ticker in (event.get("queryStringParameters", {}) or {})
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

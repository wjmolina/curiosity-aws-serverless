import json
import os
from datetime import datetime, timedelta
from time import sleep

import urllib3
from cachetools.func import TTLCache, ttl_cache

TIME_DELTA_CLIENT = timedelta(minutes=15)
TIME_DELTA_TICKER = timedelta(minutes=15)
MAX_TICKERS = 9
MAX_SIZE_CLIENT_CACHE = 100
MAX_SIZE_TICKER_CACHE = MAX_SIZE_CLIENT_CACHE * MAX_TICKERS
API_KEY = os.environ.get("API_KEY")
http = urllib3.PoolManager()


@ttl_cache(ttl=TIME_DELTA_TICKER, timer=datetime.now, maxsize=MAX_SIZE_TICKER_CACHE)
def get_ticker(ticker):
    sleep(0.5)
    print(f"MYLOG: getting ticker {ticker}...")
    try:
        response = json.loads(
            http.request(
                "GET",
                f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={API_KEY}",
            ).data.decode("utf8")
        )
        print(f"MYLOG: returning ticker {ticker}")
        return response[0]
    except Exception as exception:
        print(f"MYLOG: could not get ticker {ticker}: {exception}")
        return {}


def get_clientip(
    clientip,
    tickers,
    cache=TTLCache(
        ttl=TIME_DELTA_CLIENT, timer=datetime.now, maxsize=MAX_SIZE_CLIENT_CACHE
    ),
):
    if clientip in cache:
        print(f"MYLOG: returning hand-cached tickers {tickers}")
        return cache[clientip]
    print(f"MYLOG: getting tickers {tickers}...")
    cache[clientip] = [
        ticker_object
        for ticker in tickers[:MAX_TICKERS]
        if (ticker_object := get_ticker(ticker))
    ]
    print(f"MYLOG: returning tickers {tickers}")
    return cache[clientip]


def lambda_handler(event, _):
    tickers = [
        ticker.upper().strip()
        for ticker in (event.get("queryStringParameters", {}) or {})
        .get("tickers", "")
        .split(",")
        if ticker
    ]
    if "httpMethod" not in event:
        response = http.request(
            "GET",
            "https://esxwallpapersbucket.s3.amazonaws.com/tickertracker/wallpaper.html",
        ).data.decode("utf8")
        print(response)
        return {
            "headers": {
                "Access-Control-Allow-Origin": "*",
            },
            "body": "I did the thing.",
        }
    else:
        clientip = event.get("requestContext", {}).get("identity", {}).get("sourceIp")
        message = get_clientip(clientip, tickers)
        return {
            "headers": {
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(message),
        }

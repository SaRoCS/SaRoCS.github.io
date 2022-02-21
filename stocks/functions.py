import math
import os
import requests
import urllib.parse

from functools import wraps

#api key
IEX_KEY = os.environ.get("IEX_KEY")
if not IEX_KEY:
    raise RuntimeError("IEX_KEY not set")

def lookup(symbol):

    #contact API
    try:
        response = requests.get(f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={IEX_KEY}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    #parse response
    try:
        quote = response.json()
        
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"],
            "prevClose" : float(quote["previousClose"]),
            'exchange' : quote['primaryExchange']
        }
    except (KeyError, TypeError, ValueError):
        return None

def advancedLookup(symbol):
    #contact API
    try:
        response = requests.get(f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={IEX_KEY}")
        response.raise_for_status()
        response1 = requests.get(f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/stats?token={IEX_KEY}")
        response1.raise_for_status()
    except requests.RequestException:
        return None
    

    #parse response
    try:
        quote = response.json()
        quote1 = response1.json()
        x = shorten(quote["marketCap"])
        y = shorten(quote1["avg30Volume"])
        
        return {
            "name" : quote["companyName"],
            "price" : float(quote["latestPrice"]),
            "symbol" : quote["symbol"],
            "pe_ratio" : quote["peRatio"],
            "mktCap" : x,
            "week52L" : quote["week52Low"],
            "week52H" : quote["week52High"],
            "prevClose" : quote["previousClose"],
            "avgVolume" : y,
            "beta" : round(quote1["beta"], 2),
            "yield" : round(quote1["dividendYield"] * 100, 2),
            "eps" : quote1["ttmEPS"],
        }
    except (KeyError, TypeError, ValueError):
        return None

def batchLookup(symbols):
    #requests limited to 100 symbols get how many requests you need
    x = math.ceil(len(symbols) / 100)

    #split the list into groups of 100
    reqs = {}
    for i in range(x):
        if i == 0:
            sym = symbols[0:100]
        elif i == x - 1:
            sym = symbols[i*100:len(symbols)]
        else:
            sym = symbols[i*100:(i+1)*100]
        #format it into a string for api call
        sym = f"{*sym,}"
        reqs[i] = sym[1:-1]

    #make the calls
    quote = {}
    for req in reqs:
        #contact API
        try:
            response = requests.get(f"https://cloud.iexapis.com/stable/stock/market/batch?symbols={urllib.parse.quote_plus(reqs[req])}&types=quote&token={IEX_KEY}")
            response.raise_for_status()
        except requests.RequestException:
            return None

        #parse response
        try:
            res = response.json()
            for symbol in res:
                sym = res[symbol]['quote']
                quote[symbol] = {
                    "name": sym["companyName"],
                    "price": float(sym["latestPrice"]),
                    "symbol": sym["symbol"],
                    "prevClose" : float(sym["previousClose"]),
                    'exchange' : sym['primaryExchange']
                }
        except (KeyError, TypeError, ValueError):
            return None
    return quote

def usd(value):
    return f"${value:,.2f}"

def shorten(value):
    y = (len(str(value))-1)
    if y % 3 != 0:
        y = y - (y % 3)
    if y >= 6:
        x = round(value / (10**y), 2)
    else:
        x = value

    if y == 6:
        x = f"{x}M"
    elif y == 9:
        x = f"{x}B"
    elif y == 12:
        x = f"{x}T"
    return x



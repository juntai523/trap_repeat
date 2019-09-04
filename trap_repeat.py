import hashlib
import hmac
import requests
from datetime import datetime
import json
import ccxt
from pprint import pprint
import time
import numpy as np
import pandas as pd
import os
from os.path import join, dirname
from dotenv import load_dotenv
"""
ccxtの設定、apiキー入力
"""
load_dotenv(join(dirname(__file__),".env"))

key=os.environ.get("API_KEY")
secret=os.environ.get("API_SECRET")

bitflyer = ccxt.bitflyer()
bitflyer.apiKey = key
bitflyer.secret = secret



def buy (price_low,price_high,interval):
    """
    一括指値注文（買）を行う関数
    price_lowからprice_highにかけてinterval間隔で注文
    新規の買い注文の数だけflag["count"]をプラス
    """
    try:
        for p in range(price_low,price_high,interval):
            bitflyer.create_order(
            symbol = "BTC/JPY",
            type = "limit",
            side = "buy",
            price = p,
            amount = '0.01',
            params = {"product_code" :"FX_BTC_JPY"})
            flag["count"] += 1
    except ccxt.BaseError as e:
        print("BitflyerのAPIでエラー1発生： ", e)

def sell (price_low,price_high,interval):
    """
    一括指値注文（売）を行う関数
    price_lowからprice_highにかけてinterval間隔で注文
    """
    try:
        for p in range(price_low,price_high,interval):
            bitflyer.create_order(
            symbol = "BTC/JPY",
            type = "limit",
            side = "sell",
            price = p,
            amount = '0.01',
            params = {"product_code" :"FX_BTC_JPY"})
    except ccxt.BaseError as e:
        print("BitflyerのAPIでエラー2発生： ", e)

def check_position(start,interval,trap):
    """
    現在のポジションを確認する関数
    flag["position"]にてポジションのロット
    flag["price"]["low"]にて買い注文の下限
    flag["price"]["high"]にて売り注文の下限を定義
    """
    try:
        position = bitflyer.private_get_getpositions(params = { "product_code" : "FX_BTC_JPY"})
        position_size = [position[i]['size'] for i in range(len(position))]
        flag["position"] = round(sum(position_size)*100)
        flag["price"]["low"] = (start+interval*(flag["order"]["buy"]))
        flag["price"]["high"] = (flag["price"]["low"]+interval*(trap-flag["order"]["sum"]))
    except ccxt.BaseEroor as e:
        print("BitflyerのAPIで問題発生： ",e)

def check_order(start,interval,trap):
    """
    現在のオーダーを確認する関数
    flag["order"]["buy"],["sell"],["sum"]にて注文数
    flag["price"]["LOW"]にて買い注文の下限
    flag["price"]["HIGH"]にて売り注文の下限を定義
    """
    try:
        orders = bitflyer.fetch_open_orders(
        symbol = "BTC/JPY",
        params = { "product_code" : "FX_BTC_JPY" })
        side = [orders[i]['info']['side'] for i in range(len(orders))]
        buy = []
        sell = []
        for i in side:
            if i == "BUY":
                buy.append(i)
            else :
                sell.append(i)
        flag["order"]["buy"] = len(buy)
        flag["order"]["sell"] = len(sell)
        flag["order"]["sum"] = len(buy) + len(sell)
        flag["price"]["HIGH"] = (start+interval*(trap-flag["order"]["sell"]+1))
        flag["price"]["LOW"] = (flag["price"]["HIGH"]-interval*(trap-flag["order"]["sum"]))
    except ccxt.BaseError as e:
        print("BitflyerのAPIでエラー発生： ",e)

"""
order,position,売買の基準となる数値をflagにて管理
約定数をカウントにて管理
"""
flag = {"order" :{ "buy": 0,"sell": 0,"sum":0},"position" : 0,"price":{"low": 0,"high": 0,"LOW": 0,"HIGH": 0},"count":0}
START=1000000
INTERVAL=5000
TRAP=70

while True:
    now = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
    check_order(start=START,interval=INTERVAL,trap=TRAP)
    check_position(start=START,interval=INTERVAL,trap=TRAP)
    print("時間：",now," , ","買い注文：",flag["order"]["buy"]," , ","売り注文：",flag["order"]["sell"]," , ","合計注文数：",flag["order"]["sum"]," , ","ポジション数：",flag["position"]," , ","買い注文基準値：",flag["price"]["low"],",",flag["price"]["high"]," , ","売り注文基準値：",flag["price"]["LOW"],",",flag["price"]["HIGH"],",","約定回数：",flag["count"])
    
    if flag["order"]["sum"] != TRAP and  flag["order"]["sell"] >=  flag["position"]:
        buy(flag["price"]["low"],flag["price"]["high"],INTERVAL)
    elif flag["order"]["sum"] != TRAP and flag["order"]["sell"] < flag["position"]:
        sell(flag["price"]["LOW"],flag["price"]["HIGH"],INTERVAL)
    time.sleep(60)

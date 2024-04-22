import streamlit as st
from web3 import Web3
import openai
import requests
import json
import shelve
import os
import pandas as pd
from datetime import datetime, timedelta
# CoinGecko API base URL
COINGECKO_API_BASE_URL = 'https://api.coingecko.com/api/v3'

# Etherscan API base URL
ETHERSCAN_API_BASE_URL = 'https://api.etherscan.io/api'
st.title("Blockchat AI")
# Set up OpenAI API key
openai.api_key = ""

def crypto_price(currency):
    coin_symbol = currency.lower()
    response = requests.get(f"{COINGECKO_API_BASE_URL}/simple/price?ids={coin_symbol}&vs_currencies=usd")
    if response.status_code == 200:
        value = response.json()
        data = {"name":str(value.keys()),"price":value.get(currency)}       
        return json.dumps(data)
def filter_lowest_price(currencies):
    coin_symbol = currencies.lower()
    response = requests.get(f"{COINGECKO_API_BASE_URL}/simple/price?ids={coin_symbol}&vs_currencies=usd")
    data = response.json()
    out={}
    # Find the coin with the lowest price in USD
    lowest_price = float('inf')
    lowest_price_coin = None
    for coin, price_info in data.items():
        price_usd = price_info.get('usd', float('inf'))
        if price_usd < lowest_price:
            lowest_price = price_usd
            lowest_price_coin = coin    
    out["coin"]  = lowest_price_coin
    out["price"]= lowest_price
    print(out)
    return json.dumps(out)
def fetch_price_history(coin_id="bitcoin", days=30):
    """
    Fetches historical price data for a given cryptocurrency over a specified number of days.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        'vs_currency': 'usd',
        'from': start_date.timestamp(),
        'to': end_date.timestamp()
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = data['prices']
    df= pd.DataFrame(prices, columns=['timestamp', 'price'])
    return df
def recommendation(coin_id):
    df=fetch_price_history(coin_id)
    df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price_change'] = df['price'].pct_change()
    


    strategy={}
    df['trend'] = df['price_change'].rolling(window=5).mean()  # 5-day moving average
    if df['trend'].iloc[-1] > 0:
        strategy['trend'] = "Bullish"
        strategy['recommendation'] = "Buying"
        return json.dumps(strategy)
    elif df['trend'].iloc[-1] < 0:
        strategy['trend'] = "Bearish"
        strategy['recommendation'] = "selling"
        return json.dumps(strategy)
    else:
        strategy['trend'] = "No trend"
        strategy['recommendation'] = "holding"
        return json.dumps(strategy)


def filter_highest_price(currencies):
    coin_symbol = currencies.lower()
    response = requests.get(f"{COINGECKO_API_BASE_URL}/simple/price?ids={coin_symbol}&vs_currencies=usd")
    data = response.json()
    out={}
    # Find the coin with the lowest price in USD
    highest_price = 0.000001
    highest_price_coin = None
    for coin, price_info in data.items():
        price_usd = price_info.get('usd', float('inf'))
        if price_usd > highest_price:
            highest_price = price_usd
            highest_price_coin = coin    
    out["coin"]  = highest_price_coin
    out["price"]= highest_price
    print(out)
    return json.dumps(out)
functions = [
   {
      "name":"crypto_price",
      "description":"Get the current market price of crytocurrency, e.g. bitcoin,etheruem",
      "parameters":{
         "type":"object",
         "properties":{
            "currency":{
               "type":"string",
               "description":"the name of cryptocurrency"
            },
         },
         "required":["currency"],
      },
   },
   {
      "name":"filter_lowest_price",
      "description":"filters and returns cheapest coin and price among the given list of cryptocurrencies, e.g. bitcoin,ethereum,ripple",
      "parameters":{
         "type":"object",
         "properties":{
            "currencies":{
               "type":"string",
               "description":"list of cryptocurrencies, e.g. bitcoin,ethereum,ripple."
            },
         },
         "required":["currencies"],
      },
   },
   {
      "name":"filter_highest_price",
      "description":"filters and returns expensive coin and price among the given list of cryptocurrencies, e.g. bitcoin,ethereum,ripple",
      "parameters":{
         "type":"object",
         "properties":{
            "currencies":{
               "type":"string",
               "description":"list of cryptocurrencies, e.g. bitcoin,ethereum,ripple."
            },
         },
         "required":["currencies"],
      },
   },
   {
      "name":"recommendation",
      "description":"gets the current market trend of gievn cryptocurrency.",
      "parameters":{
         "type":"object",
         "properties":{
            "coin_id":{
               "type":"string",
               "description":"the name of cryptocurrency"
            },

         },
         "required":["coin_id"],
      },
   }
]
def bot(query):
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0613",  # Use GPT-3.5 Davinci model
        messages=[{"role":"user","content":query}],
        functions=functions,
        function_call="auto"
    )
    print(response.choices[0])
    mes=response.choices[0].message
    if mes.function_call is not None:
        return second(mes)
    else:
        return mes.content
def second(mes):
    if mes.function_call is not None:
        function_name=mes.function_call.name
        if function_name=="crypto_price":
            currency=json.loads(mes.function_call.arguments).get("currency")
            function_response=crypto_price(currency)

            sec_response = openai.chat.completions.create(
            model="gpt-3.5-turbo-0613",  # Use GPT-3.5 Davinci model
            messages=[
                {"role":"function",
                    "name":function_name,
                    "content":function_response}],
            
            )
        elif function_name=="filter_highest_price":
            currencies=json.loads(mes.function_call.arguments).get("currencies")
            function_response=filter_highest_price(currencies)

        elif function_name=="filter_lowest_price":
            currencies=json.loads(mes.function_call.arguments).get("currencies")
            function_response=filter_lowest_price(currencies)
        elif function_name=="recommendation":
            coin_id=json.loads(mes.function_call.arguments).get("coin_id")
            function_response=recommendation(coin_id)
        sec_response = openai.chat.completions.create(
        model="gpt-3.5-turbo-0613",  # Use GPT-3.5 Davinci model
        messages=[
            {"role":"function",
                "name":function_name,
                "content":function_response}],
        
        )


    return sec_response.choices[0].message.content



def load_history():
    with shelve.open("chat_history") as db:
        return db.get("messages",[])
def save_chat(messages):
    with shelve.open("chat_history") as db:
        db["messages"]=messages

def main():
    
    if "messages" not in st.session_state:
        st.session_state.messages = load_history()

    with st.sidebar:
        if st.button("DELETE CHAT"):
            st.session_state.messages = []
            save_chat([])
    # Main conversation loop
    for message in st.session_state.messages:
    
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Main chat interface
    if prompt := st.chat_input("How can I help?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            if prompt:
                with st.spinner("Waiting for response..."):
                    full_response=bot(prompt)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            message_placeholder.markdown(full_response + "|")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    # Save chat history after each interaction
    save_chat(st.session_state.messages)
if __name__ == "__main__":
    main()

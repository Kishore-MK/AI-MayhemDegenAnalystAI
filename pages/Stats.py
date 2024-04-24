import streamlit as st
import requests
import google.generativeai as genai
from pages.transactionDetails import transaction_details

COINGECKO_API_BASE_URL = 'https://api.coingecko.com/api/v3'

ETHERSCAN_API_BASE_URL = 'https://api.etherscan.io/api'

def price_of_crypto(currency):
    coin_symbol = currency.lower().strip()
    print(currency)
    response = requests.get(f"{COINGECKO_API_BASE_URL}/simple/price?ids={coin_symbol}&vs_currencies=usd")
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data
function_mapping = {
    "price_of_crypto": price_of_crypto,
    "transaction_details": transaction_details,
}
genai.configure(api_key="")

# Set up the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 0,
  "max_output_tokens": 8192,
}

safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_ONLY_HIGH"
  },
]

system_instruction = "you're going to automate a cryto price and show transaction details using coin market cap and etherscan api. if the user asks for transaction details you should return \"transaction_details\" along with the transaction hash(comma separated).if the user asks to check for price of a crypto currency you should return the \"price_of_crypto\"  with the name of the crypto currency (comma seperated single string)  alone . keep in mind the name of the crypto currency should be in standard form .your name is DeMatter. on hi introduce yourself and ask them for any questions(only when said hi or hello alone)...if question is out of the operation defined or blockchain reply that you can't reply...your duty is just to call the functions... don't provide any other information including explanation. if it returns a function name along with it's argument you have to mention that as function_call at starting. That should also be comma seperated. If the Crypto currency name is not present reply i don't know this crypto"

model = genai.GenerativeModel(model_name="gemini-1.5-pro-latest",
                              generation_config=generation_config,
                              system_instruction=system_instruction,
                              safety_settings=safety_settings)


convo = model.start_chat(history=[
  {
    "role": "user",
    "parts": ["which date  ptill you have updated your data"]
  },
  {
    "role": "model",
    "parts": ["I'm sorry, I can't answer that. I can only assist with crypto price checks and hash validations."]
  },
  {
    "role": "user",
    "parts": ["hi"]
  },
  {
    "role": "model",
    "parts": ["Hi, I'm Blockchat AI.  Do you have any questions about crypto prices or hash validations?"]
  },
  {
    "role": "user",
    "parts": ["price of bit coin"]
  },
  {
    "role": "model",
    "parts": ["function_call,price\\_of\\_crypto,bitcoin"]
  },
  {
    "role": "user",
    "parts": ["hi"]
  },
  {
    "role": "model",
    "parts": ["Hi, I'm DeMatter.  Do you have any questions about crypto prices or hash validations?"]
  },
  {
    "role": "user",
    "parts": ["who are you?"]
  },
  {
    "role": "model",
    "parts": ["I'm sorry, I can't answer that. I can only assist with crypto price checks and hash validations."]
  },
  {
    "role": "user",
    "parts": ["what's your name"]
  },
  {
    "role": "model",
    "parts": ["I'm DeMatter.  Do you have any questions about crypto prices or hash validations?"]
  },
  {
    "role": "user",
    "parts": ["how can you help me?"]
  },
  {
    "role": "model",
    "parts": ["I can help you check crypto prices and validate hashes.  Do you have any questions about those topics?"]
  },
])

if "messages" not in st.session_state:
    st.session_state.messages = []

# Main conversation loop
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
prompt = st.chat_input("What's up?")

if prompt:
     # Display loading spinner
      with st.chat_message("user"):
            convo.send_message(prompt)
            st.markdown(prompt)

      st.session_state.messages.append({"role": "user", "content": prompt})
      with st.spinner("Waiting for response..."):
        # Bot response
        with st.chat_message("assistant"):
            if convo.last:
                response = convo.last.text
                response=response.replace("\\","")
                if "function_call" in response:
                    arr=response.split(',')
                    print("Called the funtion :",arr[1])


                    data = function_mapping[arr[1]](arr[2])
                    st.markdown(data)
                    st.session_state.messages.append({"role": "assistant", "content": data})
                else:
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})

import cohere
import streamlit as st
import requests
from io import BytesIO

def get_llm_response(prompt, api_key):
    co = cohere.Client(api_key)
    response = co.chat(
        model="command-r-plus",
        message=prompt,
        max_tokens=4000
    )
    return response.text

def text_to_speech(text, access_token, tts_endpoint):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/ssml+xml; charset=utf-8',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3'
    }
    body = f"""
    <speak version='1.0' xml:lang='zh-CN'>
        <voice xml:lang='zh-CN' xml:gender='Female' name='zh-CN-XiaoxiaoMultilingualNeural'>
            <prosody rate='1.0'>
                {text}
            </prosody>
        </voice>
    </speak>
    """
    response = requests.post(tts_endpoint, headers=headers, data=body.encode('utf-8'))
    response.raise_for_status()
    return response.content

def get_access_token(subscription_key, token_endpoint):
    headers = {
        'Ocp-Apim-Subscription-Key': subscription_key
    }
    response = requests.post(token_endpoint, headers=headers)
    response.raise_for_status()
    return response.text

def split_text(text, percentage):
    try:
        if percentage == "默认随机":
            split_point = len(text) // 2
        else:
            percentage = float(percentage.rstrip('%')) / 100
            split_point = int(len(text) * percentage)
        return text[:split_point], text[split_point:]
    except ValueError:
        st.error(f"Invalid percentage value: {percentage}")
        return text, ""
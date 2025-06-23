import streamlit as st
import openai
import requests

# 🔐 API-Keys aus den Streamlit Secrets laden
client = openai.OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)
weather_api_key = st.secrets["WEATHER_API_KEY"]

# 🌤 Wetterdaten von OpenWeather abrufen
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric&lang=de"
        response = requests.get(url).json()
        if response.get("main"):
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            return f"In {city} ist es aktuell {temp}°C mit {desc}."
        else:
            return "⚠️ Wetterdaten konnten nicht gefunden werden."
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Wetterdaten: {e}"

# ✈️ Reisetipps von ChatGPT holen
def get_travel_tips(city):
    try:
        prompt = f"Gib mir drei kurze, hilfreiche Reisetipps für einen Städtetrip nach {city}."
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein freundlicher Reiseassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Reisetipps: {e}"

# 🌐 Streamlit Benutzeroberfläche
st.set_page_config(page_title="Reiseplaner mit Wetter", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit Wetter & KI")

city = st.text_input("🌍 Wohin möchtest du reisen?", placeholder="z. B. Rom, Paris, Istanbul")

if city:
    with st.spinner("🔄 Wetter wird geladen..."):
        weather = get_weather(city)
    st.success(weather)

    with st.spinner("🔄 Reisetipps werden geladen..."):
        tips = get_travel_tips(city)
    st.info(tips)

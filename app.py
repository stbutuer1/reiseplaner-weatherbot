import streamlit as st
import openai
import requests

# 🔐 API-Keys sicher über Streamlit Cloud verwalten
openai.api_key = st.secrets["OPENAI_API_KEY"]
weather_api_key = st.secrets["WEATHER_API_KEY"]

# 🌤 Wetterdaten abrufen
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

# ✈️ Reisetipps mit ChatGPT abrufen
def get_travel_tips(city):
    try:
        prompt = f"Gib mir drei kurze Reisetipps für einen Städtetrip nach {city} in Deutschland oder Europa."
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein freundlicher Reiseassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Reisetipps: {e}"

# 🌐 Streamlit UI
st.set_page_config(page_title="Reiseplaner mit Wetter", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit Wetterfunktion")

# Eingabe
city = st.text_input("🌍 Wohin möchtest du reisen?", placeholder="z. B. Rom, Paris, Istanbul")

# Ausgabe
if city:
    with st.spinner("🔄 Lade Wetterdaten..."):
        weather = get_weather(city)
    st.success(weather)

    with st.spinner("🔄 Lade Reisetipps..."):
        tips = get_travel_tips(city)
    st.info(tips)

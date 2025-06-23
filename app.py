# Neu ausführen nach Reset: PDF-Funktion entfernt und neue Features eingebaut
import streamlit as st
import openai
import requests
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import folium
from streamlit_folium import st_folium
from urllib.parse import quote_plus

# === API Keys ===
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]

# === Dynamische Stadt-Zeitzone und Währung ===
def get_local_info(city):
    try:
        geolocator = Nominatim(user_agent="reiseplaner")
        location = geolocator.geocode(city)
        if not location:
            return "Unbekannt", "Unbekannt"
        tf = TimezoneFinder()
        timezone = tf.timezone_at(lng=location.longitude, lat=location.latitude)
        local_time = datetime.now(pytz.timezone(timezone)).strftime("%H:%M:%S")
        currency = "EUR" if "Europe" in timezone else "USD"
        return local_time, currency
    except:
        return "Unbekannt", "Unbekannt"

# === Wetterdaten ===
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={quote_plus(city)}&appid={weather_api_key}&units=metric&lang=de"
        response = requests.get(url).json()
        if "main" in response:
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            return temp, desc
        elif "message" in response:
            return None, f"⚠️ Fehler: {response['message']}"
        else:
            return None, "⚠️ Unbekannter Fehler bei der Wetterabfrage."
    except Exception as e:
        return None, f"❌ Fehler beim Abrufen der Wetterdaten: {e}"

# === GPT-Reisetipps ===
def get_travel_tips(city, lang="de"):
    try:
        prompt = {
            "de": f"Gib mir drei kurze, hilfreiche Reisetipps für einen Städtetrip nach {city} in Europa.",
            "en": f"Give me three short, helpful travel tips for a city trip to {city} in Europe."
        }[lang]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful travel assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {e}"

# === Streamlit UI ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter & Links")

tabs = st.tabs(["🎒 Planung", "🕓 Ortsinfo", "🏨 Hotels", "🗺️ Karte", "🎯 Sehenswürdigkeiten"])

with tabs[0]:
    language = st.radio("🌍 Sprache", ["Deutsch", "Englisch"], horizontal=True)
    city = st.text_input("Reiseziel", placeholder="z. B. Paris, Istanbul")
    travel_date = st.date_input("📅 Reisedatum", value=datetime.now().date())

    if city:
        temp, desc = get_weather(city)
        if isinstance(temp, float):
            weather_info = f"{temp:.1f}°C mit {desc}" if language == "Deutsch" else f"{temp:.1f}°C with {desc}"
            st.success(weather_info)
        else:
            st.warning(desc)

        tips = get_travel_tips(city, lang="de" if language == "Deutsch" else "en")
        st.info(tips)

with tabs[1]:
    if city:
        time, currency = get_local_info(city)
        st.metric("🕓 Lokale Uhrzeit", time)
        st.metric("💱 Währung", currency)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

with tabs[2]:
    if city:
        booking_url = f"https://www.booking.com/searchresults.html?ss={quote_plus(city)}"
        st.subheader("🛏️ Booking Link")
        st.markdown(f"[Hotels in {city} auf Booking.com ansehen]({booking_url})")
        st.subheader("🏨 Beispielhotels (Google Links)")
        for hotel in ["Hilton", "Marriott", "Ibis"]:
            st.markdown(f"[{hotel} {city} bei Google Maps](https://www.google.com/maps/search/{quote_plus(hotel + ' ' + city)})")

with tabs[3]:
    if city:
        geolocator = Nominatim(user_agent="reiseplaner")
        location = geolocator.geocode(city)
        if location:
            m = folium.Map(location=[location.latitude, location.longitude], zoom_start=12)
            folium.Marker([location.latitude, location.longitude], tooltip=city).add_to(m)
            st_folium(m, width=700, height=450)
        else:
            st.warning("Stadt konnte nicht gefunden werden.")

with tabs[4]:
    if city:
        st.subheader(f"🎯 Sehenswürdigkeiten in {city}")
        places = ["Eiffelturm", "Louvre Museum", "Kathedrale Notre-Dame de Paris", "Triumphbogen", "Montmartre-Basilika"]
        for place in places:
            st.markdown(f"🔎 [{place} auf Google ansehen](https://www.google.com/search?q={quote_plus(place + ' ' + city)})")
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

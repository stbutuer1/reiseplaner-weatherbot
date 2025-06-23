import streamlit as st
import openai
import requests
from datetime import datetime
from urllib.parse import quote_plus
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz
import folium
from streamlit_folium import st_folium

# === API-Key-Konfiguration ===
from openai import OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]
unsplash_key = st.secrets["UNSPLASH_ACCESS_KEY"]

# === Stil: Hintergrundfarbe (blau) ===
st.set_page_config("Reiseplaner mit KI", "🌤️")
st.markdown("""
    <style>
    body {
        background-color: #e6f2ff;
    }
    [data-testid="stAppViewContainer"] > .main {
        background-color: #e6f2ff;
    }
    section[data-testid="stSidebar"] {
        background-color: #cce6ff;
    }
    </style>
""", unsafe_allow_html=True)

# === GPT-Funktion ===
def ask_gpt(prompt):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Fehler: {e}"

# === Reisetipps ===
def get_travel_tips(city, date):
    month = date.strftime("%B")
    prompt = f"Gib mir 3 kurze Reisetipps für einen Besuch in {city} im Monat {month}. Berücksichtige saisonale Besonderheiten."
    return ask_gpt(prompt)

# === Wetterdaten ===
def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={quote_plus(city)}&appid={weather_api_key}&units=metric&lang=de"
    r = requests.get(url).json()
    if "main" in r:
        return f"{r['main']['temp']}°C, {r['weather'][0]['description']}"
    return "Keine Wetterdaten gefunden."

# === Zeit & Währung ===
def get_timezone_and_currency(city):
    geolocator = Nominatim(user_agent="reiseplaner")
    tf = TimezoneFinder()
    try:
        location = geolocator.geocode(city)
        if location:
            timezone_str = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            local_time = datetime.now(pytz.timezone(timezone_str)).strftime("%H:%M:%S")
            currency = ask_gpt(f"Welche Währung wird in {city} verwendet? Gib nur den Code aus (z. B. EUR, USD, TRY).")
            return local_time, currency
    except:
        return "–", "–"
    return "–", "–"

# === Hotels ===
def get_hotel_suggestions(city):
    prompt = f"Nenne 3 beliebte Hotels in {city} für Reisende. Gib nur die Hotelnamen in einer durch Kommas getrennten Liste aus."
    try:
        names = ask_gpt(prompt).split(",")
        return [name.strip() for name in names]
    except:
        return []

# === Sehenswürdigkeiten ===
def get_attractions(city):
    prompt = f"Nenne die 3 bekanntesten Sehenswürdigkeiten in {city}. Nur die Namen, durch Kommas getrennt."
    try:
        names = ask_gpt(prompt).split(",")
        return [name.strip() for name in names]
    except:
        return []

# === Unsplash Bildsuche ===
def get_unsplash_image(query):
    try:
        url = f"https://api.unsplash.com/search/photos?query={quote_plus(query)}&client_id={unsplash_key}"
        res = requests.get(url).json()
        if res["results"]:
            return res["results"][0]["urls"]["regular"]
    except:
        return None

def get_best_image(sight, city):
    for q in [f"{sight} {city}", sight, city]:
        img = get_unsplash_image(q)
        if img:
            return img
    return None

# === Karte ===
import time

def show_map(city):
    geolocator = Nominatim(user_agent="reiseplaner")
    try:
        time.sleep(1)  # Gegen Rate-Limiting von Nominatim
        loc = geolocator.geocode(city)
        if loc:
            m = folium.Map(location=[loc.latitude, loc.longitude], zoom_start=12)
            st_folium(m, height=400)
        else:
            st.warning("❌ Stadt konnte nicht lokalisiert werden.")
    except Exception as e:
        st.error(f"🌐 Fehler bei der Standortsuche: {e}")


# === Streamlit App Tabs ===
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter, Karte & Sehenswürdigkeiten")
tabs = st.tabs(["📅 Planung", "📍 Ortsinfo", "🛏 Hotels", "🗺️ Karte", "🎯 Sehenswürdigkeiten"])

with tabs[0]:
    city = st.text_input("Reiseziel", placeholder="z. B. Paris, Istanbul")
    date = st.date_input("Reisedatum", datetime.today())
    if city:
        st.subheader("💡 Saisonale Reisetipps")
        st.markdown(get_travel_tips(city, date))
        st.subheader("🌤️ Wetter")
        st.info(get_weather(city))

with tabs[1]:
    if city:
        time_str, currency = get_timezone_and_currency(city)
        st.metric("🕒 Lokale Uhrzeit", time_str)
        st.metric("💱 Währung", currency)


with tabs[2]:
    if city:
        booking_url = f"https://www.booking.com/searchresults.html?ss={quote_plus(city)}"
        st.markdown(f"🔗 [Hotels in {city} auf Booking.com ansehen]({booking_url})")

        st.subheader("🏨 Vorschläge")
        hotels = get_hotel_suggestions(city)
        for name in hotels:
            maps_url = f"https://www.google.com/maps/search/{quote_plus(name + ' ' + city)}"
            st.markdown(f"• **{name}** [📍 Google Maps]({maps_url})")

            
with tabs[3]:
    if city:
        st.subheader("📍 Interaktive Karte")
        show_map(city)

with tabs[4]:
    if city:
        st.subheader(f"🎯 Top 3 Sehenswürdigkeiten in {city}")
        sights = get_attractions(city)
        for sight in sights:
            st.markdown(f"🔗 [{sight} bei Google suchen](https://www.google.com/search?q={quote_plus(sight + ' ' + city)})")
            image_url = get_best_image(sight, city)
            if image_url:
                st.image(image_url, caption=sight, use_container_width=True)
            else:
                st.warning(f"❌ Kein Bild für {sight} gefunden.")

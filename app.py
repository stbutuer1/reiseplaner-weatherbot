# Vollständiger Code inkl. stabiler Ortsinfo-Funktion mit Fehlerbehandlung & Delay

import streamlit as st
import openai
import requests
from datetime import datetime
import pytz
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from timezonefinder import TimezoneFinder
import time
import folium
from streamlit_folium import st_folium
from urllib.parse import quote_plus

# === API Keys ===
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]
unsplash_key = st.secrets.get("UNSPLASH_ACCESS_KEY")

# === Unsplash Bildabruf ===
def get_unsplash_image(query):
    try:
        url = f"https://api.unsplash.com/photos/random?query={quote_plus(query)}&client_id={unsplash_key}"
        response = requests.get(url).json()
        return response["urls"]["regular"]
    except:
        return None

# === GPT-basierte Währungsinfo ===
def get_local_info_gpt(city, lang="de"):
    try:
        prompt = {
            "de": f"Welche Währung wird in {city} verwendet?",
            "en": f"What currency is used in {city}?"
        }[lang]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Reiseassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Fehler: {e}"

# === GPT-Hotelsuche ===
def get_hotels_for_city(city, lang="de"):
    try:
        prompt = {
            "de": f"Nenne mir 5 bekannte Hotels in {city} (nur Namen, keine Beschreibung).",
            "en": f"Name 5 well-known hotels in {city} (only names, no descriptions)."
        }[lang]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein hilfreicher Reiseassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        text = response.choices[0].message.content
        lines = text.strip().split("\n")
        hotels = [line.strip().lstrip("0123456789.-• ").strip() for line in lines if line.strip()]
        return hotels
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der Hotels: {e}"]

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

# === Ortsinfo Tab – stabilisiert ===
def render_local_info_tab(city, language):
    if city:
        geolocator = Nominatim(user_agent="reiseplaner-app-bueturkel")
        try:
            time.sleep(1)
            location = geolocator.geocode(city)
        except GeocoderUnavailable:
            st.warning("🌐 Standortdienst aktuell nicht erreichbar. Bitte versuche es in ein paar Sekunden erneut.")
            return
        except Exception as e:
            st.warning(f"🌐 Fehler beim Abrufen der Standortdaten: {e}")
            return

        if location:
            try:
                tf = TimezoneFinder()
                timezone = tf.timezone_at(lng=location.longitude, lat=location.latitude)
                time_str = datetime.now(pytz.timezone(timezone)).strftime("%H:%M:%S")
                st.metric("🕓 Lokale Uhrzeit", time_str)
            except Exception as e:
                st.warning(f"⏰ Fehler bei Zeitzone/Uhrzeit: {e}")
        else:
            st.warning("📍 Stadt konnte nicht lokalisiert werden.")

        st.subheader("💱 Lokale Währung")
        currency_info = get_local_info_gpt(city, lang="de" if language == "Deutsch" else "en")
        st.info(currency_info)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

# === Streamlit UI ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.markdown("""
    <style>
    body {
        background-color: #f0f8ff;
    }
    section[data-testid="stSidebar"] {
        background-color: #e6f2ff;
        border-right: 2px solid #cce0ff;
        padding-top: 20px;
    }
    button[kind="primary"] {
        border-radius: 8px;
        background-color: #4da6ff;
        color: white;
        transition: 0.3s ease;
    }
    button[kind="primary"]:hover {
        background-color: #1a8cff;
        transform: scale(1.02);
    }
    div[data-testid="stVerticalBlock"] > div {
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="stVerticalBlock"] > div:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: scale(1.01);
    }
    @keyframes fly {
        0% { left: -100px; top: 30px; }
        100% { left: 110%; top: 30px; }
    }
    #plane {
        position: fixed;
        z-index: 9999;
        width: 60px;
        animation: fly 10s linear infinite;
    }
    </style>
    <img id="plane" src="https://upload.wikimedia.org/wikipedia/commons/0/0f/Airplane_emoji.png" />
""", unsafe_allow_html=True)
st.title("🌤️ Willkommen zu deinem Reiseplaner-Bot)

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
    render_local_info_tab(city, language)

with tabs[2]:
    if city:
        booking_url = f"https://www.booking.com/searchresults.html?ss={quote_plus(city)}"
        st.subheader("🛏️ Booking Link")
        st.markdown(f"[Hotels in {city} auf Booking.com ansehen]({booking_url})")

        st.subheader("🏨 Lokale Hotelvorschläge")
        hotels = get_hotels_for_city(city, lang="de" if language == "Deutsch" else "en")
        for hotel in hotels:
            url = f"https://www.google.com/maps/search/{quote_plus(hotel + ' ' + city)}"
            st.markdown(f"- [{hotel}]({url})")

with tabs[3]:
    if city:
        geolocator = Nominatim(user_agent="reiseplaner-app-bueturkel")
        try:
            location = geolocator.geocode(city)
            if location:
                m = folium.Map(location=[location.latitude, location.longitude], zoom_start=12)
                folium.Marker([location.latitude, location.longitude], tooltip=city).add_to(m)
                st_folium(m, width=700, height=450)
            else:
                st.warning("Stadt konnte nicht gefunden werden.")
        except:
            st.warning("Fehler beim Laden der Karte.")

with tabs[4]:
    if city:
        st.subheader(f"🎯 Sehenswürdigkeiten in {city}")
        places = ["Altstadt", "Museum", "Park"]
        for place in places:
            st.markdown(f"[{place} in {city} auf Google ansehen](https://www.google.com/search?q={quote_plus(place + ' ' + city)})")
            if unsplash_key:
                image_url = get_unsplash_image(f"{place} {city}")
                if image_url:
                    st.image(image_url, caption=f"{place}", use_container_width=True)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

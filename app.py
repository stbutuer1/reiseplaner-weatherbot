# Vollständiger aktualisierter Code mit GPT-Währungsabfrage in Ortsinfo-Tab

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

# === Ortsinfo Tab ===
def render_local_info_tab(city, language):
    if city:
        geolocator = Nominatim(user_agent="reiseplaner")
        location = geolocator.geocode(city)
        if location:
            tf = TimezoneFinder()
            timezone = tf.timezone_at(lng=location.longitude, lat=location.latitude)
            time = datetime.now(pytz.timezone(timezone)).strftime("%H:%M:%S")
            st.metric("🕓 Lokale Uhrzeit", time)
        else:
            st.warning("Stadt konnte nicht gefunden werden.")
            time = "Unbekannt"

        # GPT-Währung ausgeben
        st.subheader("💱 Lokale Währung")
        currency_info = get_local_info_gpt(city, lang="de" if language == "Deutsch" else "en")
        st.info(currency_info)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

# === Streamlit UI ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter, Karte & Sehenswürdigkeiten")

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
        places = ["Altstadt", "Museum", "Park"]
        for place in places:
            st.markdown(f"[{place} in {city} auf Google ansehen](https://www.google.com/search?q={quote_plus(place + ' ' + city)})")
            if unsplash_key:
                image_url = get_unsplash_image(f"{place} {city}")
                if image_url:
                    st.image(image_url, caption=f"{place}", use_container_width=True)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

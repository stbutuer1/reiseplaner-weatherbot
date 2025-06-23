# Vollständiger aktualisierter Code mit:
# 1. Saisonale Reisetipps basierend auf Reisedatum
# 2. GPT-generierten Top-3-Sehenswürdigkeiten mit Bild & Google-Link

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

# === Bild von Unsplash holen ===
def get_unsplash_image(query):
    try:
        url = f"https://api.unsplash.com/photos/random?query={quote_plus(query)}&client_id={unsplash_key}"
        response = requests.get(url).json()
        return response["urls"]["regular"]
    except:
        return None

# === GPT-Währung ===
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

# === GPT-Hotels ===
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

# === GPT-Reisetipps mit Datum ===
def get_travel_tips(city, date, lang="de"):
    try:
        formatted_date = date.strftime("%d.%m.%Y") if lang == "de" else date.strftime("%B %d, %Y")
        prompt = {
            "de": f"Gib mir drei hilfreiche, saisonale Reisetipps für einen Städtetrip nach {city} in Europa für das Datum {formatted_date}.",
            "en": f"Give me three helpful, seasonal travel tips for a city trip to {city} in Europe on {formatted_date}."
        }[lang]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein freundlicher Reiseassistent."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Reisetipps: {e}"

# === GPT-Sehenswürdigkeiten ===
def get_top_sights(city, lang="de"):
    try:
        prompt = {
            "de": f"Nenne mir die drei bekanntesten Sehenswürdigkeiten in {city}. Nur den Namen, keine Beschreibung.",
            "en": f"List the three most famous sights in {city}. Names only, no description."
        }[lang]

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Reiseführer."},
                {"role": "user", "content": prompt}
            ]
        )
        lines = response.choices[0].message.content.strip().split("\n")
        sights = [line.strip().lstrip("0123456789.-• ").strip() for line in lines if line.strip()]
        return sights
    except Exception as e:
        return [f"❌ Fehler beim Abrufen der Sehenswürdigkeiten: {e}"]

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

# === Ortsinfo Tab ===
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

        tips = get_travel_tips(city, travel_date, lang="de" if language == "Deutsch" else "en")
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
        st.subheader(f"🎯 Top 3 Sehenswürdigkeiten in {city}")
        sights = get_top_sights(city, lang="de" if language == "Deutsch" else "en")
        for sight in sights:
            sight_url = f"https://www.google.com/search?q={quote_plus(sight + ' ' + city)}"
            st.markdown(f"[{sight}]({sight_url})")
            if unsplash_key:
                image_url = get_unsplash_image(f"{sight} {city}")
                if image_url:
                    st.image(image_url, caption=sight, use_container_width=True)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

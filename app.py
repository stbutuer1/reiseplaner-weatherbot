import streamlit as st
import openai
import requests
from datetime import datetime
import pytz
from fpdf import FPDF
from io import BytesIO
import folium
from streamlit_folium import st_folium

# === API Keys ===
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]

stadt_zeitzonen = {
    "Berlin": "Europe/Berlin",
    "Paris": "Europe/Paris",
    "Istanbul": "Europe/Istanbul",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Tokyo": "Asia/Tokyo",
    "Reutte": "Europe/Vienna",
}

# === Hilfsfunktionen ===
def get_local_info(city):
    stadt = city.strip().title()
    zeitzone = stadt_zeitzonen.get(stadt, "Europe/Berlin")
    now_local = datetime.now(pytz.timezone(zeitzone)).strftime("%H:%M:%S")
    waehrung = "EUR" if zeitzone.startswith("Europe") else "USD"
    return now_local, waehrung

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric&lang=de"
    response = requests.get(url).json()
    if "main" in response:
        return response["main"]["temp"], response["weather"][0]["description"]
    return None, "⚠️ Wetterdaten konnten nicht geladen werden."

def get_travel_tips(city, lang="de"):
    prompt = {
        "de": f"Gib mir drei kurze, hilfreiche Reisetipps für einen Städtetrip nach {city}.",
        "en": f"Give me three short, helpful travel tips for a city trip to {city}."
    }[lang]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def create_pdf(name, city, date, weather, tips):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, f"Reiseplaner für {name}", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, f"Reiseziel: {city}", ln=True)
    pdf.cell(200, 10, f"Datum: {date}", ln=True)
    pdf.multi_cell(0, 10, f"Wetter: {weather}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, f"Reisetipps:\n{tips}")
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

def get_google_map(city):
    map_url = f"https://www.google.com/maps/place/{city.replace(' ', '+')}"
    return map_url

def get_poi_links(city):
    poi_list = {
        "Paris": [
            ("Eiffelturm", "https://www.google.com/search?q=Eiffelturm"),
            ("Louvre Museum", "https://www.google.com/search?q=Louvre+Museum"),
            ("Kathedrale Notre-Dame de Paris", "https://www.google.com/search?q=Notre+Dame+Paris"),
            ("Triumphbogen", "https://www.google.com/search?q=Arc+de+Triomphe"),
            ("Montmartre-Basilika (Sacre-Coeur)", "https://www.google.com/search?q=Sacre+Coeur")
        ],
        "Reutte": [
            ("Burg Ehrenberg", "https://www.google.com/search?q=Burg+Ehrenberg+Reutte"),
            ("Highline179", "https://www.google.com/search?q=Highline+179+Reutte"),
            ("Alpentherme Ehrenberg", "https://www.google.com/search?q=Alpentherme+Reutte")
        ]
    }
    return poi_list.get(city, [])

def get_hotel_links(city):
    return [
        ("Hotel 1", f"https://www.google.com/search?q=Hotel+1+{city.replace(' ', '+')}"),
        ("Hotel 2", f"https://www.google.com/search?q=Hotel+2+{city.replace(' ', '+')}"),
        ("Hotel 3", f"https://www.google.com/search?q=Hotel+3+{city.replace(' ', '+')}")
    ]

# === App UI ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter & PDF")

tabs = st.tabs(["🎒 Planung", "🕓 Ortsinfo", "📄 PDF Export", "🏨 Hotels", "🗺️ Karte", "🎯 Sehenswürdigkeiten"])

with tabs[0]:
    lang = st.radio("Sprache wählen", ["Deutsch", "Englisch"])
    name = st.text_input("Dein Name")
    city = st.text_input("🌍 Reiseziel", placeholder="z. B. Paris, Reutte")
    date = st.date_input("📅 Reisedatum", value=datetime.now().date())

    if city:
        temp, desc = get_weather(city)
        weather_info = f"{temp:.1f}°C mit {desc}" if temp else desc
        st.success(weather_info)
        tips = get_travel_tips(city, lang="de" if lang == "Deutsch" else "en")
        st.info(tips)
    else:
        weather_info = ""
        tips = ""

with tabs[1]:
    if city:
        time, currency = get_local_info(city)
        st.metric("🕓 Uhrzeit", time)
        st.metric("💱 Währung", currency)
    else:
        st.info("Bitte gib zuerst ein Reiseziel an.")

with tabs[2]:
    email = st.text_input("E-Mail (optional)")
    if name and city and tips:
        pdf_file = create_pdf(name, city, date, weather_info, tips)
        st.download_button("⬇️ PDF herunterladen", pdf_file, file_name="Reiseplan.pdf")

with tabs[3]:
    if city:
        st.markdown("**📌 Booking-Link:**")
        st.markdown(f"[Hotels in {city} auf Booking.com](https://www.booking.com/searchresults.de.html?ss={city.replace(' ', '+')})")
        st.markdown("---")
        st.markdown("**🏨 Hotelvorschläge:**")
        for name, url in get_hotel_links(city):
            st.markdown(f"[🔗 {name} in {city}]({url})")

with tabs[4]:
    if city:
        lat, lon = 48.8566, 2.3522  # default Paris
        map_ = folium.Map(location=[lat, lon], zoom_start=12)
        folium.Marker([lat, lon], tooltip=city).add_to(map_)
        st_folium(map_, height=400)

with tabs[5]:
    if city:
        st.subheader(f"🎯 Sehenswürdigkeiten in {city}")
        poi_links = get_poi_links(city)
        for name, link in poi_links:
            st.markdown(f"- [🔎 {name} auf Google ansehen]({link})")

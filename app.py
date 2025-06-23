import streamlit as st
import openai
import requests
from datetime import datetime
import pytz
from fpdf import FPDF
from io import BytesIO

# === API Keys ===
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]

# === Stadt-Zeitzonen für Uhrzeit und Währung ===
stadt_zeitzonen = {
    "Berlin": "Europe/Berlin",
    "Paris": "Europe/Paris",
    "Istanbul": "Europe/Istanbul",
    "London": "Europe/London",
    "New York": "America/New_York",
    "Tokyo": "Asia/Tokyo",
    "Reutte": "Europe/Vienna",
}

def get_local_info(city):
    stadt = city.strip().title()
    zeitzone = stadt_zeitzonen.get(stadt, "Europe/Berlin")
    now_local = datetime.now(pytz.timezone(zeitzone)).strftime("%H:%M:%S")
    waehrung = "EUR" if zeitzone.startswith("Europe") else "USD"
    return now_local, waehrung

# === Wetterdaten ===
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric&lang=de"
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

# === PDF-Erstellung ===
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

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# === App UI ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter & PDF")

# === Tabs ===
tabs = st.tabs(["🎒 Planung", "🕓 Ortsinfo", "📄 PDF Export"])

with tabs[0]:
    language = st.radio("🌍 Sprache", ["Deutsch", "Englisch"], horizontal=True)
    name = st.text_input("Dein Name")
    city = st.text_input("Reiseziel", placeholder="z. B. Paris, Reutte, Istanbul")
    travel_date = st.date_input("📅 Reisedatum", value=datetime.now().date())

    if city:
        temp, desc = get_weather(city)
        if isinstance(temp, float):
            weather_info = f"{temp:.1f}°C mit {desc}" if language == "Deutsch" else f"{temp:.1f}°C with {desc}"
            st.success(weather_info)
        else:
            weather_info = desc
            st.warning(desc)

        tips = get_travel_tips(city, lang="de" if language == "Deutsch" else "en")
        st.info(tips)
    else:
        weather_info = ""
        tips = ""

with tabs[1]:
    if city:
        time, currency = get_local_info(city)
        st.metric("🕓 Lokale Uhrzeit", time)
        st.metric("💱 Währung", currency)
    else:
        st.info("Bitte zuerst ein Reiseziel eingeben.")

with tabs[2]:
    if city and tips and name:
        if st.button("📄 PDF erstellen"):
            pdf_data = create_pdf(name, city, travel_date, weather_info, tips)
            st.download_button("⬇️ PDF herunterladen", pdf_data, file_name="Reiseplan.pdf")
    else:
        st.warning("Bitte gib Name, Reiseziel und Datum ein, um eine PDF zu erstellen.")

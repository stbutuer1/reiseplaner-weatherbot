import streamlit as st
import openai
import requests
from datetime import datetime
import pytz
from fpdf import FPDF
from io import BytesIO
import smtplib
from email.message import EmailMessage
import folium
from streamlit_folium import st_folium

# === API Keys ===
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]
EMAIL_ADDRESS = st.secrets.get("EMAIL_ADDRESS")
EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD")

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

def send_email(receiver_email, pdf_buffer):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return "❌ E-Mail-Zugangsdaten fehlen. Bitte in den Secrets eintragen."
    try:
        msg = EmailMessage()
        msg['Subject'] = "Dein Reiseplaner als PDF"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = receiver_email
        msg.set_content("Im Anhang findest du deinen individuellen Reiseplan.")

        msg.add_attachment(pdf_buffer.read(), maintype='application', subtype='pdf', filename='Reiseplan.pdf')
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        return "✅ E-Mail erfolgreich versendet."
    except Exception as e:
        return f"❌ Fehler beim Senden der E-Mail: {e}"

def get_sights(city, lang="de"):
    try:
        prompt = {
            "de": f"Nenne mir fünf bekannte Sehenswürdigkeiten in {city}. Gib nur die Namen in einer nummerierten Liste.",
            "en": f"Name five famous tourist attractions in {city}. Just list the names as a numbered list."
        }[lang]
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a travel assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        text = response.choices[0].message.content
        return [line.split(". ", 1)[1] for line in text.split("\n") if ". " in line]
    except Exception as e:
        return [f"Fehler: {e}"]

def get_city_coordinates(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={city}"
        res = requests.get(url).json()
        lat = float(res[0]["lat"])
        lon = float(res[0]["lon"])
        return lat, lon
    except:
        return 48.1374, 11.5755  # München Fallback

# === UI Setup ===
st.set_page_config(page_title="Reiseplaner", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit KI, Wetter & PDF")

tabs = st.tabs(["🎒 Planung", "🕓 Ortsinfo", "📄 PDF Export", "🏨 Hotels", "🗺️ Karte", "🎯 Sehenswürdigkeiten"])

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
    email = st.text_input("📧 E-Mail-Adresse eingeben")
    if city and tips and name and email:
        if st.button("📄 PDF erstellen und senden"):
            pdf_data = create_pdf(name, city, travel_date, weather_info, tips)
            st.download_button("⬇️ PDF herunterladen", pdf_data, file_name="Reiseplan.pdf")
            status = send_email(email, pdf_data)
            st.success(status)
    else:
        st.warning("Bitte gib Name, Reiseziel, Datum und E-Mail-Adresse ein, um eine PDF zu erstellen und zu senden.")

with tabs[3]:
    if city:
        st.header(f"🏨 Hotels in {city}")
        st.image(f"https://source.unsplash.com/800x400/?hotel,{city}", caption=f"Hotels in {city}")
        st.markdown(f"[🔗 Hotels suchen](https://www.booking.com/searchresults.html?ss={city})", unsafe_allow_html=True)

with tabs[4]:
    if city:
        st.header(f"🗺️ Stadtkarte von {city}")
        st.image(f"https://source.unsplash.com/800x400/?map,{city}", caption=f"{city}")
        st.markdown(f"[📍 {city} bei Google Maps ansehen](https://www.google.com/maps/search/{city})", unsafe_allow_html=True)

with tabs[5]:
    if city:
        st.header(f"🎯 Sehenswürdigkeiten in {city}")
        sights = get_sights(city, lang="de" if language == "Deutsch" else "en")

        for sight in sights:
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(f"https://source.unsplash.com/400x300/?{sight}+{city}", caption=sight)
            with col2:
                url = f"https://www.google.com/search?q={sight.replace(' ', '+')}+{city}"
                st.markdown(f"[🔎 {sight} auf Google ansehen]({url})", unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🗺️ Interaktive Karte")

        lat, lon = get_city_coordinates(city)
        m = folium.Map(location=[lat, lon], zoom_start=13)
        folium.Marker([lat, lon], tooltip=city).add_to(m)
        st_folium(m, height=400)
    else:
        st.info("Bitte gib zuerst eine Stadt im Planungstab ein.")

import streamlit as st
import openai
import requests
from datetime import datetime

# 🔐 API-Keys
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
weather_api_key = st.secrets["WEATHER_API_KEY"]

# 🌤 Wetter abrufen
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

# ✈️ GPT-Reisetipps
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

# 🌍 Sprache
st.set_page_config(page_title="Reiseplaner-Bot", page_icon="🌤️")

# 🎛 Sidebar
st.sidebar.title("🔍 Reiseoptionen")
language = st.sidebar.radio("🌍 Sprache wählen", ["Deutsch", "Englisch"])
today = datetime.now().date()
travel_date = st.sidebar.date_input("📅 Reisedatum wählen", value=today)

st.sidebar.markdown("---")
city = st.sidebar.text_input("🌆 Reiseziel eingeben", placeholder="z. B. Rom, Paris, Istanbul")

if city:
    # 🔗 Transport-Links
    st.sidebar.markdown("**🚉 Anreiseoptionen**")
    st.sidebar.markdown("[🚆 Deutsche Bahn](https://reiseauskunft.bahn.de)", unsafe_allow_html=True)
    st.sidebar.markdown(f"[✈️ Flüge nach {city} (Skyscanner)](https://www.skyscanner.de/transport/fluge-nach/{city})", unsafe_allow_html=True)

    # 🖼️ Bild aus Unsplash
    st.sidebar.image(f"https://source.unsplash.com/400x300/?{city}", caption=f"{city}", use_column_width=True)

    # 🔗 Weitere Links
    st.sidebar.markdown("**🔗 Weitere Links**")
    st.sidebar.markdown(f"[🏨 Hotels in {city}](https://www.booking.com/searchresults.html?ss={city})", unsafe_allow_html=True)
    st.sidebar.markdown(f"[🗺️ {city} auf Google Maps](https://www.google.com/maps/search/{city})", unsafe_allow_html=True)
    st.sidebar.markdown(f"[🎯 Tripadvisor: {city}](https://www.tripadvisor.de/Search?q={city})", unsafe_allow_html=True)

    # 🌐 Info: Uhrzeit & Währung (symbolisch)
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🌍 Ortsinfo (symbolisch)**")
    st.sidebar.markdown("🕒 Lokale Uhrzeit: wird angepasst")  # Placeholder
    st.sidebar.markdown("💱 Währung: z. B. EUR")

st.sidebar.markdown("---")
st.sidebar.info("Gib ein Reiseziel und Datum ein, um Tipps & Wetter zu erhalten.")

# 🧠 Hauptbereich
st.title("🌤️ Reiseplaner-Bot mit Wetter, Sprache & KI")

if city:
    temp, weather = get_weather(city)

    if isinstance(temp, float):
        if language == "Deutsch":
            st.success(f"In {city} ist es aktuell {temp:.1f}°C mit {weather}.")
        else:
            st.success(f"The current weather in {city} is {temp:.1f}°C with {weather}.")
    else:
        st.warning(weather)

    with st.spinner("🔄 Lade Reisetipps..."):
        tips = get_travel_tips(city, lang="de" if language == "Deutsch" else "en")
    st.info(tips)

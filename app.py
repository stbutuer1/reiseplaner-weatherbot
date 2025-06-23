import streamlit as st
import openai
import requests

# 🔐 API-Keys aus Streamlit Cloud
client = openai.OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)
weather_api_key = st.secrets["WEATHER_API_KEY"]

# 🌤 Wetter abrufen von OpenWeather
def get_weather(city):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric&lang=de"
        response = requests.get(url).json()
        if "main" in response:
            temp = response["main"]["temp"]
            desc = response["weather"][0]["description"]
            return f"In {city} ist es aktuell {temp}°C mit {desc}."
        elif "message" in response:
            return f"⚠️ Fehler: {response['message']}"
        else:
            return "⚠️ Unbekannter Fehler bei der Wetterabfrage."
    except Exception as e:
        return f"❌ Fehler beim Abrufen der Wetterdaten: {e}"

# ✈️ Reisetipps mit GPT-3.5
def get_travel_tips(city):
    try:
        prompt = f"Gib mir drei kurze, hilfreiche Reisetipps für einen Städtetrip nach {city} in Europa."
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

# 🌐 Streamlit UI
st.set_page_config(page_title="Reiseplaner mit Wetter", page_icon="🌍")
st.title("🌤️ Reiseplaner-Bot mit Wetter & KI")

# Seitenleiste (Sidebar)
st.sidebar.title("🔍 Weitere Infos")
st.sidebar.markdown("**🔗 Nützliche Links**")

# Platzhalter für Links – nur wenn eine Stadt eingegeben ist
city = st.text_input("🌍 Wohin möchtest du reisen?", placeholder="z. B. Rom, Paris, Istanbul")

if city:
    # Dynamische Links basierend auf Stadt
    st.sidebar.markdown(f"[🏨 Hotels in {city} (Booking.com)](https://www.booking.com/searchresults.html?ss={city})", unsafe_allow_html=True)
    st.sidebar.markdown(f"[📍 {city} bei Google Maps](https://www.google.com/maps/search/{city})", unsafe_allow_html=True)
    st.sidebar.markdown(f"[🎯 Sehenswürdigkeiten in {city} (Tripadvisor)](https://www.tripadvisor.de/Search?q={city})", unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("**🌍 Sprache** (nicht aktiv)")
st.sidebar.radio("Sprache wählen", ["Deutsch", "Englisch"], index=0)

st.sidebar.markdown("---")
st.sidebar.info("💡 Gib oben eine Stadt ein und erhalte sofort Wetter & Reisetipps!")

# Hauptinhalt
if city:
    with st.spinner("🔄 Wetter wird geladen..."):
        weather = get_weather(city)
    st.success(weather)

    with st.spinner("🔄 Reisetipps werden geladen..."):
        tips = get_travel_tips(city)
    st.info(tips)

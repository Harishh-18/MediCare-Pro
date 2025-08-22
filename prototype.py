import streamlit as st
import google.generativeai as genai
import tempfile
import speech_recognition as sr
from PyPDF2 import PdfReader
from gtts import gTTS
from PIL import Image

# -------------------------------
# CONFIG (Google Gemini API key)
# -------------------------------
genai.configure(api_key="AIzaSyC1tDObPc_6SCDiMfM2bH85qMr0KzE4M58")

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-flash")

# -------------------------------
# Helper Functions
# -------------------------------

def extract_text_from_pdf(file):
    pdf = PdfReader(file)
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
    return text

def transcribe_audio(file):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file) as source:
        audio_data = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Speech recognition service error."

def record_from_microphone():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now (max 10s)...")
        audio_data = recognizer.listen(source, timeout=5, phrase_time_limit=10)
    try:
        return recognizer.recognize_google(audio_data)
    except sr.UnknownValueError:
        return "Could not understand the audio."
    except sr.RequestError:
        return "Speech recognition service error."

# ✅ Use Gemini for text or image input
def get_ai_response(user_input=None, image_file=None):
    try:
        if image_file:
            img = Image.open(image_file)
            response = model.generate_content(
                [
                    "You are a helpful medical assistant. Analyze the image for educational purposes only. Do NOT provide professional medical advice.",
                    img
                ]
            )
        else:
            response = model.generate_content(
                f"You are a helpful medical assistant. Provide only educational information, not professional medical advice.\n\nUser: {user_input}"
            )
        return response.text
    except Exception as e:
        return f"Error: {e}"

def text_to_speech(text):
    tts = gTTS(text)
    temp_audio = "response.mp3"
    tts.save(temp_audio)
    return temp_audio

# -------------------------------
# Streamlit UI
# -------------------------------
st.set_page_config(page_title="MediCare Chatbot", page_icon="💊", layout="wide")

st.title("💊 MediCare Chatbot with Voice & Image (Gemini API)")

uploaded_file = st.file_uploader("📂 Upload (PDF, TXT, WAV, MP3, PNG, JPEG)",
                                 type=["pdf", "txt", "wav", "mp3", "png", "jpeg", "jpg"])
file_text = ""
image_file = None

if uploaded_file:
    if uploaded_file.type == "application/pdf":
        file_text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.type == "text/plain":
        file_text = uploaded_file.read().decode("utf-8")
    elif "audio" in uploaded_file.type:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(uploaded_file.read())
            audio_path = temp_file.name
        file_text = transcribe_audio(audio_path)
    elif "image" in uploaded_file.type:
        image_file = uploaded_file
        st.image(image_file, caption="🩺 Uploaded Medical Image", use_container_width=True)

if file_text:
    st.subheader("📄 Extracted/Transcribed Content:")
    st.write(file_text)

if st.button("🎤 Record from Microphone"):
    spoken_text = record_from_microphone()
    st.subheader("🗣️ You said:")
    st.write(spoken_text)
    file_text = spoken_text

user_input = st.text_area("💬 Enter your question:", height=100)

if st.button("Ask AI"):
    if user_input or file_text or image_file:
        query = user_input if user_input else file_text
        response = get_ai_response(query, image_file)
        st.subheader("🤖 AI Response:")
        st.write(response)

        audio_file = text_to_speech(response)
        st.audio(audio_file, format="audio/mp3")
    else:
        st.warning("Please enter a question or upload a file/voice/image.")

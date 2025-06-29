# streamlit_tts_app.py
# Sintesis de Voz Multilingüe con Streamlit
# Requisitos: pip install streamlit edge-tts

import time
import asyncio
import subprocess
import sys
from pathlib import Path
import streamlit as st

# Asegurar que edge-tts esté instalado
try:
    import edge_tts
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "edge-tts"])
    import edge_tts

# Voces agrupadas
groups = {
    "Español": {
        "es-ES-ElviraNeural": "Elvira (es-ES fem.)",
        "es-ES-AlbaNeural": "Alba (es-ES fem.)",
        "es-ES-AlvaroNeural": "Álvaro (es-ES masc.)",
    },
    "Inglés (US)": {
        "en-US-JennyNeural": "Jenny (en-US fem.)",
        "en-US-BrandonNeural": "Brandon (en-US masc.)",
    },
    "Inglés (UK)": {
        "en-GB-LibbyNeural": "Libby (en-GB fem.)",
        "en-GB-RyanNeural": "Ryan (en-GB masc.)",
    },
    "Alemán": {
        "de-DE-KatjaNeural": "Katja (de-DE fem.)",
        "de-DE-ConradNeural": "Conrad (de-DE masc.)",
    },
    "Portugués": {
        "pt-PT-RaquelNeural": "Raquel (pt-PT fem.)",
        "pt-BR-AntonioNeural": "Antônio (pt-BR masc.)",
    },
}

# Aplanar opciones con etiqueta de grupo
voice_options = []
for group, voices in groups.items():
    for key, label in voices.items():
        voice_options.append((f"{group} — {label}", key))

# Valores por defecto
default_text = "Hola, esto es una prueba de síntesis de voz."
default_voice = "es-ES-ElviraNeural"

# Configuración de página
st.set_page_config(page_title="TTS Multilingüe", layout="centered")
st.title("🎙️ Síntesis de Voz Multilingüe")

# Área de texto
text = st.text_area("Introduce tu texto…", value=default_text, height=150)

# Selector de voz
def format_option(option):
    return option[0]

voice_choice = st.selectbox(
    "Elige una voz:",
    options=voice_options,
    format_func=format_option,
    index=[label for label, key in voice_options].index(next(label for label, key in voice_options if key == default_voice))
)[1]

# Botón de generación\if st.button("Generar audio"):
tmp_path = Path("tts_temp.mp3")
with st.spinner("Generando audio…"):
    asyncio.run(edge_tts.Communicate(text=text, voice=voice_choice).save(tmp_path))
ts = int(time.time())
audio_bytes = tmp_path.read_bytes()
st.audio(audio_bytes, format="audio/mp3")
st.success("✅ Audio listo")
st.markdown(f"[⬇️ Descargar MP3](tts_temp.mp3?t={ts})")

# Nota: En despliegues gestionados, revisa el manejo de archivos temporales según la plataforma.

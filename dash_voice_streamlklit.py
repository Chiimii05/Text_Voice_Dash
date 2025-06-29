# streamlit_tts_app.py
# Sintesis de Voz Multilingüe con Streamlit
# Requisitos: pip install streamlit edge-tts

import time
import asyncio
from pathlib import Path
import streamlit as st

# Intentar importar edge-tts y mostrar mensaje si no está instalado
try:
    import edge_tts
except ImportError:
    st.error("El paquete 'edge-tts' no está instalado. Por favor, ejecuta 'pip install edge-tts' en tu entorno.")
    st.stop()

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
voice_options = [(f"{grp} — {lbl}", key) for grp, vs in groups.items() for key, lbl in vs.items()]

# Valores por defecto
default_text = "Hola, esto es una prueba de síntesis de voz."
default_voice = "es-ES-ElviraNeural"

# Configuración de página
st.set_page_config(page_title="TTS Multilingüe", layout="centered")
st.title("🎙️ Síntesis de Voz Multilingüe")

# Área de texto
text = st.text_area("Introduce tu texto…", value=default_text, height=150)

# Selector de voz
voice_labels = [lbl for lbl, _ in voice_options]
voice_keys = [key for _, key in voice_options]
def format_option(label, idx): return label

selected_idx = voice_keys.index(default_voice) if default_voice in voice_keys else 0
choice = st.selectbox("Elige una voz:", options=voice_labels, index=selected_idx)
voice_choice = voice_keys[voice_labels.index(choice)]

# Generar audio al pulsar
if st.button("Generar audio"):
    tmp_path = Path("tts_temp.mp3")
    with st.spinner("Generando audio…"):
        asyncio.run(edge_tts.Communicate(text=text, voice=voice_choice).save(tmp_path))
    audio_bytes = tmp_path.read_bytes()
    st.audio(audio_bytes, format="audio/mp3")
    st.success("✅ Audio listo")
    ts = int(time.time())
    st.markdown(f"[⬇️ Descargar MP3](tts_temp.mp3?t={ts})")

# Nota: En plataformas gestionadas, maneja los archivos temporales según la plataforma.

# streamlit_tts_app.py
# Síntesis de Voz Multilingüe con Streamlit
# Requisitos: pip install streamlit edge-tts

import time
import asyncio
from pathlib import Path
import base64
import streamlit as st
import streamlit.components.v1 as components

# Voces agrupadas
groups = {
    "Español": {
        "es-ES-ElviraNeural": "Elvira (es-ES fem.)",
        "es-ES-XimenaNeural": "Ximena (es-ES fem.)",
        "es-ES-AlvaroNeural": "Álvaro (es-ES masc.)",
    },
    "Inglés (US)": {
        "en-US-JennyNeural": "Jenny (en-US fem.)",
        "en-US-ChristopherNeural": "Christopher (en-US masc., narración)",
        "en-US-AndrewNeural": "Andrew (en-US masc.)",
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
selected_idx = voice_keys.index(default_voice) if default_voice in voice_keys else 0
choice = st.selectbox("Elige una voz:", options=voice_labels, index=selected_idx)
voice_choice = voice_keys[voice_labels.index(choice)]

# Generar audio al pulsar
if st.button("Generar audio"):
    # Intentar importar edge-tts
    try:
        import edge_tts
    except ImportError:
        st.error(
            '''⚠️ El paquete 'edge-tts' no está instalado en tu entorno de ejecución.
Por favor, instala las dependencias antes de reiniciar la app ejecutando:

    pip install edge-tts
'''        )
        st.stop()

    # Generar y guardar MP3 temporal
    tmp_path = Path("tts_temp.mp3")
    with st.spinner("Generando audio…"):
        asyncio.run(
            edge_tts.Communicate(text=text, voice=voice_choice).save(tmp_path)
        )

    # Leer bytes
    audio_bytes = tmp_path.read_bytes()

    # Mostrar reproductor
    st.audio(audio_bytes, format="audio/mp3")
    st.success("✅ Audio listo")

    # Auto-descarga usando un link oculto y JS
    b64 = base64.b64encode(audio_bytes).decode()
    dl_html = f"<a id='dl' href='data:audio/mp3;base64,{b64}' download='tts.mp3'></a>"
    dl_html += "<script>document.getElementById('dl').click();</script>"
    components.html(dl_html)

# Nota: En plataformas gestionadas, maneja archivos temporales según la plataforma.

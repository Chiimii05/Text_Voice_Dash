#!/usr/bin/env python3
"""
Dash TTS multilingüe — v11 (audio servido para duración y descarga)
────────────────────────────────────────────────────────────────
• El audio ya no se incrusta en base64; tanto el reproductor como el enlace
  de descarga usan la ruta `/download` con bust de caché.
• Esto permite que el navegador muestre correctamente la duración y guarde el fichero
  en la carpeta Descargas.
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Dependencias
REQUIREMENTS = {
    "dash": "dash>=2.8",
    "edge_tts": "edge-tts>=6.1.5",
}
MIN_DBC_VERSION = "1.3.0"

# Verificar e instalar módulos
try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata
from packaging.version import parse as vparse

for mod, spec in REQUIREMENTS.items():
    try:
        __import__(mod)
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", spec])

try:
    import dash_bootstrap_components as dbc
    if vparse(metadata.version("dash_bootstrap_components")) < vparse(MIN_DBC_VERSION):
        raise ModuleNotFoundError
except ModuleNotFoundError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", f"dash-bootstrap-components>={MIN_DBC_VERSION}"])
    import dash_bootstrap_components as dbc

# Import principal
import dash
from dash import dcc, html, Output, Input, State, ctx
from flask import send_file
import edge_tts

# Voces agrupadas
GROUPS = {
    "Español": {
        "es-ES-ElviraNeural": "🎙️ Elvira (es-ES fem.)",
        "es-ES-XimenaNeural": "🎙️ Ximena (es-ES fem.)",
        "es-ES-AlvaroNeural": "🎙️ Álvaro (es-ES masc.)",
    },
    "Inglés (US)": {
        "en-US-JennyNeural": "🎙️ Jenny (en-US fem.)",
        "en-US-ChristopherNeural": "🎙️ Christopher (en-US masc., narración)",
        "en-US-AndrewNeural": "🎙️ Andrew (en-US masc.)",
        "en-US-AriaNeural": "🎙️ Aria (en-US fem., narración)",
    },
    "Inglés (UK)": {
        "en-GB-LibbyNeural": "🎙️ Libby (en-GB fem.)",
        "en-GB-RyanNeural": "🎙️ Ryan (en-GB masc.)",
    },
    "Alemán": {
        "de-DE-KatjaNeural": "🎙️ Katja (de-DE fem.)",
        "de-DE-ConradNeural": "🎙️ Conrad (de-DE masc.)",
    },
    "Portugués": {
        "pt-PT-RaquelNeural": "🎙️ Raquel (pt-PT fem.)",
        "pt-BR-AntonioNeural": "🎙️ Antônio (pt-BR masc.)",
    },
}
DEFAULT_VOICE = "es-ES-ElviraNeural"
TEXTO_DEMO = "Hola, esto es una prueba de síntesis de voz."

# Construir opciones del selector
options = []
for cat, voices in GROUPS.items():
    options.append({"label": f"── {cat} ──", "value": f"hdr_{cat}", "disabled": True})
    for key, label in voices.items():
        options.append({"label": label, "value": key})

# Crear app
app = dash.Dash(
    __name__,
    title="TTS Multilingüe",
    external_stylesheets=[
        dbc.themes.MINTY,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css",
    ],
)

# Layout
header = dbc.Row(dbc.Col(
    dbc.Card(dbc.CardBody(html.H2([
        html.I(className="fa-solid fa-wave-square me-2"),
        "Síntesis de Voz Multilingüe",
    ], className="card-title text-center mb-0")), className="shadow-sm border-0"), width=12))

controls = dbc.Row([
    dbc.Col(dbc.FormFloating([
        dbc.Textarea(id="texto", value=TEXTO_DEMO, style={"height": "120px"}, className="border-0 shadow-sm"),
        dbc.Label("Introduce tu texto…"),
    ]), md=12, className="mb-3"),
    dbc.Col(dbc.RadioItems(id="voz", options=options, value=DEFAULT_VOICE, inline=False,
                           style={"maxHeight": "320px", "overflowY": "auto"}, className="my-2",
                           input_class_name="me-2", label_checked_class_name="fw-semibold text-primary"),
             md=12, className="mb-3"),
    dbc.Col(dbc.Button("Generar audio", id="generar", color="primary", className="w-100",
                       style={"fontSize": "1.1rem"}), md=12),
])

audio_card = dbc.Card(dbc.CardBody(dcc.Loading(type="circle", children=html.Div(id="salida", className="text-center"))),
                      className="shadow border-0 mt-4")
app.layout = dbc.Container([header, html.Hr(), controls, dbc.Row(dbc.Col(audio_card, width=12))],
                           fluid=True, className="py-4")

# Callback: genera y muestra audio con duración real
@app.callback(
    Output("salida", "children"),
    Input("generar", "n_clicks"),
    State("texto", "value"),
    State("voz", "value"),
    prevent_initial_call=True,
)
def sintetizar(_, texto, voice_key):
    if ctx.triggered_id != "generar":
        raise dash.exceptions.PreventUpdate

    # Generar y guardar MP3
    tmp_mp3 = Path("tts_temp.mp3")
    asyncio.run(edge_tts.Communicate(text=texto, voice=voice_key).save(tmp_mp3))

    # Parámetro para bust de caché
    ts = int(time.time())
    audio_url = f"/download?t={ts}"

    # Componentes: reproductor y descarga
    audio_tag = html.Audio(src=audio_url, controls=True, style={"width": "100%"}, preload="metadata")
    download_btn = html.A("⬇️ Descargar MP3", href=audio_url, download="tts.mp3", className="btn btn-success mt-3")
    status = html.P("✅ Audio listo", className="mt-2")

    return [audio_tag, download_btn, status]

# Ruta Flask para servir el archivo
@app.server.route('/download')
def download_mp3():
    return send_file("tts_temp.mp3", mimetype="audio/mpeg", as_attachment=True, download_name="tts.mp3")

# Ejecutar servidor
if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)  # solo este PC; run_server ya no existe desde Dash 3

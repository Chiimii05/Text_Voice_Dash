#!/usr/bin/env python3
"""
Dash TTS multilingüe — v10 (ajuste final)
──────────────────────────────────────
• Se elimina el parámetro incorrecto `output_format` de Communicate(),
  usando la configuración por defecto de edge-tts (genera MP3 automáticamente).
• Se mantiene el enlace de descarga y el reproductor en Dash.
"""

import base64
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

# Comprueba e instala/actualiza si falta alguno
try:
    import importlib.metadata as metadata
except ImportError:
    import importlib_metadata as metadata  # type: ignore
from packaging.version import parse as vparse

for mod, spec in REQUIREMENTS.items():
    try:
        __import__(mod)
    except ModuleNotFoundError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", spec])

# dash-bootstrap-components y Flask for download
import dash  # servidor de la app
import dash_bootstrap_components as dbc  # componentes de Bootstrap para Dash
from flask import send_file  # para servir descargas
from dash import dcc, html, Output, Input, State, ctx
import edge_tts  # síntesis de voz

# Verificar versión mínima de dash-bootstrap-components
try:
    if vparse(metadata.version("dash_bootstrap_components")) < vparse(MIN_DBC_VERSION):
        raise ModuleNotFoundError
except ModuleNotFoundError:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--quiet", "--upgrade",
        f"dash-bootstrap-components>={MIN_DBC_VERSION}"    
    ])
    import importlib
    dbc = importlib.import_module("dash_bootstrap_components")

# Voces agrupadas
GROUPS = {
    "Español": {
        "es-ES-ElviraNeural": "🎙️ Elvira (es-ES fem.)",
        "es-ES-AlbaNeural": "🎙️ Alba (es-ES fem.)",
        "es-ES-AlvaroNeural": "🎙️ Álvaro (es-ES masc.)",
    },
    "Inglés (US)": {
        "en-US-JennyNeural": "🎙️ Jenny (en-US fem.)",
        "en-US-BrandonNeural": "🎙️ Brandon (en-US masc.)",
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

audio_card = dbc.Card(dbc.CardBody(dcc.Loading(type="circle", children=html.Div(id="salida", className="text-center"))), className="shadow border-0 mt-4")
app.layout = dbc.Container([header, html.Hr(), controls, dbc.Row(dbc.Col(audio_card, width=12))], fluid=True, className="py-4")

# Callback
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

    # Generar audio
    tmp_mp3 = Path("tts_temp.mp3")
    asyncio.run(edge_tts.Communicate(text=texto, voice=voice_key).save(tmp_mp3))

    # Codificar a base64
    b64_audio = base64.b64encode(tmp_mp3.read_bytes()).decode()
    ts = int(time.time())
    data_uri = f"data:audio/mpeg;base64,{b64_audio}?v={ts}"

    # Crear componentes
    audio_tag = html.Audio(src=data_uri, controls=True, style={"width": "100%"})
    # Link de descarga directo al servidor
    download_btn = html.A(
        "⬇️ Descargar MP3",
        href="/download",
        className="btn btn-success mt-3",
    )
    status = html.P("✅ Audio listo", className="mt-2")

    return [audio_tag, download_btn, status]

# Ruta para servir archivo MP3 y forzar descarga en carpeta Descargas
@app.server.route('/download')
def download_mp3():
    # Envía el último archivo generado como descarga
    return send_file(
        "tts_temp.mp3",
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name="tts.mp3"
    )

# Ejecutar servidor
if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8050)

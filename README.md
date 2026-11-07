# Dash TTS Multilingüe v11

Una aplicación web de síntesis de voz multilingüe basada en Dash y Edge TTS, que ofrece audio servido para obtener la duración correcta y descarga del fichero MP3.

---

## 📋 Características

* 🎤 Síntesis de texto a voz en múltiples idiomas (Español, Inglés US/UK, Alemán, Portugués).
* 🔄 Audio servido mediante endpoint `/download` con bust de caché para:

  * Mostrar la duración real en el reproductor de audio.
  * Permitir la descarga del archivo MP3 en la carpeta de Descargas.
* 🛠️ Interfaz moderna construida con Dash, Dash Bootstrap Components y Font Awesome.
* 🚀 Instalación automática de dependencias faltantes al inicio.

## 📦 Requisitos

* Python 3.7+
* Módulos:

  * dash >= 2.8
  * dash-bootstrap-components >= 1.3.0
  * edge-tts >= 6.1.5
  * packaging (para comparar versiones)
  * flask (se instala con Dash)

## 🚀 Instalación y ejecución

1. **Clona el repositorio**

   ```bash
   git clone https://github.com/Chiimii05/Text_Voice_Dash.git
   cd Text_Voice_Dash
   pip install -r requirements.txt
   ```

2. **Ejecuta la aplicación**

   ```bash
   # El script instala automáticamente las dependencias faltantes
   python dash_voice.py
   ```

3. **Abre en el navegador**

   * Visita `http://localhost:8050`.

## ⚙️ Uso

1. Ingresa el texto que deseas sintetizar en el área de texto.
2. Selecciona la voz deseada del listado (agrupado por idioma y género).
3. Haz clic en **Generar audio**.
4. El reproductor mostrará la duración real; también podrás descargar el MP3.

## 🗣️ Voces disponibles

| Idioma      | Voz (clave)           | Descripción             |
| ----------- | --------------------- | ----------------------- |
| Español     | `es-ES-ElviraNeural`  | 🎙️ Elvira (femenina)   |
|             | `es-ES-XimenaNeural`  | 🎙️ Ximena (femenina)     |
|             | `es-ES-AlvaroNeural`  | 🎙️ Álvaro (masculina)  |
| Inglés (US) | `en-US-ChristopherNeural` | 🎙️ Christopher (masculina, narración) |
|             | `en-US-AndrewNeural`  | 🎙️ Andrew (masculina)  |
|             | `en-US-AriaNeural`    | 🎙️ Aria (femenina, narración) |
|             | `en-US-JennyNeural`   | 🎙️ Jenny (femenina)    |
| Inglés (UK) | `en-GB-LibbyNeural`   | 🎙️ Libby (femenina)    |
|             | `en-GB-RyanNeural`    | 🎙️ Ryan (masculina)    |
| Alemán      | `de-DE-KatjaNeural`   | 🎙️ Katja (femenina)    |
|             | `de-DE-ConradNeural`  | 🎙️ Conrad (masculina)  |
| Portugués   | `pt-PT-RaquelNeural`  | 🎙️ Raquel (femenina)   |
|             | `pt-BR-AntonioNeural` | 🎙️ Antônio (masculina) |

## 🎬 Voz de un vídeo entero: `voz_escenas.py`

Convierte un guion completo en audio, escena por escena, con subtítulos. Es lo que usa el canal de YouTube.

```bash
python voz_escenas.py <carpeta del vídeo>             # lee locucion.md y genera lo que falte o haya cambiado
python voz_escenas.py <carpeta> --escena 01           # una sola escena, para escucharla
python voz_escenas.py <carpeta> --solo-contar         # no genera nada
python voz_escenas.py --ver-voces en                  # voces disponibles de un idioma
python voz_escenas.py --muestra "Texto" --voz en-US-AndrewNeural --velocidad -5%
```

* **Entrada:** `locucion.md`, una escena por cada `## 01`, `## 02`… con el texto tal cual se lee.
* **Salida** en `voz/`: `escena-<id>.mp3` y `.srt` por escena, `locucion-completa.mp3` y `.srt` (con ffmpeg) y `registro.csv`.
* Si una escena no ha cambiado (texto, voz, velocidad y tono), no se vuelve a generar.
* Reintenta solo cuando el servicio falla de forma puntual.
* La voz, la velocidad y el tono por defecto están en `voces.json`.
* No hace falta cuenta ni clave, pero sí conexión a internet: las voces son el servicio de lectura en voz alta de Microsoft Edge.
* Pruebas: `python -m unittest test_voz_escenas`.

## 🔧 Personalización

* Para cambiar el tema de Bootstrap, edita `external_stylesheets` en `dash_voice.py`.
* Modifica `TEXTO_DEMO` y `DEFAULT_VOICE` para ajustar texto y voz predeterminados.
* Añade o quita voces editando el diccionario `GROUPS`.

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

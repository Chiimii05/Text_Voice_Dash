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
   git clone https://github.com/tu_usuario/tu_repositorio.git
   cd tu_repositorio
   ```

2. **Ejecuta la aplicación**

   ```bash
   # El script instala automáticamente las dependencias faltantes
   python3 app.py
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
|             | `es-ES-AlbaNeural`    | 🎙️ Alba (femenina)     |
|             | `es-ES-AlvaroNeural`  | 🎙️ Álvaro (masculina)  |
| Inglés (US) | `en-US-JennyNeural`   | 🎙️ Jenny (femenina)    |
|             | `en-US-BrandonNeural` | 🎙️ Brandon (masculina) |
| Inglés (UK) | `en-GB-LibbyNeural`   | 🎙️ Libby (femenina)    |
|             | `en-GB-RyanNeural`    | 🎙️ Ryan (masculina)    |
| Alemán      | `de-DE-KatjaNeural`   | 🎙️ Katja (femenina)    |
|             | `de-DE-ConradNeural`  | 🎙️ Conrad (masculina)  |
| Portugués   | `pt-PT-RaquelNeural`  | 🎙️ Raquel (femenina)   |
|             | `pt-BR-AntonioNeural` | 🎙️ Antônio (masculina) |

## 🔧 Personalización

* Para cambiar el tema de Bootstrap, edita `external_stylesheets` en `app.py`.
* Modifica `TEXTO_DEMO` y `DEFAULT_VOICE` para ajustar texto y voz predeterminados.
* Añade o quita voces editando el diccionario `GROUPS`.

## 📄 Licencia

Este proyecto está licenciado bajo la [MIT License](LICENSE).

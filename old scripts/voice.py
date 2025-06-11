# pip install edge-tts
import asyncio
import edge_tts

TEXTO = "Hola, esto es una prueba de síntesis de voz en español (España)."

# 1 voz femenina + 2 voces españolas adicionales (todas es-ES)
VOCES = [
    "es-ES-ElviraNeural",       # femenina, castellano estándar
    "es-ES-AlvaroNeural",       # masculino
    "es-ES-ManuelEsCUNeural"    # masculino con matiz canario
]

async def sintetizar(texto: str, voz: str, fichero: str):
    tts = edge_tts.Communicate(text=texto, voice=voz)
    await tts.save(fichero)           # genera un .mp3

async def main():
    tareas = [
        sintetizar(TEXTO, voz, f"voz_{i+1}_{voz}.mp3")
        for i, voz in enumerate(VOCES)
    ]
    await asyncio.gather(*tareas)
    print("✅ 3 archivos MP3 creados")

if __name__ == "__main__":
    asyncio.run(main())

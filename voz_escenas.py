#!/usr/bin/env python3
"""
Voz de un vídeo entero con edge-tts, escena por escena, con subtítulos.

Entrada: <carpeta del vídeo>/locucion.md, una escena por cada «## <id>» y el texto tal cual se lee.
Salida, en <carpeta del vídeo>/voz/:
  escena-<id>.mp3 y escena-<id>.srt   una por escena
  locucion-completa.mp3 y .srt        todo seguido (hace falta ffmpeg)
  registro.csv                        qué se generó, con qué voz, velocidad y tono

    python voz_escenas.py <carpeta>                  # genera lo que falte o haya cambiado
    python voz_escenas.py <carpeta> --escena 01      # solo una escena, para escucharla
    python voz_escenas.py <carpeta> --solo-contar    # no genera nada: cuenta escenas y caracteres
    python voz_escenas.py --ver-voces en             # voces disponibles de un idioma
    python voz_escenas.py --muestra "Texto" --voz en-US-ChristopherNeural   # prueba rápida en muestras/

Voz, velocidad y tono por defecto están en voces.json, al lado de este archivo.
No hace falta cuenta ni clave. Si una escena no se ha cambiado, no se vuelve a generar.
"""
import argparse
import asyncio
import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import edge_tts

HERE = Path(__file__).resolve().parent
LOG_FIELDS = ["fecha", "video", "escena", "caracteres", "voz", "velocidad", "tono", "huella", "segundos", "archivo"]
RETRIES = 4   # el servicio a veces devuelve «No audio was received» sin motivo; al reintentar sale bien


class VoiceError(Exception):
    """Un alto con un mensaje para quien lo está ejecutando."""


def load_config(path=HERE / "voces.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parse_scenes(text):
    """[(id de escena, texto)] a partir de los títulos «## id»; solo se juntan los espacios."""
    scenes, current, lines = [], None, []
    for line in text.splitlines():
        heading = re.match(r"^##\s+(\S+)\s*$", line)
        if heading:
            if current is not None:
                scenes.append((current, " ".join(" ".join(lines).split())))
            current, lines = heading.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        scenes.append((current, " ".join(" ".join(lines).split())))
    ids = [s for s, _ in scenes]
    if not scenes:
        raise VoiceError("locucion.md no tiene escenas: cada una empieza por «## 01», «## 02»…")
    if len(ids) != len(set(ids)):
        raise VoiceError("Hay escenas con el mismo número en locucion.md.")
    if not re.fullmatch(r"[\w.-]+", "".join(ids)):
        raise VoiceError("Los números de escena solo pueden llevar letras, números, punto, guion y guion bajo.")
    empty = [s for s, t in scenes if not t]
    if empty:
        raise VoiceError(f"Escenas sin texto: {', '.join(empty)}.")
    return scenes


def settings(cfg, voice=None, rate=None, pitch=None):
    """Voz, velocidad y tono: lo que se pida por la línea de órdenes, o lo de voces.json."""
    chosen = voice or cfg["voces"][cfg["voz_elegida"]]["id"]
    rate = rate or cfg.get("velocidad", "+0%")
    pitch = pitch or cfg.get("tono", "+0Hz")
    if not re.fullmatch(r"[+-]\d{1,2}%", rate):
        raise VoiceError(f"Velocidad «{rate}» no válida: usa por ejemplo -5% o +10%.")
    if not re.fullmatch(r"[+-]\d{1,3}Hz", pitch):
        raise VoiceError(f"Tono «{pitch}» no válido: usa por ejemplo -2Hz o +0Hz.")
    return chosen, rate, pitch


def fingerprint(text, voice, rate, pitch):
    """Cambia siempre que cambiaría el audio: texto, voz, velocidad o tono."""
    raw = json.dumps([text, voice, rate, pitch])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def read_log(path):
    if not Path(path).exists():
        return []
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def append_log(path, row):
    path = Path(path)
    new = not path.exists()
    with open(path, "a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            writer.writeheader()
        writer.writerow(row)


def pending(scenes, out_dir, voice, rate, pitch):
    """Escenas sin MP3 o hechas con otro texto, voz, velocidad o tono."""
    done = {r["escena"]: r["huella"] for r in read_log(out_dir / "registro.csv")}
    todo = []
    for scene, text in scenes:
        mp3 = out_dir / f"escena-{scene}.mp3"
        if not (mp3.exists() and mp3.stat().st_size > 0 and done.get(scene) == fingerprint(text, voice, rate, pitch)):
            todo.append((scene, text))
    return todo


async def _synthesize(text, voice, rate, pitch):
    audio, subs = bytearray(), edge_tts.SubMaker()
    async for chunk in edge_tts.Communicate(text, voice, rate=rate, pitch=pitch).stream():
        if chunk["type"] == "audio":
            audio.extend(chunk["data"])
        elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
            subs.feed(chunk)
    return bytes(audio), subs.get_srt()


def synthesize(text, voice, rate, pitch, engine=_synthesize, wait=time.sleep):
    """(mp3, srt), con reintentos: el servicio falla de vez en cuando sin motivo."""
    last = None
    for attempt in range(RETRIES):
        try:
            audio, srt = asyncio.run(engine(text, voice, rate, pitch))
            if audio:
                return audio, srt
            last = "no llegó audio"
        except Exception as err:   # edge-tts y aiohttp lanzan varios tipos; todos se reintentan igual
            last = f"{type(err).__name__}: {err}"
        wait(2 * (attempt + 1))
    raise VoiceError(f"No se pudo generar después de {RETRIES} intentos ({last}). ¿Hay conexión a internet?")


def duration(mp3):
    """Segundos del MP3, con ffprobe. None si no está instalado."""
    if not shutil.which("ffprobe"):
        return None
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return None


SRT_TIME = re.compile(r"(\d+):(\d{2}):(\d{2}),(\d{3})")


def _shift(stamp, offset):
    h, m, s, ms = map(int, SRT_TIME.fullmatch(stamp).groups())
    total = round((h * 3600 + m * 60 + s) * 1000 + ms + offset * 1000)
    h, rest = divmod(total, 3600000)
    m, rest = divmod(rest, 60000)
    s, ms = divmod(rest, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def merge_srt(parts):
    """Junta los .srt de cada escena en uno, sumando la duración de las anteriores. parts: [(texto srt, desfase en s)]."""
    blocks, n = [], 0
    for srt, offset in parts:
        for block in re.split(r"\n\s*\n", srt.strip()):
            lines = block.strip().splitlines()
            if len(lines) < 3 or "-->" not in lines[1]:
                continue
            start, end = [x.strip() for x in lines[1].split("-->")]
            n += 1
            blocks.append(f"{n}\n{_shift(start, offset)} --> {_shift(end, offset)}\n" + "\n".join(lines[2:]))
    return "\n\n".join(blocks) + "\n"


def join_all(scenes, out_dir, out=print):
    """locucion-completa.mp3 y .srt con todas las escenas, en orden. Necesita ffmpeg."""
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        out("Sin ffmpeg: no se hace la locución completa (las escenas sí están).")
        return None
    mp3s = [out_dir / f"escena-{s}.mp3" for s, _ in scenes]
    if not all(p.exists() for p in mp3s):
        return None
    listing = out_dir / "lista-escenas.txt"
    listing.write_text("".join(f"file '{p.name}'\n" for p in mp3s), encoding="utf-8")
    full = out_dir / "locucion-completa.mp3"
    joined = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing.name, "-c", "copy",
                             full.name], cwd=out_dir, capture_output=True, text=True)
    listing.unlink()
    if joined.returncode:
        out(f"No se pudo juntar la locución completa (las escenas sí están): {joined.stderr.strip()[:200]}")
        return None
    parts, offset = [], 0.0
    for p in mp3s:
        srt = p.with_suffix(".srt")
        parts.append((srt.read_text(encoding="utf-8") if srt.exists() else "", offset))
        offset += duration(p) or 0.0
    full.with_suffix(".srt").write_text(merge_srt(parts), encoding="utf-8")
    out(f"Locución completa: {full.name} ({offset:.1f} s) y {full.with_suffix('.srt').name}")
    return full


def run(video_dir, cfg, voice=None, rate=None, pitch=None, only=None, count_only=False, engine=_synthesize, out=print,
        join=True):
    video_dir = Path(video_dir)
    source = video_dir / "locucion.md"
    if not source.exists():
        raise VoiceError(f"No existe {source}.")
    voice, rate, pitch = settings(cfg, voice, rate, pitch)
    scenes = parse_scenes(source.read_text(encoding="utf-8"))
    selected = [s for s in scenes if s[0] == only] if only else scenes
    if only and not selected:
        raise VoiceError(f"No hay escena {only} en locucion.md.")
    out_dir = video_dir / "voz"
    todo = pending(selected, out_dir, voice, rate, pitch)
    out(f"Voz {voice}, velocidad {rate}, tono {pitch}. Escenas: {len(selected)}, "
        f"{sum(len(t) for _, t in selected)} caracteres. Por generar: {len(todo)}.")
    if count_only:
        out("No se ha generado nada.")
        return []
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    for scene, text in todo:
        audio, srt = synthesize(text, voice, rate, pitch, engine)
        mp3 = out_dir / f"escena-{scene}.mp3"
        tmp = mp3.with_suffix(".part")
        tmp.write_bytes(audio)
        tmp.replace(mp3)
        mp3.with_suffix(".srt").write_text(srt, encoding="utf-8")
        seconds = duration(mp3)
        append_log(out_dir / "registro.csv", {
            "fecha": dt.datetime.now().isoformat(timespec="seconds"), "video": video_dir.name, "escena": scene,
            "caracteres": len(text), "voz": voice, "velocidad": rate, "tono": pitch,
            "huella": fingerprint(text, voice, rate, pitch), "segundos": f"{seconds:.2f}" if seconds else "", "archivo": mp3.name})
        made.append(mp3)
        out(f"Escena {scene}: {len(text)} caracteres -> {mp3.name}" + (f" ({seconds:.1f} s)" if seconds else ""))
    if join and not only and (made or not (out_dir / "locucion-completa.mp3").exists()):
        join_all(scenes, out_dir, out)
    return made


async def _voices():
    return await edge_tts.list_voices()


def list_voices(language, out=print):
    voices = [v for v in asyncio.run(_voices()) if v["Locale"].lower().startswith(language.lower())]
    for v in sorted(voices, key=lambda v: v["ShortName"]):
        tag = v.get("VoiceTag", {})
        out(f"{v['ShortName']:<36} {v['Gender']:<7} {', '.join(tag.get('ContentCategories', []))} · "
            f"{', '.join(tag.get('VoicePersonalities', []))}")
    return len(voices)


def sample(text, cfg, voice=None, rate=None, pitch=None, out=print):
    voice, rate, pitch = settings(cfg, voice, rate, pitch)
    folder = HERE / "muestras"
    folder.mkdir(exist_ok=True)
    audio, _ = synthesize(text, voice, rate, pitch)
    path = folder / f"{voice}{'' if rate == '+0%' else '_' + rate}.mp3"
    path.write_bytes(audio)
    out(f"Muestra: {path}")
    return path


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description="Voz de un vídeo, por escenas, con edge-tts.")
    p.add_argument("video", nargs="?", help="carpeta del vídeo, con locucion.md")
    p.add_argument("--escena", help="solo esta escena")
    p.add_argument("--voz", help="por ejemplo en-US-ChristopherNeural; si no, la de voces.json")
    p.add_argument("--velocidad", help="por ejemplo -5%% o +10%%")
    p.add_argument("--tono", help="por ejemplo -2Hz")
    p.add_argument("--solo-contar", action="store_true", help="no genera nada")
    p.add_argument("--ver-voces", metavar="IDIOMA", help="lista las voces de un idioma: en, es, en-GB…")
    p.add_argument("--muestra", metavar="TEXTO", help="genera una prueba corta en muestras/")
    args = p.parse_args(argv)
    cfg = load_config()
    try:
        if args.ver_voces:
            return 0 if list_voices(args.ver_voces) else 1
        if args.muestra:
            sample(args.muestra, cfg, args.voz, args.velocidad, args.tono)
            return 0
        if not args.video:
            p.error("falta la carpeta del vídeo")
        run(args.video, cfg, args.voz, args.velocidad, args.tono, args.escena, args.solo_contar)
    except VoiceError as err:
        print(err)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

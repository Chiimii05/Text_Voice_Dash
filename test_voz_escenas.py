"""Pruebas de voz_escenas.py sin conexión: el motor de voz es falso. python -m unittest test_voz_escenas"""
import tempfile
import unittest
from pathlib import Path

import voz_escenas as vz

CFG = {"voz_elegida": "a", "velocidad": "+0%", "tono": "+0Hz", "voces": {"a": {"id": "en-US-FakeNeural"}}}
SRT = "1\n00:00:00,100 --> 00:00:01,500\nHello there.\n"


def fake_engine(calls, fail_first=0):
    async def engine(text, voice, rate, pitch):
        calls.append(text)
        if len(calls) <= fail_first:
            raise RuntimeError("No audio was received")
        return b"ID3" + text.encode(), SRT
    return engine


class Scenes(unittest.TestCase):
    def test_parse(self):
        text = "# Título\nnada\n## 01\nHola\n  mundo.\n\n## 02\nAdiós."
        self.assertEqual(vz.parse_scenes(text), [("01", "Hola mundo."), ("02", "Adiós.")])

    def test_errors(self):
        for bad in ("sin escenas", "## 01\nA\n## 01\nB", "## 01\n\n## 02\nB", "## a/b\nA"):
            with self.assertRaises(vz.VoiceError):
                vz.parse_scenes(bad)

    def test_settings_validated(self):
        self.assertEqual(vz.settings(CFG), ("en-US-FakeNeural", "+0%", "+0Hz"))
        with self.assertRaises(vz.VoiceError):
            vz.settings(CFG, rate="rápido")
        with self.assertRaises(vz.VoiceError):
            vz.settings(CFG, pitch="5")


class Run(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "locucion.md").write_text("## 01\nFirst scene.\n## 02\nSecond scene.\n", encoding="utf-8")

    def run_it(self, calls, **kw):
        return vz.run(self.dir, CFG, engine=fake_engine(calls), out=lambda *_: None, join=False, **kw)

    def test_generates_and_caches(self):
        calls = []
        made = self.run_it(calls)
        self.assertEqual([p.name for p in made], ["escena-01.mp3", "escena-02.mp3"])
        self.assertTrue((self.dir / "voz" / "escena-01.srt").exists())
        self.assertEqual(len(vz.read_log(self.dir / "voz" / "registro.csv")), 2)
        self.assertEqual(self.run_it(calls), [])            # nada cambia: no se vuelve a generar
        self.assertEqual(len(calls), 2)

    def test_regenerates_only_what_changed(self):
        calls = []
        self.run_it(calls)
        (self.dir / "locucion.md").write_text("## 01\nFirst scene.\n## 02\nSecond scene, changed.\n", encoding="utf-8")
        self.assertEqual([p.name for p in self.run_it(calls)], ["escena-02.mp3"])
        self.assertEqual([p.name for p in self.run_it(calls, rate="-5%")], ["escena-01.mp3", "escena-02.mp3"])

    def test_count_only_and_one_scene(self):
        calls = []
        self.assertEqual(self.run_it(calls, count_only=True), [])
        self.assertEqual(calls, [])
        self.assertEqual([p.name for p in self.run_it(calls, only="02")], ["escena-02.mp3"])
        with self.assertRaises(vz.VoiceError):
            self.run_it(calls, only="09")


    def test_bad_audio_does_not_break_the_join(self):
        calls, said = [], []
        vz.run(self.dir, CFG, engine=fake_engine(calls), out=said.append)   # MP3 falsos: ffmpeg no los puede juntar
        self.assertTrue((self.dir / "voz" / "escena-02.mp3").exists())
        self.assertFalse((self.dir / "voz" / "lista-escenas.txt").exists())


class Retries(unittest.TestCase):
    def test_retries_then_works(self):
        calls = []
        audio, _ = vz.synthesize("Hi", "v", "+0%", "+0Hz", fake_engine(calls, fail_first=2), wait=lambda s: None)
        self.assertTrue(audio.startswith(b"ID3"))
        self.assertEqual(len(calls), 3)

    def test_gives_up(self):
        with self.assertRaises(vz.VoiceError):
            vz.synthesize("Hi", "v", "+0%", "+0Hz", fake_engine([], fail_first=99), wait=lambda s: None)


class Subtitles(unittest.TestCase):
    def test_merge_shifts_and_renumbers(self):
        merged = vz.merge_srt([(SRT, 0.0), (SRT, 61.25)])
        self.assertIn("1\n00:00:00,100 --> 00:00:01,500\nHello there.", merged)
        self.assertIn("2\n00:01:01,350 --> 00:01:02,750\nHello there.", merged)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import os
import io
import sys
import ssl
import json
import time
import math
import base64
import socket
import struct
import random
import colorsys
import threading
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from concurrent.futures import ThreadPoolExecutor
import urllib3
import numpy as np
import mss
import customtkinter as ctk

# Wyłączenie ostrzeżeń o LibreSSL w starszych środowiskach macOS
urllib3.disable_warnings()

# Obsługa przetwarzania okładek Spotify w pamięci RAM
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Opcjonalna obsługa globalnych skrótów klawiszowych macOS w tle
try:
    from pynput import keyboard as pynput_keyboard
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False

# =====================================================================
# KONFIGURACJA HOME ASSISTANT, SPOTIFY API, SIECI I ŚWIATEŁ
# =====================================================================
HA_URL = "http://localhost:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNjg5YmRiMjMxZjI0NGJhODk0ZDZmOTRkNzU1NWVlYiIsImlhdCI6MTc5MjAzODA3NCwiZXhwIjoyMTA3Mzk4MDc0fQ.ZQu_rZ2WDVTkeiDdciNQFs8wRf8Sz1nzm8UiDw5wvDs"

SPOTIFY_API_URL = "https://skawiskawi.pl/api/spotify"
MOBILE_PORT = 8765
PRESETS_FILE = Path.home() / ".spatial_ambient_presets.json"

LIGHTS_CONFIG = {
    "light.ambientl":        {"name": "2. Monitor Lewa",   "icon": "🖥️", "zone": "left",        "game_max": 1.00, "film_max": 0.85, "normal_max": 1.00, "is_ceiling": False, "pos": [0.36, 0.20]},
    "light.ambientr":        {"name": "1. Monitor Prawa",  "icon": "🖥️", "zone": "right",       "game_max": 1.00, "film_max": 0.85, "normal_max": 1.00, "is_ceiling": False, "pos": [0.64, 0.20]},
    "light.komputer":        {"name": "4. Sufit Biurko",   "icon": "💡", "zone": "top",         "game_max": 0.22, "film_max": 0.12, "normal_max": 0.05, "is_ceiling": True,  "pos": [0.50, 0.34]},
    "light.lsc_moodlight":   {"name": "9. LSC Moodlight",  "icon": "🔮", "zone": "left_mid",    "game_max": 0.95, "film_max": 0.75, "normal_max": 0.35, "is_ceiling": False, "pos": [0.18, 0.38]},
    "light.lampa_stojaca":   {"name": "8. Lampa Stojąca",  "icon": "🛋️", "zone": "right_mid",   "game_max": 0.70, "film_max": 0.50, "normal_max": 0.20, "is_ceiling": False, "pos": [0.82, 0.45]},
    "light.kuchnia":         {"name": "5. Sufit Kuchnia",  "icon": "☕", "zone": "left_deep",   "game_max": 0.50, "film_max": 0.35, "normal_max": 0.08, "is_ceiling": True,  "pos": [0.20, 0.72]},
    "light.drzwi_wejsciowe": {"name": "3. Sufit Drzwi",    "icon": "🚪", "zone": "right_deep",  "game_max": 0.35, "film_max": 0.25, "normal_max": 0.07, "is_ceiling": True,  "pos": [0.82, 0.75]},
    "light.naroznik":        {"name": "6. Sufit Sofa",     "icon": "✨", "zone": "center_deep", "game_max": 0.35, "film_max": 0.25, "normal_max": 0.07, "is_ceiling": True,  "pos": [0.50, 0.68]},
    "light.lampka_nocna":    {"name": "7. Za Sofą Róg",    "icon": "🌙", "zone": "center_deep", "game_max": 0.80, "film_max": 0.65, "normal_max": 0.22, "is_ceiling": False, "pos": [0.48, 0.88]},
}

FLOW_SEQUENCE = [
    [("light.kuchnia", 0.75)],
    [("light.lsc_moodlight", 1.00)],
    [("light.ambientl", 1.00)],
    [("light.ambientr", 1.00), ("light.komputer", 0.45)],
    [("light.lampa_stojaca", 0.95), ("light.drzwi_wejsciowe", 0.55)],
    [("light.lampka_nocna", 1.00), ("light.naroznik", 0.55)],
]

WAVE_THEMES = [
    ("Cyberpunk",     (0, 240, 255),   (255, 0, 140),   (130, 0, 255)),
    ("Zorza Polarna", (0, 255, 130),   (0, 140, 255),   (110, 0, 255)),
    ("Złoty Zachód",  (255, 200, 0),   (255, 50, 0),    (180, 0, 90)),
    ("Głębia Oceanu", (0, 255, 200),   (0, 80, 255),    (60, 0, 220)),
    ("Neon Synth",    (255, 0, 255),   (0, 220, 255),   (255, 100, 0)),
    ("Szmaragd",      (160, 255, 0),   (0, 220, 90),    (0, 130, 180)),
]

QUICK_PALETTE = [
    ("Ciepła Biel",    (255, 190, 125), 2700),
    ("Czysta Biel",    (255, 245, 235), 4800),
    ("Róż Nati",       (255, 95, 190),  None),
    ("Głęboki Fiolet", (95, 0, 210),    None),
    ("Cyber Cyan",     (0, 235, 255),   None),
    ("Złoty Bursztyn", (255, 140, 0),   None),
    ("Szmaragd",       (0, 230, 118),   None),
    ("Karmazyn",       (255, 25, 65),   None),
]

NATI_LIGHT_PINK = (255, 110, 195)
NATI_DARK_PURPLE = (60, 0, 125)


def get_local_lan_ip() -> str:
    """Wykrywa lokalny adres IP MacBooka w sieci Wi-Fi/LAN."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def kelvin_to_rgb(kelvin: int) -> tuple[int, int, int]:
    """Przelicza temperaturę barwową (K) na RGB (algorytm Tannera Hellanda)."""
    temp = float(np.clip(kelvin, 1000, 40000)) / 100.0
    if temp <= 66.0:
        r = 255.0
        g = 99.4708025861 * np.log(temp) - 161.1195681661
        b = 0.0 if temp <= 19.0 else (138.5177312231 * np.log(temp - 10.0) - 305.0447927307)
    else:
        r = 329.698727446 * ((temp - 60.0) ** -0.1332047592)
        g = 288.1221695283 * ((temp - 60.0) ** -0.0755148492)
        b = 255.0
    return (
        int(np.clip(r, 0, 255)),
        int(np.clip(g, 0, 255)),
        int(np.clip(b, 0, 255)),
    )


def hsl_to_rgb(h_deg: float, s_norm: float = 0.85, l_norm: float = 0.55) -> tuple[int, int, int]:
    """Konwertuje HSL (z algorytmu skawiskawi.pl) na krotkę RGB (0-255)."""
    r, g, b = colorsys.hls_to_rgb((h_deg % 360.0) / 360.0, l_norm, s_norm)
    return (int(np.clip(r * 255, 0, 255)), int(np.clip(g * 255, 0, 255)), int(np.clip(b * 255, 0, 255)))


def lerp_hue_deg(current: float, target: float, factor: float) -> float:
    """Płynna interpolacja kąta Hue po najkrótszym łuku koła barw (0-360)."""
    diff = (target - current) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (current + diff * factor) % 360.0


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{int(np.clip(rgb[0], 0, 255)):02x}{int(np.clip(rgb[1], 0, 255)):02x}{int(np.clip(rgb[2], 0, 255)):02x}"


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 6:
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    return (255, 255, 255)


# =====================================================================
# SILNIK SYNCHRONIZACJI SPOTIFY (OKŁADKI + BPM + STROBOSKOP + EKG)
# =====================================================================
class SpotifyBeatSync:
    """
    Odtwarza mechanikę ze strony skawiskawi.pl:
    - pobiera aktualny utwór i BPM z endpointu /api/spotify (wspierając się WebSocketem HA),
    - ekstrahuje 2 dominujące odcienie (Hue) z okładki 64x64 metodą koszykową co 25°,
    - zarządza losowymi błyskami (Strobe Flashes) w rytm BPM oraz trybem EKG podczas pauzy.
    """
    def __init__(self, engine: "AmbientEngine"):
        self.engine = engine
        self.http = urllib3.PoolManager(
            headers={"User-Agent": "SpatialAmbientStudio/7.0"},
            num_pools=4,
            maxsize=8
        )

        self.is_playing = False
        self.track_id = None
        self.title = "Oczekiwanie na Spotify..."
        self.artist = "Włącz muzykę"
        self.album_url = ""
        self.bpm = 120.0

        # Kolory bazowe (w stopniach Hue 0-360, dokładnie jak w skawiskawi.pl)
        self.target_hue1 = 200.0
        self.target_hue2 = 300.0
        self.current_hue1 = 200.0
        self.current_hue2 = 300.0
        self.is_grayscale = False

        self.color1_rgb = hsl_to_rgb(200.0, 0.85, 0.55)
        self.color2_rgb = hsl_to_rgb(300.0, 0.85, 0.55)

        # Konfiguracja błysków (Strobe)
        self.strobe_density = 2          # Ile losowych lamp błyska naraz (1 - 6)
        self.ceiling_strobe_enabled = False  # Czy sufit też ma ostro błyskać (False = sufit robi tylko płynne bloby)
        self.strobe_flash_white_mix = 0.45   # Domieszka czystej bieli do błysku (efekt .strobe-flash)

        # Timery choreografii
        self.next_strobe_ts = time.perf_counter() + 0.75
        self.active_flashes = {}  # entity_id -> timestamp wygaśnięcia błysku
        self.last_beat_pulse_ts = 0.0
        self._force_poll_event = threading.Event()

        self.worker = threading.Thread(target=self._poll_loop, daemon=True)
        self.worker.start()

    def trigger_immediate_poll(self):
        """Wywoływane przez WebSocket HA, gdy encja media_player zmieni stan."""
        self._force_poll_event.set()

    def extract_palette_from_image_bytes(self, raw_bytes: bytes) -> dict | None:
        """Dokładny port funkcji extractPaletteFromUrl() ze skawiskawi.pl na NumPy."""
        if not HAS_PIL or not raw_bytes:
            return None
        try:
            img = Image.open(io.BytesIO(raw_bytes)).convert("RGB").resize((64, 64), Image.Resampling.BILINEAR)
            arr = np.asarray(img, dtype=np.float32) / 255.0
            pixels = arr.reshape(-1, 3)[::4]  # Co 4. piksel (identyczny krok jak i += 16 na tablicy RGBA w JS)

            buckets = {}
            total_sat = 0.0
            sample_count = 0

            for r, g, b in pixels:
                max_c = max(r, g, b)
                min_c = min(r, g, b)
                lum = (max_c + min_c) * 0.5
                if lum < 0.12 or lum > 0.90:
                    continue

                sat = 0.0
                if max_c != min_c:
                    sat = (max_c - min_c) / (2.0 - max_c - min_c) if lum > 0.5 else (max_c - min_c) / (max_c + min_c)

                total_sat += sat
                sample_count += 1

                hue = 0.0
                if max_c != min_c:
                    d = max_c - min_c
                    if max_c == r:
                        hue = (g - b) / d + (6.0 if g < b else 0.0)
                    elif max_c == g:
                        hue = (b - r) / d + 2.0
                    else:
                        hue = (r - g) / d + 4.0
                    hue = round(hue * 60.0)

                h_bucket = int(round(hue / 25.0) * 25) % 360
                score = 1.0 + (sat * 3.0)
                buckets[h_bucket] = buckets.get(h_bucket, 0.0) + score

            avg_sat = (total_sat / sample_count) if sample_count > 0 else 0.0
            if avg_sat < 0.12:
                return {"is_grayscale": True, "c1": 200.0, "c2": 300.0}

            if not buckets:
                return None

            sorted_buckets = sorted(buckets.items(), key=lambda x: x[1], reverse=True)
            primary_hue = float(sorted_buckets[0][0])
            secondary_hue = (primary_hue + 60.0) % 360.0

            for cand_hue, _score in sorted_buckets[1:]:
                diff = abs(cand_hue - primary_hue)
                if 35.0 < diff < 325.0:
                    secondary_hue = float(cand_hue)
                    break

            return {"is_grayscale": False, "c1": primary_hue, "c2": secondary_hue}
        except Exception:
            return None

    def _poll_loop(self):
        while self.engine.running:
            try:
                res = self.http.request("GET", SPOTIFY_API_URL, timeout=3.5)
                if res.status == 200:
                    data = json.loads(res.data.decode("utf-8"))
                    title = data.get("title")
                    if title:
                        self.title = title
                        self.artist = data.get("artist") or "Spotify"
                        self.is_playing = bool(data.get("isPlaying", False))

                        new_id = data.get("id") or title
                        if new_id != self.track_id:
                            self.track_id = new_id
                            raw_tempo = data.get("tempo")
                            self.bpm = float(np.clip(raw_tempo if raw_tempo else 120.0, 50.0, 220.0))

                        new_cover = data.get("albumImageUrl") or ""
                        if new_cover and new_cover != self.album_url:
                            self.album_url = new_cover
                            img_res = self.http.request("GET", new_cover, timeout=3.5)
                            if img_res.status == 200:
                                palette = self.extract_palette_from_image_bytes(img_res.data)
                                if palette:
                                    self.is_grayscale = palette["is_grayscale"]
                                    self.target_hue1 = palette["c1"]
                                    self.target_hue2 = palette["c2"]
                    else:
                        self.is_playing = False
                        self.title = "Brak aktywności"
                        self.artist = "Spotify (Tryb EKG)"
            except Exception:
                pass

            # Czeka 3.5 sekundy lub budzi się natychmiast na sygnał z Home Assistanta
            self._force_poll_event.wait(timeout=3.5)
            self._force_poll_event.clear()

    def step_frame(self, now: float):
        """Wywoływane z pętli głównej silnika (~25 FPS) w trybie SPOTIFY."""
        # 1. Płynna interpolacja odcieni Hue (dokładnie jak lerpHue w renderCanvas na stronie)
        self.current_hue1 = lerp_hue_deg(self.current_hue1, self.target_hue1, 0.06)
        self.current_hue2 = lerp_hue_deg(self.current_hue2, self.target_hue2, 0.06)

        if self.is_grayscale:
            self.color1_rgb = kelvin_to_rgb(5500)
            self.color2_rgb = kelvin_to_rgb(3800)
        else:
            sat = float(np.clip(0.82 * (self.engine.saturation_boost / 1.35), 0.45, 1.0))
            self.color1_rgb = hsl_to_rgb(self.current_hue1, sat, 0.54)
            self.color2_rgb = hsl_to_rgb(self.current_hue2, sat, 0.54)

        active_eids = [eid for eid, enabled in self.engine.enabled_lights.items() if enabled]
        if not active_eids:
            return

        # 2. Jeśli muzyka ZATRZYMANA -> Tryb "Flatline EKG" (impuls co 3.6 s jak na stronie)
        if not self.is_playing:
            self.active_flashes.clear()
            ekg_cycle = now % 3.6
            pulse_duration = 1.1
            is_pulsing = ekg_cycle < pulse_duration
            pulse_progress = (ekg_cycle / pulse_duration) if is_pulsing else -1.0

            for eid in active_eids:
                cfg = LIGHTS_CONFIG[eid]
                px, py = cfg["pos"]
                # Pozycja lampy wzdłuż pokoju (0.0 -> 1.0)
                spatial_pos = float(np.clip(py * 0.7 + px * 0.3, 0.0, 1.0))

                base_rgb = self.engine.blend_colors(self.color1_rgb, self.color2_rgb, spatial_pos)
                base_bri = 28.0 * self.engine.master_brightness
                trans = 0.35

                if is_pulsing:
                    dist = abs(spatial_pos - pulse_progress)
                    if dist < 0.24:
                        spike = math.exp(-((dist / 0.11) ** 2))
                        base_rgb = self.engine.blend_colors(base_rgb, (255, 255, 255), spike * 0.65)
                        base_bri += (145.0 * spike) * self.engine.master_brightness
                        trans = 0.08

                if cfg["is_ceiling"]:
                    base_bri *= 0.55

                self.engine.update_light(eid, rgb=base_rgb, bri=int(np.clip(base_bri, 6, 255)), transition=trans)
            return

        # 3. Muzyka GRA -> Sprawdzenie wygasłych błysków i wyzwalanie nowych w rytm BPM
        expired = [eid for eid, exp_ts in self.active_flashes.items() if now >= exp_ts]
        for eid in expired:
            del self.active_flashes[eid]

        if now >= self.next_strobe_ts:
            self.last_beat_pulse_ts = now
            # Kandydaci do błysku (z uwzględnieniem przełącznika ochrony sufitu)
            candidates = [
                eid for eid in active_eids
                if self.ceiling_strobe_enabled or not LIGHTS_CONFIG[eid]["is_ceiling"]
            ]
            if not candidates:
                candidates = active_eids

            k_count = min(len(candidates), max(1, int(self.strobe_density)))
            chosen = random.sample(candidates, k=k_count)

            speed_mult = float(np.clip(120.0 / max(50.0, self.bpm), 0.45, 1.8))
            # Na stronie błysk trwa 50-110ms, dla fizycznych żarówek dajemy 110-180ms by zdążyły osiągnąć pik
            flash_duration = (random.uniform(0.11, 0.18)) * speed_mult

            for eid in chosen:
                self.active_flashes[eid] = now + flash_duration
                # Kolor błysku: kontrastujący kolor z okładki wzmocniony czystą bielą (jak .strobe-flash)
                flash_base = self.color2_rgb if random.random() > 0.35 else self.color1_rgb
                flash_rgb = self.engine.blend_colors(flash_base, (255, 255, 255), self.strobe_flash_white_mix)

                max_scale = 0.65 if LIGHTS_CONFIG[eid]["is_ceiling"] else 1.0
                flash_bri = int(np.clip(255.0 * max_scale * self.engine.master_brightness, 40, 255))

                self.engine.update_light(
                    eid,
                    rgb=flash_rgb,
                    bri=flash_bri,
                    transition=0.04,
                    force=True,
                )

            # Dokładny wzór ze skawiskawi.pl: (60 / BPM) * (0.65 do 1.25 uderzenia)
            beat_sec = 60.0 / float(np.clip(self.bpm, 50.0, 220.0))
            next_interval = beat_sec * random.uniform(0.75, 1.35)
            self.next_strobe_ts = now + next_interval

        # 4. Warstwa tła (pływające Bloby z okładki dla lamp, które aktualnie nie są w trakcie błysku)
        bpm_factor = float(np.clip(self.bpm / 120.0, 0.6, 2.0))
        for idx, eid in enumerate(active_eids):
            if eid in self.active_flashes:
                continue

            cfg = LIGHTS_CONFIG[eid]
            px, py = cfg["pos"]
            # Faza przestrzenna zależna od ułożenia lampy w pokoju
            spatial_phase = (now * 0.85 * bpm_factor) + (px * 3.2) + (py * 2.5) + (idx * 0.5)
            mix_ratio = (1.0 - math.cos(spatial_phase)) * 0.5

            blob_rgb = self.engine.blend_colors(self.color1_rgb, self.color2_rgb, mix_ratio)

            # Delikatne oddychanie jasności tła (odpowiednik fali dźwiękowej)
            wave_breath = 0.24 + 0.14 * ((1.0 + math.sin(now * 1.6 * bpm_factor + idx)) * 0.5)
            if cfg["is_ceiling"]:
                wave_breath *= 0.55

            target_bri = int(np.clip(255.0 * wave_breath * self.engine.master_brightness, 10, 210))
            self.engine.update_light(eid, rgb=blob_rgb, bri=target_bri, transition=0.28)


# =====================================================================
# MOBILNA APLIKACJA WEBOWA (PWA HTML5 + GLASSMORPHISM UI DLA ANDROID/IOS)
# =====================================================================
MOBILE_PWA_HTML = """<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#090D16">
<title>Spatial Ambient Mobile v7.0</title>
<style>
  :root {
    --bg: #090D16;
    --card: rgba(17, 24, 39, 0.88);
    --border: rgba(51, 65, 85, 0.55);
    --accent: #38BDF8;
    --text: #F8FAFC;
    --sub: #94A3B8;
  }
  * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  body {
    margin: 0; padding: 12px 12px 40px 12px;
    background: radial-gradient(circle at top, #162036 0%, #090D16 55%);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    user-select: none;
  }
  .top-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--card); border: 1px solid var(--border);
    padding: 12px 14px; border-radius: 16px; margin-bottom: 12px;
    backdrop-filter: blur(12px);
  }
  .title { font-size: 16px; font-weight: 800; letter-spacing: 0.4px; }
  .subtitle { font-size: 11px; color: var(--accent); margin-top: 2px; }
  .badge {
    background: #1E293B; padding: 6px 10px; border-radius: 10px;
    font-family: monospace; font-size: 11px; color: #4ADE80; font-weight: 700;
  }
  .sec-title {
    font-size: 11px; font-weight: 800; color: var(--sub);
    text-transform: uppercase; letter-spacing: 0.8px;
    margin: 14px 4px 8px 4px;
  }
  .modes-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
  }
  .mode-btn {
    background: var(--card); border: 1px solid var(--border);
    color: var(--text); border-radius: 14px; padding: 13px 12px;
    font-size: 13px; font-weight: 700; text-align: left;
    display: flex; align-items: center; gap: 8px;
    transition: transform 0.1s, background 0.2s, border-color 0.2s;
  }
  .mode-btn:active { transform: scale(0.97); }
  .mode-btn.active-ZWYKLY { background: #0D9488; border-color: #2DD4BF; }
  .mode-btn.active-GAMING { background: #2563EB; border-color: #60A5FA; }
  .mode-btn.active-FILM { background: #D97706; border-color: #FBBF24; }
  .mode-btn.active-NATI { background: #DB2777; border-color: #F472B6; }
  .mode-btn.active-SPOTIFY { background: #16A34A; border-color: #4ADE80; grid-column: span 2; }
  .mode-btn.active-MAX_WHITE { background: #EAB308; color: #0F172A; border-color: #FEF08A; }
  .mode-btn.active-IDLE { background: #475569; border-color: #94A3B8; }

  .spotify-banner {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 12px 14px; margin-top: 10px;
    display: flex; align-items: center; justify-content: space-between; gap: 10px;
  }
  .sp-dots { display: flex; gap: 6px; align-items: center; }
  .sp-swatch { width: 22px; height: 22px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.3); }

  .quick-row {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-top: 8px;
  }
  .q-btn {
    background: #1E293B; border: 1px solid var(--border); color: var(--text);
    padding: 10px 4px; border-radius: 11px; font-size: 11px; font-weight: 700;
    text-align: center;
  }
  .q-btn:active { transform: scale(0.95); }

  .panel-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 12px 14px; margin-bottom: 10px;
  }
  .slider-row {
    display: flex; align-items: center; gap: 10px; margin: 8px 0;
  }
  .slider-lbl { font-size: 12px; width: 120px; color: #CBD5E1; font-weight: 600; }
  .slider-val { font-family: monospace; font-size: 12px; width: 48px; text-align: right; color: var(--accent); }
  input[type=range] {
    flex: 1; -webkit-appearance: none; appearance: none;
    height: 8px; background: #1E293B; border-radius: 6px; outline: none;
  }
  input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none; width: 22px; height: 22px;
    border-radius: 50%; background: var(--accent); cursor: pointer;
    border: 2px solid #FFF;
  }

  .presets-bar {
    display: flex; gap: 6px; overflow-x: auto; padding-bottom: 4px;
  }
  .preset-pill {
    background: #1E293B; border: 1px solid var(--border); color: var(--text);
    padding: 8px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;
    white-space: nowrap;
  }
  .save-row { display: flex; gap: 6px; margin-top: 8px; }
  .save-input {
    flex: 1; background: #0F172A; border: 1px solid var(--border);
    color: #FFF; padding: 9px 12px; border-radius: 10px; font-size: 12px;
  }

  .lights-list { display: flex; flex-direction: column; gap: 10px; }
  .light-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; padding: 12px;
  }
  .light-top {
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;
  }
  .light-info { display: flex; align-items: center; gap: 10px; }
  .color-pick-wrap {
    position: relative; width: 38px; height: 38px; border-radius: 10px;
    border: 2px solid rgba(255,255,255,0.35); overflow: hidden;
    display: flex; align-items: center; justify-content: center;
  }
  .color-pick-wrap input[type=color] {
    position: absolute; opacity: 0; width: 100%; height: 100%; cursor: pointer;
  }
  .light-name { font-size: 14px; font-weight: 700; }
  .light-sub { font-size: 11px; color: var(--sub); }
  .light-btns { display: flex; gap: 6px; }
  .mini-btn {
    border: none; padding: 7px 11px; border-radius: 8px;
    font-size: 11px; font-weight: 800; color: #FFF;
  }
  .palette-dots {
    display: flex; justify-content: space-between; gap: 5px; margin-top: 8px;
  }
  .dot {
    flex: 1; height: 22px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.2);
  }
</style>
</head>
<body>

<div class="top-bar">
  <div>
    <div class="title">✨ SPATIAL AMBIENT v7.0</div>
    <div class="subtitle" id="statusText">Łączenie z MacBookiem...</div>
  </div>
  <div class="badge" id="pingBadge">WS ●</div>
</div>

<div class="sec-title">Sceny Automatyczne</div>
<div class="modes-grid">
  <button class="mode-btn" style="grid-column: span 2;" id="btn-SPOTIFY" onclick="sendAct({action:'set_mode', mode:'SPOTIFY'})">🎵 SPOTIFY BEAT (Okładka + Błyski BPM)</button>
  <button class="mode-btn" id="btn-ZWYKLY" onclick="sendAct({action:'set_mode', mode:'ZWYKLY'})">☕ Zwykły</button>
  <button class="mode-btn" id="btn-GAMING" onclick="sendAct({action:'set_mode', mode:'GAMING'})">🎮 Gaming</button>
  <button class="mode-btn" id="btn-FILM" onclick="sendAct({action:'set_mode', mode:'FILM'})">🎬 Kino / Film</button>
  <button class="mode-btn" id="btn-NATI" onclick="sendAct({action:'set_mode', mode:'NATI'})">🌸 Nati (3s)</button>
  <button class="mode-btn" id="btn-MAX_WHITE" onclick="sendAct({action:'set_mode', mode:'MAX_WHITE'})">☀️ Max Biel 100%</button>
  <button class="mode-btn" id="btn-IDLE" onclick="sendAct({action:'set_mode', mode:'IDLE'})">🎛️ Ręczny (HA)</button>
</div>

<div class="spotify-banner">
  <div style="min-width:0; flex:1;">
    <div style="font-size:10px; font-weight:800; color:#4ADE80; text-transform:uppercase;" id="spStatus">SPOTIFY SYNC</div>
    <div style="font-size:13px; font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" id="spTrack">Pobieranie...</div>
  </div>
  <div class="sp-dots">
    <div class="sp-swatch" id="spCol1"></div>
    <div class="sp-swatch" id="spCol2"></div>
  </div>
</div>

<div class="quick-row">
  <button class="q-btn" onclick="sendAct({action:'set_mode', mode:'MAX_WHITE'})">💡 100% Biel</button>
  <button class="q-btn" style="color:#F87171" onclick="sendAct({action:'sleep_all'})">🌑 Zgaś pokój</button>
  <button class="q-btn" onclick="sendAct({action:'sync_all', state:true})">🔗 Sync 9/9</button>
  <button class="q-btn" onclick="sendAct({action:'sync_all', state:false})">✋ Ręczny 9</button>
</div>

<div class="sec-title">Parametry Globalne & Spotify Strobe</div>
<div class="panel-card">
  <div class="slider-row">
    <span class="slider-lbl">🔆 Skala Jasności</span>
    <input type="range" id="gMaster" min="15" max="150" value="100" oninput="onGlobalSlide()">
    <span class="slider-val" id="vMaster">100%</span>
  </div>
  <div class="slider-row">
    <span class="slider-lbl">⚡ Błyski Spotify</span>
    <input type="range" id="gStrobe" min="1" max="6" step="1" value="2" oninput="onGlobalSlide()">
    <span class="slider-val" id="vStrobe">2 lampy</span>
  </div>
  <div class="slider-row">
    <span class="slider-lbl">🌡️ Temp. Bieli</span>
    <input type="range" id="gKelvin" min="2200" max="6500" step="50" value="4500" oninput="onGlobalSlide()">
    <span class="slider-val" id="vKelvin">4500K</span>
  </div>
  <div class="slider-row">
    <span class="slider-lbl">🎨 Nasycenie</span>
    <input type="range" id="gSat" min="80" max="220" value="135" oninput="onGlobalSlide()">
    <span class="slider-val" id="vSat">1.35x</span>
  </div>
</div>

<div class="sec-title">Własne Sceny Pokoju</div>
<div class="panel-card">
  <div class="presets-bar" id="presetsBar"></div>
  <div class="save-row">
    <input type="text" class="save-input" id="presetName" placeholder="Nazwa nowej sceny...">
    <button class="q-btn" style="padding:0 14px; background:#0D9488" onclick="savePreset()">💾 Zapisz</button>
  </div>
</div>

<div class="sec-title">Wszystkie Światła (Zaznacz 🔗 SYNC dla błysków Spotify)</div>
<div class="lights-list" id="lightsContainer"></div>

<script>
const QUICK_COLORS = [
  {rgb:[255,190,125], k:2700},
  {rgb:[255,245,235], k:4800},
  {rgb:[255,95,190],  k:null},
  {rgb:[95,0,210],    k:null},
  {rgb:[0,235,255],   k:null},
  {rgb:[255,140,0],   k:null},
  {rgb:[0,230,118],   k:null},
  {rgb:[255,25,65],   k:null}
];

let touchingSlider = false;
let touchTimer = null;

function markTouch() {
  touchingSlider = true;
  if (touchTimer) clearTimeout(touchTimer);
  touchTimer = setTimeout(() => { touchingSlider = false; }, 1200);
}

function haptic() {
  if (navigator.vibrate) navigator.vibrate(12);
}

async function sendAct(payload) {
  haptic();
  try {
    await fetch('/api/action', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    fetchState();
  } catch (e) {}
}

function onGlobalSlide() {
  markTouch();
  const m = document.getElementById('gMaster').value;
  const st = document.getElementById('gStrobe').value;
  const k = document.getElementById('gKelvin').value;
  const s = document.getElementById('gSat').value;
  document.getElementById('vMaster').innerText = m + '%';
  document.getElementById('vStrobe').innerText = st + ' lamp';
  document.getElementById('vKelvin').innerText = k + 'K';
  document.getElementById('vSat').innerText = (s / 100).toFixed(2) + 'x';
  fetch('/api/action', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      action: 'set_global',
      master_brightness: m / 100.0,
      strobe_density: parseInt(st),
      white_temp_kelvin: parseInt(k),
      saturation_boost: s / 100.0
    })
  });
}

function savePreset() {
  const inp = document.getElementById('presetName');
  const name = inp.value.trim() || 'Mobilna Scena';
  inp.value = '';
  sendAct({action: 'save_preset', name: name});
}

function buildLightsDOM(lights) {
  const container = document.getElementById('lightsContainer');
  container.innerHTML = '';
  lights.forEach(l => {
    const card = document.createElement('div');
    card.className = 'light-card';
    card.id = 'card-' + l.id;

    let dotsHtml = '';
    QUICK_COLORS.forEach(c => {
      const hex = '#' + c.rgb.map(x => x.toString(16).padStart(2,'0')).join('');
      const kArg = c.k ? c.k : 'null';
      dotsHtml += `<div class="dot" style="background:${hex}" onclick="sendAct({action:'set_light', entity_id:'${l.id}', rgb:[${c.rgb}], kelvin:${kArg}})"></div>`;
    });

    card.innerHTML = `
      <div class="light-top">
        <div class="light-info">
          <div class="color-pick-wrap" id="swatch-${l.id}" style="background:${l.hex}">
            <span>${l.icon}</span>
            <input type="color" value="${l.hex}" onchange="sendAct({action:'set_light', entity_id:'${l.id}', hex:this.value})">
          </div>
          <div>
            <div class="light-name">${l.name}</div>
            <div class="light-sub" id="sub-${l.id}">Jasność: ${l.bri_pct}%</div>
          </div>
        </div>
        <div class="light-btns">
          <button class="mini-btn" id="sync-${l.id}" onclick="sendAct({action:'toggle_sync', entity_id:'${l.id}'})">SYNC</button>
          <button class="mini-btn" id="pwr-${l.id}" onclick="sendAct({action:'toggle_power', entity_id:'${l.id}'})">ON</button>
        </div>
      </div>
      <div class="slider-row">
        <span style="font-size:12px">🔆</span>
        <input type="range" id="bri-${l.id}" min="1" max="255" value="${l.bri}"
          oninput="markTouch(); fetch('/api/action',{method:'POST',body:JSON.stringify({action:'set_light',entity_id:'${l.id}',bri:parseInt(this.value)})})">
        <span class="slider-val" id="bval-${l.id}">${l.bri_pct}%</span>
      </div>
      <div class="slider-row">
        <span style="font-size:12px">🌡️</span>
        <input type="range" id="ct-${l.id}" min="2000" max="6500" step="50" value="${l.kelvin}"
          oninput="markTouch(); fetch('/api/action',{method:'POST',body:JSON.stringify({action:'set_light',entity_id:'${l.id}',kelvin:parseInt(this.value)})})">
        <span class="slider-val" id="kval-${l.id}">${l.kelvin}K</span>
      </div>
      <div class="palette-dots">${dotsHtml}</div>
    `;
    container.appendChild(card);
  });
}

let domBuilt = false;

async function fetchState() {
  try {
    const res = await fetch('/api/state');
    const data = await res.json();

    document.getElementById('statusText').innerText = `Tryb: ${data.mode} • Aktywne: ${data.sync_count}/9`;
    document.getElementById('pingBadge').innerText = `${data.ws_online ? 'WS⚡' : 'REST'} ${data.ping_ms.toFixed(0)}ms`;

    ['SPOTIFY','ZWYKLY','GAMING','FILM','NATI','MAX_WHITE','IDLE'].forEach(m => {
      const b = document.getElementById('btn-' + m);
      if (b) b.className = 'mode-btn' + (data.mode === m ? ' active-' + m : '');
    });

    if (data.spotify) {
      document.getElementById('spStatus').innerText = data.spotify.is_playing
        ? `🎵 NOW PLAYING • ${Math.round(data.spotify.bpm)} BPM`
        : `⏸️ PAUZA (TRYB EKG 3.6s)`;
      document.getElementById('spTrack').innerText = `${data.spotify.title} — ${data.spotify.artist}`;
      document.getElementById('spCol1').style.background = data.spotify.hex1;
      document.getElementById('spCol2').style.background = data.spotify.hex2;
    }

    if (!touchingSlider) {
      document.getElementById('gMaster').value = Math.round(data.master_brightness * 100);
      document.getElementById('vMaster').innerText = Math.round(data.master_brightness * 100) + '%';
      document.getElementById('gStrobe').value = data.strobe_density;
      document.getElementById('vStrobe').innerText = data.strobe_density + ' lamp';
      document.getElementById('gKelvin').value = data.white_temp_kelvin;
      document.getElementById('vKelvin').innerText = data.white_temp_kelvin + 'K';
      document.getElementById('gSat').value = Math.round(data.saturation_boost * 100);
      document.getElementById('vSat').innerText = data.saturation_boost.toFixed(2) + 'x';
    }

    const pBar = document.getElementById('presetsBar');
    pBar.innerHTML = '';
    data.presets.forEach(pName => {
      const btn = document.createElement('button');
      btn.className = 'preset-pill';
      btn.innerText = '✨ ' + pName;
      btn.onclick = () => sendAct({action: 'load_preset', name: pName});
      pBar.appendChild(btn);
    });

    if (!domBuilt) {
      buildLightsDOM(data.lights);
      domBuilt = true;
    } else {
      data.lights.forEach(l => {
        const sw = document.getElementById('swatch-' + l.id);
        if (sw) sw.style.background = l.is_on ? l.hex : '#1E293B';
        const sub = document.getElementById('sub-' + l.id);
        if (sub) sub.innerText = l.is_on ? `Aktywna • ${l.bri_pct}% • ${l.kelvin}K` : 'Wyłączona (Standby)';

        const syncBtn = document.getElementById('sync-' + l.id);
        if (syncBtn) {
          syncBtn.innerText = l.in_sync ? '🔗 SYNC' : '✋ RĘCZNY';
          syncBtn.style.background = l.in_sync ? '#0F766E' : '#475569';
        }
        const pwrBtn = document.getElementById('pwr-' + l.id);
        if (pwrBtn) {
          pwrBtn.innerText = l.is_on ? 'ON' : 'OFF';
          pwrBtn.style.background = l.is_on ? '#2563EB' : '#334155';
        }
        if (!touchingSlider) {
          const bSlider = document.getElementById('bri-' + l.id);
          if (bSlider) bSlider.value = l.bri;
          const bVal = document.getElementById('bval-' + l.id);
          if (bVal) bVal.innerText = l.bri_pct + '%';
          const cSlider = document.getElementById('ct-' + l.id);
          if (cSlider) cSlider.value = l.kelvin;
          const kVal = document.getElementById('kval-' + l.id);
          if (kVal) kVal.innerText = l.kelvin + 'K';
        }
      });
    }
  } catch (e) {}
}

fetchState();
setInterval(fetchState, 600);
</script>
</body>
</html>
"""


# =====================================================================
# SERWER HTTP DLA URZĄDZEŃ MOBILNYCH (ANDROID / IOS / HA COMPANION)
# =====================================================================
class MobileRemoteServer:
    def __init__(self, engine: "AmbientEngine", port: int = MOBILE_PORT):
        self.engine = engine
        self.port = port
        self.lan_ip = get_local_lan_ip()
        self.url = f"http://{self.lan_ip}:{self.port}"
        self.mobile_hits = 0
        self.last_client_ip = "Brak połączeń"
        self.server = None

        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()

    def _run_server(self):
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _send_cors(self):
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")

            def do_OPTIONS(self):
                self.send_response(200)
                self._send_cors()
                self.end_headers()

            def do_GET(self):
                parent.mobile_hits += 1
                parent.last_client_ip = self.client_address[0]

                if self.path == "/" or self.path.startswith("/index"):
                    body = MOBILE_PWA_HTML.encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if self.path == "/api/state":
                    state_data = parent.engine.export_mobile_state()
                    body = json.dumps(state_data, ensure_ascii=False).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                    return

                if self.path.startswith("/api/mode/"):
                    target = self.path.split("/api/mode/")[-1].upper().strip()
                    parent.engine.execute_mobile_command({"action": "set_mode", "mode": target})
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True, "mode": target}).encode("utf-8"))
                    return

                self.send_response(404)
                self.end_headers()

            def do_POST(self):
                parent.mobile_hits += 1
                parent.last_client_ip = self.client_address[0]

                if self.path == "/api/action":
                    length = int(self.headers.get("Content-Length", 0))
                    raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
                    try:
                        payload = json.loads(raw)
                        parent.engine.execute_mobile_command(payload)
                    except Exception:
                        pass
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(b'{"ok":true}')
                    return

                self.send_response(404)
                self.end_headers()

        for p in (self.port, self.port + 1, self.port + 2):
            try:
                self.server = ThreadingHTTPServer(("0.0.0.0", p), Handler)
                self.port = p
                self.url = f"http://{self.lan_ip}:{self.port}"
                self.server.serve_forever()
                break
            except OSError:
                continue

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
            except Exception:
                pass


# =====================================================================
# NATYWNY KLIENT HOME ASSISTANT WEBSOCKET API (RFC 6455 + FRAGMENTACJA)
# =====================================================================
class HAWebSocketClient:
    def __init__(self, ha_url: str, token: str, engine: "AmbientEngine"):
        self.ha_url = ha_url
        self.token = token
        self.engine = engine

        self.sock = None
        self._rx_buf = bytearray()
        self.connected = False
        self.running = True

        self.send_lock = threading.Lock()
        self.id_lock = threading.Lock()
        self._msg_id = 0
        self._pending_pings = {}
        self._pending_ct_calls = {}
        self._get_states_id = None

        self.worker_thread = threading.Thread(target=self._connection_loop, daemon=True)
        self.worker_thread.start()

    def _next_id(self) -> int:
        with self.id_lock:
            self._msg_id += 1
            return self._msg_id

    def _read_exact(self, n: int) -> bytes:
        while len(self._rx_buf) < n:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Zamknięto strumień WebSocket.")
            self._rx_buf.extend(chunk)
        out = bytes(self._rx_buf[:n])
        del self._rx_buf[:n]
        return out

    def _connect_socket(self):
        parsed = urlparse(self.ha_url)
        use_ssl = parsed.scheme in ("https", "wss")
        host = parsed.hostname or "localhost"
        port = parsed.port or (443 if use_ssl else 8123)
        path = "/api/websocket"

        raw_sock = socket.create_connection((host, port), timeout=3.0)
        raw_sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        if use_ssl:
            ctx = ssl.create_default_context()
            self.sock = ctx.wrap_socket(raw_sock, server_hostname=host)
        else:
            self.sock = raw_sock

        self._rx_buf.clear()
        ws_key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            f"Upgrade: websocket\r\n"
            f"Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {ws_key}\r\n"
            f"Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake.encode("ascii"))

        while b"\r\n\r\n" not in self._rx_buf:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("Błąd podczas WebSocket HTTP Handshake.")
            self._rx_buf.extend(chunk)

        sep_idx = self._rx_buf.index(b"\r\n\r\n") + 4
        header_text = bytes(self._rx_buf[:sep_idx]).decode("latin1", errors="ignore")
        del self._rx_buf[:sep_idx]

        if "101" not in header_text.splitlines()[0]:
            raise ConnectionError("Serwer odrzucił połączenie WebSocket.")

        self.sock.settimeout(None)

    def _send_frame(self, payload_bytes: bytes, opcode: int = 0x1):
        mask_key = os.urandom(4)
        length = len(payload_bytes)
        header = bytearray([0x80 | (opcode & 0x0F)])

        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))

        header.extend(mask_key)
        masked_payload = bytes(b ^ mask_key[i & 3] for i, b in enumerate(payload_bytes))

        with self.send_lock:
            if self.sock is not None:
                self.sock.sendall(header + masked_payload)

    def send_json(self, data: dict) -> bool:
        if not self.connected and data.get("type") != "auth":
            return False
        try:
            raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
            self._send_frame(raw, opcode=0x1)
            return True
        except Exception:
            self.connected = False
            return False

    def _recv_message(self) -> tuple[int, bytes]:
        """Odbiera pełną wiadomość RFC 6455, łącząc pofragmentowane ramki (FIN=0)."""
        full_payload = bytearray()
        first_opcode = None

        while True:
            b1, b2 = self._read_exact(2)
            fin = bool(b1 & 0x80)
            opcode = b1 & 0x0F
            is_masked = bool(b2 & 0x80)
            length = b2 & 0x7F

            if length == 126:
                (length,) = struct.unpack("!H", self._read_exact(2))
            elif length == 127:
                (length,) = struct.unpack("!Q", self._read_exact(8))

            mask_key = self._read_exact(4) if is_masked else None
            payload = self._read_exact(length)
            if is_masked and mask_key:
                payload = bytes(b ^ mask_key[i & 3] for i, b in enumerate(payload))

            if opcode in (0x8, 0x9, 0xA):
                return opcode, payload

            if first_opcode is None:
                first_opcode = opcode
            full_payload.extend(payload)

            if fin:
                return first_opcode or 0x1, bytes(full_payload)

    def _connection_loop(self):
        while self.running:
            try:
                self._connect_socket()

                while self.running:
                    opcode, payload = self._recv_message()
                    if opcode == 0x8:
                        break
                    if opcode == 0x9:
                        self._send_frame(payload, opcode=0xA)
                        continue
                    if opcode != 0x1:
                        continue

                    msg = json.loads(payload.decode("utf-8"))
                    msg_type = msg.get("type")

                    if msg_type == "auth_required":
                        self.send_json({"type": "auth", "access_token": self.token})

                    elif msg_type == "auth_ok":
                        self.connected = True
                        self._msg_id = 0
                        self._pending_pings.clear()
                        self._pending_ct_calls.clear()

                        self._get_states_id = self._next_id()
                        self.send_json({"id": self._get_states_id, "type": "get_states"})

                        sub_id = self._next_id()
                        self.send_json({
                            "id": sub_id,
                            "type": "subscribe_events",
                            "event_type": "state_changed",
                        })

                    elif msg_type == "auth_invalid":
                        self.connected = False
                        time.sleep(5.0)
                        break

                    elif msg_type == "result":
                        msg_id = msg.get("id")
                        t_sent = self._pending_pings.pop(msg_id, None)
                        if t_sent is not None:
                            self.engine.ha_ping_ms = (time.perf_counter() - t_sent) * 1000.0

                        if msg_id == self._get_states_id and msg.get("success"):
                            for state_obj in msg.get("result") or []:
                                self.engine.ingest_ha_state(state_obj, is_initial=True)

                        ct_info = self._pending_ct_calls.pop(msg_id, None)
                        if ct_info is not None and not msg.get("success", True):
                            eid, kelvin, bri, trans = ct_info
                            self.engine.light_caps[eid]["supports_ct"] = False
                            fallback_rgb = kelvin_to_rgb(kelvin)
                            self.call_light_turn_on(eid, rgb=fallback_rgb, bri=bri, transition=trans)

                    elif msg_type == "event":
                        ev = msg.get("event") or {}
                        if ev.get("event_type") == "state_changed":
                            new_state = (ev.get("data") or {}).get("new_state")
                            if new_state:
                                self.engine.ingest_ha_state(new_state, is_initial=False)

            except Exception:
                self.connected = False
                try:
                    if self.sock:
                        self.sock.close()
                except Exception:
                    pass
                self.sock = None
                if self.running:
                    time.sleep(1.5)

    def call_light_turn_on(self, entity_id: str, rgb=None, kelvin=None, bri: int = 255, transition: float = 0.2) -> bool:
        if not self.connected:
            return False

        msg_id = self._next_id()
        service_data = {
            "entity_id": entity_id,
            "brightness": int(np.clip(bri, 1, 255)),
            "transition": round(float(transition), 2),
        }

        if kelvin is not None:
            caps = self.engine.light_caps.get(entity_id, {})
            clamped_k = int(np.clip(kelvin, caps.get("min_k", 2000), caps.get("max_k", 6500)))
            service_data["color_temp_kelvin"] = clamped_k
            self._pending_ct_calls[msg_id] = (entity_id, clamped_k, bri, transition)
        elif rgb is not None:
            service_data["rgb_color"] = [int(rgb[0]), int(rgb[1]), int(rgb[2])]

        self._pending_pings[msg_id] = time.perf_counter()
        if len(self._pending_pings) > 60:
            self._pending_pings.clear()

        return self.send_json({
            "id": msg_id,
            "type": "call_service",
            "domain": "light",
            "service": "turn_on",
            "service_data": service_data,
        })

    def call_light_turn_off(self, entity_ids, transition: float = 0.8) -> bool:
        if not self.connected:
            return False
        msg_id = self._next_id()
        self._pending_pings[msg_id] = time.perf_counter()
        return self.send_json({
            "id": msg_id,
            "type": "call_service",
            "domain": "light",
            "service": "turn_off",
            "service_data": {
                "entity_id": entity_ids,
                "transition": round(float(transition), 2),
            },
        })

    def close(self):
        self.running = False
        self.connected = False
        try:
            if self.sock:
                self._send_frame(b"", opcode=0x8)
                self.sock.close()
        except Exception:
            pass


# =====================================================================
# GŁÓWNY SILNIK OŚWIETLENIA (AMBIENT ENGINE v7.0)
# =====================================================================
class AmbientEngine:
    def __init__(self, dev_mode=False):
        self.running = True
        self.mode = "IDLE"
        self.dev_mode = dev_mode
        self.ui_mode_callback = None

        self.wave_lock = threading.Lock()
        self.wave_token = 0
        self.wave_in_progress = False

        self.enabled_lights = {eid: True for eid in LIGHTS_CONFIG}

        self.auto_override_from_ha = True
        self._last_script_cmd_ts = {eid: 0.0 for eid in LIGHTS_CONFIG}
        self.last_override_notice = ""

        self.circadian_enabled = True

        self.light_caps = {
            eid: {"supports_ct": True, "min_k": 2000, "max_k": 6500}
            for eid in LIGHTS_CONFIG
        }

        self.min_brightness = 10
        self.saturation_boost = 1.35
        self.master_brightness = 1.00
        self.white_temp_kelvin = 4500
        self.smoothing_alpha = 0.35

        base_omega = np.pi / 3.0
        self.nati_offsets = {}
        self.nati_omegas = {}
        for idx, eid in enumerate(LIGHTS_CONFIG):
            self.nati_offsets[eid] = (idx * (2.0 * np.pi / len(LIGHTS_CONFIG))) + random.uniform(-0.35, 0.35)
            self.nati_omegas[eid] = base_omega * random.uniform(0.92, 1.08)

        self.smoothed_state = {}
        self.last_sent_state = {}
        self.current_ui_state = {
            eid: {"is_on": False, "rgb": (255, 210, 160), "bri": 0, "kelvin": 4000}
            for eid in LIGHTS_CONFIG
        }

        self.fps = 0.0
        self.frame_time_ms = 0.0
        self.ha_ping_ms = 0.0
        self.luma_left = 0.0
        self.luma_right = 0.0
        self.crop_info = "Pełny obraz"

        self.user_presets = self._load_presets_from_disk()

        self.http = urllib3.PoolManager(
            headers={
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json",
            },
            num_pools=4,
            maxsize=10
        )
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.spotify_sync = SpotifyBeatSync(self)
        self.ws_client = HAWebSocketClient(HA_URL, HA_TOKEN, self)
        self.mobile_server = MobileRemoteServer(self, port=MOBILE_PORT)

    # -----------------------------------------------------------------
    # API DLA SERWERA MOBILNEGO (SYNCHRONIZACJA TELEFON <-> MACOS <-> HA)
    # -----------------------------------------------------------------
    def export_mobile_state(self) -> dict:
        lights_payload = []
        for eid, cfg in LIGHTS_CONFIG.items():
            st = self.current_ui_state[eid]
            is_on = bool(st.get("is_on", False) and st.get("bri", 0) > 0)
            bri = int(st.get("bri", 0))
            rgb = st.get("rgb", (255, 210, 160))
            lights_payload.append({
                "id": eid,
                "name": cfg["name"],
                "icon": cfg.get("icon", "💡"),
                "is_on": is_on,
                "in_sync": bool(self.enabled_lights.get(eid, True)),
                "bri": bri if bri > 0 else 200,
                "bri_pct": int((bri / 255.0) * 100) if is_on else 0,
                "kelvin": int(st.get("kelvin", 4000)),
                "hex": rgb_to_hex(rgb),
            })

        return {
            "mode": self.mode,
            "ws_online": self.ws_client.connected,
            "ping_ms": self.ha_ping_ms,
            "fps": self.fps,
            "sync_count": sum(1 for v in self.enabled_lights.values() if v),
            "master_brightness": self.master_brightness,
            "strobe_density": self.spotify_sync.strobe_density,
            "white_temp_kelvin": self.white_temp_kelvin,
            "saturation_boost": self.saturation_boost,
            "presets": list(self.user_presets.keys()),
            "spotify": {
                "is_playing": self.spotify_sync.is_playing,
                "title": self.spotify_sync.title,
                "artist": self.spotify_sync.artist,
                "bpm": self.spotify_sync.bpm,
                "hex1": rgb_to_hex(self.spotify_sync.color1_rgb),
                "hex2": rgb_to_hex(self.spotify_sync.color2_rgb),
            },
            "lights": lights_payload,
        }

    def execute_mobile_command(self, payload: dict):
        action = payload.get("action")
        if action == "set_mode":
            m = str(payload.get("mode", "IDLE")).upper()
            if m in ("OFF", "SLEEP"):
                self.turn_off_lights_and_standby()
                if self.ui_mode_callback:
                    self.ui_mode_callback("IDLE", "📱 Pilot Mobilny: Wygaszono wszystkie światła")
            elif m == "MAX_WHITE":
                self.set_max_white_mode()
                if self.ui_mode_callback:
                    self.ui_mode_callback("MAX_WHITE", "📱 Pilot Mobilny: Włączono ☀️ MAX BIEL (100%)")
            elif m == "IDLE":
                self.set_manual_passthrough()
                if self.ui_mode_callback:
                    self.ui_mode_callback("IDLE", "📱 Pilot Mobilny: Przełączono na 🎛️ Tryb Ręczny")
            elif m in ("ZWYKLY", "GAMING", "FILM", "NATI", "SPOTIFY"):
                if m == "SPOTIFY":
                    self.spotify_sync.trigger_immediate_poll()
                self.trigger_spatial_wave(m)
                if self.ui_mode_callback:
                    self.ui_mode_callback(m, f"📱 Pilot Mobilny: Uruchomiono scenę {m}")

        elif action == "sleep_all":
            self.turn_off_lights_and_standby()
            if self.ui_mode_callback:
                self.ui_mode_callback("IDLE", "📱 Pilot Mobilny: Wygaszono pokój")

        elif action == "sync_all":
            state = bool(payload.get("state", True))
            for eid in LIGHTS_CONFIG:
                self.enabled_lights[eid] = state
                self.last_sent_state.pop(eid, None)

        elif action == "set_global":
            if "master_brightness" in payload:
                self.master_brightness = float(np.clip(payload["master_brightness"], 0.15, 1.50))
            if "strobe_density" in payload:
                self.spotify_sync.strobe_density = int(np.clip(payload["strobe_density"], 1, 9))
            if "white_temp_kelvin" in payload:
                self.white_temp_kelvin = int(np.clip(payload["white_temp_kelvin"], 2200, 6500))
            if "saturation_boost" in payload:
                self.saturation_boost = float(np.clip(payload["saturation_boost"], 0.8, 2.2))
            if self.mode == "MAX_WHITE":
                self.set_max_white_mode()

        elif action == "set_light":
            eid = payload.get("entity_id")
            if eid in LIGHTS_CONFIG:
                rgb = payload.get("rgb")
                if "hex" in payload and payload["hex"]:
                    rgb = hex_to_rgb(payload["hex"])
                kelvin = payload.get("kelvin")
                bri = payload.get("bri")
                self.manual_set_light(eid, rgb=rgb, kelvin=kelvin, bri=bri, transition=0.2)

        elif action == "toggle_power":
            eid = payload.get("entity_id")
            if eid in LIGHTS_CONFIG:
                self.manual_toggle_power(eid)

        elif action == "toggle_sync":
            eid = payload.get("entity_id")
            if eid in LIGHTS_CONFIG:
                self.toggle_light_participation(eid)

        elif action == "load_preset":
            name = payload.get("name")
            if name:
                self.activate_user_preset(name)
                if self.ui_mode_callback:
                    self.ui_mode_callback("IDLE", f"📱 Pilot Mobilny: Wczytano scenę '{name}'")

        elif action == "save_preset":
            name = payload.get("name")
            if name:
                self.save_current_as_preset(name)
                if self.ui_mode_callback:
                    self.ui_mode_callback(self.mode, f"📱 Pilot Mobilny: Zapisano scenę '{name}'")

    # -----------------------------------------------------------------
    # OBSŁUGA ZAPISYWANIA PRESETÓW SCEN I POZYCJI LAMP NA DYSKU
    # -----------------------------------------------------------------
    def _load_presets_from_disk(self) -> dict:
        default_presets = {
            "Cyber Noc": {
                "lights": {
                    eid: {"is_on": True, "rgb": [0, 230, 255] if "l" in eid else [255, 0, 140], "bri": 190, "kelvin": None}
                    for eid in LIGHTS_CONFIG
                }
            },
            "Ciepły Relaks": {
                "lights": {
                    eid: {"is_on": True, "rgb": list(kelvin_to_rgb(2600)), "bri": 140, "kelvin": 2600}
                    for eid in LIGHTS_CONFIG
                }
            },
        }
        if PRESETS_FILE.exists():
            try:
                raw = json.loads(PRESETS_FILE.read_text(encoding="utf-8"))
                saved_positions = raw.get("_map_positions", {})
                for eid, pos in saved_positions.items():
                    if eid in LIGHTS_CONFIG and isinstance(pos, list) and len(pos) == 2:
                        LIGHTS_CONFIG[eid]["pos"] = [float(pos[0]), float(pos[1])]
                return raw.get("presets", default_presets)
            except Exception:
                pass
        return default_presets

    def save_presets_to_disk(self):
        data = {
            "_map_positions": {eid: cfg["pos"] for eid, cfg in LIGHTS_CONFIG.items()},
            "presets": self.user_presets,
        }
        try:
            PRESETS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    def save_current_as_preset(self, name: str):
        clean_name = name.strip()
        if not clean_name:
            return
        snapshot = {}
        for eid, st in self.current_ui_state.items():
            snapshot[eid] = {
                "is_on": bool(st.get("is_on", True)),
                "rgb": list(st.get("rgb", (255, 220, 180))),
                "bri": int(st.get("bri", 200)),
                "kelvin": st.get("kelvin"),
            }
        self.user_presets[clean_name] = {"lights": snapshot}
        self.save_presets_to_disk()

    def activate_user_preset(self, name: str):
        preset = self.user_presets.get(name)
        if not preset:
            return
        self.set_manual_passthrough()
        lights_data = preset.get("lights", {})
        for eid, cfg in lights_data.items():
            if eid not in LIGHTS_CONFIG:
                continue
            if not cfg.get("is_on", True) or cfg.get("bri", 0) <= 0:
                self.current_ui_state[eid]["is_on"] = False
                self.current_ui_state[eid]["bri"] = 0
                self._mark_script_cmd(eid)
                self._turn_off_entities([eid], transition=0.8)
            else:
                rgb = tuple(cfg.get("rgb", [255, 220, 180]))
                bri = int(cfg.get("bri", 200))
                kelvin = cfg.get("kelvin")
                self.manual_set_light(eid, rgb=rgb, kelvin=kelvin, bri=bri, transition=0.8)

    # -----------------------------------------------------------------
    # SYNCHRONIZACJA STANU Z HOME ASSISTANTEM + AUTO-OVERRIDE + MEDIA_PLAYER
    # -----------------------------------------------------------------
    def _mark_script_cmd(self, entity_id: str):
        self._last_script_cmd_ts[entity_id] = time.perf_counter()

    def ingest_ha_state(self, state_obj: dict, is_initial: bool = False):
        entity_id = state_obj.get("entity_id") or ""

        # Natychmiastowe wykrywanie pauzy/zmiany utworu z encji Spotify w Home Assistant
        if entity_id.startswith("media_player.spotify"):
            state_str = state_obj.get("state")
            was_playing = self.spotify_sync.is_playing
            if state_str in ("paused", "idle", "off", "standby"):
                self.spotify_sync.is_playing = False
            elif state_str == "playing":
                self.spotify_sync.is_playing = True
                if not is_initial and not was_playing:
                    self.spotify_sync.trigger_immediate_poll()
            return

        if entity_id not in LIGHTS_CONFIG:
            return

        attrs = state_obj.get("attributes") or {}
        color_modes = attrs.get("supported_color_modes")

        if isinstance(color_modes, list) and len(color_modes) > 0:
            supports_ct = "color_temp" in color_modes
            min_k = int(attrs.get("min_color_temp_kelvin") or 2000)
            max_k = int(attrs.get("max_color_temp_kelvin") or 6500)
            self.light_caps[entity_id] = {
                "supports_ct": supports_ct,
                "min_k": min_k,
                "max_k": max_k,
            }

        state_str = state_obj.get("state")
        bri = int(attrs.get("brightness") or 0) if state_str == "on" else 0
        rgb = attrs.get("rgb_color")
        kelvin = attrs.get("color_temp_kelvin")

        now_perf = time.perf_counter()
        time_since_our_cmd = now_perf - self._last_script_cmd_ts.get(entity_id, 0.0)

        # W trybie SPOTIFY (przez dynamiczne skoki jasności Strobe) okno ochronne wynosi 3.0s
        override_grace = 3.0 if self.mode == "SPOTIFY" else 1.35

        if (
            not is_initial
            and self.auto_override_from_ha
            and self.mode != "IDLE"
            and not self.wave_in_progress
            and self.enabled_lights.get(entity_id, True)
            and time_since_our_cmd > override_grace
        ):
            prev_sent = self.last_sent_state.get(entity_id)
            external_change = False
            if state_str == "off":
                external_change = True
            elif prev_sent is not None and self.mode != "SPOTIFY":
                sent_rgb, sent_bri, _ = prev_sent
                if abs(bri - sent_bri) > 22:
                    external_change = True
                elif rgb and len(rgb) == 3:
                    c_diff = abs(int(rgb[0]) - sent_rgb[0]) + abs(int(rgb[1]) - sent_rgb[1]) + abs(int(rgb[2]) - sent_rgb[2])
                    if c_diff > 45:
                        external_change = True

            if external_change:
                self.enabled_lights[entity_id] = False
                self.last_override_notice = f"✋ Auto-Override z HA: {LIGHTS_CONFIG[entity_id]['name']}"

        if is_initial or self.mode == "IDLE" or not self.enabled_lights.get(entity_id, True):
            prev_ui = self.current_ui_state[entity_id]
            if state_str == "off":
                self.current_ui_state[entity_id] = {
                    "is_on": False,
                    "rgb": prev_ui["rgb"],
                    "bri": 0,
                    "kelvin": prev_ui.get("kelvin", 4000),
                }
            elif state_str == "on":
                if kelvin:
                    ui_rgb = kelvin_to_rgb(int(kelvin))
                    k_val = int(kelvin)
                elif rgb and len(rgb) == 3:
                    ui_rgb = (int(rgb[0]), int(rgb[1]), int(rgb[2]))
                    k_val = prev_ui.get("kelvin", 4000)
                else:
                    ui_rgb = (255, 220, 180)
                    k_val = 4000

                self.current_ui_state[entity_id] = {
                    "is_on": True,
                    "rgb": ui_rgb,
                    "bri": bri if bri > 0 else 255,
                    "kelvin": k_val,
                }

    # -----------------------------------------------------------------
    # BEZPOŚREDNIE STEROWANIE STUDYJNE
    # -----------------------------------------------------------------
    def manual_set_light(self, entity_id: str, rgb=None, kelvin=None, bri: int = None, transition: float = 0.25):
        if self.mode not in ("IDLE", "MAX_WHITE") and self.enabled_lights.get(entity_id, True):
            self.enabled_lights[entity_id] = False

        cur = self.current_ui_state[entity_id]
        target_bri = int(np.clip(bri if bri is not None else (cur["bri"] or 200), 1, 255))

        if kelvin is not None:
            target_k = int(np.clip(kelvin, 2000, 6500))
            target_rgb = kelvin_to_rgb(target_k)
        elif rgb is not None:
            target_rgb = (int(np.clip(rgb[0], 0, 255)), int(np.clip(rgb[1], 0, 255)), int(np.clip(rgb[2], 0, 255)))
            target_k = cur.get("kelvin", 4000)
        else:
            target_rgb = cur["rgb"] if any(cur["rgb"]) else (255, 220, 180)
            target_k = cur.get("kelvin", 4000)

        self.current_ui_state[entity_id] = {
            "is_on": True,
            "rgb": target_rgb,
            "bri": target_bri,
            "kelvin": target_k,
        }
        self._mark_script_cmd(entity_id)
        self._send_direct_ha(entity_id, rgb=target_rgb if kelvin is None else None, kelvin=kelvin, bri=target_bri, transition=transition)

    def manual_toggle_power(self, entity_id: str) -> bool:
        if self.mode not in ("IDLE", "MAX_WHITE") and self.enabled_lights.get(entity_id, True):
            self.enabled_lights[entity_id] = False

        cur = self.current_ui_state[entity_id]
        new_on = not cur.get("is_on", False)
        self._mark_script_cmd(entity_id)
        if not new_on:
            self.current_ui_state[entity_id]["is_on"] = False
            self.current_ui_state[entity_id]["bri"] = 0
            self._turn_off_entities([entity_id], transition=0.5)
        else:
            restore_bri = 220
            restore_rgb = cur["rgb"] if any(cur["rgb"]) else (255, 215, 170)
            self.current_ui_state[entity_id]["is_on"] = True
            self.current_ui_state[entity_id]["bri"] = restore_bri
            self.current_ui_state[entity_id]["rgb"] = restore_rgb
            self._send_direct_ha(entity_id, rgb=restore_rgb, bri=restore_bri, transition=0.4)
        return new_on

    def manual_apply_to_all(self, rgb=None, kelvin=None, bri: int = 255):
        self.set_manual_passthrough()
        for eid in LIGHTS_CONFIG:
            self.manual_set_light(eid, rgb=rgb, kelvin=kelvin, bri=bri, transition=0.6)

    def _send_direct_ha(self, entity_id: str, rgb=None, kelvin=None, bri: int = 255, transition: float = 0.25):
        self._mark_script_cmd(entity_id)
        use_kelvin = (
            kelvin is not None
            and self.light_caps.get(entity_id, {}).get("supports_ct", True)
        )
        if self.ws_client.connected:
            if use_kelvin:
                if self.ws_client.call_light_turn_on(entity_id, kelvin=kelvin, bri=bri, transition=transition):
                    return
            else:
                send_rgb = rgb if rgb is not None else kelvin_to_rgb(kelvin or 4000)
                if self.ws_client.call_light_turn_on(entity_id, rgb=send_rgb, bri=bri, transition=transition):
                    return

        def _rest_fallback():
            url = f"{HA_URL}/api/services/light/turn_on"
            payload = {
                "entity_id": entity_id,
                "brightness": int(np.clip(bri, 1, 255)),
                "transition": round(float(transition), 2),
            }
            if use_kelvin:
                caps = self.light_caps.get(entity_id, {})
                payload["color_temp_kelvin"] = int(np.clip(kelvin, caps.get("min_k", 2000), caps.get("max_k", 6500)))
            else:
                send_rgb = rgb if rgb is not None else kelvin_to_rgb(kelvin or 4000)
                payload["rgb_color"] = [int(send_rgb[0]), int(send_rgb[1]), int(send_rgb[2])]
            try:
                encoded = json.dumps(payload).encode("utf-8")
                self.http.request("POST", url, body=encoded, timeout=0.8)
            except Exception:
                pass

        self.executor.submit(_rest_fallback)

    # -----------------------------------------------------------------
    # ZARZĄDZANIE TOKENEM ANULOWANIA FALI I SCENAMI
    # -----------------------------------------------------------------
    def _advance_wave_token(self) -> int:
        with self.wave_lock:
            self.wave_token += 1
            self.wave_in_progress = False
            return self.wave_token

    def _interruptible_sleep(self, duration: float, token: int) -> bool:
        end_time = time.perf_counter() + duration
        while time.perf_counter() < end_time:
            if not self.running or self.wave_token != token:
                return False
            time.sleep(min(0.015, max(0.0, end_time - time.perf_counter())))
        return self.running and (self.wave_token == token)

    def toggle_light_participation(self, entity_id: str) -> bool:
        new_state = not self.enabled_lights[entity_id]
        self.enabled_lights[entity_id] = new_state
        self.last_sent_state.pop(entity_id, None)
        self.smoothed_state.pop(entity_id, None)
        return new_state

    def _turn_off_entities(self, entity_ids: list, transition: float = 0.8):
        if not entity_ids:
            return
        for eid in entity_ids:
            self._mark_script_cmd(eid)
        if self.ws_client.call_light_turn_off(entity_ids, transition=transition):
            return

        def _rest_off():
            url = f"{HA_URL}/api/services/light/turn_off"
            payload = {"entity_id": entity_ids, "transition": round(float(transition), 2)}
            try:
                encoded = json.dumps(payload).encode("utf-8")
                self.http.request("POST", url, body=encoded, timeout=1.0)
            except Exception:
                pass

        self.executor.submit(_rest_off)

    def update_light(self, entity_id, rgb=None, bri=255, transition=0.2, force=False, kelvin=None, expected_token=None):
        if not self.enabled_lights.get(entity_id, True) or self.mode == "IDLE":
            return
        if expected_token is not None and self.wave_token != expected_token:
            return

        bri = int(np.clip(bri, 1, 255))
        if kelvin is not None:
            kelvin = int(np.clip(kelvin, 1800, 6500))
            ui_rgb = kelvin_to_rgb(kelvin)
        else:
            ui_rgb = (
                int(np.clip(rgb[0], 0, 255)),
                int(np.clip(rgb[1], 0, 255)),
                int(np.clip(rgb[2], 0, 255)),
            )

        self.current_ui_state[entity_id] = {
            "is_on": True,
            "rgb": ui_rgb,
            "bri": bri,
            "kelvin": kelvin or self.current_ui_state[entity_id].get("kelvin", 4000),
        }

        prev = self.last_sent_state.get(entity_id)
        if not force and prev is not None:
            prev_rgb, prev_bri, prev_kelvin = prev
            bri_diff = abs(bri - prev_bri)
            if kelvin is not None and prev_kelvin is not None:
                if abs(kelvin - prev_kelvin) < 35 and bri_diff < 3:
                    return
            elif kelvin is None and prev_kelvin is None:
                color_diff = (
                    abs(ui_rgb[0] - prev_rgb[0])
                    + abs(ui_rgb[1] - prev_rgb[1])
                    + abs(ui_rgb[2] - prev_rgb[2])
                )
                if color_diff < 8 and bri_diff < 3:
                    return

        self.last_sent_state[entity_id] = (ui_rgb, bri, kelvin)
        self._send_direct_ha(entity_id, rgb=ui_rgb, kelvin=kelvin, bri=bri, transition=transition)

    def set_manual_passthrough(self):
        self._advance_wave_token()
        self.mode = "IDLE"
        self.last_sent_state.clear()
        self.smoothed_state.clear()
        self.fps = 0.0
        self.frame_time_ms = 0.0

    def turn_off_lights_and_standby(self):
        self.set_manual_passthrough()
        all_entities = list(LIGHTS_CONFIG.keys())
        for eid in all_entities:
            self.current_ui_state[eid]["is_on"] = False
            self.current_ui_state[eid]["bri"] = 0
        self._turn_off_entities(all_entities, transition=1.4)

    def set_max_white_mode(self):
        self._advance_wave_token()
        self.mode = "MAX_WHITE"
        self.last_sent_state.clear()
        self.smoothed_state.clear()
        target_bri = int(np.clip(255 * self.master_brightness, 10, 255))
        for eid in LIGHTS_CONFIG:
            if self.enabled_lights.get(eid, True):
                self.update_light(
                    eid,
                    bri=target_bri,
                    transition=0.9,
                    force=True,
                    kelvin=self.white_temp_kelvin,
                )

    def turn_off_all_smoothly(self):
        self._advance_wave_token()
        self.running = False
        self.save_presets_to_disk()
        self.mobile_server.stop()
        all_entities = list(LIGHTS_CONFIG.keys())
        if not self.ws_client.call_light_turn_off(all_entities, transition=1.8):
            url = f"{HA_URL}/api/services/light/turn_off"
            try:
                encoded = json.dumps({"entity_id": all_entities, "transition": 1.8}).encode("utf-8")
                self.http.request("POST", url, body=encoded, timeout=1.2)
            except Exception:
                pass
        self.ws_client.close()

    def trigger_spatial_wave(self, target_mode: str):
        with self.wave_lock:
            self.wave_token += 1
            current_token = self.wave_token
            self.wave_in_progress = True
            self.mode = target_mode

        def wave_worker():
            if target_mode == "SPOTIFY":
                col1 = self.spotify_sync.color1_rgb
                col2 = self.spotify_sync.color2_rgb
                col3 = self.blend_colors(col1, col2, 0.5)
            else:
                _theme_name, col1, col2, col3 = random.choice(WAVE_THEMES)
                if random.random() > 0.5:
                    col1, col2 = col2, col1

            waves = [
                (col1, 225, 0.40, 0.11),
                (col2, 240, 0.45, 0.11),
                (col3, 110, 0.50, 0.08),
            ]

            for col, base_bri, trans, pause in waves:
                for group in FLOW_SEQUENCE:
                    if self.wave_token != current_token or not self.running:
                        return
                    active_in_group = [(eid, b) for eid, b in group if self.enabled_lights.get(eid, True)]
                    for eid, bri_scale in active_in_group:
                        self.update_light(
                            eid,
                            rgb=col,
                            bri=int(base_bri * bri_scale),
                            transition=trans,
                            force=True,
                            expected_token=current_token,
                        )
                    if active_in_group:
                        if not self._interruptible_sleep(pause, current_token):
                            return

            if not self._interruptible_sleep(0.25, current_token):
                return

            with self.wave_lock:
                if self.wave_token == current_token:
                    self.mode = target_mode
                    self.last_sent_state.clear()
                    self.wave_in_progress = False

        threading.Thread(target=wave_worker, daemon=True).start()

    # -----------------------------------------------------------------
    # ANALIZA OBRAZU I PĘTLA GŁÓWNA
    # -----------------------------------------------------------------
    def get_circadian_warmth_target(self) -> tuple[tuple[int, int, int], float]:
        hour = datetime.now().hour
        is_night = (hour >= 21 or hour < 7)
        if self.circadian_enabled and is_night:
            return kelvin_to_rgb(2400), 0.58
        return kelvin_to_rgb(min(self.white_temp_kelvin, 4200)), 0.35

    def auto_crop_black_bars(self, img):
        luma = 0.2126 * img[:, :, 0] + 0.7152 * img[:, :, 1] + 0.0722 * img[:, :, 2]
        row_means = np.mean(luma, axis=1)
        col_means = np.mean(luma, axis=0)

        valid_rows = np.where(row_means > 7.0)[0]
        valid_cols = np.where(col_means > 7.0)[0]

        h, w = img.shape[:2]
        if len(valid_rows) > h * 0.25 and len(valid_cols) > w * 0.25:
            r1, r2 = valid_rows[0], valid_rows[-1] + 1
            c1, c2 = valid_cols[0], valid_cols[-1] + 1
            if r1 > 2 or r2 < h - 2 or c1 > 2 or c2 < w - 2:
                self.crop_info = f"Aktywny ({c2-c1}x{r2-r1})"
                return img[r1:r2, c1:c2]

        self.crop_info = "Pełny obraz"
        return img

    def extract_vivid_color(self, region, edge_side=None):
        if region.size == 0:
            return (0, 0, 0), 0.0

        h, w, _ = region.shape
        r = region[:, :, 0].astype(np.float32)
        g = region[:, :, 1].astype(np.float32)
        b = region[:, :, 2].astype(np.float32)

        max_c = np.maximum(np.maximum(r, g), b)
        min_c = np.minimum(np.minimum(r, g), b)
        delta = max_c - min_c

        sat = np.where(max_c == 0, 0, delta / (max_c + 1e-5))
        val = max_c / 255.0

        luma_map = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255.0
        mean_luma = float(np.percentile(luma_map, 75))

        weights = 0.12 + (sat ** 1.4) * 5.0 * (val ** 0.8)

        if edge_side == "left":
            x_grad = np.linspace(2.5, 0.7, w, dtype=np.float32)[np.newaxis, :]
            weights *= x_grad
        elif edge_side == "right":
            x_grad = np.linspace(0.7, 2.5, w, dtype=np.float32)[np.newaxis, :]
            weights *= x_grad
        elif edge_side == "top":
            y_grad = np.linspace(2.5, 0.7, h, dtype=np.float32)[:, np.newaxis]
            weights *= y_grad

        w_sum = np.sum(weights) + 1e-5
        avg_r = np.sum(r * weights) / w_sum
        avg_g = np.sum(g * weights) / w_sum
        avg_b = np.sum(b * weights) / w_sum

        rgb = np.array([avg_r, avg_g, avg_b], dtype=np.float32)
        max_v = np.max(rgb)
        if max_v > 10:
            mean_v = np.mean(rgb)
            rgb = mean_v + (rgb - mean_v) * self.saturation_boost
            rgb = np.clip(rgb, 0, 255)
            scale = 255.0 / (np.max(rgb) + 1e-5)
            rgb = np.clip(rgb * scale, 0, 255)
        else:
            rgb = np.array([180, 160, 220], dtype=np.float32)

        return (int(rgb[0]), int(rgb[1]), int(rgb[2])), mean_luma

    def blend_colors(self, c1, c2, ratio=0.5):
        return (
            int(c1[0] * (1.0 - ratio) + c2[0] * ratio),
            int(c1[1] * (1.0 - ratio) + c2[1] * ratio),
            int(c1[2] * (1.0 - ratio) + c2[2] * ratio),
        )

    def run_loop(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1]

            while self.running:
                t_start = time.perf_counter()

                if self.wave_in_progress or self.mode == "IDLE":
                    time.sleep(0.12)
                    continue

                if self.mode == "MAX_WHITE":
                    target_bri = int(np.clip(255 * self.master_brightness, 10, 255))
                    for eid in LIGHTS_CONFIG:
                        if self.enabled_lights.get(eid, True):
                            self.update_light(
                                eid,
                                bri=target_bri,
                                transition=0.6,
                                kelvin=self.white_temp_kelvin,
                            )
                    self.frame_time_ms = (time.perf_counter() - t_start) * 1000.0
                    self.fps = 2.0
                    time.sleep(0.45)
                    continue

                if self.mode == "NATI":
                    now = time.time()
                    for eid in LIGHTS_CONFIG:
                        if not self.enabled_lights.get(eid, True):
                            continue

                        phase = now * self.nati_omegas[eid] + self.nati_offsets[eid]
                        mix_ratio = (1.0 - np.cos(phase)) * 0.5

                        shimmer_rgb = self.blend_colors(NATI_LIGHT_PINK, NATI_DARK_PURPLE, mix_ratio)
                        bri_factor = 0.42 * (1.0 - mix_ratio) + 0.16 * mix_ratio
                        target_bri = int(np.clip(255 * bri_factor * self.master_brightness, 8, 255))

                        self.update_light(eid, rgb=shimmer_rgb, bri=target_bri, transition=0.45)

                    self.frame_time_ms = (time.perf_counter() - t_start) * 1000.0
                    self.fps = 2.5
                    time.sleep(0.40)
                    continue

                # Obsługa nowego trybu SPOTIFY bez obciążania CPU zrzutami ekranu mss!
                if self.mode == "SPOTIFY":
                    self.spotify_sync.step_frame(t_start)
                    elapsed = time.perf_counter() - t_start
                    self.frame_time_ms = elapsed * 1000.0
                    sleep_target = 0.045  # ~22 FPS dla precyzyjnego wyzwalania stroboskopu BPM
                    self.fps = 1.0 / max(elapsed, sleep_target)
                    if elapsed < sleep_target:
                        time.sleep(sleep_target - elapsed)
                    continue

                raw_shot = sct.grab(monitor)
                img = np.frombuffer(raw_shot.bgra, dtype=np.uint8).reshape((raw_shot.height, raw_shot.width, 4))
                img_small = img[::8, ::8, 2::-1]

                cropped = self.auto_crop_black_bars(img_small)
                h, w, _ = cropped.shape

                left_region = cropped[:, :max(1, int(w * 0.35))]
                right_region = cropped[:, min(w - 1, int(w * 0.65)):]
                top_region = cropped[:max(1, int(h * 0.30)), :]

                col_left, luma_l = self.extract_vivid_color(left_region, edge_side="left")
                col_right, luma_r = self.extract_vivid_color(right_region, edge_side="right")
                col_top, luma_t = self.extract_vivid_color(top_region, edge_side="top")
                col_center = self.blend_colors(col_left, col_right, 0.5)
                luma_c = (luma_l + luma_r) * 0.5

                self.luma_left = luma_l
                self.luma_right = luma_r

                if self.mode == "GAMING":
                    alpha = self.smoothing_alpha
                    trans_time = 0.12
                    sleep_target = 0.08
                elif self.mode == "ZWYKLY":
                    alpha = self.smoothing_alpha * 0.70
                    trans_time = 0.22
                    sleep_target = 0.10
                else:  # FILM
                    alpha = self.smoothing_alpha * 0.45
                    trans_time = 0.35
                    sleep_target = 0.14

                warm_neutral, ceiling_warm_ratio = self.get_circadian_warmth_target()

                for eid, cfg in LIGHTS_CONFIG.items():
                    if not self.enabled_lights.get(eid, True):
                        continue

                    zone = cfg["zone"]
                    if self.mode == "GAMING":
                        max_factor = cfg["game_max"]
                    elif self.mode == "FILM":
                        max_factor = cfg["film_max"]
                    else:
                        max_factor = cfg["normal_max"]

                    max_factor = min(1.0, max_factor * self.master_brightness)

                    if zone == "left":
                        target_rgb, zone_luma = col_left, luma_l
                    elif zone == "right":
                        target_rgb, zone_luma = col_right, luma_r
                    elif zone == "top":
                        target_rgb, zone_luma = col_top, luma_t
                    elif zone == "left_mid":
                        target_rgb = self.blend_colors(col_left, col_top, 0.25)
                        zone_luma = luma_l * 0.85 + luma_t * 0.15
                    elif zone == "right_mid":
                        target_rgb = self.blend_colors(col_right, col_top, 0.25)
                        zone_luma = luma_r * 0.85 + luma_t * 0.15
                    elif zone == "left_deep":
                        target_rgb = self.blend_colors(col_left, col_center, 0.4)
                        zone_luma = (luma_l + luma_c) * 0.5
                    elif zone == "right_deep":
                        target_rgb = self.blend_colors(col_right, col_center, 0.4)
                        zone_luma = (luma_r + luma_c) * 0.5
                    else:
                        target_rgb, zone_luma = col_center, luma_c

                    if self.mode == "ZWYKLY" and zone not in ("left", "right"):
                        blend_ratio = ceiling_warm_ratio if cfg["is_ceiling"] else (ceiling_warm_ratio * 0.55)
                        target_rgb = self.blend_colors(target_rgb, warm_neutral, blend_ratio)

                    effective_min_bri = min(self.min_brightness, int(255 * max_factor * 0.6))
                    raw_bri = effective_min_bri + (zone_luma ** 1.15) * (255 * max_factor - effective_min_bri)
                    target_bri = float(np.clip(raw_bri, 2, 255 * max_factor))

                    if eid not in self.smoothed_state:
                        self.smoothed_state[eid] = (np.array(target_rgb, dtype=np.float32), target_bri)
                    else:
                        prev_rgb_arr, prev_b = self.smoothed_state[eid]
                        local_alpha = self.smoothing_alpha if (self.mode == "ZWYKLY" and zone in ("left", "right")) else alpha
                        new_rgb_arr = prev_rgb_arr * (1.0 - local_alpha) + np.array(target_rgb, dtype=np.float32) * local_alpha
                        new_b = prev_b * (1.0 - local_alpha) + target_bri * local_alpha
                        self.smoothed_state[eid] = (new_rgb_arr, new_b)

                    final_rgb, final_bri = self.smoothed_state[eid]
                    self.update_light(eid, rgb=final_rgb, bri=final_bri, transition=trans_time)

                elapsed = time.perf_counter() - t_start
                self.frame_time_ms = elapsed * 1000.0
                total_cycle = max(elapsed, sleep_target)
                self.fps = 1.0 / total_cycle

                if elapsed < sleep_target:
                    time.sleep(sleep_target - elapsed)


# =====================================================================
# KOMPONENT KARTY POJEDYNCZEJ LAMPY (STUDIO LIGHT CARD)
# =====================================================================
class LightControlCard(ctk.CTkFrame):
    def __init__(self, parent, entity_id: str, cfg: dict, engine: AmbientEngine, on_select_callback):
        super().__init__(
            parent,
            corner_radius=12,
            fg_color="#111827",
            border_width=1,
            border_color="#1E293B",
        )
        self.entity_id = entity_id
        self.cfg = cfg
        self.engine = engine
        self.on_select_callback = on_select_callback
        self._dragging_bri = False
        self._dragging_ct = False

        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 4))

        self.swatch_btn = ctk.CTkButton(
            top_row,
            text=cfg.get("icon", "💡"),
            width=34,
            height=34,
            corner_radius=8,
            fg_color="#1E293B",
            hover_color="#334155",
            font=ctk.CTkFont(size=15),
            command=lambda: self.on_select_callback(self.entity_id),
        )
        self.swatch_btn.pack(side="left", padx=(0, 8))

        title_box = ctk.CTkFrame(top_row, fg_color="transparent")
        title_box.pack(side="left", fill="x", expand=True)

        self.name_lbl = ctk.CTkLabel(
            title_box,
            text=cfg["name"],
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F8FAFC",
            anchor="w",
            cursor="hand2",
        )
        self.name_lbl.pack(fill="x")
        self.name_lbl.bind("<Button-1>", lambda _e: self.on_select_callback(self.entity_id))

        self.sub_lbl = ctk.CTkLabel(
            title_box,
            text="Połączono z HA",
            font=ctk.CTkFont(size=10),
            text_color="#94A3B8",
            anchor="w",
        )
        self.sub_lbl.pack(fill="x")

        self.sync_btn = ctk.CTkButton(
            top_row,
            text="🔗 SYNC",
            width=54,
            height=24,
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0F766E",
            hover_color="#0D9488",
            command=self.toggle_sync,
        )
        self.sync_btn.pack(side="right", padx=(4, 0))

        self.power_btn = ctk.CTkButton(
            top_row,
            text="ON",
            width=44,
            height=24,
            corner_radius=6,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.toggle_power,
        )
        self.power_btn.pack(side="right", padx=2)

        bri_row = ctk.CTkFrame(self, fg_color="transparent")
        bri_row.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(bri_row, text="🔆", font=ctk.CTkFont(size=11), width=18).pack(side="left")
        self.bri_slider = ctk.CTkSlider(
            bri_row,
            from_=1,
            to=255,
            height=14,
            button_color="#38BDF8",
            progress_color="#0284C7",
            command=self.on_bri_slide,
        )
        self.bri_slider.set(200)
        self.bri_slider.pack(side="left", fill="x", expand=True, padx=6)
        self.bri_slider.bind("<ButtonPress-1>", lambda _e: setattr(self, "_dragging_bri", True))
        self.bri_slider.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_dragging_bri", False))

        self.bri_val_lbl = ctk.CTkLabel(
            bri_row, text="0%", font=ctk.CTkFont(family="Menlo", size=10), width=34, anchor="e"
        )
        self.bri_val_lbl.pack(side="right")

        ct_row = ctk.CTkFrame(self, fg_color="transparent")
        ct_row.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(ct_row, text="🌡️", font=ctk.CTkFont(size=11), width=18).pack(side="left")
        self.ct_slider = ctk.CTkSlider(
            ct_row,
            from_=2000,
            to=6500,
            height=14,
            button_color="#FACC15",
            progress_color="#CA8A04",
            command=self.on_ct_slide,
        )
        self.ct_slider.set(4000)
        self.ct_slider.pack(side="left", fill="x", expand=True, padx=6)
        self.ct_slider.bind("<ButtonPress-1>", lambda _e: setattr(self, "_dragging_ct", True))
        self.ct_slider.bind("<ButtonRelease-1>", lambda _e: setattr(self, "_dragging_ct", False))

        self.ct_val_lbl = ctk.CTkLabel(
            ct_row, text="4000K", font=ctk.CTkFont(family="Menlo", size=10), width=38, anchor="e"
        )
        self.ct_val_lbl.pack(side="right")

        palette_row = ctk.CTkFrame(self, fg_color="transparent")
        palette_row.pack(fill="x", padx=10, pady=(4, 8))

        for _name, rgb, kelvin in QUICK_PALETTE:
            hex_c = rgb_to_hex(rgb)
            btn = ctk.CTkButton(
                palette_row,
                text="",
                width=22,
                height=16,
                corner_radius=4,
                fg_color=hex_c,
                hover_color=hex_c,
                border_width=1,
                border_color="#334155",
                command=lambda r=rgb, k=kelvin: self.apply_quick_color(r, k),
            )
            btn.pack(side="left", padx=2, expand=True)

    def toggle_power(self):
        self.engine.manual_toggle_power(self.entity_id)
        self.on_select_callback(self.entity_id)

    def toggle_sync(self):
        self.engine.toggle_light_participation(self.entity_id)

    def on_bri_slide(self, val):
        bri = int(val)
        pct = int((bri / 255.0) * 100)
        self.bri_val_lbl.configure(text=f"{pct}%")
        self.engine.manual_set_light(self.entity_id, bri=bri, transition=0.15)

    def on_ct_slide(self, val):
        kelvin = int(val)
        self.ct_val_lbl.configure(text=f"{kelvin}K")
        self.engine.manual_set_light(self.entity_id, kelvin=kelvin, transition=0.2)

    def apply_quick_color(self, rgb, kelvin):
        if kelvin is not None:
            self.engine.manual_set_light(self.entity_id, kelvin=kelvin, transition=0.3)
        else:
            self.engine.manual_set_light(self.entity_id, rgb=rgb, transition=0.3)
        self.on_select_callback(self.entity_id)

    def refresh_from_state(self, is_selected: bool):
        state = self.engine.current_ui_state[self.entity_id]
        is_on = state.get("is_on", False) and state.get("bri", 0) > 0
        rgb = state.get("rgb", (0, 0, 0))
        bri = state.get("bri", 0)
        kelvin = state.get("kelvin", 4000)
        in_sync = self.engine.enabled_lights.get(self.entity_id, True)
        is_flashing = (self.engine.mode == "SPOTIFY" and self.entity_id in self.engine.spotify_sync.active_flashes)

        if is_flashing:
            self.configure(border_color="#4ADE80", border_width=2)
        else:
            self.configure(border_color="#38BDF8" if is_selected else "#1E293B", border_width=2 if is_selected else 1)

        if is_on:
            hex_col = rgb_to_hex(rgb)
            bri_pct = int((bri / 255.0) * 100)
            self.swatch_btn.configure(fg_color=hex_col)
            self.power_btn.configure(text="ON", fg_color="#2563EB", hover_color="#1D4ED8")
            flash_tag = " ⚡FLASH" if is_flashing else ""
            self.sub_lbl.configure(text=f"Aktywna • {bri_pct}% • RGB {rgb}{flash_tag}", text_color="#4ADE80" if is_flashing else "#94A3B8")
            if not self._dragging_bri:
                self.bri_slider.set(bri)
                self.bri_val_lbl.configure(text=f"{bri_pct}%")
        else:
            self.swatch_btn.configure(fg_color="#1E293B")
            self.power_btn.configure(text="OFF", fg_color="#334155", hover_color="#475569")
            self.sub_lbl.configure(text="Wyłączona (Standby)", text_color="#64748B")
            if not self._dragging_bri:
                self.bri_val_lbl.configure(text="0%")

        if not self._dragging_ct:
            self.ct_slider.set(kelvin)
            self.ct_val_lbl.configure(text=f"{kelvin}K")

        if in_sync:
            self.sync_btn.configure(text="🔗 SYNC", fg_color="#0F766E")
        else:
            self.sync_btn.configure(text="✋ RĘCZNY", fg_color="#475569")


# =====================================================================
# GŁÓWNE OKNO APLIKACJI: SPATIAL AMBIENT STUDIO v7.0 (DESKTOP + MOBILE)
# =====================================================================
class AmbientStudioApp(ctk.CTk):
    def __init__(self, engine: AmbientEngine):
        super().__init__()
        self.engine = engine
        self.engine.ui_mode_callback = self._on_external_mode_change
        self.selected_entity = "light.ambientl"
        self._dragging_map_entity = None
        self._last_preset_count = len(self.engine.user_presets)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("✨ Spatial Ambient Studio v7.0 — Spotify Beat & Mobile PWA Center")
        self.geometry("1240x860")
        self.minsize(1120, 780)
        self.configure(fg_color="#090D16")
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

        self.cards = {}
        self._build_top_bar()
        self._build_main_workspace()
        self._build_bottom_bar()
        self._setup_keybindings()

        self.after(100, self.update_telemetry_loop)

    def _on_external_mode_change(self, mode_key: str, status_msg: str):
        self.after(0, lambda: self._apply_external_ui_sync(mode_key, status_msg))

    def _apply_external_ui_sync(self, mode_key: str, status_msg: str):
        self._highlight_mode_btn(mode_key)
        self.status_label.configure(text=status_msg, text_color="#38BDF8")
        if len(self.engine.user_presets) != self._last_preset_count:
            self._last_preset_count = len(self.engine.user_presets)
            self.refresh_user_presets_ui()

    # -----------------------------------------------------------------
    # SKRÓTY KLAWISZOWE (1-6, 0)
    # -----------------------------------------------------------------
    def _setup_keybindings(self):
        self.bind("1", lambda e: self._hotkey_action("ZWYKLY") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("2", lambda e: self._hotkey_action("GAMING") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("3", lambda e: self._hotkey_action("FILM") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("4", lambda e: self._hotkey_action("NATI") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("5", lambda e: self._hotkey_action("MAX_WHITE") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("6", lambda e: self._hotkey_action("SPOTIFY") if not isinstance(e.widget, ctk.CTkEntry) else None)
        self.bind("0", lambda e: self._hotkey_action("IDLE") if not isinstance(e.widget, ctk.CTkEntry) else None)

        if False and HAS_PYNPUT:
            try:
                hotkeys = pynput_keyboard.GlobalHotKeys({
                    "<cmd>+<shift>+1": lambda: self.after(0, lambda: self.switch_mode("ZWYKLY")),
                    "<cmd>+<shift>+2": lambda: self.after(0, lambda: self.switch_mode("GAMING")),
                    "<cmd>+<shift>+3": lambda: self.after(0, lambda: self.switch_mode("FILM")),
                    "<cmd>+<shift>+4": lambda: self.after(0, lambda: self.switch_mode("NATI")),
                    "<cmd>+<shift>+5": lambda: self.after(0, self.activate_max_white),
                    "<cmd>+<shift>+6": lambda: self.after(0, lambda: self.switch_mode("SPOTIFY")),
                    "<cmd>+<shift>+0": lambda: self.after(0, lambda: self.switch_mode("IDLE")),
                })
                hotkeys.daemon = True
                hotkeys.start()
            except Exception:
                pass

    def _hotkey_action(self, mode_key: str):
        if self.focus_get() == self.preset_entry:
            return
        self.switch_mode(mode_key)

    # -----------------------------------------------------------------
    # GÓRNY PASEK NAWIGACJI + TELEMETRIA SPOTIFY
    # -----------------------------------------------------------------
    def _build_top_bar(self):
        self.top_bar = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0, height=64)
        self.top_bar.pack(fill="x", side="top")

        title_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)

        ctk.CTkLabel(
            title_frame,
            text="✨ SPATIAL AMBIENT STUDIO v7.0",
            font=ctk.CTkFont(size=19, weight="bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w")

        self.status_label = ctk.CTkLabel(
            title_frame,
            text=f"📱 Pilot Mobilny aktywny: {self.engine.mobile_server.url}  |  Klawisz [6] ➔ Spotify Beat",
            font=ctk.CTkFont(size=12),
            text_color="#38BDF8",
        )
        self.status_label.pack(anchor="w")

        telemetry_box = ctk.CTkFrame(self.top_bar, fg_color="#1E293B", corner_radius=10)
        telemetry_box.pack(side="right", padx=20, pady=12)

        self.sp_swatch1 = ctk.CTkFrame(telemetry_box, width=18, height=18, corner_radius=5, fg_color="#1ED760")
        self.sp_swatch1.pack(side="left", padx=(10, 3), pady=6)
        self.sp_swatch2 = ctk.CTkFrame(telemetry_box, width=18, height=18, corner_radius=5, fg_color="#6366F1")
        self.sp_swatch2.pack(side="left", padx=(0, 8), pady=6)

        self.sp_top_lbl = ctk.CTkLabel(
            telemetry_box,
            text="🎵 Spotify: Sprawdzanie...",
            font=ctk.CTkFont(family="Menlo", size=11, weight="bold"),
            text_color="#4ADE80",
        )
        self.sp_top_lbl.pack(side="left", padx=(0, 10), pady=6)

        self.mobile_btn = ctk.CTkButton(
            telemetry_box,
            text=f"📱 {self.engine.mobile_server.url}",
            height=28,
            corner_radius=8,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(family="Menlo", size=11, weight="bold"),
            command=self.open_mobile_info_modal,
        )
        self.mobile_btn.pack(side="left", padx=(4, 8), pady=6)

        self.ws_badge = ctk.CTkLabel(
            telemetry_box,
            text="● WS ŁĄCZENIE",
            font=ctk.CTkFont(family="Menlo", size=11, weight="bold"),
            text_color="#FACC15",
        )
        self.ws_badge.pack(side="left", padx=(4, 8), pady=8)

        self.metrics_lbl = ctk.CTkLabel(
            telemetry_box,
            text="RTT: 0.0 ms | FPS: 0.0 | Sync: 9/9",
            font=ctk.CTkFont(family="Menlo", size=11),
            text_color="#E2E8F0",
        )
        self.metrics_lbl.pack(side="left", padx=(0, 12), pady=8)

    def open_mobile_info_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("📱 Pilot Mobilny (Android / iOS / Home Assistant)")
        modal.geometry("540x380")
        modal.configure(fg_color="#0F172A")
        modal.attributes("-topmost", True)

        url = self.engine.mobile_server.url

        ctk.CTkLabel(
            modal,
            text="📱 STEROWANIE Z TELEFONU I TABLETU",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#38BDF8",
        ).pack(pady=(18, 6))

        ctk.CTkLabel(
            modal,
            text="1. Upewnij się, że telefon lub tablet jest w tej samej sieci Wi-Fi.\n"
                 "2. Otwórz przeglądarkę (Chrome / Safari) i wpisz poniższy adres:",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1",
            justify="center",
        ).pack(pady=4)

        url_entry = ctk.CTkEntry(
            modal, width=360, height=38, font=ctk.CTkFont(family="Menlo", size=15, weight="bold"), justify="center"
        )
        url_entry.insert(0, url)
        url_entry.configure(state="readonly")
        url_entry.pack(pady=8)

        ha_info = (
            "💡 Wskazówka dla Home Assistant (Bubble Card / Dashboard):\n"
            f"Możesz dodać kartę 'Strona internetowa (Webpage)' z adresem {url}\n"
            "lub wywoływać sceny przez Webhooki GET:\n"
            f"• {url}/api/mode/SPOTIFY\n"
            f"• {url}/api/mode/NATI\n"
            f"• {url}/api/mode/GAMING\n"
            f"• {url}/api/mode/MAX_WHITE\n"
            f"• {url}/api/mode/OFF"
        )
        box = ctk.CTkFrame(modal, fg_color="#111827", corner_radius=10)
        box.pack(fill="x", padx=24, pady=10)
        ctk.CTkLabel(
            box, text=ha_info, font=ctk.CTkFont(family="Menlo", size=11), text_color="#94A3B8", justify="left"
        ).pack(padx=14, pady=12, anchor="w")

        ctk.CTkLabel(
            modal,
            text=f"Ostatnie połączenie mobilne: {self.engine.mobile_server.last_client_ip} "
                 f"(Żądania: {self.engine.mobile_server.mobile_hits})",
            font=ctk.CTkFont(size=11),
            text_color="#4ADE80",
        ).pack(pady=4)

    # -----------------------------------------------------------------
    # GŁÓWNA PRZESTRZEŃ ROBOCZA
    # -----------------------------------------------------------------
    def _build_main_workspace(self):
        self.workspace = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace.pack(fill="both", expand=True, padx=16, pady=10)
        self.workspace.grid_columnconfigure(0, weight=0)
        self.workspace.grid_columnconfigure(1, weight=1)
        self.workspace.grid_columnconfigure(2, weight=0)
        self.workspace.grid_rowconfigure(0, weight=1)

        self._build_left_sidebar()
        self._build_center_panel()
        self._build_right_inspector()

    def _build_left_sidebar(self):
        sidebar = ctk.CTkFrame(self.workspace, width=265, corner_radius=14, fg_color="#0F172A")
        sidebar.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar,
            text="SCENY AUTOMATYCZNE (KLAWISZE 1-6, 0)",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B",
        ).pack(anchor="w", padx=14, pady=(10, 3))

        self.mode_buttons = {}
        modes = [
            ("SPOTIFY",   "🎵  [6] SPOTIFY (Beat & Okładka)", "#16A34A"),
            ("ZWYKLY",    "☕  [1] ZWYKŁY (Ciepły Ambient)",  "#0D9488"),
            ("GAMING",    "🎮  [2] GAMING (Ultra Szybki)",    "#2563EB"),
            ("FILM",      "🎬  [3] KINO / FILM (Płynny)",     "#D97706"),
            ("NATI",      "🌸  [4] NATI (Róż ⇄ Fiolet 3s)",   "#DB2777"),
            ("MAX_WHITE", "☀️  [5] PEŁNA BIEL (100% CCT)",    "#EAB308"),
            ("IDLE",      "🎛️  [0] TRYB RĘCZNY (HA Live)",    "#475569"),
        ]

        for key, label, active_col in modes:
            btn = ctk.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=33,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#475569" if key == "IDLE" else "#1E293B",
                hover_color=active_col,
                command=lambda k=key: self.switch_mode(k),
            )
            btn.pack(fill="x", padx=14, pady=2)
            self.mode_buttons[key] = (btn, active_col)

        ctk.CTkLabel(
            sidebar,
            text="CAŁY POKÓJ & INTELIGENCJA",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B",
        ).pack(anchor="w", padx=14, pady=(8, 3))

        quick_grid = ctk.CTkFrame(sidebar, fg_color="transparent")
        quick_grid.pack(fill="x", padx=12)
        quick_grid.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            quick_grid,
            text="💡 Biel 100%",
            height=28,
            fg_color="#1E293B",
            hover_color="#0284C7",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.activate_max_white,
        ).grid(row=0, column=0, padx=3, pady=2, sticky="ew")

        ctk.CTkButton(
            quick_grid,
            text="🌑 Zgaś pokój",
            height=28,
            fg_color="#1E293B",
            hover_color="#DC2626",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.sleep_all_lights,
        ).grid(row=0, column=1, padx=3, pady=2, sticky="ew")

        ctk.CTkButton(
            quick_grid,
            text="🔗 Sync 9/9",
            height=26,
            fg_color="#1E293B",
            hover_color="#0F766E",
            font=ctk.CTkFont(size=11),
            command=lambda: self.set_all_participation(True),
        ).grid(row=1, column=0, padx=3, pady=2, sticky="ew")

        ctk.CTkButton(
            quick_grid,
            text="✋ Ręczny 9/9",
            height=26,
            fg_color="#1E293B",
            hover_color="#475569",
            font=ctk.CTkFont(size=11),
            command=lambda: self.set_all_participation(False),
        ).grid(row=1, column=1, padx=3, pady=2, sticky="ew")

        smart_box = ctk.CTkFrame(sidebar, fg_color="#111827", corner_radius=10)
        smart_box.pack(fill="x", padx=14, pady=(6, 4))

        self.sw_override = ctk.CTkSwitch(
            smart_box,
            text="Auto-Override z HA",
            font=ctk.CTkFont(size=11),
            command=self.on_smart_switches,
        )
        self.sw_override.select()
        self.sw_override.pack(anchor="w", padx=10, pady=(6, 2))

        self.sw_circadian = ctk.CTkSwitch(
            smart_box,
            text="🌙 Night Shift (21:00+)",
            font=ctk.CTkFont(size=11),
            command=self.on_smart_switches,
        )
        self.sw_circadian.select()
        self.sw_circadian.pack(anchor="w", padx=10, pady=2)

        self.sw_ceiling_strobe = ctk.CTkSwitch(
            smart_box,
            text="⚡ Sufit błyska w Spotify",
            font=ctk.CTkFont(size=11),
            command=self.on_smart_switches,
        )
        self.sw_ceiling_strobe.deselect()
        self.sw_ceiling_strobe.pack(anchor="w", padx=10, pady=(2, 6))

        sliders_box = ctk.CTkFrame(sidebar, fg_color="#111827", corner_radius=10)
        sliders_box.pack(fill="x", padx=14, pady=4)

        self.lbl_master = ctk.CTkLabel(sliders_box, text="Skala Jasności: 100%", font=ctk.CTkFont(size=11))
        self.lbl_master.pack(anchor="w", padx=10, pady=(6, 0))
        self.s_master = ctk.CTkSlider(sliders_box, from_=0.15, to=1.50, height=13, command=self.on_global_sliders)
        self.s_master.set(self.engine.master_brightness)
        self.s_master.pack(fill="x", padx=10, pady=(1, 3))

        self.lbl_strobe = ctk.CTkLabel(sliders_box, text="Błyski Spotify naraz: 2 lampy", font=ctk.CTkFont(size=11, weight="bold"), text_color="#4ADE80")
        self.lbl_strobe.pack(anchor="w", padx=10)
        self.s_strobe = ctk.CTkSlider(
            sliders_box, from_=1, to=6, number_of_steps=5, height=13,
            button_color="#4ADE80", progress_color="#16A34A", command=self.on_global_sliders
        )
        self.s_strobe.set(self.engine.spotify_sync.strobe_density)
        self.s_strobe.pack(fill="x", padx=10, pady=(1, 3))

        self.lbl_kelvin = ctk.CTkLabel(sliders_box, text="Temp. Bieli: 4500K", font=ctk.CTkFont(size=11))
        self.lbl_kelvin.pack(anchor="w", padx=10)
        self.s_kelvin = ctk.CTkSlider(sliders_box, from_=2200, to=6500, height=13, command=self.on_global_sliders)
        self.s_kelvin.set(self.engine.white_temp_kelvin)
        self.s_kelvin.pack(fill="x", padx=10, pady=(1, 3))

        self.lbl_sat = ctk.CTkLabel(sliders_box, text="Nasycenie Kolorów: 1.35x", font=ctk.CTkFont(size=11))
        self.lbl_sat.pack(anchor="w", padx=10)
        self.s_sat = ctk.CTkSlider(sliders_box, from_=0.8, to=2.2, height=13, command=self.on_global_sliders)
        self.s_sat.set(self.engine.saturation_boost)
        self.s_sat.pack(fill="x", padx=10, pady=(1, 6))

    # -----------------------------------------------------------------
    # ŚRODKOWY PANEL: KARTY 3x3 + MAPA 2D
    # -----------------------------------------------------------------
    def _build_center_panel(self):
        center = ctk.CTkFrame(self.workspace, corner_radius=14, fg_color="#0F172A")
        center.grid(row=0, column=1, sticky="nsew")

        header_bar = ctk.CTkFrame(center, fg_color="transparent")
        header_bar.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header_bar,
            text="WSZYSTKIE STREFY ŚWIATŁA (KLIKNIJ 🔗 SYNC ABY WYBRAĆ LAMPY DO BŁYSKÓW)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(side="left")

        self.view_switcher = ctk.CTkSegmentedButton(
            header_bar,
            values=["🎛️ Mikser Kart (3x3)", "🗺️ Mapa Pokoju 2D (Drag & Drop)"],
            command=self.switch_center_view,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.view_switcher.set("🎛️ Mikser Kart (3x3)")
        self.view_switcher.pack(side="right")

        self.center_container = ctk.CTkFrame(center, fg_color="transparent")
        self.center_container.pack(fill="both", expand=True, padx=12, pady=(2, 12))

        self.grid_view = ctk.CTkFrame(self.center_container, fg_color="transparent")
        self.grid_view.pack(fill="both", expand=True)
        self.grid_view.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_view.grid_rowconfigure((0, 1, 2), weight=1)

        for idx, (eid, cfg) in enumerate(LIGHTS_CONFIG.items()):
            r, c = divmod(idx, 3)
            card = LightControlCard(
                self.grid_view,
                entity_id=eid,
                cfg=cfg,
                engine=self.engine,
                on_select_callback=self.select_entity_for_inspector,
            )
            card.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            self.cards[eid] = card

        self.map_view = ctk.CTkFrame(self.center_container, fg_color="#090D16", corner_radius=12)
        self.room_canvas = ctk.CTkCanvas(
            self.map_view, bg="#090D16", highlightthickness=0, cursor="hand2"
        )
        self.room_canvas.pack(fill="both", expand=True, padx=8, pady=8)
        self.room_canvas.bind("<ButtonPress-1>", self.on_room_canvas_press)
        self.room_canvas.bind("<B1-Motion>", self.on_room_canvas_drag)
        self.room_canvas.bind("<ButtonRelease-1>", self.on_room_canvas_release)

    # -----------------------------------------------------------------
    # PRAWY PANEL: KOŁO BARW HSV + WŁASNE SCENY
    # -----------------------------------------------------------------
    def _build_right_inspector(self):
        inspector = ctk.CTkFrame(self.workspace, width=290, corner_radius=14, fg_color="#0F172A")
        inspector.grid(row=0, column=2, sticky="ns", padx=(12, 0))
        inspector.grid_propagate(False)

        ctk.CTkLabel(
            inspector,
            text="INSPEKTOR & KOŁO BARW",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B",
        ).pack(anchor="w", padx=16, pady=(12, 2))

        self.insp_title = ctk.CTkLabel(
            inspector,
            text=LIGHTS_CONFIG[self.selected_entity]["name"],
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38BDF8",
        )
        self.insp_title.pack(anchor="w", padx=16)

        self.insp_entity_lbl = ctk.CTkLabel(
            inspector,
            text=self.selected_entity,
            font=ctk.CTkFont(family="Menlo", size=11),
            text_color="#64748B",
        )
        self.insp_entity_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        self.target_scope = ctk.CTkSegmentedButton(
            inspector,
            values=["🎯 Wybrana lampa", "🏠 Cały pokój (9)"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.target_scope.set("🎯 Wybrana lampa")
        self.target_scope.pack(fill="x", padx=16, pady=(0, 6))

        self.wheel_size = 195
        self.wheel_canvas = ctk.CTkCanvas(
            inspector,
            width=self.wheel_size,
            height=self.wheel_size,
            bg="#0F172A",
            highlightthickness=0,
            cursor="crosshair",
        )
        self.wheel_canvas.pack(pady=2)
        self._draw_hsv_color_wheel()
        self.wheel_cursor = self.wheel_canvas.create_oval(
            92, 92, 104, 104, outline="#FFFFFF", width=2, fill="#FFFFFF"
        )
        self.wheel_canvas.bind("<Button-1>", self.on_color_wheel_pick)
        self.wheel_canvas.bind("<B1-Motion>", self.on_color_wheel_pick)

        preview_box = ctk.CTkFrame(inspector, fg_color="#111827", corner_radius=8)
        preview_box.pack(fill="x", padx=16, pady=4)

        self.hex_preview = ctk.CTkLabel(
            preview_box,
            text="#FFFFFF  |  RGB(255, 255, 255)",
            font=ctk.CTkFont(family="Menlo", size=11, weight="bold"),
            height=26,
            corner_radius=6,
            fg_color="#1E293B",
        )
        self.hex_preview.pack(fill="x", padx=6, pady=6)

        presets_grid = ctk.CTkFrame(inspector, fg_color="transparent")
        presets_grid.pack(fill="x", padx=14, pady=2)
        presets_grid.grid_columnconfigure((0, 1), weight=1)

        studio_presets = [
            ("🕯️ Świeca 2200K",   None, 2200, "#F97316"),
            ("☕ Ciepła 3000K",    None, 3000, "#F59E0B"),
            ("☀️ Neutral 4500K",   None, 4500, "#EAB308"),
            ("❄️ Dzienna 6500K",   None, 6500, "#38BDF8"),
        ]

        for idx, (label, rgb_val, k_val, btn_col) in enumerate(studio_presets):
            r, c = divmod(idx, 2)
            ctk.CTkButton(
                presets_grid,
                text=label,
                height=26,
                corner_radius=6,
                fg_color="#1E293B",
                hover_color=btn_col,
                font=ctk.CTkFont(size=11),
                command=lambda r_v=rgb_val, k_v=k_val: self.apply_inspector_preset(r_v, k_v),
            ).grid(row=r, column=c, padx=3, pady=2, sticky="ew")

        ctk.CTkLabel(
            inspector,
            text="WŁASNE SCENY POKOJU (MACOS & TELEFON)",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#64748B",
        ).pack(anchor="w", padx=16, pady=(8, 2))

        save_row = ctk.CTkFrame(inspector, fg_color="transparent")
        save_row.pack(fill="x", padx=14, pady=2)

        self.preset_entry = ctk.CTkEntry(
            save_row,
            placeholder_text="Nazwa sceny...",
            height=28,
            font=ctk.CTkFont(size=11),
        )
        self.preset_entry.pack(side="left", fill="x", expand=True, padx=(2, 4))

        ctk.CTkButton(
            save_row,
            text="💾 Zapisz",
            width=72,
            height=28,
            fg_color="#0D9488",
            hover_color="#0F766E",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self.save_new_user_preset,
        ).pack(side="right", padx=2)

        self.user_presets_frame = ctk.CTkScrollableFrame(
            inspector, height=85, fg_color="#111827", corner_radius=8
        )
        self.user_presets_frame.pack(fill="both", expand=True, padx=14, pady=(4, 10))
        self.refresh_user_presets_ui()

    def refresh_user_presets_ui(self):
        for widget in self.user_presets_frame.winfo_children():
            widget.destroy()

        for name in list(self.engine.user_presets.keys()):
            row = ctk.CTkFrame(self.user_presets_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)

            ctk.CTkButton(
                row,
                text=f"✨ {name}",
                anchor="w",
                height=26,
                fg_color="#1E293B",
                hover_color="#2563EB",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda n=name: self.load_user_preset(n),
            ).pack(side="left", fill="x", expand=True, padx=(0, 4))

            ctk.CTkButton(
                row,
                text="✕",
                width=26,
                height=26,
                fg_color="#334155",
                hover_color="#DC2626",
                font=ctk.CTkFont(size=11),
                command=lambda n=name: self.delete_user_preset(n),
            ).pack(side="right")

    def save_new_user_preset(self):
        name = self.preset_entry.get().strip()
        if not name:
            name = f"Scena {len(self.engine.user_presets) + 1}"
        self.engine.save_current_as_preset(name)
        self._last_preset_count = len(self.engine.user_presets)
        self.preset_entry.delete(0, "end")
        self.refresh_user_presets_ui()
        self.status_label.configure(text=f"💾 Zapisano własną scenę pokoju: '{name}'", text_color="#4ADE80")

    def load_user_preset(self, name: str):
        self._highlight_mode_btn("IDLE")
        self.engine.activate_user_preset(name)
        self.status_label.configure(text=f"✨ Wczytano scenę użytkownika: '{name}'", text_color="#38BDF8")

    def delete_user_preset(self, name: str):
        self.engine.user_presets.pop(name, None)
        self._last_preset_count = len(self.engine.user_presets)
        self.engine.save_presets_to_disk()
        self.refresh_user_presets_ui()

    def _draw_hsv_color_wheel(self):
        radius = self.wheel_size // 2 - 8
        cx, cy = self.wheel_size // 2, self.wheel_size // 2

        for r_step in range(radius, 0, -6):
            sat = r_step / float(radius)
            circumference = max(24, int(2 * math.pi * r_step / 4))
            for i in range(circumference):
                angle = (2 * math.pi * i) / circumference
                hue = (angle / (2 * math.pi)) % 1.0
                r, g, b = colorsys.hsv_to_rgb(hue, sat, 1.0)
                hex_c = rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))
                x = cx + r_step * math.cos(angle)
                y = cy + r_step * math.sin(angle)
                self.wheel_canvas.create_oval(x - 4, y - 4, x + 4, y + 4, fill=hex_c, outline=hex_c)

    def on_color_wheel_pick(self, event):
        cx, cy = self.wheel_size // 2, self.wheel_size // 2
        radius = self.wheel_size // 2 - 8
        dx = event.x - cx
        dy = event.y - cy
        dist = math.hypot(dx, dy)
        if dist > radius:
            dx = dx * (radius / dist)
            dy = dy * (radius / dist)
            dist = radius

        angle = math.atan2(dy, dx) % (2 * math.pi)
        hue = angle / (2 * math.pi)
        sat = dist / float(radius)

        r, g, b = colorsys.hsv_to_rgb(hue, sat, 1.0)
        rgb = (int(r * 255), int(g * 255), int(b * 255))
        hex_c = rgb_to_hex(rgb)

        self.wheel_canvas.coords(
            self.wheel_cursor, cx + dx - 6, cy + dy - 6, cx + dx + 6, cy + dy + 6
        )
        self.wheel_canvas.itemconfig(self.wheel_cursor, fill=hex_c)
        self.hex_preview.configure(
            text=f"{hex_c.upper()}  |  RGB{rgb}",
            fg_color=hex_c,
            text_color="#0F172A" if (rgb[0] * 0.299 + rgb[1] * 0.587 + rgb[2] * 0.114) > 150 else "#F8FAFC",
        )

        if self.target_scope.get() == "🏠 Cały pokój (9)":
            self.engine.manual_apply_to_all(rgb=rgb, bri=int(255 * self.engine.master_brightness))
            self._highlight_mode_btn("IDLE")
        else:
            self.engine.manual_set_light(self.selected_entity, rgb=rgb, transition=0.12)

    def apply_inspector_preset(self, rgb_val, k_val):
        if self.target_scope.get() == "🏠 Cały pokój (9)":
            self.engine.manual_apply_to_all(
                rgb=rgb_val, kelvin=k_val, bri=int(255 * self.engine.master_brightness)
            )
            self._highlight_mode_btn("IDLE")
        else:
            self.engine.manual_set_light(
                self.selected_entity, rgb=rgb_val, kelvin=k_val, transition=0.35
            )

    # -----------------------------------------------------------------
    # DOLNY PASEK STATUSU
    # -----------------------------------------------------------------
    def _build_bottom_bar(self):
        bottom = ctk.CTkFrame(self, fg_color="#0F172A", corner_radius=0, height=48)
        bottom.pack(fill="x", side="bottom")

        self.crop_lbl = ctk.CTkLabel(
            bottom,
            text="🖥️ Analiza ekranu: Pełny obraz  |  Luma L: 0.00  P: 0.00",
            font=ctk.CTkFont(family="Menlo", size=11),
            text_color="#94A3B8",
        )
        self.crop_lbl.pack(side="left", padx=20, pady=10)

        ctk.CTkButton(
            bottom,
            text="🚪 Zamknij Studio i Zgaś Światła",
            fg_color="#991B1B",
            hover_color="#DC2626",
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.on_exit,
        ).pack(side="right", padx=20, pady=8)

        ctk.CTkButton(
            bottom,
            text="⏸️ Zamknij (Zostaw światła włączone)",
            fg_color="#1E293B",
            hover_color="#334155",
            height=30,
            font=ctk.CTkFont(size=12),
            command=self.on_exit_keep_lights,
        ).pack(side="right", padx=4, pady=8)

    # -----------------------------------------------------------------
    # INTERAKTYWNA MAPA POKOJU 2D
    # -----------------------------------------------------------------
    def select_entity_for_inspector(self, entity_id: str):
        self.selected_entity = entity_id
        self.insp_title.configure(text=LIGHTS_CONFIG[entity_id]["name"])
        self.insp_entity_lbl.configure(text=entity_id)

    def switch_center_view(self, value: str):
        if "Mapa" in value:
            self.grid_view.pack_forget()
            self.map_view.pack(fill="both", expand=True)
            self.draw_spatial_room_map()
        else:
            self.map_view.pack_forget()
            self.grid_view.pack(fill="both", expand=True)

    def draw_spatial_room_map(self):
        c = self.room_canvas
        c.delete("all")
        w = max(480, c.winfo_width())
        h = max(420, c.winfo_height())

        c.create_rectangle(30, 25, w - 30, h - 25, outline="#1E293B", width=2, fill="#0B1120")
        c.create_rectangle(w * 0.32, 35, w * 0.68, 72, outline="#334155", fill="#1E293B")
        c.create_text(w * 0.50, 53, text="🖥️ BIURKO & MONITOR (Przeciągnij lampy myszką)", fill="#94A3B8", font=("Menlo", 10, "bold"))

        c.create_rectangle(w * 0.33, h * 0.62, w * 0.67, h * 0.80, outline="#334155", fill="#162032")
        c.create_text(w * 0.50, h * 0.71, text="🛋️ NAROŻNIK / SOFA", fill="#64748B", font=("Menlo", 10, "bold"))

        c.create_text(w * 0.18, h * 0.88, text="☕ STREFA KUCHNI", fill="#475569", font=("Menlo", 10, "bold"))
        c.create_text(w * 0.83, h * 0.88, text="🚪 WEJŚCIE", fill="#475569", font=("Menlo", 10, "bold"))

        for eid, cfg in LIGHTS_CONFIG.items():
            px, py = cfg["pos"]
            x = int(40 + px * (w - 80))
            y = int(40 + py * (h - 80))
            state = self.engine.current_ui_state[eid]
            is_on = state.get("is_on", False) and state.get("bri", 0) > 0
            rgb = state.get("rgb", (0, 0, 0))
            bri = state.get("bri", 0)
            hex_col = rgb_to_hex(rgb) if is_on else "#1E293B"
            is_flashing = (self.engine.mode == "SPOTIFY" and eid in self.engine.spotify_sync.active_flashes)

            if is_on:
                glow_r = int(24 + (bri / 255.0) * (36 if is_flashing else 28))
                c.create_oval(
                    x - glow_r, y - glow_r, x + glow_r, y + glow_r,
                    outline="#FFFFFF" if is_flashing else hex_col,
                    width=3 if is_flashing else 2,
                    fill="#111827"
                )

            is_sel = (eid == self.selected_entity)
            node_r = 20
            c.create_oval(
                x - node_r, y - node_r, x + node_r, y + node_r,
                fill=hex_col,
                outline="#4ADE80" if is_flashing else ("#FFFFFF" if is_sel else "#475569"),
                width=3 if (is_sel or is_flashing) else 1,
            )
            bri_pct = int((bri / 255.0) * 100) if is_on else 0
            c.create_text(
                x, y + 32,
                text=f"{cfg['name']}\n({bri_pct}%)",
                fill="#F8FAFC" if is_sel else "#CBD5E1",
                font=("Helvetica", 10, "bold" if is_sel else "normal"),
                justify="center",
            )

    def on_room_canvas_press(self, event):
        c = self.room_canvas
        w = max(480, c.winfo_width())
        h = max(420, c.winfo_height())
        best_eid = None
        best_dist = 9999.0
        for eid, cfg in LIGHTS_CONFIG.items():
            px, py = cfg["pos"]
            x = int(40 + px * (w - 80))
            y = int(40 + py * (h - 80))
            d = math.hypot(event.x - x, event.y - y)
            if d < best_dist and d < 48:
                best_dist = d
                best_eid = eid
        if best_eid:
            self._dragging_map_entity = best_eid
            self.select_entity_for_inspector(best_eid)
            self.draw_spatial_room_map()

    def on_room_canvas_drag(self, event):
        if not self._dragging_map_entity:
            return
        c = self.room_canvas
        w = max(480, c.winfo_width())
        h = max(420, c.winfo_height())
        nx = float(np.clip((event.x - 40) / float(max(1, w - 80)), 0.04, 0.96))
        ny = float(np.clip((event.y - 40) / float(max(1, h - 80)), 0.06, 0.92))
        LIGHTS_CONFIG[self._dragging_map_entity]["pos"] = [nx, ny]
        self.draw_spatial_room_map()

    def on_room_canvas_release(self, _event):
        if self._dragging_map_entity:
            self._dragging_map_entity = None
            self.engine.save_presets_to_disk()

    def _highlight_mode_btn(self, active_key: str):
        for key, (btn, col) in self.mode_buttons.items():
            if key == active_key:
                btn.configure(
                    fg_color=col,
                    text_color="#0F172A" if key == "MAX_WHITE" else "#F8FAFC",
                )
            else:
                btn.configure(fg_color="#1E293B", text_color="#F8FAFC")

    def switch_mode(self, mode_key: str):
        if mode_key == "MAX_WHITE":
            self.activate_max_white()
            return
        if mode_key == "IDLE":
            self._highlight_mode_btn("IDLE")
            self.engine.set_manual_passthrough()
            self.status_label.configure(
                text=f"Tryb: 🎛️ Sterowanie ręczne HA Live  |  📱 Pilot: {self.engine.mobile_server.url}",
                text_color="#38BDF8",
            )
            return

        if mode_key == "SPOTIFY":
            self.engine.spotify_sync.trigger_immediate_poll()

        self._highlight_mode_btn(mode_key)
        self.status_label.configure(
            text=f"🌊 Płynna fala przestrzenna ➔ Uruchamianie trybu: {mode_key}...",
            text_color="#4ADE80" if mode_key == "SPOTIFY" else "#38BDF8",
        )
        self.engine.trigger_spatial_wave(mode_key)

    def activate_max_white(self):
        self._highlight_mode_btn("MAX_WHITE")
        self.engine.set_max_white_mode()
        self.status_label.configure(
            text=f"☀️ Tryb: PEŁNA BIEL (100% jasności | Natywna barwa: {self.engine.white_temp_kelvin}K)",
            text_color="#FACC15",
        )

    def sleep_all_lights(self):
        self._highlight_mode_btn("IDLE")
        self.engine.turn_off_lights_and_standby()
        self.status_label.configure(
            text="🌑 Wszystkie światła wygaszone (Tryb Ręczny / Standby)",
            text_color="#F87171",
        )

    def set_all_participation(self, state: bool):
        for eid in LIGHTS_CONFIG:
            self.engine.enabled_lights[eid] = state
            self.engine.last_sent_state.pop(eid, None)

    def on_smart_switches(self):
        self.engine.auto_override_from_ha = bool(self.sw_override.get())
        self.engine.circadian_enabled = bool(self.sw_circadian.get())
        self.engine.spotify_sync.ceiling_strobe_enabled = bool(self.sw_ceiling_strobe.get())

    def on_global_sliders(self, _=None):
        self.engine.master_brightness = float(self.s_master.get())
        self.engine.spotify_sync.strobe_density = int(round(self.s_strobe.get()))
        self.engine.white_temp_kelvin = int(self.s_kelvin.get())
        self.engine.saturation_boost = float(self.s_sat.get())

        self.lbl_master.configure(text=f"Skala Jasności: {int(self.engine.master_brightness * 100)}%")
        self.lbl_strobe.configure(text=f"Błyski Spotify naraz: {self.engine.spotify_sync.strobe_density} lampy")
        self.lbl_kelvin.configure(text=f"Temp. Bieli: {self.engine.white_temp_kelvin}K")
        self.lbl_sat.configure(text=f"Nasycenie Kolorów: {self.engine.saturation_boost:.2f}x")
        if self.engine.mode == "MAX_WHITE":
            self.engine.set_max_white_mode()

    # -----------------------------------------------------------------
    # PĘTLA ODŚWIEŻANIA GUI
    # -----------------------------------------------------------------
    def update_telemetry_loop(self):
        if self.engine.ws_client.connected:
            self.ws_badge.configure(text="● WS ONLINE", text_color="#4ADE80")
        else:
            self.ws_badge.configure(text="● REST FALLBACK", text_color="#FACC15")

        if self.engine.last_override_notice:
            self.status_label.configure(text=self.engine.last_override_notice, text_color="#FACC15")
            self.engine.last_override_notice = ""

        # Aktualizacja paska Spotify w górnym panelu
        sp = self.engine.spotify_sync
        self.sp_swatch1.configure(fg_color=rgb_to_hex(sp.color1_rgb))
        self.sp_swatch2.configure(fg_color=rgb_to_hex(sp.color2_rgb))
        short_title = (sp.title[:22] + "…") if len(sp.title) > 23 else sp.title
        if sp.is_playing:
            self.sp_top_lbl.configure(text=f"🎵 {short_title} ({int(sp.bpm)} BPM)", text_color="#4ADE80")
        else:
            self.sp_top_lbl.configure(text=f"⏸️ {short_title} (EKG)", text_color="#94A3B8")

        # Synchronizacja suwaków globalnych, jeśli zmieniono je na telefonie
        self.lbl_master.configure(text=f"Skala Jasności: {int(self.engine.master_brightness * 100)}%")
        self.lbl_strobe.configure(text=f"Błyski Spotify naraz: {sp.strobe_density} lampy")
        self.lbl_kelvin.configure(text=f"Temp. Bieli: {self.engine.white_temp_kelvin}K")
        self.lbl_sat.configure(text=f"Nasycenie Kolorów: {self.engine.saturation_boost:.2f}x")

        active_cnt = sum(1 for v in self.engine.enabled_lights.values() if v)
        self.metrics_lbl.configure(
            text=f"RTT: {self.engine.ha_ping_ms:3.1f} ms | FPS: {self.engine.fps:4.1f} | Sync: {active_cnt}/9"
        )
        self.crop_lbl.configure(
            text=(
                f"🖥️ Auto-Crop: {self.engine.crop_info}  |  "
                f"Luma L: {self.engine.luma_left:.2f}  P: {self.engine.luma_right:.2f}  |  "
                f"🎵 Spotify: {sp.title} — {sp.artist}"
            )
        )

        for eid, card in self.cards.items():
            card.refresh_from_state(is_selected=(eid == self.selected_entity))

        if "Mapa" in self.view_switcher.get() and not self._dragging_map_entity:
            self.draw_spatial_room_map()

        if self.engine.running:
            self.after(80, self.update_telemetry_loop)

    def on_exit_keep_lights(self):
        self.engine.running = False
        self.engine.save_presets_to_disk()
        self.engine.mobile_server.stop()
        self.engine.ws_client.close()
        self.destroy()

    def on_exit(self):
        self.status_label.configure(text="🌙 Wygaszanie świateł i zamykanie sesji...", text_color="#F87171")
        self.update()
        self.engine.turn_off_all_smoothly()
        time.sleep(0.25)
        self.destroy()


if __name__ == "__main__":
    engine = AmbientEngine(dev_mode="--dev" in sys.argv)

    worker = threading.Thread(target=engine.run_loop, daemon=True)
    worker.start()

    app = AmbientStudioApp(engine)
    app.mainloop()
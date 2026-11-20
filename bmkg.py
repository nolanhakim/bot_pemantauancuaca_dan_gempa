"""
Modul API BMKG Terbuka (Open Data BMKG)
- Data Cuaca: https://github.com/infoBMKG/data-cuaca.git (https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=...)
- Data CAP Nowcast: https://github.com/infoBMKG/data-cap.git (https://www.bmkg.go.id/alerts/nowcast/id/rss.xml)
- Data Gempa: https://data.bmkg.go.id/DataMKG/TEWS/

Sumber Data Resmi: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)
"""

import os
import re
import json
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

import requests

logger = logging.getLogger(__name__)

# Lokasi file database wilayah
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
WILAYAH_FILE = os.path.join(DATA_DIR, "wilayah.json")

# In-memory cache database wilayah
_WILAYAH_DB: dict[str, Any] | None = None


def load_wilayah_db() -> dict[str, Any]:
    """Muat database wilayah Indonesia ke dalam memory."""
    global _WILAYAH_DB
    if _WILAYAH_DB is not None:
        return _WILAYAH_DB

    if os.path.exists(WILAYAH_FILE):
        try:
            with open(WILAYAH_FILE, "r", encoding="utf-8") as f:
                _WILAYAH_DB = json.load(f)
                return _WILAYAH_DB
        except Exception as e:
            logger.error("Gagal membaca wilayah.json: %s", e)

    _WILAYAH_DB = {"aliases": {}, "items": []}
    return _WILAYAH_DB


def search_wilayah(query: str, limit: int = 5) -> list[dict]:
    """
    Cari kode wilayah adm4 berdasarkan nama kota, kabupaten, kecamatan,
    alias populer, atau kode adm4 langsung (misal: 31.71.01.1001).
    """
    db = load_wilayah_db()
    aliases = db.get("aliases", {})
    items = db.get("items", [])

    query_clean = query.strip().lower()
    if not query_clean:
        return []

    # Cek jika format adm4 langsung: xx.xx.xx.xxxx
    if re.match(r"^\d{2}\.\d{2}\.\d{2}\.\d{4}$", query_clean):
        return [{
            "name": f"Kode {query_clean}",
            "adm4": query_clean,
            "parent": "Wilayah Kustom",
            "type": "adm4",
        }]

    # Cek alias populer (misal 'jakarta', 'bandung', 'jogja', 'solo', 'bali')
    if query_clean in aliases:
        target_adm4 = aliases[query_clean]
        for it in items:
            if it.get("adm4") == target_adm4:
                return [it]
        return [{
            "name": query.title(),
            "adm4": target_adm4,
            "parent": "Indonesia",
            "type": "alias",
        }]

    exact_matches = []
    prefix_matches = []
    contains_matches = []

    for it in items:
        name_lower = it.get("name", "").lower()
        # Hilangkan prefix administratif untuk matching yang lebih luwes
        name_simple = re.sub(r"^(kabupaten|kota|kecamatan)\s+", "", name_lower)

        if name_simple == query_clean:
            exact_matches.append(it)
        elif name_simple.startswith(query_clean):
            prefix_matches.append(it)
        elif query_clean in name_lower:
            contains_matches.append(it)

    combined = exact_matches + prefix_matches + contains_matches
    seen_adm4 = set()
    results = []
    for item in combined:
        adm4 = item.get("adm4")
        if adm4 and adm4 not in seen_adm4:
            seen_adm4.add(adm4)
            results.append(item)
            if len(results) >= limit:
                break

    return results


# ===================== CUACA BMKG (data-cuaca) =====================

# Emoji kondisi cuaca BMKG
WEATHER_EMOJIS = {
    "cerah": "☀️",
    "cerah berawan": "🌤️",
    "berawan": "☁️",
    "berawan tebal": "🌥️",
    "udara kabur": "🌫️",
    "asap": "💨",
    "kabut": "🌁",
    "hujan ringan": "🌧️",
    "hujan sedang": "🌧️",
    "hujan lebat": "⛈️",
    "hujan lokal": "🌦️",
    "hujan petir": "⛈️⚡",
}


def get_weather_emoji(desc: str) -> str:
    """Ambil emoji cuaca berdasarkan deskripsi BMKG."""
    desc_clean = desc.strip().lower()
    for key, emoji in WEATHER_EMOJIS.items():
        if key in desc_clean:
            return emoji
    return "🌡️"


def get_weather_bmkg(adm4: str) -> dict | None:
    """
    Ambil data prakiraan cuaca terbuka BMKG berdasarkan kode adm4.
    Endpoint: https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={adm4}
    """
    url = "https://api.bmkg.go.id/publik/prakiraan-cuaca"
    params = {"adm4": adm4}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("data"):
            return None
        return data
    except Exception as e:
        logger.error("Gagal mengambil cuaca BMKG (adm4=%s): %s", adm4, e)
        return None


def extract_cuaca_timeline(data: dict) -> list[dict]:
    """Ekstrak seluruh interval cuaca menjadi satu timeline berurutan."""
    timeline = []
    cuaca_days = data.get("data", [{}])[0].get("cuaca", [])
    for day in cuaca_days:
        if isinstance(day, list):
            for slot in day:
                timeline.append(slot)
    return timeline


def format_current_weather(data: dict) -> str:
    """Format cuaca saat ini dari data BMKG."""
    lokasi = data.get("lokasi", {})
    desa = lokasi.get("desa", "")
    kecamatan = lokasi.get("kecamatan", "")
    kotkab = lokasi.get("kotkab", "")
    provinsi = lokasi.get("provinsi", "")
    adm4 = lokasi.get("adm4", "")

    timeline = extract_cuaca_timeline(data)
    if not timeline:
        return "❌ Data cuaca tidak tersedia untuk wilayah ini."

    # Ambil slot prakiraan terdekat (slot pertama dalam timeline)
    current = timeline[0]

    desc = current.get("weather_desc", "Tidak diketahui")
    desc_en = current.get("weather_desc_en", "")
    temp = current.get("t", "-")
    humidity = current.get("hu", "-")
    wind_spd = current.get("ws", "-")
    wind_dir = current.get("wd", "-")
    cloud_cov = current.get("tcc", "-")
    rain_prec = current.get("tp", 0.0)
    local_time = current.get("local_datetime", "")
    emoji = get_weather_emoji(desc)

    # Format waktu lokal
    waktu_str = local_time
    try:
        dt = datetime.strptime(local_time, "%Y-%m-%d %H:%M:%S")
        waktu_str = dt.strftime("%d %b %Y, %H:%M")
    except Exception:
        pass

    loc_name = f"{desa}, {kotkab}" if desa and desa != kotkab else kotkab
    if not loc_name:
        loc_name = kecamatan or "Indonesia"

    desc_line = f"*{desc}*"
    if desc_en:
        desc_line += f" _({desc_en})_"

    lines = [
        f"{emoji} *Cuaca di {loc_name}*",
        f"📍 _{provinsi} (adm4: `{adm4}`)_",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"☁️ Kondisi: {desc_line}",
        f"🌡️ Suhu Udara: *{temp}°C*",
        f"💧 Kelembapan: *{humidity}%*",
        f"💨 Kecepatan Angin: *{wind_spd} km/jam* (dari {wind_dir})",
        f"☁️ Tutupan Awan: *{cloud_cov}%*",
        f"🌧️ Potensi Curah Hujan: *{rain_prec} mm*\n",
        f"🕐 _Waktu Prakiraan: {waktu_str} WIB_",
        "🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_",
    ]

    return "\n".join(lines)


def format_forecast_bmkg(data: dict, day_offset: int = 0) -> str:
    """Format ramalan cuaca (harian atau 24 jam) dari BMKG."""
    lokasi = data.get("lokasi", {})
    desa = lokasi.get("desa", "")
    kotkab = lokasi.get("kotkab", "")
    provinsi = lokasi.get("provinsi", "")

    cuaca_days = data.get("data", [{}])[0].get("cuaca", [])
    if not cuaca_days:
        return "❌ Data ramalan cuaca tidak ditemukan."

    loc_name = f"{desa}, {kotkab}" if desa and desa != kotkab else kotkab

    # Jika day_offset = 0 (24 Jam ke depan dari timeline)
    if day_offset == 0:
        timeline = extract_cuaca_timeline(data)[:8]  # 8 slot x 3 jam = 24 jam
        title = f"📅 *Prakiraan Cuaca 24 Jam — {loc_name}*"
        slots = timeline
    else:
        # Berdasarkan hari ke- (1, 2, atau 3)
        day_idx = min(day_offset - 1, len(cuaca_days) - 1)
        slots = cuaca_days[day_idx]
        title = f"📅 *Prakiraan Cuaca Hari ke-{day_offset} — {loc_name}*"

    lines = [
        title,
        f"📍 _{provinsi}_\n━━━━━━━━━━━━━━━━━━━\n",
    ]

    for slot in slots:
        local_dt = slot.get("local_datetime", "")
        time_part = local_dt
        try:
            dt = datetime.strptime(local_dt, "%Y-%m-%d %H:%M:%S")
            time_part = dt.strftime("%d %b %H:%M")
        except Exception:
            pass

        temp = slot.get("t", "-")
        desc = slot.get("weather_desc", "-")
        hu = slot.get("hu", "-")
        ws = slot.get("ws", "-")
        emoji = get_weather_emoji(desc)

        lines.append(f"`{time_part}` {emoji} *{temp}°C* — {desc}\n   💧 {hu}% | 💨 {ws} km/j")

    lines.append("\n🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_")
    return "\n".join(lines)


# ===================== CAP NOWCAST BMKG (data-cap) =====================


def get_nowcast_alerts(filter_prov: str | None = None) -> list[dict]:
    """
    Ambil daftar peringatan dini cuaca aktif dari BMKG CAP RSS feed.
    Endpoint: https://www.bmkg.go.id/alerts/nowcast/id/rss.xml
    """
    rss_url = "https://www.bmkg.go.id/alerts/nowcast/id/rss.xml"
    try:
        resp = requests.get(rss_url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        channel = root.find("channel")
        if channel is None:
            return []

        alerts = []
        for item in channel.findall("item"):
            title = item.findtext("title", "Peringatan Dini Cuaca")
            link = item.findtext("link", "")
            pubDate = item.findtext("pubDate", "")
            desc = item.findtext("description", "")
            guid = item.findtext("guid", link)

            # Ekstrak alert_id dari link: e.g. CJB20261120006
            alert_id = ""
            if link:
                match = re.search(r"([A-Za-z0-9_]+)_alert\.xml", link)
                if match:
                    alert_id = match.group(1)

            alert_data = {
                "id": alert_id or guid,
                "title": title,
                "link": link,
                "pubDate": pubDate,
                "desc": desc,
            }

            if filter_prov:
                fp = filter_prov.lower()
                if fp in title.lower() or fp in desc.lower():
                    alerts.append(alert_data)
            else:
                alerts.append(alert_data)

        return alerts
    except Exception as e:
        logger.error("Gagal mengambil data CAP BMKG: %s", e)
        return []


def get_nowcast_detail(alert_link_or_id: str) -> dict | None:
    """
    Ambil detail peringatan dini cuaca CAP XML dari BMKG.
    URL contoh: https://www.bmkg.go.id/alerts/nowcast/id/{ID}_alert.xml
    """
    if alert_link_or_id.startswith("http"):
        url = alert_link_or_id
    else:
        url = f"https://www.bmkg.go.id/alerts/nowcast/id/{alert_link_or_id}_alert.xml"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
        info = root.find("cap:info", ns)
        if info is None:
            # Coba tanpa namespace jika namespace berbeda
            info = root.find("info")

        if info is None:
            return None

        def get_field(name: str) -> str:
            res = info.findtext(f"cap:{name}", "", ns)
            if not res:
                res = info.findtext(name, "")
            return res

        headline = get_field("headline")
        event = get_field("event")
        urgency = get_field("urgency")
        severity = get_field("severity")
        certainty = get_field("certainty")
        effective = get_field("effective")
        expires = get_field("expires")
        sender = get_field("senderName")
        desc = get_field("description")
        web = get_field("web")
        area_desc = info.findtext("cap:area/cap:areaDesc", "", ns) or info.findtext("area/areaDesc", "")

        return {
            "headline": headline,
            "event": event,
            "urgency": urgency,
            "severity": severity,
            "certainty": certainty,
            "effective": effective,
            "expires": expires,
            "senderName": sender,
            "description": desc,
            "web": web,
            "areaDesc": area_desc,
        }
    except Exception as e:
        logger.error("Gagal mengambil detail CAP XML (%s): %s", alert_link_or_id, e)
        return None


def format_nowcast_list(alerts: list[dict], filter_prov: str | None = None) -> str:
    """Format daftar peringatan dini cuaca aktif."""
    if not alerts:
        if filter_prov:
            return f"✅ Tidak ada peringatan dini cuaca aktif untuk wilayah *{filter_prov}* saat ini."
        return "✅ Saat ini *tidak ada peringatan dini cuaca aktif* di seluruh wilayah Indonesia."

    header = "⚠️ *Peringatan Dini Cuaca (Nowcast) BMKG*\n"
    if filter_prov:
        header = f"⚠️ *Peringatan Dini Cuaca BMKG — {filter_prov}*\n"
    header += f"Ditemukan *{len(alerts)}* peringatan cuaca aktif:\n━━━━━━━━━━━━━━━━━━━\n"

    lines = [header]
    for idx, a in enumerate(alerts[:8], 1):
        title = a.get("title", "Peringatan Cuaca")
        pub = a.get("pubDate", "")
        desc = a.get("desc", "")
        # Ambil ringkasan kalimat pertama deskripsi
        desc_snippet = desc.split("\n")[0] if desc else ""
        if len(desc_snippet) > 120:
            desc_snippet = desc_snippet[:117] + "..."

        lines.append(f"*{idx}. {title}*")
        if pub:
            lines.append(f"   🕒 _{pub}_")
        if desc_snippet:
            lines.append(f"   📝 {desc_snippet}")
        lines.append("")

    lines.append("🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_")
    return "\n".join(lines)


def format_nowcast_detail(data: dict) -> str:
    """Format tampilan detail peringatan dini CAP."""
    headline = data.get("headline", "Peringatan Dini Cuaca BMKG")
    event = data.get("event", "-")
    severity = data.get("severity", "-")
    effective = data.get("effective", "-")
    expires = data.get("expires", "-")
    desc = data.get("description", "-")
    web = data.get("web", "")
    area = data.get("areaDesc", "")

    # Terjemahan severity
    sev_map = {
        "Extreme": "🔴 Ekstrem",
        "Severe": "🟠 Parah / Berat",
        "Moderate": "🟡 Sedang",
        "Minor": "🟢 Ringan",
    }
    sev_str = sev_map.get(severity, severity)

    lines = [
        f"🚨 *{headline}*",
        "━━━━━━━━━━━━━━━━━━━\n",
        f"⚡ *Jenis:* {event}",
        f"⚠️ *Tingkat:* {sev_str}",
        f"🕒 *Mulai:* `{effective}`",
        f"⏳ *Berakhir:* `{expires}`\n",
        f"📍 *Area Terdampak:* {area}\n",
        f"📝 *Deskripsi & Detail:*\n{desc}\n",
    ]

    if web and web != "#":
        lines.append(f"🗺️ [Lihat Infografis Resmi BMKG]({web})\n")

    lines.append("🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_")
    return "\n".join(lines)


# ===================== GEMPA BMKG =====================


def get_latest_earthquake() -> dict | None:
    """Ambil data gempa terbaru dari BMKG."""
    url = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["Infogempa"]["gempa"]
    except Exception as e:
        logger.error("BMKG autogempa error: %s", e)
        return None


def get_recent_earthquakes() -> list | None:
    """Ambil 15 gempa terkini M 5.0+ dari BMKG."""
    url = "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["Infogempa"]["gempa"]
    except Exception as e:
        logger.error("BMKG gempaterkini error: %s", e)
        return None


def get_felt_earthquakes() -> list | None:
    """Ambil 15 gempa dirasakan dari BMKG."""
    url = "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data["Infogempa"]["gempa"]
    except Exception as e:
        logger.error("BMKG gempadirasakan error: %s", e)
        return None


def format_earthquake(gempa: dict) -> str:
    """Format data gempa tunggal."""
    potensi = gempa.get("Potensi", "Tidak berpotensi tsunami")

    tsunami_warn = ""
    if "tsunami" in potensi.lower() and "tidak" not in potensi.lower():
        tsunami_warn = "\n\n🚨 *PERINGATAN TSUNAMI!*"

    shakemap = gempa.get("Shakemap", "")
    shakemap_line = ""
    if shakemap:
        shakemap_line = f"\n🗺️ [Lihat Peta Shakemap](https://data.bmkg.go.id/DataMKG/TEWS/{shakemap})"

    dirasakan = gempa.get("Dirasakan", "")
    dirasakan_line = f"\n💥 Dirasakan (MMI): {dirasakan}" if dirasakan else ""

    return (
        f"🌍 *Gempa Terbaru — BMKG*\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 Tanggal: {gempa.get('Tanggal', '-')}\n"
        f"🕐 Waktu: {gempa.get('Jam', '-')}\n"
        f"📏 Magnitudo: *M {gempa.get('Magnitude', '-')}*\n"
        f"📍 Kedalaman: {gempa.get('Kedalaman', '-')}\n"
        f"📌 Koordinat: {gempa.get('Lintang', '-')}, {gempa.get('Bujur', '-')}\n"
        f"🗺️ Wilayah: {gempa.get('Wilayah', '-')}\n"
        f"⚠️ Potensi: {potensi}"
        f"{dirasakan_line}"
        f"{tsunami_warn}"
        f"{shakemap_line}\n\n"
        f"🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_"
    )


def format_earthquake_list(gempa_list: list, title: str) -> str:
    """Format daftar gempa."""
    if not gempa_list:
        return "❌ Tidak ada data gempa."

    lines = [f"🌍 *{title}*\n━━━━━━━━━━━━━━━━━━━\n"]

    for i, g in enumerate(gempa_list[:10], 1):
        tanggal = g.get("Tanggal", "-")
        jam = g.get("Jam", "-")
        mag = g.get("Magnitude", "-")
        wilayah = g.get("Wilayah", "-")
        kedalaman = g.get("Kedalaman", "-")

        lines.append(
            f"*{i}.* M *{mag}* — {wilayah}\n"
            f"   📅 {tanggal} {jam} | 📍 {kedalaman}\n"
        )

    lines.append("🏛️ _Sumber: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_")
    return "\n".join(lines)

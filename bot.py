"""
Bot Telegram BMKG (Cuaca, Peringatan Dini CAP, & Gempa) 🌤️⚠️🌍

Sumber Data Resmi:
- Data Cuaca: https://github.com/infoBMKG/data-cuaca.git (https://api.bmkg.go.id/publik/prakiraan-cuaca)
- Data Peringatan Dini (CAP): https://github.com/infoBMKG/data-cap.git (https://www.bmkg.go.id/alerts/nowcast/id/rss.xml)
- Data Gempa: https://data.bmkg.go.id/DataMKG/TEWS/

Attribution: Wajib mencantumkan BMKG (Badan Meteorologi, Klimatologi, dan Geofisika).
"""

import os
import logging
from typing import Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import bmkg

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Konfigurasi Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Kota-kota populer untuk quick keyboard
POPULAR_CITIES = [
    ("Jakarta", "🏙️", "31.71.01.1001"),
    ("Surabaya", "🌊", "35.78.01.1001"),
    ("Bandung", "🌄", "32.73.01.1001"),
    ("Medan", "🌴", "12.71.01.1001"),
    ("Semarang", "🏛️", "33.74.01.1001"),
    ("Makassar", "⛵", "73.71.01.1001"),
    ("Yogyakarta", "🏯", "34.71.01.1001"),
    ("Denpasar", "🌺", "51.71.01.1001"),
    ("Palembang", "🌉", "16.71.01.1001"),
    ("Manado", "🐠", "71.71.01.1001"),
    ("Balikpapan", "🛢️", "64.71.01.1001"),
    ("Batam", "🚢", "21.71.01.1001"),
]


# ===================== HELPER KEYBOARDS =====================


def build_popular_cities_keyboard() -> InlineKeyboardMarkup:
    """Buat inline keyboard untuk daftar kota populer."""
    keyboard = []
    row = []
    for city, emoji, adm4 in POPULAR_CITIES:
        row.append(InlineKeyboardButton(f"{emoji} {city}", callback_data=f"cuaca|{adm4}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def build_weather_actions_keyboard(adm4: str, prov: str = "") -> InlineKeyboardMarkup:
    """Buat tombol aksi setelah melihat cuaca (Ramalan 24 Jam, Ramalan 3 Hari, dll)."""
    buttons = [
        [
            InlineKeyboardButton("📅 Ramalan 24 Jam", callback_data=f"ramalan|{adm4}|0"),
            InlineKeyboardButton("📆 3 Hari", callback_data=f"ramalan|{adm4}|1"),
        ],
    ]

    # Cek apakah ada peringatan dini CAP untuk provinsi tersebut
    if prov:
        alerts = bmkg.get_nowcast_alerts(filter_prov=prov)
        if alerts:
            buttons.append([
                InlineKeyboardButton(
                    f"⚠️ Peringatan Cuaca di {prov} ({len(alerts)})",
                    callback_data=f"cap|prov|{prov[:20]}",
                )
            ])

    buttons.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")])
    return InlineKeyboardMarkup(buttons)


# ===================== COMMAND HANDLERS =====================


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /start."""
    keyboard = [
        [
            InlineKeyboardButton("🌤️ Cek Cuaca", callback_data="menu|cuaca"),
            InlineKeyboardButton("⚠️ Peringatan Dini", callback_data="cap|list"),
        ],
        [
            InlineKeyboardButton("🌍 Info Gempa BMKG", callback_data="menu|gempa"),
            InlineKeyboardButton("📖 Panduan", callback_data="menu|help"),
        ],
    ]
    await update.message.reply_text(
        "👋 *Halo! Selamat datang di Bot Cuaca, Peringatan Dini & Gempa BMKG!*\n\n"
        "Bot ini menyajikan data resmi real-time langsung dari *BMKG*:\n"
        "🌤️ *Prakiraan Cuaca Terbuka* (hingga tingkat desa/kelurahan/kecamatan)\n"
        "⚠️ *Peringatan Dini Cuaca Nowcast* berbasis CAP\n"
        "🌍 *Informasi Gempabumi Terkini* & Dirasakan\n\n"
        "*Perintah Utama:*\n"
        "• `/cuaca <kota/kecamatan>` — Cek cuaca saat ini\n"
        "• `/ramalan <kota>` — Prakiraan cuaca 24 jam / 3 hari\n"
        "• `/peringatan [provinsi]` — Peringatan dini cuaca aktif\n"
        "• `/gempa` — Gempa bumi terbaru\n"
        "• `/gempaterkini` — 10 gempa M 5.0+ terkini\n"
        "• `/gempadirasakan` — 10 gempa dirasakan\n\n"
        "Atau silakan pilih menu di bawah 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /help."""
    text = (
        "📖 *Panduan Penggunaan Bot BMKG*\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "*🌤️ Prakiraan Cuaca:*\n"
        "• `/cuaca Jakarta` — Cek cuaca di Jakarta\n"
        "• `/cuaca Kuta` — Cuaca di kecamatan/wilayah spesifik\n"
        "• `/cuaca 31.71.01.1001` — Cek cuaca via kode ADM4 langsung\n"
        "• `/ramalan Bandung` — Ramalan 24 jam & 3 hari ke depan\n\n"
        "*⚠️ Peringatan Dini Cuaca (CAP Nowcast):*\n"
        "• `/peringatan` — Daftar semua peringatan dini aktif\n"
        "• `/peringatan Jawa Barat` — Peringatan cuaca di provinsi tertentu\n\n"
        "*🌍 Informasi Gempa:*\n"
        "• `/gempa` — Info gempa terbaru + Shakemap\n"
        "• `/gempaterkini` — Daftar gempa M 5.0+ terkini\n"
        "• `/gempadirasakan` — Daftar gempa yang dirasakan masyarakat\n\n"
        "*💡 Tips Praktis:*\n"
        "• Anda dapat langsung mengetik nama kota/daerah tanpa perintah slash.\n"
        "• Data cuaca mencakup 514 kabupaten/kota dan 7.000+ kecamatan se-Indonesia.\n\n"
        "🏛️ _Sumber Data: BMKG (Badan Meteorologi, Klimatologi, dan Geofisika)_"
    )
    if update.callback_query:
        await query_safe_edit(update.callback_query, text)
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def query_safe_edit(query: Any, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
    """Edit pesan callback query dengan aman terhadap error parse mode Markdown."""
    try:
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
    except Exception:
        await query.edit_message_text(text, reply_markup=reply_markup)


async def cuaca_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /cuaca <kota/kecamatan/adm4>."""
    if not context.args:
        # Tampilkan keyboard pilihan kota populer
        await update.message.reply_text(
            "🌤️ *Pilih kota populer di bawah, atau ketik:*\n`/cuaca <nama kota atau kecamatan>`\n\n"
            "Contoh: `/cuaca Bandung`, `/cuaca Kuta`, `/cuaca Solo`",
            parse_mode="Markdown",
            reply_markup=build_popular_cities_keyboard(),
        )
        return

    query = " ".join(context.args)
    msg = await update.message.reply_text(f"⏳ Mencari cuaca untuk *{query}*...", parse_mode="Markdown")
    await handle_weather_search(msg, query)


async def ramalan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /ramalan <kota>."""
    if not context.args:
        await update.message.reply_text(
            "⚠️ Masukkan nama kota atau kecamatan.\nContoh: `/ramalan Bandung` atau `/ramalan Surabaya`",
            parse_mode="Markdown",
        )
        return

    query = " ".join(context.args)
    msg = await update.message.reply_text(f"⏳ Mengambil ramalan cuaca untuk *{query}*...", parse_mode="Markdown")

    matches = bmkg.search_wilayah(query, limit=1)
    if not matches:
        await msg.edit_text(
            f"❌ Wilayah *{query}* tidak ditemukan.\n"
            "Silakan coba nama kota/kabupaten lain, misalnya: `Bandung`, `Surabaya`, `Jakarta`.",
            parse_mode="Markdown",
        )
        return

    adm4 = matches[0]["adm4"]
    data = bmkg.get_weather_bmkg(adm4)
    if not data:
        await msg.edit_text("❌ Gagal mengambil data ramalan cuaca dari BMKG.")
        return

    text = bmkg.format_forecast_bmkg(data, day_offset=0)
    keyboard = [
        [
            InlineKeyboardButton("📅 24 Jam", callback_data=f"ramalan|{adm4}|0"),
            InlineKeyboardButton("Hari 1", callback_data=f"ramalan|{adm4}|1"),
            InlineKeyboardButton("Hari 2", callback_data=f"ramalan|{adm4}|2"),
            InlineKeyboardButton("Hari 3", callback_data=f"ramalan|{adm4}|3"),
        ],
        [InlineKeyboardButton("🌤️ Cuaca Saat Ini", callback_data=f"cuaca|{adm4}")],
    ]
    try:
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def peringatan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /peringatan [provinsi] — BMKG CAP Nowcast."""
    filter_prov = " ".join(context.args) if context.args else None
    prompt = f" untuk wilayah *{filter_prov}*" if filter_prov else ""
    msg = await update.message.reply_text(f"⏳ Mengambil data peringatan dini cuaca BMKG{prompt}...", parse_mode="Markdown")

    alerts = bmkg.get_nowcast_alerts(filter_prov=filter_prov)
    text = bmkg.format_nowcast_list(alerts, filter_prov=filter_prov)

    keyboard = []
    # Jika ada alerts, tambahkan tombol untuk membaca detail alert
    for a in alerts[:4]:
        title = a.get("title", "Lihat Detail")
        alert_id = a.get("id")
        if alert_id:
            keyboard.append([InlineKeyboardButton(f"🚨 {title[:35]}", callback_data=f"cap|detail|{alert_id}")])

    keyboard.append([InlineKeyboardButton("🔄 Refresh Peringatan", callback_data="cap|list")])
    try:
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ===================== GEMPA HANDLERS =====================


async def gempa_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /gempa — gempa terbaru BMKG."""
    msg = await update.message.reply_text("⏳ Mengambil data gempa terbaru dari BMKG...")
    gempa = bmkg.get_latest_earthquake()

    if not gempa:
        await msg.edit_text("❌ Gagal mengambil data gempa dari BMKG.")
        return

    text = bmkg.format_earthquake(gempa)
    keyboard = [
        [
            InlineKeyboardButton("📋 Gempa Terkini (M 5.0+)", callback_data="gempa|terkini"),
            InlineKeyboardButton("💢 Gempa Dirasakan", callback_data="gempa|dirasakan"),
        ],
    ]
    try:
        await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        await msg.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def gempa_terkini_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /gempaterkini."""
    msg = await update.message.reply_text("⏳ Mengambil 10 gempa M 5.0+ terkini...")
    gempa_list = bmkg.get_recent_earthquakes()

    if not gempa_list:
        await msg.edit_text("❌ Gagal mengambil data gempa terkini.")
        return

    text = bmkg.format_earthquake_list(gempa_list, "10 Gempa Terkini (M 5.0+) — BMKG")
    try:
        await msg.edit_text(text, parse_mode="Markdown")
    except Exception:
        await msg.edit_text(text)


async def gempa_dirasakan_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk /gempadirasakan."""
    msg = await update.message.reply_text("⏳ Mengambil data gempa dirasakan terkini...")
    gempa_list = bmkg.get_felt_earthquakes()

    if not gempa_list:
        await msg.edit_text("❌ Gagal mengambil data gempa dirasakan.")
        return

    text = bmkg.format_earthquake_list(gempa_list, "10 Gempa Dirasakan Terkini — BMKG")
    try:
        await msg.edit_text(text, parse_mode="Markdown")
    except Exception:
        await msg.edit_text(text)


# ===================== TEXT SEARCH HANDLER =====================


async def handle_weather_search(msg_target: Any, query: str) -> None:
    """Cari wilayah dan tampilkan hasil cuaca atau daftar opsi jika ambigu."""
    matches = bmkg.search_wilayah(query, limit=5)

    if not matches:
        await msg_target.edit_text(
            f"❌ Wilayah *{query}* tidak ditemukan.\n\n"
            "💡 *Tips Pencarian:*\n"
            "• Gunakan nama kota/kabupaten besar (contoh: `Bandung`, `Surabaya`, `Medan`)\n"
            "• Atau nama kecamatan (contoh: `Kuta`, `Lembang`, `Gambir`, `Cilandak`)\n"
            "• Atau ketik kode adm4 BMKG (contoh: `31.71.01.1001`)",
            parse_mode="Markdown",
        )
        return

    # Jika hanya 1 hasil atau match pertama sangat kuat
    if len(matches) == 1 or matches[0].get("type") in ("adm4", "alias"):
        chosen = matches[0]
        adm4 = chosen["adm4"]
        data = bmkg.get_weather_bmkg(adm4)
        if not data:
            await msg_target.edit_text("❌ Gagal mengambil data cuaca dari BMKG untuk wilayah ini.")
            return

        prov = data.get("lokasi", {}).get("provinsi", "")
        text = bmkg.format_current_weather(data)
        keyboard = build_weather_actions_keyboard(adm4, prov=prov)
        try:
            await msg_target.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        except Exception:
            await msg_target.edit_text(text, reply_markup=keyboard)
        return

    # Jika terdapat beberapa kecocokan, sajikan tombol pilihan
    keyboard = []
    for it in matches:
        nama = it.get("name", "")
        parent = it.get("parent", "")
        adm4 = it.get("adm4", "")
        label = f"{nama} ({parent})" if parent else nama
        if len(label) > 40:
            label = label[:37] + "..."
        keyboard.append([InlineKeyboardButton(f"📍 {label}", callback_data=f"cuaca|{adm4}")])

    await msg_target.edit_text(
        f"🔍 Ditemukan beberapa wilayah untuk *{query}*.\nSilakan pilih salah satu:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler pesan teks biasa — otomatis dicari sebagai nama kota/wilayah."""
    text = update.message.text.strip()
    if not text:
        return

    msg = await update.message.reply_text(f"⏳ Mencari info cuaca untuk *{text}*...", parse_mode="Markdown")
    await handle_weather_search(msg, text)


# ===================== CALLBACK QUERY HANDLER =====================


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler untuk interaksi tombol inline keyboard."""
    query = update.callback_query
    await query.answer()

    data_parts = query.data.split("|")
    action = data_parts[0]

    # --- Navigasi Menu ---
    if action == "menu":
        target = data_parts[1]
        if target == "main":
            keyboard = [
                [
                    InlineKeyboardButton("🌤️ Cek Cuaca", callback_data="menu|cuaca"),
                    InlineKeyboardButton("⚠️ Peringatan Dini", callback_data="cap|list"),
                ],
                [
                    InlineKeyboardButton("🌍 Info Gempa BMKG", callback_data="menu|gempa"),
                    InlineKeyboardButton("📖 Panduan", callback_data="menu|help"),
                ],
            ]
            await query_safe_edit(
                query,
                "👋 *Menu Utama Bot BMKG*\n\nSilakan pilih menu di bawah:",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        elif target == "cuaca":
            await query_safe_edit(
                query,
                "🌤️ *Pilih kota di bawah atau ketik langsung nama kota/wilayah:*\n"
                "Contoh: `Bandung`, `Kuta`, `Surabaya`",
                reply_markup=build_popular_cities_keyboard(),
            )
        elif target == "gempa":
            keyboard = [
                [InlineKeyboardButton("🌍 Gempa Terbaru", callback_data="gempa|terbaru")],
                [
                    InlineKeyboardButton("📋 10 Gempa M 5.0+ Terkini", callback_data="gempa|terkini"),
                    InlineKeyboardButton("💢 Gempa Dirasakan", callback_data="gempa|dirasakan"),
                ],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")],
            ]
            await query_safe_edit(
                query,
                "🌍 *Pilihan Informasi Gempa Bumi BMKG:*",
                reply_markup=InlineKeyboardMarkup(keyboard),
            )
        elif target == "help":
            await help_command(update, context)

    # --- Cuaca Saat Ini ---
    elif action == "cuaca":
        adm4 = data_parts[1]
        await query.edit_message_text("⏳ Mengambil data cuaca BMKG...", parse_mode="Markdown")
        data = bmkg.get_weather_bmkg(adm4)
        if not data:
            await query.edit_message_text("❌ Gagal mengambil data cuaca BMKG.")
            return

        prov = data.get("lokasi", {}).get("provinsi", "")
        text = bmkg.format_current_weather(data)
        keyboard = build_weather_actions_keyboard(adm4, prov=prov)
        await query_safe_edit(query, text, reply_markup=keyboard)

    # --- Ramalan Cuaca ---
    elif action == "ramalan":
        adm4 = data_parts[1]
        day_offset = int(data_parts[2]) if len(data_parts) > 2 else 0

        await query.edit_message_text("⏳ Mengambil data ramalan cuaca...", parse_mode="Markdown")
        data = bmkg.get_weather_bmkg(adm4)
        if not data:
            await query.edit_message_text("❌ Gagal mengambil ramalan cuaca BMKG.")
            return

        text = bmkg.format_forecast_bmkg(data, day_offset=day_offset)
        keyboard = [
            [
                InlineKeyboardButton("📅 24 Jam", callback_data=f"ramalan|{adm4}|0"),
                InlineKeyboardButton("Hari 1", callback_data=f"ramalan|{adm4}|1"),
                InlineKeyboardButton("Hari 2", callback_data=f"ramalan|{adm4}|2"),
                InlineKeyboardButton("Hari 3", callback_data=f"ramalan|{adm4}|3"),
            ],
            [
                InlineKeyboardButton("🌤️ Cuaca Saat Ini", callback_data=f"cuaca|{adm4}"),
                InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main"),
            ],
        ]
        await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Peringatan Dini CAP Nowcast ---
    elif action == "cap":
        subaction = data_parts[1]
        if subaction == "list":
            await query.edit_message_text("⏳ Memeriksa peringatan dini cuaca BMKG aktif...", parse_mode="Markdown")
            alerts = bmkg.get_nowcast_alerts()
            text = bmkg.format_nowcast_list(alerts)
            keyboard = []
            for a in alerts[:5]:
                t = a.get("title", "Lihat")
                aid = a.get("id")
                if aid:
                    keyboard.append([InlineKeyboardButton(f"🚨 {t[:35]}", callback_data=f"cap|detail|{aid}")])
            keyboard.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")])
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif subaction == "prov":
            prov_name = data_parts[2]
            await query.edit_message_text(f"⏳ Mengambil peringatan cuaca di *{prov_name}*...", parse_mode="Markdown")
            alerts = bmkg.get_nowcast_alerts(filter_prov=prov_name)
            text = bmkg.format_nowcast_list(alerts, filter_prov=prov_name)
            keyboard = []
            for a in alerts[:4]:
                aid = a.get("id")
                if aid:
                    keyboard.append([InlineKeyboardButton(f"🚨 {a.get('title', '')[:35]}", callback_data=f"cap|detail|{aid}")])
            keyboard.append([InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")])
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif subaction == "detail":
            alert_id = data_parts[2]
            await query.edit_message_text("⏳ Mengambil detail peringatan dini cuaca...", parse_mode="Markdown")
            detail = bmkg.get_nowcast_detail(alert_id)
            if not detail:
                await query.edit_message_text("❌ Gagal memuat detail peringatan CAP.")
                return

            text = bmkg.format_nowcast_detail(detail)
            keyboard = [
                [InlineKeyboardButton("📋 Daftar Peringatan", callback_data="cap|list")],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")],
            ]
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

    # --- Gempa ---
    elif action == "gempa":
        subaction = data_parts[1]
        if subaction == "terbaru":
            await query.edit_message_text("⏳ Mengambil data gempa terbaru...", parse_mode="Markdown")
            gempa = bmkg.get_latest_earthquake()
            if not gempa:
                await query.edit_message_text("❌ Gagal mengambil data gempa.")
                return
            text = bmkg.format_earthquake(gempa)
            keyboard = [
                [
                    InlineKeyboardButton("📋 10 Gempa Terkini", callback_data="gempa|terkini"),
                    InlineKeyboardButton("💢 Dirasakan", callback_data="gempa|dirasakan"),
                ],
                [InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")],
            ]
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif subaction == "terkini":
            await query.edit_message_text("⏳ Mengambil 10 gempa terkini M 5.0+...", parse_mode="Markdown")
            gempa_list = bmkg.get_recent_earthquakes()
            if not gempa_list:
                await query.edit_message_text("❌ Gagal mengambil data gempa terkini.")
                return
            text = bmkg.format_earthquake_list(gempa_list, "10 Gempa Terkini (M 5.0+) — BMKG")
            keyboard = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")]]
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))

        elif subaction == "dirasakan":
            await query.edit_message_text("⏳ Mengambil 10 gempa dirasakan...", parse_mode="Markdown")
            gempa_list = bmkg.get_felt_earthquakes()
            if not gempa_list:
                await query.edit_message_text("❌ Gagal mengambil data gempa dirasakan.")
                return
            text = bmkg.format_earthquake_list(gempa_list, "10 Gempa Dirasakan Terkini — BMKG")
            keyboard = [[InlineKeyboardButton("🔙 Menu Utama", callback_data="menu|main")]]
            await query_safe_edit(query, text, reply_markup=InlineKeyboardMarkup(keyboard))


# ===================== MAIN APPLICATION =====================


def main() -> None:
    if not TELEGRAM_TOKEN:
        raise SystemExit("❌ TELEGRAM_BOT_TOKEN belum diset di file .env")

    # Inisialisasi aplikasi Telegram Bot
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Daftarkan command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("cuaca", cuaca_command))
    app.add_handler(CommandHandler("ramalan", ramalan_command))
    app.add_handler(CommandHandler("peringatan", peringatan_command))
    app.add_handler(CommandHandler("nowcast", peringatan_command))
    app.add_handler(CommandHandler("gempa", gempa_command))
    app.add_handler(CommandHandler("gempaterkini", gempa_terkini_command))
    app.add_handler(CommandHandler("gempadirasakan", gempa_dirasakan_command))

    # Callback query handler untuk tombol inline
    app.add_handler(CallbackQueryHandler(button_callback))

    # Message handler untuk teks pencarian langsung (harus paling akhir)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message))

    logger.info("🌤️⚠️ Bot Cuaca & Gempa BMKG siap berjalan...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

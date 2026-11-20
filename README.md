# 🌤️⚠️🌍 Bot Telegram BMKG (Cuaca, Peringatan Dini, & Gempa)

Bot Telegram resmi berbasis data terbuka BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) Indonesia.

Mengintegrasikan repositori resmi open-data BMKG:
- **[infoBMKG/data-cuaca](https://github.com/infoBMKG/data-cuaca.git)**: Prakiraan cuaca real-time & 3 harian seluruh desa/kecamatan di Indonesia (endpoint `api.bmkg.go.id`).
- **[infoBMKG/data-cap](https://github.com/infoBMKG/data-cap.git)**: Peringatan dini cuaca aktif (Nowcast CAP XML / RSS).
- **BMKG TEWS**: Info gempabumi real-time, terkini M 5.0+, dirasakan, serta peta Shakemap.

> [!NOTE]
> **100% Gratis & Tanpa API Key Pihak Ketiga!** Anda tidak membutuhkan akun OpenWeatherMap atau API key luar negeri lagi. Hanya memerlukan token bot Telegram dari `@BotFather`.

---

## Fitur Utama

- 🌤️ **Prakiraan Cuaca Real-Time BMKG**:
  - Cakupan seluruh 514 kabupaten/kota dan 7.000+ kecamatan se-Indonesia
  - Parameter lengkap: suhu udara (°C), kondisi cuaca, kelembapan (%), kecepatan & arah angin, tutupan awan (%), potensi curah hujan (mm)
  - Ramalan 24 jam ke depan dan ramalan harian 3 hari
  - Mendukung input nama kota, nama kecamatan, alias populer (contoh: `Solo`, `Jogja`), maupun kode ADM4 resmi Kemendagri

- ⚠️ **Peringatan Dini Cuaca (CAP Nowcast)**:
  - Notifikasi langsung dari sistem peringatan dini cuaca darurat berbasis standar internasional *Common Alerting Protocol* (CAP)
  - Detail wilayah terdampak, tingkat keparahan (*severity*), durasi berlaku, dan tautan gambar infografis resmi BMKG
  - Otomatis mendeteksi peringatan dini aktif di provinsi saat mengecek cuaca kota

- 🌍 **Informasi Gempabumi BMKG**:
  - `/gempa` — Gempa bumi terbaru dengan status potensi tsunami & tautan peta Shakemap
  - `/gempaterkini` — Daftar 10 gempa M 5.0+ terkini
  - `/gempadirasakan` — Daftar 10 gempa yang dirasakan masyarakat (skala MMI)

---

## Panduan Instalasi & Menjalankan

### 1. Install Dependencies

```bash
cd telegram-weather-bot
pip install -r requirements.txt
```

### 2. Atur Token Bot Telegram

Salin file contoh konfigurasi `.env.example` ke `.env`:
```bash
cp .env.example .env
```

Buka file `.env` dan masukkan token bot Anda dari [@BotFather](https://t.me/BotFather):
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

*(Tidak diperlukan API key lainnya)*

### 3. Jalankan Bot

```bash
python bot.py
```

---

## Daftar Perintah Bot

| Perintah | Deskripsi |
|----------|-----------|
| `/start` | Membuka menu navigasi utama & tombol interaktif |
| `/cuaca <kota>` | Cek cuaca terkini di kota/kecamatan tertentu |
| `/ramalan <kota>` | Prakiraan cuaca 24 jam & 3 hari ke depan |
| `/peringatan [prov]` | Cek peringatan dini cuaca aktif (CAP Nowcast) se-Indonesia atau per provinsi |
| `/gempa` | Informasi gempa bumi terbaru beserta Shakemap |
| `/gempaterkini` | Daftar 10 gempa bumi M 5.0+ terkini |
| `/gempadirasakan` | Daftar 10 gempa bumi yang dirasakan |
| `/help` | Menampilkan panduan lengkap bot |
| _Ketik langsung nama kota_ | Bot langsung mencari daerah dan menyajikan info cuaca |

---

## Contoh Penggunaan

- `/cuaca Jakarta`
- `/cuaca Bandung`
- `/cuaca Kuta`
- `/cuaca 31.71.01.1001`
- `/ramalan Surabaya`
- `/peringatan Jawa Barat`
- `/gempa`

---

## Sumber Data & Atribusi

Data pada bot ini bersumber dari portal data terbuka resmi **Badan Meteorologi, Klimatologi, dan Geofisika (BMKG)** Indonesia:
- [BMKG Open Data Cuaca](https://data.bmkg.go.id/prakiraan-cuaca) & [GitHub infoBMKG/data-cuaca](https://github.com/infoBMKG/data-cuaca)
- [BMKG Common Alerting Protocol (CAP)](https://data.bmkg.go.id/peringatan-dini-cuaca) & [GitHub infoBMKG/data-cap](https://github.com/infoBMKG/data-cap)
- [BMKG TEWS Gempabumi](https://data.bmkg.go.id/gempabumi)

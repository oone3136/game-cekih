# 🃏 Remi Cekih Edisi Pos Ronda (Visual UI & Custom Skin)

Game kartu Remi Cekih tradisional Indonesia dengan **Tampilan Grafis Meja Modern**, 4 pemain (1 Pemain vs 3 Bot: Pak RT, Pak RW, Pak Sukardi), efek suara sintetis, animasi partikel kemenangan, dan **Sistem Toko Skin (Custom Meja, Kartu & Animasi)**.

---

## 🚀 Cara Menjalankan Game Next.js (Sesuai Sketsa Meja)

1. **Cara Cepat (Tinggal Klik 2x):**
   * Masuk ke folder **`D:\hilman-game`**.
   * Klik 2x file **`run_next.bat`** (atau `run_ui.bat`).
   * Sistem otomatis menjalankan Python Backend Server (Port 8000) dan Next.js Server (Port 3000), lalu membuka browser di:
     👉 **`http://localhost:3000`**

2. **Atau Lewat Terminal / PowerShell:**
   * **Terminal 1 (Backend API):**
     ```powershell
     cd D:\hilman-game
     python server.py 8000
     ```
   * **Terminal 2 (Next.js Frontend):**
     ```powershell
     cd D:\hilman-game\frontend
     npm run dev
     ```
   * Buka browser di **`http://localhost:3000`**.

*(Catatan: Versi standalone bawaan Python tetap bisa diakses di `http://localhost:8000`).*

---

## 🎨 Fitur Toko Skin & Kustomisasi (Siap Monetisasi)

Klik tombol **🛒 Toko Skin Meja & Kartu** di kanan atas layar untuk mencoba gonta-ganti skin secara langsung (*real-time*):

### 1. Latar Meja (Table Skins):
* **Pos Ronda Kayu & Beludru (Default / Gratis):** Meja kayu jati khas pos ronda dengan karpet beludru hijau hangat.
* **Kasino Royal Gold (Skin VIP):** Karpet beludru merah maroon mewah dengan lis ukiran emas 24 karat.
* **Cyber Ronda Neon (Skin Cyber):** Meja futuristik dark mode dengan aksen garis neon cyan & magenta.

### 2. Skin Kartu (Card Backs):
* **Batik Pos Ronda (Default / Gratis):** Motif batik tradisional biru tua khas Nusantara.
* **Golden Dragon VIP (Skin Kartu):** Punggung kartu naga emas berkilau berlatar hitam elegan.
* **Nusantara Merah Bara (Skin Kartu):** Ornamen wayang merah menyala dengan bingkai perak.

### 3. Efek Animasi Menang (Victory FX):
* **Petasan Pos Ronda (Default / Gratis):** Ledakan confetti warna-warni meriah dengan tulisan Cekih menggelegar.
* **Hujan Koin Emas (Efek Sultan):** Ratusan koin emas berjatuhan dari atas layar saat kamu berhasil Tutup.
* **Petir Halilintar (Efek Legend):** Sambaran kilat petir menyambar meja saat kartu kunci ditutup!

### 4. Animasi Lemparan Gertak Cekih (Taunt FX):
* **Lempar Batu Kali 🪨 (Default / Gratis):** Lempar batu pos ronda melayang dengan suara *BONK* bikin Pak Sukardi kaget!
* **Siram Air Segelas 💧 (Skin Lemparan):** Guyuran air segar dengan suara *SPLASH* membasahi lawan.
* **Lempar Sandal Jepit 🩴 (Skin Lemparan):** Sandal jepit melayang *PLAK* mendarat pas di kepala Pak Sukardi!

---

## 🎮 Cara Bermain & Fitur Lengkap:
1. **Timer Dua Fase (30 Detik Ambil + 30 Detik Buang):**
   * Fase 1: Kamu diberi **30 detik** untuk mengambil kartu (tarik kocokan atau serok buangan).
   * Fase 2: Setelah kartu terambil, timer di-reset ke **30 detik baru** untuk memilih kartu buang.
   * Auto-Discard cerdas: Jika waktu buang habis, sistem otomatis membuang kartu aman, dan **Joker 100% dilindungi** agar terhindar dari denda -250 poin.
2. **Tombol 🚨 Gertak Cekih!:**
   * Tombol merah untuk menggertak pemain sebelum Anda (Pak Sukardi).
   * Proyektil (batu/air/sandal) akan melayang terbang menabrak avatar Pak Sukardi dengan efek getaran layar dan balon dialog kaget dari Pak Sukardi.
3. **Serok Buangan Fleksibel (Bisa 3, 4, 5, 6+ Kartu):**
   * Saat menyerok dari buangan, Anda tidak terbatas hanya 3 kartu. Anda bisa memilih 2, 3, 4, 5 kartu dari tangan untuk disambungkan dengan kartu buangan selama rangkaiannya nyambung (Seri atau Tris).
4. **Kartu Terbuka di Meja (Open Melds):**
   * Kartu hasil serokan buangan ditaruh terbuka di meja di hadapan masing-masing pemain (tidak dimasukkan kembali ke kartu tangan tertutup).
5. **Cekih Gantung & Penyatuan Joker:**
   * Jika kartu Anda sudah jadi dan Anda memilih **Cekih Gantung (Lanjut Main)**, kartu Joker dapat langsung disatukan ke rangkaian kartu di meja sehingga Anda bebas dari ancaman denda Joker mentah.
6. **Gusar-Geser Kartu (Drag & Drop):**
   * Geser dan pindahkan posisi kartu di tangan untuk memisahkan kartu jadi dan kartu mentah.
   * Tombol **`🧹 Susun Kembang`** dan **`🔢 Susun Angka`** tersedia untuk perapian otomatis instan.
7. **Pemenang Ronde Mulai Duluan:**
   * Pada ronde ke-2 dan seterusnya, pemain dengan total skor tertinggi akan otomatis mendapatkan giliran pertama.

---

## 📁 Struktur File Projek

* [`run_ui.bat`](file:///D:/hilman-game/run_ui.bat) — Shortcut launcher UI untuk Windows.
* [`server.py`](file:///D:/hilman-game/server.py) — Web server & REST API lokal (tanpa perlu install library tambahan).
* [`web/index.html`](file:///D:/hilman-game/web/index.html) — Halaman meja kartu dan antarmuka interaktif.
* [`web/style.css`](file:///D:/hilman-game/web/style.css) — Desain meja poker, tema skin, dan animasi.
* [`web/game_ui.js`](file:///D:/hilman-game/web/game_ui.js) — Logika antarmuka, Web Audio FX, partikel canvas, dan integrasi bot.
* [`config.py`](file:///D:/hilman-game/config.py) — Saklar pengaturan aturan game (Rule Engine).
* [`rules.py`](file:///D:/hilman-game/rules.py) — Mesin validasi Seri/Tris, Serok buangan, Cek Tutup, dan Skor.
* [`card.py`](file:///D:/hilman-game/card.py) & [`deck.py`](file:///D:/hilman-game/deck.py) — Model kartu & kocokan.
* [`bot.py`](file:///D:/hilman-game/bot.py) — Kecerdasan buatan Pak RT, Pak RW, dan Pak Sukardi.
* [`main.py`](file:///D:/hilman-game/main.py) & [`main.bat`](file:///D:/hilman-game/main.bat) — Alternatif versi terminal/CLI.

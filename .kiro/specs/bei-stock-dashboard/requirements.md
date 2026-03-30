# Requirements Document

## Introduction

BEI Stock Dashboard adalah aplikasi web production-ready untuk analisa saham di Bursa Efek Indonesia (BEI). Aplikasi ini memungkinkan investor ritel dan analis untuk mencari, memfilter, menilai, dan memantau saham BEI berdasarkan data fundamental, teknikal, dan metrik valuasi. MVP berfokus pada pencarian saham, tampilan metrik kunci (PER, PBV, ROE, Dividend Yield), watchlist personal, dan ranking saham berdasarkan skor internal.

## Glossary

- **Dashboard**: Aplikasi web utama BEI Stock Dashboard
- **User**: Pengguna terdaftar yang telah login ke Dashboard
- **Emiten**: Perusahaan yang sahamnya terdaftar di BEI
- **Stock_Code**: Kode ticker saham BEI (contoh: BBCA, TLKM, GOTO), terdiri dari 4 huruf kapital
- **Stock_Profile**: Halaman detail satu emiten yang menampilkan data fundamental, teknikal, dan metrik valuasi
- **Screener**: Fitur pencarian dan filter saham berdasarkan kriteria tertentu
- **Watchlist**: Daftar saham yang disimpan oleh User untuk dipantau
- **Score**: Skor internal saham yang dihitung dari kombinasi metrik fundamental, valuasi, dan teknikal (skala 0–100)
- **PER**: Price-to-Earnings Ratio — rasio harga saham terhadap laba per saham
- **PBV**: Price-to-Book Value — rasio harga saham terhadap nilai buku per saham
- **ROE**: Return on Equity — tingkat pengembalian ekuitas pemegang saham (dalam persen)
- **Dividend_Yield**: Persentase dividen tahunan terhadap harga saham saat ini
- **Sector**: Klasifikasi industri emiten berdasarkan IDX Industry Classification
- **Price_History**: Data harga historis saham (OHLCV — Open, High, Low, Close, Volume)
- **Fundamental_Data**: Data laporan keuangan emiten (neraca, laba rugi, arus kas)
- **Corporate_Action**: Aksi korporasi emiten seperti dividen, stock split, rights issue
- **Auth_Service**: Layanan autentikasi dan manajemen sesi pengguna
- **Stock_Service**: Layanan pengambilan dan pemrosesan data saham dari sumber data BEI
- **Scoring_Engine**: Komponen yang menghitung Score saham berdasarkan metrik fundamental dan teknikal
- **API**: Backend REST API yang melayani permintaan dari Frontend
- **Frontend**: Aplikasi Next.js yang diakses pengguna melalui browser
- **Database**: PostgreSQL yang menyimpan data pengguna, watchlist, dan cache data saham
- **AI_Analyzer**: Komponen yang menggunakan model AI untuk menganalisa data saham dan menghasilkan ringkasan serta rekomendasi investasi dalam Bahasa Indonesia

---

## Requirements

### Requirement 1: Autentikasi Pengguna

**User Story:** Sebagai investor, saya ingin mendaftar dan login ke Dashboard, agar watchlist dan preferensi saya tersimpan secara personal.

#### Acceptance Criteria

1. THE Auth_Service SHALL menyediakan endpoint registrasi yang menerima email, password, dan nama pengguna
2. WHEN User mengirimkan email yang sudah terdaftar, THE Auth_Service SHALL mengembalikan pesan error "Email sudah digunakan"
3. WHEN User berhasil registrasi, THE Auth_Service SHALL mengirimkan email verifikasi ke alamat email yang didaftarkan
4. WHEN User mengirimkan kredensial yang valid, THE Auth_Service SHALL mengembalikan JWT access token dengan masa berlaku 1 jam dan refresh token dengan masa berlaku 7 hari
5. WHEN User mengirimkan kredensial yang tidak valid, THE Auth_Service SHALL mengembalikan HTTP 401 dengan pesan error yang tidak mengungkap detail spesifik (email atau password mana yang salah)
6. WHEN refresh token masih valid, THE Auth_Service SHALL menerbitkan access token baru tanpa meminta User login ulang
7. WHEN User melakukan logout, THE Auth_Service SHALL mencabut refresh token yang aktif
8. THE Auth_Service SHALL menyimpan password menggunakan algoritma bcrypt dengan cost factor minimal 12

---

### Requirement 2: Pencarian Saham

**User Story:** Sebagai investor, saya ingin mencari saham berdasarkan kode atau nama emiten, agar saya dapat dengan cepat menemukan saham yang ingin saya analisa.

#### Acceptance Criteria

1. WHEN User memasukkan minimal 1 karakter pada kolom pencarian, THE Screener SHALL menampilkan daftar saran emiten yang cocok berdasarkan Stock_Code atau nama emiten
2. WHEN User memasukkan Stock_Code yang tepat, THE Screener SHALL menampilkan hasil pencarian dalam waktu kurang dari 500ms
3. WHEN pencarian tidak menghasilkan hasil, THE Screener SHALL menampilkan pesan "Saham tidak ditemukan" beserta saran untuk memeriksa kode yang dimasukkan
4. THE Screener SHALL mendukung pencarian case-insensitive untuk Stock_Code dan nama emiten
5. THE Screener SHALL menampilkan maksimal 10 hasil saran pada dropdown pencarian

---

### Requirement 3: Tampilan Profil Emiten

**User Story:** Sebagai investor, saya ingin melihat profil lengkap suatu emiten, agar saya dapat memahami bisnis dan kondisi keuangannya sebelum berinvestasi.

#### Acceptance Criteria

1. WHEN User membuka halaman Stock_Profile, THE Dashboard SHALL menampilkan nama emiten, Stock_Code, Sector, dan deskripsi singkat bisnis
2. THE Dashboard SHALL menampilkan harga terakhir, perubahan harga (nominal dan persentase), serta volume perdagangan hari ini
3. THE Dashboard SHALL menampilkan metrik valuasi: PER, PBV, ROE, dan Dividend_Yield
4. WHEN data metrik tidak tersedia untuk suatu emiten, THE Dashboard SHALL menampilkan tanda "N/A" pada metrik tersebut
5. THE Dashboard SHALL menampilkan grafik Price_History dengan pilihan rentang waktu: 1 minggu, 1 bulan, 3 bulan, 6 bulan, 1 tahun, dan 5 tahun
6. WHEN User memilih rentang waktu pada grafik, THE Dashboard SHALL memperbarui tampilan grafik dalam waktu kurang dari 1 detik
7. THE Dashboard SHALL menampilkan Score emiten beserta breakdown komponen skor (valuasi, kualitas, momentum)

---

### Requirement 4: Filter Sektor

**User Story:** Sebagai investor, saya ingin memfilter saham berdasarkan sektor industri, agar saya dapat membandingkan saham dalam industri yang sama.

#### Acceptance Criteria

1. THE Screener SHALL menampilkan daftar semua Sector yang tersedia berdasarkan IDX Industry Classification
2. WHEN User memilih satu atau lebih Sector, THE Screener SHALL menampilkan hanya emiten yang termasuk dalam Sector yang dipilih
3. WHEN User menghapus semua filter Sector, THE Screener SHALL menampilkan kembali semua emiten
4. THE Screener SHALL mempertahankan filter Sector yang aktif ketika User melakukan pencarian teks bersamaan

---

### Requirement 5: Skor Internal Saham

**User Story:** Sebagai investor, saya ingin melihat skor objektif untuk setiap saham, agar saya dapat dengan cepat membandingkan kualitas saham tanpa harus menganalisa semua metrik secara manual.

#### Acceptance Criteria

1. THE Scoring_Engine SHALL menghitung Score untuk setiap emiten pada skala 0 hingga 100
2. THE Scoring_Engine SHALL menghitung Score berdasarkan tiga komponen: skor valuasi (bobot 40%), skor kualitas fundamental (bobot 40%), dan skor momentum teknikal (bobot 20%)
3. THE Scoring_Engine SHALL memperbarui Score setiap hari setelah penutupan pasar BEI (setelah pukul 16:30 WIB)
4. WHEN data fundamental tidak lengkap untuk suatu emiten, THE Scoring_Engine SHALL menghitung Score hanya dari komponen yang datanya tersedia dan menandai Score sebagai "Parsial"
5. THE Dashboard SHALL menampilkan Score dengan label kategori: 80–100 = "Sangat Baik", 60–79 = "Baik", 40–59 = "Cukup", 0–39 = "Perlu Perhatian"

---

### Requirement 6: Watchlist

**User Story:** Sebagai investor, saya ingin menyimpan daftar saham yang ingin saya pantau, agar saya dapat dengan mudah mengakses saham pilihan saya setiap kali membuka Dashboard.

#### Acceptance Criteria

1. WHILE User sudah login, THE Dashboard SHALL menampilkan tombol "Tambah ke Watchlist" pada setiap halaman Stock_Profile
2. WHEN User menambahkan saham ke Watchlist, THE Database SHALL menyimpan relasi antara User dan Stock_Code tersebut
3. WHEN User mencoba menambahkan saham yang sudah ada di Watchlist, THE Dashboard SHALL menampilkan pesan "Saham sudah ada di watchlist" tanpa membuat duplikasi
4. THE Dashboard SHALL menampilkan halaman Watchlist yang memuat semua saham yang disimpan User beserta harga terkini, perubahan harga, dan Score
5. WHEN User menghapus saham dari Watchlist, THE Database SHALL menghapus relasi tersebut dan THE Dashboard SHALL memperbarui tampilan Watchlist tanpa perlu reload halaman
6. THE Dashboard SHALL membatasi jumlah saham dalam Watchlist satu User maksimal 50 saham
7. IF User yang belum login mencoba menambahkan saham ke Watchlist, THEN THE Dashboard SHALL mengarahkan User ke halaman login

---

### Requirement 7: Ranking Saham

**User Story:** Sebagai investor, saya ingin melihat daftar saham yang diurutkan berdasarkan skor terbaik, agar saya dapat menemukan saham berkualitas tinggi dengan cepat.

#### Acceptance Criteria

1. THE Dashboard SHALL menampilkan halaman Ranking yang memuat daftar emiten diurutkan berdasarkan Score dari tertinggi ke terendah
2. THE Dashboard SHALL menampilkan minimal kolom berikut pada halaman Ranking: Stock_Code, nama emiten, Sector, harga terakhir, Score, PER, PBV, ROE, dan Dividend_Yield
3. WHEN User mengklik header kolom pada tabel Ranking, THE Dashboard SHALL mengurutkan ulang daftar berdasarkan kolom tersebut secara ascending atau descending
4. THE Dashboard SHALL mendukung filter Sector pada halaman Ranking
5. THE Dashboard SHALL menampilkan data Ranking dengan pagination, menampilkan 25 emiten per halaman

---

### Requirement 8: Perbandingan Metrik vs Sektor

**User Story:** Sebagai investor, saya ingin membandingkan metrik suatu saham dengan rata-rata sektornya, agar saya dapat menilai apakah saham tersebut undervalued atau overvalued relatif terhadap kompetitornya.

#### Acceptance Criteria

1. THE Dashboard SHALL menampilkan perbandingan PER, PBV, ROE, dan Dividend_Yield emiten terhadap median Sector yang sama
2. THE Dashboard SHALL menampilkan indikator visual (ikon atau warna) yang menunjukkan apakah metrik emiten lebih baik atau lebih buruk dari median Sector
3. THE Stock_Service SHALL menghitung median metrik per Sector setiap hari setelah penutupan pasar
4. WHEN suatu Sector memiliki kurang dari 3 emiten dengan data lengkap, THE Dashboard SHALL menampilkan pesan "Data sektor tidak cukup untuk perbandingan"

---

### Requirement 9: Integrasi Data Saham BEI

**User Story:** Sebagai pengelola sistem, saya ingin data saham diperbarui secara otomatis dari sumber resmi BEI, agar pengguna selalu mendapatkan informasi yang akurat dan terkini.

#### Acceptance Criteria

1. THE Stock_Service SHALL mengambil data harga intraday dari sumber data BEI setiap 15 menit selama jam perdagangan (09:00–16:30 WIB pada hari bursa)
2. THE Stock_Service SHALL mengambil data Fundamental_Data dari laporan keuangan emiten setiap kali laporan keuangan baru dipublikasikan
3. THE Stock_Service SHALL mengambil data Corporate_Action dan memperbarui kalkulasi metrik yang terpengaruh dalam waktu 24 jam setelah Corporate_Action diumumkan
4. IF sumber data eksternal tidak dapat diakses selama lebih dari 30 menit, THEN THE Stock_Service SHALL menampilkan banner peringatan pada Dashboard bahwa data mungkin tidak terkini
5. THE Stock_Service SHALL menyimpan Price_History minimal 5 tahun ke belakang untuk setiap emiten yang aktif
6. THE Database SHALL menyimpan cache data harga terkini untuk mengurangi ketergantungan pada sumber data eksternal saat terjadi gangguan

---

### Requirement 10: Kerangka Analisa Valuasi, Kualitas, dan Risiko

**User Story:** Sebagai investor, saya ingin melihat analisa terstruktur untuk setiap saham berdasarkan tiga dimensi (valuasi, kualitas, risiko), agar saya dapat membuat keputusan investasi yang lebih terinformasi.

#### Acceptance Criteria

1. THE Dashboard SHALL menampilkan tab "Analisa" pada halaman Stock_Profile yang memuat tiga bagian: Valuasi, Kualitas Fundamental, dan Risiko
2. THE Dashboard SHALL menampilkan pada bagian Valuasi: PER, PBV, EV/EBITDA, dan perbandingan terhadap nilai historis 3 tahun terakhir emiten tersebut
3. THE Dashboard SHALL menampilkan pada bagian Kualitas Fundamental: ROE, ROA, Debt-to-Equity Ratio, Current Ratio, dan Net Profit Margin
4. THE Dashboard SHALL menampilkan pada bagian Risiko: Beta saham, volatilitas 30 hari, dan rasio utang terhadap ekuitas
5. WHEN data historis untuk perbandingan valuasi tidak tersedia, THE Dashboard SHALL menampilkan "Data historis tidak tersedia" pada bagian tersebut

---

### Requirement 11: Rekomendasi Beli/Jual

**User Story:** Sebagai investor, saya ingin melihat rekomendasi beli atau jual berdasarkan analisa fundamental dan teknikal, agar saya mendapatkan panduan awal dalam pengambilan keputusan.

#### Acceptance Criteria

1. THE Scoring_Engine SHALL menghasilkan rekomendasi dengan empat level: "Beli Kuat" (Score ≥ 75), "Beli" (Score 60–74), "Tahan" (Score 40–59), dan "Jual" (Score < 40)
2. THE Dashboard SHALL menampilkan rekomendasi beserta ringkasan alasan yang mencantumkan maksimal 3 faktor pendukung utama
3. THE Dashboard SHALL menampilkan disclaimer yang menyatakan bahwa rekomendasi bersifat informatif dan bukan merupakan saran investasi resmi
4. WHEN Score suatu emiten berubah sehingga mengubah level rekomendasi, THE Dashboard SHALL memperbarui tampilan rekomendasi pada sesi User berikutnya

---

### Requirement 12: Keamanan dan Performa Aplikasi

**User Story:** Sebagai pengguna, saya ingin aplikasi berjalan dengan cepat dan aman, agar pengalaman analisa saham saya tidak terganggu oleh masalah teknis.

#### Acceptance Criteria

1. THE API SHALL menerapkan rate limiting sebesar maksimal 100 request per menit per pengguna terautentikasi
2. THE API SHALL menerapkan rate limiting sebesar maksimal 20 request per menit untuk endpoint publik per alamat IP
3. THE Frontend SHALL mencapai skor Lighthouse Performance minimal 80 pada kondisi jaringan 4G yang disimulasikan
4. THE Database SHALL menggunakan indeks pada kolom Stock_Code, Sector, dan Score untuk memastikan query pencarian selesai dalam waktu kurang dari 100ms
5. THE API SHALL mengembalikan response untuk endpoint daftar saham dalam waktu kurang dari 300ms pada kondisi normal
6. THE Auth_Service SHALL memblokir akun sementara selama 15 menit setelah 5 kali percobaan login yang gagal berturut-turut dari alamat IP yang sama

---

### Requirement 13: Analisa Saham oleh AI

**User Story:** Sebagai investor, saya ingin mendapatkan analisa saham yang dihasilkan oleh AI berdasarkan data fundamental, teknikal, dan valuasi yang tersedia, agar saya dapat memperoleh ringkasan dan rekomendasi yang mudah dipahami sebagai bahan pertimbangan investasi.

#### Acceptance Criteria

1. WHEN User membuka tab "Analisa AI" pada halaman Stock_Profile, THE AI_Analyzer SHALL menghasilkan ringkasan analisa dalam Bahasa Indonesia berdasarkan data Fundamental_Data, Price_History, dan metrik valuasi yang tersedia
2. THE AI_Analyzer SHALL menghasilkan rekomendasi dengan empat level: "Beli Kuat", "Beli", "Tahan", atau "Jual", beserta penjelasan alasan yang mencantumkan minimal 3 faktor pendukung utama
3. THE AI_Analyzer SHALL menjelaskan faktor-faktor utama yang mendukung rekomendasinya, mencakup aspek valuasi, kualitas fundamental, dan momentum teknikal secara terpisah
4. THE Dashboard SHALL menampilkan disclaimer pada setiap hasil analisa AI yang menyatakan bahwa analisa bersifat informatif dan bukan merupakan saran investasi resmi
5. WHEN data saham diperbarui oleh Stock_Service, THE AI_Analyzer SHALL memperbarui hasil analisa AI untuk emiten yang bersangkutan dalam waktu kurang dari 5 menit setelah pembaruan data selesai
6. IF data yang tersedia untuk suatu emiten tidak mencukupi untuk menghasilkan analisa yang akurat (kurang dari 2 kuartal Fundamental_Data atau kurang dari 30 hari Price_History), THEN THE AI_Analyzer SHALL menampilkan pesan "Data tidak cukup untuk menghasilkan analisa AI yang akurat" beserta keterangan data apa yang masih kurang
7. THE AI_Analyzer SHALL menyimpan hasil analisa ke dalam Database sehingga User dapat melihat analisa terakhir tanpa menunggu proses analisa ulang
8. WHILE proses analisa AI sedang berjalan, THE Dashboard SHALL menampilkan indikator loading dan memperkirakan waktu tunggu kepada User

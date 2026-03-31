#!/usr/bin/env python3
"""Seed BEI stocks into the database (100+ stocks with syariah classification)."""

import sys
from pathlib import Path

# Allow running as standalone script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.stock import Stock

STOCKS_DATA = [
    # ── Perbankan Konvensional ──────────────────────────────────────────────
    {"code": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BBRI", "name": "Bank Rakyat Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BMRI", "name": "Bank Mandiri Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BBNI", "name": "Bank Negara Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BDMN", "name": "Bank Danamon Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BJBR", "name": "Bank Pembangunan Daerah Jawa Barat Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BNLI", "name": "Bank Permata Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "PNBN", "name": "Bank Pan Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "NISP", "name": "Bank OCBC NISP Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "MEGA", "name": "Bank Mega Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BBTN", "name": "Bank Tabungan Negara Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BBYB", "name": "Bank Neo Commerce Tbk", "sector": "Keuangan", "sub_sector": "Perbankan Digital", "is_syariah": False},
    {"code": "ARTO", "name": "Bank Jago Tbk", "sector": "Keuangan", "sub_sector": "Perbankan Digital", "is_syariah": False},
    # ── Perbankan Syariah ──────────────────────────────────────────────────
    {"code": "BRIS", "name": "Bank Syariah Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan Syariah", "is_syariah": True},
    {"code": "BTPS", "name": "Bank BTPN Syariah Tbk", "sector": "Keuangan", "sub_sector": "Perbankan Syariah", "is_syariah": True},
    # ── Asuransi & Multifinance (konvensional) ──────────────────────────────
    {"code": "PNLF", "name": "Panin Financial Tbk", "sector": "Keuangan", "sub_sector": "Asuransi", "is_syariah": False},
    {"code": "ADMF", "name": "Adira Dinamika Multi Finance Tbk", "sector": "Keuangan", "sub_sector": "Multifinance", "is_syariah": False},
    # ── Telekomunikasi ──────────────────────────────────────────────────────
    {"code": "TLKM", "name": "Telkom Indonesia Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi", "is_syariah": True},
    {"code": "EXCL", "name": "XL Axiata Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi", "is_syariah": True},
    {"code": "ISAT", "name": "Indosat Ooredoo Hutchison Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi", "is_syariah": True},
    {"code": "TOWR", "name": "Sarana Menara Nusantara Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi", "is_syariah": True},
    {"code": "TBIG", "name": "Tower Bersama Infrastructure Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi", "is_syariah": True},
    {"code": "MTEL", "name": "Dayamitra Telekomunikasi Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi", "is_syariah": True},
    # ── Otomotif & Industri ─────────────────────────────────────────────────
    {"code": "ASII", "name": "Astra International Tbk", "sector": "Industri", "sub_sector": "Otomotif", "is_syariah": True},
    {"code": "AUTO", "name": "Astra Otoparts Tbk", "sector": "Industri", "sub_sector": "Otomotif", "is_syariah": True},
    {"code": "SMSM", "name": "Selamat Sempurna Tbk", "sector": "Industri", "sub_sector": "Otomotif", "is_syariah": True},
    # ── Teknologi ───────────────────────────────────────────────────────────
    {"code": "GOTO", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Teknologi", "sub_sector": "E-Commerce", "is_syariah": True},
    {"code": "BUKA", "name": "Bukalapak.com Tbk", "sector": "Teknologi", "sub_sector": "E-Commerce", "is_syariah": True},
    {"code": "EMTK", "name": "Elang Mahkota Teknologi Tbk", "sector": "Teknologi", "sub_sector": "Media Digital", "is_syariah": True},
    {"code": "DCII", "name": "DCI Indonesia Tbk", "sector": "Teknologi", "sub_sector": "Data Center", "is_syariah": True},
    # ── Energi & Pertambangan ──────────────────────────────────────────────
    {"code": "BREN", "name": "Barito Renewables Energy Tbk", "sector": "Energi", "sub_sector": "Energi Terbarukan", "is_syariah": True},
    {"code": "PTBA", "name": "Bukit Asam Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": True},
    {"code": "ADRO", "name": "Adaro Energy Indonesia Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": True},
    {"code": "ITMG", "name": "Indo Tambangraya Megah Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": True},
    {"code": "BUMI", "name": "Bumi Resources Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": False},
    {"code": "HRUM", "name": "Harum Energy Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": True},
    {"code": "DSSA", "name": "Dian Swastatika Sentosa Tbk", "sector": "Energi", "sub_sector": "Batubara", "is_syariah": True},
    {"code": "ANTM", "name": "Aneka Tambang Tbk", "sector": "Energi", "sub_sector": "Logam", "is_syariah": True},
    {"code": "MDKA", "name": "Merdeka Copper Gold Tbk", "sector": "Energi", "sub_sector": "Logam", "is_syariah": True},
    {"code": "INCO", "name": "Vale Indonesia Tbk", "sector": "Energi", "sub_sector": "Logam", "is_syariah": True},
    {"code": "TINS", "name": "Timah Tbk", "sector": "Energi", "sub_sector": "Logam", "is_syariah": True},
    {"code": "AMMN", "name": "Amman Mineral Internasional Tbk", "sector": "Energi", "sub_sector": "Logam", "is_syariah": True},
    {"code": "MEDC", "name": "Medco Energi Internasional Tbk", "sector": "Energi", "sub_sector": "Minyak & Gas", "is_syariah": True},
    {"code": "PGAS", "name": "Perusahaan Gas Negara Tbk", "sector": "Energi", "sub_sector": "Gas", "is_syariah": True},
    {"code": "ELSA", "name": "Elnusa Tbk", "sector": "Energi", "sub_sector": "Jasa Migas", "is_syariah": True},
    {"code": "ESSA", "name": "Surya Esa Perkasa Tbk", "sector": "Energi", "sub_sector": "Gas", "is_syariah": True},
    {"code": "PGEO", "name": "Pertamina Geothermal Energy Tbk", "sector": "Energi", "sub_sector": "Geothermal", "is_syariah": True},
    # ── Kimia & Petrokimia ────────────────────────────────────────────────
    {"code": "TPIA", "name": "Chandra Asri Pacific Tbk", "sector": "Industri Dasar", "sub_sector": "Kimia", "is_syariah": True},
    {"code": "BRPT", "name": "Barito Pacific Tbk", "sector": "Industri Dasar", "sub_sector": "Kimia", "is_syariah": True},
    # ── Consumer Goods ──────────────────────────────────────────────────────
    {"code": "UNVR", "name": "Unilever Indonesia Tbk", "sector": "Barang Konsumsi", "sub_sector": "Produk Rumah Tangga", "is_syariah": True},
    {"code": "ICBP", "name": "Indofood CBP Sukses Makmur Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "INDF", "name": "Indofood Sukses Makmur Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "MYOR", "name": "Mayora Indah Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "CPIN", "name": "Charoen Pokphand Indonesia Tbk", "sector": "Barang Konsumsi", "sub_sector": "Pakan Ternak", "is_syariah": True},
    {"code": "JPFA", "name": "Japfa Comfeed Indonesia Tbk", "sector": "Barang Konsumsi", "sub_sector": "Pakan Ternak", "is_syariah": True},
    {"code": "HMSP", "name": "HM Sampoerna Tbk", "sector": "Barang Konsumsi", "sub_sector": "Rokok", "is_syariah": False},
    {"code": "GGRM", "name": "Gudang Garam Tbk", "sector": "Barang Konsumsi", "sub_sector": "Rokok", "is_syariah": False},
    {"code": "GOOD", "name": "Garudafood Putra Putri Jaya Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "ROTI", "name": "Nippon Indosari Corpindo Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "ULTJ", "name": "Ultra Jaya Milk Industry Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    {"code": "CLEO", "name": "Sariguna Primatirta Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman", "is_syariah": True},
    # ── Ritel & Perdagangan ────────────────────────────────────────────────
    {"code": "AMRT", "name": "Sumber Alfaria Trijaya Tbk", "sector": "Perdagangan", "sub_sector": "Ritel", "is_syariah": True},
    {"code": "ACES", "name": "Ace Hardware Indonesia Tbk", "sector": "Perdagangan", "sub_sector": "Ritel", "is_syariah": True},
    {"code": "LPPF", "name": "Matahari Department Store Tbk", "sector": "Perdagangan", "sub_sector": "Ritel", "is_syariah": True},
    {"code": "ERAA", "name": "Erajaya Swasembada Tbk", "sector": "Perdagangan", "sub_sector": "Ritel Elektronik", "is_syariah": True},
    # ── Farmasi & Kesehatan ─────────────────────────────────────────────────
    {"code": "KLBF", "name": "Kalbe Farma Tbk", "sector": "Kesehatan", "sub_sector": "Farmasi", "is_syariah": True},
    {"code": "SIDO", "name": "Industri Jamu Sido Muncul Tbk", "sector": "Kesehatan", "sub_sector": "Farmasi", "is_syariah": True},
    {"code": "KAEF", "name": "Kimia Farma Tbk", "sector": "Kesehatan", "sub_sector": "Farmasi", "is_syariah": True},
    {"code": "MIKA", "name": "Mitra Keluarga Karyasehat Tbk", "sector": "Kesehatan", "sub_sector": "Rumah Sakit", "is_syariah": True},
    # ── Semen & Material ────────────────────────────────────────────────────
    {"code": "SMGR", "name": "Semen Indonesia Tbk", "sector": "Industri Dasar", "sub_sector": "Semen", "is_syariah": True},
    {"code": "INTP", "name": "Indocement Tunggal Prakarsa Tbk", "sector": "Industri Dasar", "sub_sector": "Semen", "is_syariah": True},
    {"code": "WTON", "name": "Wijaya Karya Beton Tbk", "sector": "Industri Dasar", "sub_sector": "Beton", "is_syariah": True},
    # ── Properti ────────────────────────────────────────────────────────────
    {"code": "BSDE", "name": "Bumi Serpong Damai Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "CTRA", "name": "Ciputra Development Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "PWON", "name": "Pakuwon Jati Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "SMRA", "name": "Summarecon Agung Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "LPKR", "name": "Lippo Karawaci Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    # ── Infrastruktur & Konstruksi ─────────────────────────────────────────
    {"code": "JSMR", "name": "Jasa Marga Tbk", "sector": "Infrastruktur", "sub_sector": "Jalan Tol", "is_syariah": True},
    {"code": "WIKA", "name": "Wijaya Karya Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi", "is_syariah": True},
    {"code": "WSKT", "name": "Waskita Karya Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi", "is_syariah": True},
    {"code": "PTPP", "name": "PP (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi", "is_syariah": True},
    {"code": "ADHI", "name": "Adhi Karya Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi", "is_syariah": True},
    # ── Distribusi & Perdagangan ────────────────────────────────────────────
    {"code": "AKRA", "name": "AKR Corporindo Tbk", "sector": "Perdagangan", "sub_sector": "Distribusi", "is_syariah": True},
    {"code": "UNTR", "name": "United Tractors Tbk", "sector": "Perdagangan", "sub_sector": "Alat Berat", "is_syariah": True},
    {"code": "HEXA", "name": "Hexindo Adiperkasa Tbk", "sector": "Perdagangan", "sub_sector": "Alat Berat", "is_syariah": True},
    # ── Perkebunan ──────────────────────────────────────────────────────────
    {"code": "AALI", "name": "Astra Agro Lestari Tbk", "sector": "Perkebunan", "sub_sector": "Kelapa Sawit", "is_syariah": True},
    {"code": "LSIP", "name": "PP London Sumatra Indonesia Tbk", "sector": "Perkebunan", "sub_sector": "Kelapa Sawit", "is_syariah": True},
    {"code": "DSNG", "name": "Dharma Satya Nusantara Tbk", "sector": "Perkebunan", "sub_sector": "Kelapa Sawit", "is_syariah": True},
    {"code": "TAPG", "name": "Triputra Agro Persada Tbk", "sector": "Perkebunan", "sub_sector": "Kelapa Sawit", "is_syariah": True},
    # ── Media ───────────────────────────────────────────────────────────────
    {"code": "SCMA", "name": "Surya Citra Media Tbk", "sector": "Teknologi", "sub_sector": "Media", "is_syariah": True},
    {"code": "MNCN", "name": "MNC Digital Entertainment Tbk", "sector": "Teknologi", "sub_sector": "Media", "is_syariah": True},
    {"code": "BMTR", "name": "Global Mediacom Tbk", "sector": "Teknologi", "sub_sector": "Media", "is_syariah": False},
    # ── Transportasi ──────────────────────────────────────────────────────
    {"code": "BIRD", "name": "Blue Bird Tbk", "sector": "Transportasi", "sub_sector": "Transportasi Darat", "is_syariah": True},
    {"code": "ASSA", "name": "Adi Sarana Armada Tbk", "sector": "Transportasi", "sub_sector": "Transportasi Darat", "is_syariah": True},
    {"code": "SMDR", "name": "Samudera Indonesia Tbk", "sector": "Transportasi", "sub_sector": "Transportasi Laut", "is_syariah": True},
    # ── Elektronik & Kabel ──────────────────────────────────────────────────
    {"code": "SCCO", "name": "Supreme Cable Manufacturing Tbk", "sector": "Industri", "sub_sector": "Kabel", "is_syariah": True},
    # ── Pulp & Kertas ───────────────────────────────────────────────────────
    {"code": "TKIM", "name": "Pabrik Kertas Tjiwi Kimia Tbk", "sector": "Industri Dasar", "sub_sector": "Pulp & Kertas", "is_syariah": True},
    {"code": "INKP", "name": "Indah Kiat Pulp & Paper Tbk", "sector": "Industri Dasar", "sub_sector": "Pulp & Kertas", "is_syariah": True},
    # ── Tekstil ─────────────────────────────────────────────────────────────
    {"code": "SRIL", "name": "Sri Rejeki Isman Tbk", "sector": "Industri", "sub_sector": "Tekstil", "is_syariah": False},
    # ── Tambahan saham populer ──────────────────────────────────────────────
    {"code": "BBKP", "name": "Bank KB Bukopin Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "BGTG", "name": "Bank Ganesha Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "AGRO", "name": "Bank Raya Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan", "is_syariah": False},
    {"code": "ARNA", "name": "Arwana Citramulia Tbk", "sector": "Industri Dasar", "sub_sector": "Keramik", "is_syariah": True},
    {"code": "MARK", "name": "Mark Dynamics Indonesia Tbk", "sector": "Industri", "sub_sector": "Sarung Tangan", "is_syariah": True},
    {"code": "MDKI", "name": "Ecogreen Oleochemicals Tbk", "sector": "Industri Dasar", "sub_sector": "Kimia", "is_syariah": True},
    {"code": "PANI", "name": "Pantai Indah Kapuk Dua Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "DNET", "name": "Indoritel Makmur Internasional Tbk", "sector": "Perdagangan", "sub_sector": "Ritel", "is_syariah": True},
    {"code": "MAPI", "name": "Mitra Adiperkasa Tbk", "sector": "Perdagangan", "sub_sector": "Ritel", "is_syariah": True},
    {"code": "ERAL", "name": "Eral Realty Tbk", "sector": "Properti", "sub_sector": "Properti", "is_syariah": True},
    {"code": "BFIN", "name": "BFI Finance Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Multifinance", "is_syariah": False},
    {"code": "ASRM", "name": "Asuransi Ramayana Tbk", "sector": "Keuangan", "sub_sector": "Asuransi", "is_syariah": False},
    {"code": "MFIN", "name": "Mandala Multifinance Tbk", "sector": "Keuangan", "sub_sector": "Multifinance", "is_syariah": False},
    {"code": "SRTG", "name": "Saratoga Investama Sedaya Tbk", "sector": "Keuangan", "sub_sector": "Investasi", "is_syariah": False},
]


def seed():
    """Insert or update stocks using upsert (on_conflict_do_update)."""
    db = SessionLocal()
    try:
        for stock_data in STOCKS_DATA:
            stmt = insert(Stock).values(
                code=stock_data["code"],
                name=stock_data["name"],
                sector=stock_data.get("sector"),
                sub_sector=stock_data.get("sub_sector"),
                is_syariah=stock_data.get("is_syariah", False),
                is_active=True,
            ).on_conflict_do_update(
                index_elements=["code"],
                set_={
                    "name": stock_data["name"],
                    "sector": stock_data.get("sector"),
                    "sub_sector": stock_data.get("sub_sector"),
                    "is_syariah": stock_data.get("is_syariah", False),
                    "is_active": True,
                },
            )
            db.execute(stmt)
        db.commit()
        print(f"✅ Seeded/updated {len(STOCKS_DATA)} stocks successfully.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding stocks: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

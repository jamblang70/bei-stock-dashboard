#!/usr/bin/env python3
"""
Seed initial BEI stock data into the stocks table.
Usage: python scripts/seed_stocks.py
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy.dialects.postgresql import insert  # noqa: E402

from app.core.database import SessionLocal  # noqa: E402
from app.models.stock import Stock  # noqa: E402

STOCKS_DATA = [
    # Perbankan
    {"code": "BBCA", "name": "Bank Central Asia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BBRI", "name": "Bank Rakyat Indonesia (Persero) Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BMRI", "name": "Bank Mandiri (Persero) Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BBNI", "name": "Bank Negara Indonesia (Persero) Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BNGA", "name": "Bank CIMB Niaga Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BDMN", "name": "Bank Danamon Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BJBR", "name": "Bank Pembangunan Daerah Jawa Barat dan Banten Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "BNLI", "name": "Bank Permata Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "PNBN", "name": "Bank Pan Indonesia Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "NISP", "name": "Bank OCBC NISP Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    {"code": "MEGA", "name": "Bank Mega Tbk", "sector": "Keuangan", "sub_sector": "Perbankan"},
    # Telekomunikasi
    {"code": "TLKM", "name": "Telkom Indonesia (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi"},
    {"code": "EXCL", "name": "XL Axiata Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi"},
    {"code": "ISAT", "name": "Indosat Tbk", "sector": "Infrastruktur", "sub_sector": "Telekomunikasi"},
    {"code": "TOWR", "name": "Sarana Menara Nusantara Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi"},
    {"code": "TBIG", "name": "Tower Bersama Infrastructure Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi"},
    {"code": "MTEL", "name": "Dayamitra Telekomunikasi Tbk", "sector": "Infrastruktur", "sub_sector": "Menara Telekomunikasi"},
    # Otomotif & Industri
    {"code": "ASII", "name": "Astra International Tbk", "sector": "Industri", "sub_sector": "Otomotif"},
    # Teknologi
    {"code": "GOTO", "name": "GoTo Gojek Tokopedia Tbk", "sector": "Teknologi", "sub_sector": "E-Commerce & Ride Hailing"},
    # Energi & Pertambangan
    {"code": "BREN", "name": "Barito Renewables Energy Tbk", "sector": "Energi", "sub_sector": "Energi Terbarukan"},
    {"code": "PTBA", "name": "Bukit Asam Tbk", "sector": "Energi", "sub_sector": "Pertambangan Batubara"},
    {"code": "ADRO", "name": "Adaro Energy Indonesia Tbk", "sector": "Energi", "sub_sector": "Pertambangan Batubara"},
    {"code": "ITMG", "name": "Indo Tambangraya Megah Tbk", "sector": "Energi", "sub_sector": "Pertambangan Batubara"},
    {"code": "BUMI", "name": "Bumi Resources Tbk", "sector": "Energi", "sub_sector": "Pertambangan Batubara"},
    {"code": "ANTM", "name": "Aneka Tambang Tbk", "sector": "Energi", "sub_sector": "Pertambangan Logam"},
    {"code": "MDKA", "name": "Merdeka Copper Gold Tbk", "sector": "Energi", "sub_sector": "Pertambangan Logam"},
    {"code": "MEDC", "name": "Medco Energi Internasional Tbk", "sector": "Energi", "sub_sector": "Minyak & Gas"},
    {"code": "PGAS", "name": "Perusahaan Gas Negara Tbk", "sector": "Energi", "sub_sector": "Gas"},
    # Kimia & Petrokimia
    {"code": "TPIA", "name": "Chandra Asri Pacific Tbk", "sector": "Industri Dasar", "sub_sector": "Kimia"},
    # Consumer Goods
    {"code": "UNVR", "name": "Unilever Indonesia Tbk", "sector": "Barang Konsumsi", "sub_sector": "Produk Rumah Tangga"},
    {"code": "ICBP", "name": "Indofood CBP Sukses Makmur Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman"},
    {"code": "INDF", "name": "Indofood Sukses Makmur Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman"},
    {"code": "KLBF", "name": "Kalbe Farma Tbk", "sector": "Kesehatan", "sub_sector": "Farmasi"},
    {"code": "SIDO", "name": "Industri Jamu dan Farmasi Sido Muncul Tbk", "sector": "Kesehatan", "sub_sector": "Farmasi"},
    {"code": "MYOR", "name": "Mayora Indah Tbk", "sector": "Barang Konsumsi", "sub_sector": "Makanan & Minuman"},
    {"code": "HMSP", "name": "H.M. Sampoerna Tbk", "sector": "Barang Konsumsi", "sub_sector": "Rokok"},
    {"code": "GGRM", "name": "Gudang Garam Tbk", "sector": "Barang Konsumsi", "sub_sector": "Rokok"},
    # Semen & Material
    {"code": "SMGR", "name": "Semen Indonesia (Persero) Tbk", "sector": "Industri Dasar", "sub_sector": "Semen"},
    {"code": "INTP", "name": "Indocement Tunggal Prakarsa Tbk", "sector": "Industri Dasar", "sub_sector": "Semen"},
    # Properti
    {"code": "BSDE", "name": "Bumi Serpong Damai Tbk", "sector": "Properti", "sub_sector": "Pengembang Properti"},
    {"code": "CTRA", "name": "Ciputra Development Tbk", "sector": "Properti", "sub_sector": "Pengembang Properti"},
    {"code": "PWON", "name": "Pakuwon Jati Tbk", "sector": "Properti", "sub_sector": "Pengembang Properti"},
    {"code": "SMRA", "name": "Summarecon Agung Tbk", "sector": "Properti", "sub_sector": "Pengembang Properti"},
    {"code": "LPKR", "name": "Lippo Karawaci Tbk", "sector": "Properti", "sub_sector": "Pengembang Properti"},
    # Infrastruktur & Konstruksi
    {"code": "JSMR", "name": "Jasa Marga (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Jalan Tol"},
    {"code": "AKRA", "name": "AKR Corporindo Tbk", "sector": "Perdagangan", "sub_sector": "Distribusi"},
    {"code": "WIKA", "name": "Wijaya Karya (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi"},
    {"code": "WSKT", "name": "Waskita Karya (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi"},
    {"code": "PTPP", "name": "PP (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi"},
    {"code": "ADHI", "name": "Adhi Karya (Persero) Tbk", "sector": "Infrastruktur", "sub_sector": "Konstruksi"},
]


def seed_stocks() -> None:
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0

        for stock_data in STOCKS_DATA:
            stmt = (
                insert(Stock)
                .values(**stock_data)
                .on_conflict_do_nothing(index_elements=["code"])
            )
            result = db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                skipped += 1

        db.commit()
        print(f"Seeding complete: {inserted} inserted, {skipped} skipped (already exist).")
    except Exception as e:
        db.rollback()
        print(f"Error seeding stocks: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_stocks()

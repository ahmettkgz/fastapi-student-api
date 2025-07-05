# fastapiexercise/myproject/app/database.py

import os
import asyncpg
from fastapi import Depends, HTTPException

def load_database_config() -> dict:
    """Ortam değişkenlerinden veritabanı ayarlarını yükler."""
    
    # Doğrudan Docker Compose'da ayarlanan ortam değişkenlerini kullanıyoruz.
    # Hassas bilgiler için varsayılan değerler kaldırıldı.
    # Bu, bu değişkenlerin ortamda ayarlanmasını ZORUNLU kılar.
    config = {
        "host": os.getenv("DATABASE_HOST", "db"), # 'db' Docker Compose servis adı için varsayılan
        "database": os.getenv("DATABASE_NAME", "denemedb"), # 'denemedb' varsayılan veritabanı adı
        "user": os.getenv("DATABASE_USER"), # Varsayılan yok, ortam değişkeni ZORUNLU
        "password": os.getenv("DATABASE_PASSWORD"), # Varsayılan yok, ortam değişkeni ZORUNLU
        "port": os.getenv("DATABASE_PORT", "5432"), # Varsayılan port
    }

    # Kritik veritabanı bilgileri için kontrol
    missing_vars = [key for key, value in config.items() if value is None]
    if missing_vars:
        raise ValueError(
            f"❌ Eksik veritabanı ortam değişkenleri: {', '.join(missing_vars)}. "
            "Lütfen DATABASE_USER ve DATABASE_PASSWORD gibi değişkenleri ayarlayın."
        )

    # Portu integer'a dönüştür
    if isinstance(config["port"], str):
        try:
            config["port"] = int(config["port"])
        except ValueError:
            print(f"❌ Port değeri '{config['port']}' integer'a dönüştürülemiyor. Varsayılan 5432 kullanılacak.")
            config["port"] = 5432 
    
    print(f"DEBUG: Yüklenen veritabanı konfigürasyonu: {config}") # Debugging için ekledik
    return config

# Modül yüklendiğinde veritabanı konfigürasyonunu bir kez yükle
DB_CONFIG = load_database_config()

async def get_db_connection():
    """Yeni bir asyncpg veritabanı bağlantısı oluşturur."""
    try:
        conn = await asyncpg.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Veritabanı bağlantı hatası (get_db_connection): {e}")
        raise # Daha üst seviyeye hatayı fırlat

async def get_db():
    """FastAPI bağımlılığı olarak veritabanı bağlantısı sağlar."""
    conn = None
    try:
        conn = await get_db_connection()
        yield conn
    except Exception as e:
        # Burada sadece HTTP hatası yükseltiyoruz, detaylar loglandı
        raise HTTPException(status_code=500, detail="Veritabanı bağlantısı veya işlemi başarısız oldu")
    finally:
        if conn:
            await conn.close()

# Diğer modüllerin konfigürasyona erişmesi için fonksiyon
def get_database_config():
    """Yüklenen veritabanı konfigürasyonunu döndürür."""
    return DB_CONFIG.copy() # Güvenli olması için bir kopya döndür

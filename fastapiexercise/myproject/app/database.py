# fastapiexercise/myproject/app/database.py
import os
import asyncpg
from fastapi import Depends, HTTPException

def load_database_config() -> dict:
    """Ortam değişkenlerinden veritabanı ayarlarını yükler."""
    # Hem Docker (DATABASE_*) hem de CLI (.env dosyası DB_*) variable'larını destekler
    config = {
        "host": os.getenv("DATABASE_HOST") or os.getenv("DB_HOST", "localhost"),
        "database": os.getenv("DATABASE_NAME") or os.getenv("DB_NAME", "denemedb"),
        "user": os.getenv("DATABASE_USER") or os.getenv("DB_USER"),
        "password": os.getenv("DATABASE_PASSWORD") or os.getenv("DB_PASSWORD"),
        "port": os.getenv("DATABASE_PORT") or os.getenv("DB_PORT", "5432"),
    }
    
    # Kritik veritabanı bilgileri için kontrol
    missing_vars = [key for key, value in config.items() if value is None]
    if missing_vars:
        # Hangi environment variable'ların eksik olduğunu göster
        missing_docker_vars = []
        missing_cli_vars = []
        
        for key in missing_vars:
            if key == "user":
                missing_docker_vars.append("DATABASE_USER")
                missing_cli_vars.append("DB_USER")
            elif key == "password":
                missing_docker_vars.append("DATABASE_PASSWORD")
                missing_cli_vars.append("DB_PASSWORD")
            elif key == "host":
                missing_docker_vars.append("DATABASE_HOST")
                missing_cli_vars.append("DB_HOST")
            elif key == "database":
                missing_docker_vars.append("DATABASE_NAME")
                missing_cli_vars.append("DB_NAME")
            elif key == "port":
                missing_docker_vars.append("DATABASE_PORT")
                missing_cli_vars.append("DB_PORT")
        
        raise ValueError(
            f"❌ Eksik veritabanı ortam değişkenleri: {', '.join(missing_vars)}. "
            f"Docker için: {', '.join(missing_docker_vars)} "
            f"veya CLI için: {', '.join(missing_cli_vars)} değişkenlerini ayarlayın."
        )
    
    # Portu integer'a dönüştür
    if isinstance(config["port"], str):
        try:
            config["port"] = int(config["port"])
        except ValueError:
            print(f"❌ Port değeri '{config['port']}' integer'a dönüştürülemiyor. Varsayılan 5432 kullanılacak.")
            config["port"] = 5432
    
    # Hangi değişkenlerin kullanıldığını göster
    source_info = []
    if os.getenv("DATABASE_HOST"):
        source_info.append("Docker variables (DATABASE_*)")
    if os.getenv("DB_HOST"):
        source_info.append("CLI variables (DB_*)")
    
    print(f"DEBUG: Kullanılan değişken kaynağı: {', '.join(source_info) if source_info else 'Varsayılan değerler'}")
    print(f"DEBUG: Yüklenen veritabanı konfigürasyonu: {config}")
    
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
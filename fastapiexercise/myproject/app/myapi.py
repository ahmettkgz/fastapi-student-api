# fastapiexercise/myproject/app/myapi.py

from fastapi import FastAPI, HTTPException, Path, Depends
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import asyncpg # asyncpg'yi doğrudan kullanmasak bile, async fonksiyonlar için bu import genelde tutulur.
# database.py'den gerekli fonksiyonları içe aktar
from .database import get_db, get_database_config # Göreceli içe aktarma

# Veritabanı konfigürasyonunu database.py modülünden al
DATABASE_CONFIG = get_database_config() # Bu DATABASE_CONFIG artık doğru yerden geliyor

# Pydantic modelleri (Değişiklik yok)
class Student(BaseModel):
    name: str
    age: int
    class_: Optional[str] = None

class UpdateStudent(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    class_: Optional[str] = None

class StudentResponse(BaseModel):
    id: int
    name: str
    age: int
    class_: Optional[str] = None

# Veritabanı tablosunu oluştur (asyncpg uyumlu)
async def create_tables():
    try:
        # database.py'deki get_db_connection yerine doğrudan asyncpg.connect kullanıyoruz
        # çünkü bu sadece başlatma sırasında bir kez olacak bir bağlantı.
        conn = await asyncpg.connect(**DATABASE_CONFIG) 
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INTEGER NOT NULL,
                class VARCHAR(50)
            );
        """)
        count = await conn.fetchval("SELECT COUNT(*) FROM students")
        if count == 0:
            await conn.execute("""
                INSERT INTO students (name, age, class) VALUES
                ('John', 20, 'Year 2'),
                ('Jane', 22, 'Year 4');
            """)
        await conn.close()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        # Hata durumunda uygulamanın başlamasını engelle
        raise

# Lifespan context manager (asyncpg uyumlu)
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Uygulama başlıyor...")
    try:
        # Veritabanı bağlantısını test et
        conn = await asyncpg.connect(**DATABASE_CONFIG)
        await conn.execute("SELECT 1;")
        await conn.close()
        print("✅ Veritabanı bağlantısı başarıyla kuruldu.")

        # Tabloları oluştur
        await create_tables() # create_tables'ı await ile çağırın

    except Exception as e:
        print(f"❌ Veritabanına bağlanılamadı veya tablolar oluşturulamadı: {e}")
        raise e # Uygulamanın başlamasına engel ol

    yield # Uygulama ömrü burada devam eder

    print("🔄 Uygulama kapanıyor...")

# FastAPI uygulaması
app = FastAPI(
    title="Student Management API",
    description="A simple API to manage students with PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

# Ana sayfa
@app.get("/")
async def index(): # Asenkron hale getirildi
    return {"message": "Student Management API", "status": "running"}

# Tüm öğrencileri getir (asyncpg uyumlu)
@app.get("/students", response_model=List[StudentResponse])
async def get_all_students(conn=Depends(get_db)):
    try:
        rows = await conn.fetch("SELECT id, name, age, class as class_ FROM students ORDER BY id;")
        return [StudentResponse(**dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# ID ile öğrenci getir (asyncpg uyumlu)
@app.get("/students/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: int = Path(..., title="Getirilecek öğrencinin ID'si", gt=0),
    conn=Depends(get_db)
):
    try:
        row = await conn.fetchrow("SELECT id, name, age, class as class_ FROM students WHERE id = $1;", student_id)
        if not row:
            raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")
        return StudentResponse(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# İsim ile öğrenci getir (asyncpg uyumlu)
@app.get("/students/search/{name}", response_model=List[StudentResponse])
async def get_student_by_name(name: str, conn=Depends(get_db)):
    try:
        rows = await conn.fetch("SELECT id, name, age, class as class_ FROM students WHERE name ILIKE $1;", f"%{name}%")
        return [StudentResponse(**dict(row)) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Yeni öğrenci ekle (asyncpg uyumlu)
@app.post("/students", response_model=StudentResponse)
async def add_student(student: Student, conn=Depends(get_db)):
    try:
        row = await conn.fetchrow("""
            INSERT INTO students (name, age, class)
            VALUES ($1, $2, $3)
            RETURNING id, name, age, class as class_;
        """, student.name, student.age, student.class_)
        return StudentResponse(**dict(row))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Öğrenci güncelle (asyncpg uyumlu)
@app.put("/students/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: int,
    student: UpdateStudent,
    conn=Depends(get_db)
):
    try:
        exists = await conn.fetchval("SELECT id FROM students WHERE id = $1;", student_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")
        update_fields = []
        values = []
        if student.name is not None:
            update_fields.append("name = $%d" % (len(values)+1))
            values.append(student.name)
        if student.age is not None:
            update_fields.append("age = $%d" % (len(values)+1))
            values.append(student.age)
        if student.class_ is not None:
            update_fields.append("class = $%d" % (len(values)+1))
            values.append(student.class_)
        if not update_fields:
            raise HTTPException(status_code=400, detail="Güncellenecek alan bulunamadı")
        values.append(student_id)
        query = f"""
            UPDATE students
            SET {', '.join(update_fields)}
            WHERE id = ${len(values)}
            RETURNING id, name, age, class as class_;
        """
        row = await conn.fetchrow(query, *values)
        return StudentResponse(**dict(row))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Öğrenci sil (asyncpg uyumlu)
@app.delete("/students/{student_id}")
async def delete_student(student_id: int, conn=Depends(get_db)):
    try:
        row = await conn.fetchrow("DELETE FROM students WHERE id = $1 RETURNING id;", student_id)
        if not row:
            raise HTTPException(status_code=404, detail="Öğrenci bulunamadı")
        return {"message": "Öğrenci başarıyla silindi", "deleted_id": row["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")

# Veritabanı durumu kontrol et (asyncpg uyumlu)
@app.get("/health")
async def health_check(conn=Depends(get_db)):
    try:
        count = await conn.fetchval("SELECT COUNT(*) FROM students;")
        return {
            "status": "healthy",
            "database": "connected",
            "total_students": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sağlık kontrolü başarısız oldu: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Çalıştırırken, uygulama nesnesinin yolu myproject.app.myapi içinde 'app'dir.
    uvicorn.run("myproject.app.myapi:app", host="0.0.0.0", port=8000, reload=True)
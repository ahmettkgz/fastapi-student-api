# main.py
from fastapi import FastAPI, HTTPException, Path, Depends
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "your_database"),
    "user": os.getenv("DB_USER", "your_username"),
    "password": os.getenv("DB_PASSWORD", "your_password"),
    "port": os.getenv("DB_PORT", "5432")
}

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

def get_db():
    conn = None
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        yield conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")
    finally:
        if conn:
            conn.close()

# Veritabanı tablosunu oluştur
def create_tables():
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INTEGER NOT NULL,
                class VARCHAR(50)
            );
        """)
        
        cursor.execute("SELECT COUNT(*) FROM students")
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute("""
                INSERT INTO students (name, age, class) VALUES 
                ('John', 20, 'Year 2'),
                ('Jane', 22, 'Year 4');
            """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database tables created successfully")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        conn = psycopg2.connect(**DATABASE_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        cursor.close()
        conn.close()
        print("✅ Database connection established successfully")
        
        create_tables()
        
    except Exception as e:
        print(f"❌ Could not connect to the database: {e}")
        raise e
    
    yield
    
    print("🔄 Shutting down...")

# FastAPI uygulaması
app = FastAPI(
    title="Student Management API",
    description="A simple API to manage students with PostgreSQL",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
def index():
    return {"message": "Student Management API", "status": "running"}

@app.get("/students", response_model=List[StudentResponse])
def get_all_students(conn=Depends(get_db)):
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, name, age, class FROM students ORDER BY id;")
        students = cursor.fetchall()
        cursor.close()
        
        return [StudentResponse(**dict(student)) for student in students]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int = Path(..., title="The ID of the student to retrieve", gt=0),
    conn=Depends(get_db)
):
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT id, name, age, class FROM students WHERE id = %s;", (student_id,))
        student = cursor.fetchone()
        cursor.close()
        
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        return StudentResponse(**dict(student))
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/students", response_model=StudentResponse)
def add_student(student: Student, conn=Depends(get_db)):
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            INSERT INTO students (name, age, class) 
            VALUES (%s, %s, %s) 
            RETURNING id, name, age, class;
        """, (student.name, student.age, student.class_))
        
        new_student = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return StudentResponse(**dict(new_student))
    
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.put("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int, 
    student: UpdateStudent, 
    conn=Depends(get_db)
):
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT id FROM students WHERE id = %s;", (student_id,))
        if not cursor.fetchone():
            cursor.close()
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Güncelleme sorgusu oluştur
        update_fields = []
        values = []
        
        if student.name is not None:
            update_fields.append("name = %s")
            values.append(student.name)
        
        if student.age is not None:
            update_fields.append("age = %s")
            values.append(student.age)
        
        if student.class_ is not None:
            update_fields.append("class = %s")
            values.append(student.class_)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        values.append(student_id)
        
        cursor.execute(f"""
            UPDATE students 
            SET {', '.join(update_fields)} 
            WHERE id = %s 
            RETURNING id, name, age, class;
        """, values)
        
        updated_student = cursor.fetchone()
        conn.commit()
        cursor.close()
        
        return StudentResponse(**dict(updated_student))
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.delete("/students/{student_id}")
def delete_student(student_id: int, conn=Depends(get_db)):
    try:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM students WHERE id = %s RETURNING id;", (student_id,))
        deleted_student = cursor.fetchone()
        
        if not deleted_student:
            cursor.close()
            raise HTTPException(status_code=404, detail="Student not found")
        
        conn.commit()
        cursor.close()
        
        return {"message": "Student deleted successfully", "deleted_id": deleted_student[0]}
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()


students = {
    1: {"name": "John", "age": 20, "class": "Year 2"},
    2: {"name": "Jane", "age": 22, "class": "Year 4"},
}


class Student(BaseModel):
    name: str
    age: int
    class_: Optional[str] = None


class UpdateStudent(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    class_: Optional[str] = None


@app.get("/")
def index():
    return {"name": "First Data!"}


@app.get("/get-student/{student_id}")
def get_student(
    student_id: int = Path(
        ..., title="The ID of the student to retrieve", gt=0, lt=1000
    ),
):
    if student_id in students:
        return students[student_id]
    else:
        raise HTTPException(status_code=404, detail="Student not found")


@app.get("/get-by-name")
def get_student_by_name(name: str):
    for student_id in students:
        if students[student_id]["name"] == name:
            return students[student_id]


@app.get("/get-students", response_model=List[Student])
def get_students():
    return [
        Student(name=data["name"], age=data["age"], class_=data.get("class"))
        for data in students.values()
    ]


@app.post("/add-student/{student_id}")
def add_student(
    student_id: int,
    student: Student,
):
    if student_id in students:
        return {"Error": "Student already exists"}
    students[student_id] = student
    return students[student_id]


@app.put("/update-student/{student_id}")
def update_student(student_id: int, student: UpdateStudent):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.name is not None:
        students[student_id]["name"] = student.name
    if student.age is not None:
        students[student_id]["age"] = student.age
    if student.class_ is not None:
        students[student_id]["class"] = student.class_
    students[student_id] = student
    return students[student_id]


@app.delete("/delete-student/{student_id}")
def delete_student(student_id: int):
    if student_id not in students:
        raise HTTPException(status_code=404, detail="Student not found")
    del students[student_id]
    return {"message": "Student deleted successfully"}

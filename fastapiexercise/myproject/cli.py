import os
from dotenv import load_dotenv
from pathlib import Path

# --- Load Environment Variables ---
# Check if we're running in Docker (you can detect this various ways)
# Here we'll look for a .env.local file first, then fall back to .env
dotenv_path = Path(__file__).resolve().parent.parent / '.env.local'
if not dotenv_path.exists():
    dotenv_path = Path(__file__).resolve().parent.parent / '.env'

# Load environment variables from the specified path
load_dotenv(dotenv_path=dotenv_path)
# Now, import your application modules
from app.database import get_db_connection
import asyncio
import asyncpg
from typing import Optional

import typer

# Initialize Typer application with the requested name 'cli_app'
cli_app = typer.Typer()

@cli_app.command("list-students")
def list_students():
    """
    Lists all students currently in the database.
    """
    asyncio.run(async_list_students())

async def async_list_students():
    """
    Async function to list all students.
    """
    typer.echo("Listing students...")
    conn = None
    try:
        conn = await get_db_connection()
        # Query all students from the database - using "class" instead of "class_"
        rows = await conn.fetch("SELECT id, name, age, class FROM students ORDER BY id")
        
        if not rows:
            typer.echo("No students found.")
            return
            
        for row in rows:
            typer.echo(f"ID: {row['id']}, Name: {row['name']}, Age: {row['age']}, Class: {row['class']}")
    except Exception as e:
        typer.echo(f"Error listing students: {e}")
    finally:
        if conn:
            await conn.close()

@cli_app.command("add-student")
def add_student(
    name: str = typer.Option(..., help="Name of the student"),
    age: int = typer.Option(..., help="Age of the student"),
    class_: str = typer.Option(..., help="Class of the student")
):
    """
    Adds a new student to the database.
    """
    asyncio.run(async_add_student(name, age, class_))

async def async_add_student(name: str, age: int, class_: str):
    """
    Async function to add a new student.
    """
    typer.echo(f"Adding student: {name}, {age}, {class_}")
    conn = None
    try:
        conn = await get_db_connection()
        # Insert new student into the database - using "class" instead of "class_"
        student_id = await conn.fetchval(
            "INSERT INTO students (name, age, class) VALUES ($1, $2, $3) RETURNING id",
            name, age, class_
        )
        typer.echo(f"Student '{name}' added successfully with ID: {student_id}")
    except Exception as e:
        typer.echo(f"Error adding student: {e}")
    finally:
        if conn:
            await conn.close()

@cli_app.command("get-student")
def get_student(
    student_id: int = typer.Option(..., help="ID of the student to retrieve")
):
    """
    Retrieves a student by their ID.
    """
    asyncio.run(async_get_student(student_id))

async def async_get_student(student_id: int):
    """
    Async function to get a student by ID.
    """
    typer.echo(f"Retrieving student with ID: {student_id}")
    conn = None
    try:
        conn = await get_db_connection()
        # Query student by ID - using "class" instead of "class_"
        row = await conn.fetchrow(
            "SELECT id, name, age, class FROM students WHERE id = $1",
            student_id
        )
        
        if row:
            typer.echo(f"Found Student: ID={row['id']}, Name={row['name']}, Age={row['age']}, Class={row['class']}")
        else:
            typer.echo(f"Student with ID {student_id} not found.")
    except Exception as e:
        typer.echo(f"Error retrieving student: {e}")
    finally:
        if conn:
            await conn.close()

@cli_app.command("delete-student")
def delete_student(
    student_id: int = typer.Option(..., help="ID of the student to delete")
):
    """
    Deletes a student by their ID.
    """
    asyncio.run(async_delete_student(student_id))

async def async_delete_student(student_id: int):
    """
    Async function to delete a student by ID.
    """
    typer.echo(f"Deleting student with ID: {student_id}")
    conn = None
    try:
        conn = await get_db_connection()
        
        # First, get the student to check if it exists and get the name
        student = await conn.fetchrow(
            "SELECT id, name FROM students WHERE id = $1",
            student_id
        )
        
        if student:
            # Delete the student
            await conn.execute(
                "DELETE FROM students WHERE id = $1",
                student_id
            )
            typer.echo(f"Student '{student['name']}' (ID: {student['id']}) deleted successfully.")
        else:
            typer.echo(f"Student with ID {student_id} not found.")
    except Exception as e:
        typer.echo(f"Error deleting student: {e}")
    finally:
        if conn:
            await conn.close()

# This block ensures the Typer app runs when cli.py is executed directly
if __name__ == "__main__":
    cli_app()
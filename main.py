
from fastapi import FastAPI, HTTPException, Depends, Query
from typing import Optional
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

from database import get_connection

from career_schemas import (
    UserCreate,
    UserLogin,
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationDetailsUpdate,
    ApplicationNotesUpdate
)

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)


app = FastAPI(
    title="CareerTrack API",
    description="Job Application Tracking System",
    version="2.1"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



def validate_date(date_value):
    if date_value is None:
        return

    try:
        parsed_date = datetime.strptime(date_value, "%Y-%m-%d")

        if parsed_date.strftime("%Y-%m-%d") != date_value:
            raise ValueError

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Date must be in YYYY-MM-DD format"
        )



def fetch_applications(cursor):
    rows = cursor.fetchall()
    return [dict(row) for row in rows]




@app.get("/")
def home():
    return {
        "message": "Welcome to CareerTrack API!",
        "status": "Running"
    }




@app.post("/register")
def register(user: UserCreate):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE email = ?",
            (user.email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="Email already registered!"
            )

        hashed_password = hash_password(user.password)

        cursor.execute(
            """
            INSERT INTO users (name, email, password)
            VALUES (?, ?, ?)
            """,
            (user.name, user.email, hashed_password)
        )

        conn.commit()

        return {
            "message": "User registered successfully!",
            "name": user.name,
            "email": user.email
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error during registration"
        )

    finally:
        conn.close()




@app.post("/login")
def login(user: UserLogin):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = ?",
            (user.email,)
        )

        existing_user = cursor.fetchone()

        if not existing_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password!"
            )

        if not verify_password(
            user.password,
            existing_user["password"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password!"
            )

        access_token = create_access_token(
            existing_user["id"]
        )

        return {
            "message": "Login successful!",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": existing_user["id"],
                "name": existing_user["name"],
                "email": existing_user["email"]
            }
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error during login"
        )

    finally:
        conn.close()


# --------------------------------------------------
# CURRENT USER API
# --------------------------------------------------

@app.get("/users/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user)
):
    return {
        "message": "User profile fetched successfully!",
        "user": current_user
    }




@app.post("/applications")
def add_application(
    application: ApplicationCreate,
    current_user: dict = Depends(get_current_user)
):

    validate_date(application.applied_date)
    validate_date(application.follow_up_date)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id FROM applications
            WHERE user_id = ?
            AND LOWER(company) = LOWER(?)
            AND LOWER(position) = LOWER(?)
            """,
            (
                current_user["id"],
                application.company,
                application.position
            )
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=409,
                detail="This application already exists!"
            )

        applied_date = (
            application.applied_date
            or datetime.now().strftime("%Y-%m-%d")
        )

        cursor.execute(
            """
            INSERT INTO applications
            (user_id, company, position, status,
             applied_date, notes, follow_up_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user["id"],
                application.company,
                application.position,
                application.status,
                applied_date,
                application.notes,
                application.follow_up_date
            )
        )

        application_id = cursor.lastrowid

        conn.commit()

        return {
            "message": "Application added successfully!",
            "application_id": application_id,
            "company": application.company,
            "position": application.position,
            "status": application.status
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while adding application"
        )

    finally:
        conn.close()




@app.get("/applications")
def get_applications(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),

    status: Optional[str] = None,
    company: Optional[str] = None,
    position: Optional[str] = None,

    from_date: Optional[str] = None,
    to_date: Optional[str] = None,

    sort_by: str = "applied_date",
    order: str = "desc",

    current_user: dict = Depends(get_current_user)
):

    if status and status not in [
        "Applied", "Interview", "Selected", "Rejected"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid application status"
        )

    validate_date(from_date)
    validate_date(to_date)

    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            status_code=400,
            detail="from_date cannot be greater than to_date"
        )

    allowed_sort_columns = {
        "id": "id",
        "company": "company",
        "position": "position",
        "status": "status",
        "applied_date": "applied_date",
        "follow_up_date": "follow_up_date"
    }

    if sort_by not in allowed_sort_columns:
        raise HTTPException(
            status_code=400,
            detail="Invalid sorting field"
        )

    if order.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Order must be asc or desc"
        )

    conditions = ["user_id = ?"]
    values = [current_user["id"]]

    if status:
        conditions.append("status = ?")
        values.append(status)

    if company:
        conditions.append("company LIKE ?")
        values.append("%" + company + "%")

    if position:
        conditions.append("position LIKE ?")
        values.append("%" + position + "%")

    if from_date:
        conditions.append("applied_date >= ?")
        values.append(from_date)

    if to_date:
        conditions.append("applied_date <= ?")
        values.append(to_date)

    where_clause = " AND ".join(conditions)

    offset = (page - 1) * limit

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT COUNT(*) FROM applications WHERE {where_clause}",
            values
        )

        total_applications = cursor.fetchone()[0]

        cursor.execute(
            f"""
            SELECT * FROM applications
            WHERE {where_clause}
            ORDER BY {allowed_sort_columns[sort_by]} {order.upper()}
            LIMIT ? OFFSET ?
            """,
            values + [limit, offset]
        )

        applications = fetch_applications(cursor)

        return {
            "page": page,
            "limit": limit,
            "total_applications": total_applications,
            "total_pages": (
                total_applications + limit - 1
            ) // limit,
            "applications": applications
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching applications"
        )

    finally:
        conn.close()




@app.get("/applications/id/{application_id}")
def get_application_by_id(
    application_id: int,
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM applications
            WHERE id = ? AND user_id = ?
            """,
            (application_id, current_user["id"])
        )

        application = cursor.fetchone()

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found!"
            )

        return {
            "application": dict(application)
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching application"
        )

    finally:
        conn.close()



@app.put("/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    data: ApplicationStatusUpdate,
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE applications
            SET status = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                data.status,
                application_id,
                current_user["id"]
            )
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found!"
            )

        conn.commit()

        return {
            "message": "Application status updated successfully!",
            "application_id": application_id,
            "status": data.status
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while updating status"
        )

    finally:
        conn.close()




@app.put("/applications/{application_id}/details")
def update_application_details(
    application_id: int,
    data: ApplicationDetailsUpdate,
    current_user: dict = Depends(get_current_user)
):

    validate_date(data.applied_date)
    validate_date(data.follow_up_date)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE applications
            SET company = ?,
                position = ?,
                applied_date = ?,
                notes = ?,
                follow_up_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                data.company,
                data.position,
                data.applied_date,
                data.notes,
                data.follow_up_date,
                application_id,
                current_user["id"]
            )
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found!"
            )

        conn.commit()

        return {
            "message": "Application details updated successfully!",
            "application_id": application_id
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while updating application details"
        )

    finally:
        conn.close()




@app.patch("/applications/{application_id}/notes")
def update_application_notes(
    application_id: int,
    data: ApplicationNotesUpdate,
    current_user: dict = Depends(get_current_user)
):

    validate_date(data.follow_up_date)

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE applications
            SET notes = ?, follow_up_date = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                data.notes,
                data.follow_up_date,
                application_id,
                current_user["id"]
            )
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found!"
            )

        conn.commit()

        return {
            "message": "Notes and follow-up date updated successfully!",
            "application_id": application_id
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while updating notes"
        )

    finally:
        conn.close()




@app.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM applications
            WHERE id = ? AND user_id = ?
            """,
            (application_id, current_user["id"])
        )

        if cursor.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Application not found!"
            )

        conn.commit()

        return {
            "message": "Application deleted successfully!",
            "application_id": application_id
        }

    except HTTPException:
        raise

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while deleting application"
        )

    finally:
        conn.close()




@app.get("/applications/dashboard")
def application_dashboard(
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM applications
            WHERE user_id = ?
            """,
            (current_user["id"],)
        )

        total = cursor.fetchone()["total"]

        cursor.execute(
            """
            SELECT status, COUNT(*) AS count
            FROM applications
            WHERE user_id = ?
            GROUP BY status
            """,
            (current_user["id"],)
        )

        statistics = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "total_applications": total,
            "statistics": statistics
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching dashboard"
        )

    finally:
        conn.close()




@app.get("/applications/company-stats")
def company_statistics(
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT company, COUNT(*) AS total
            FROM applications
            WHERE user_id = ?
            GROUP BY company
            ORDER BY total DESC
            """,
            (current_user["id"],)
        )

        statistics = [
            dict(row) for row in cursor.fetchall()
        ]

        return {
            "company_statistics": statistics
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching company statistics"
        )

    finally:
        conn.close()




@app.get("/applications/search")
def search_applications(
    company: str,
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM applications
            WHERE user_id = ? AND company LIKE ?
            """,
            (
                current_user["id"],
                "%" + company + "%"
            )
        )

        applications = fetch_applications(cursor)

        return {
            "search": company,
            "total_results": len(applications),
            "applications": applications
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while searching applications"
        )

    finally:
        conn.close()




@app.get("/applications/recent")
def recent_applications(
    limit: int = Query(5, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM applications
            WHERE user_id = ?
            ORDER BY applied_date DESC, id DESC
            LIMIT ?
            """,
            (current_user["id"], limit)
        )

        applications = fetch_applications(cursor)

        return {
            "recent_applications": applications
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while fetching recent applications"
        )

    finally:
        conn.close()




@app.get("/applications/count")
def application_count(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):

    if status and status not in [
        "Applied", "Interview", "Selected", "Rejected"
    ]:
        raise HTTPException(
            status_code=400,
            detail="Invalid application status"
        )

    conn = get_connection()

    try:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE user_id = ? AND status = ?
                """,
                (current_user["id"], status)
            )

        else:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM applications
                WHERE user_id = ?
                """,
                (current_user["id"],)
            )

        total = cursor.fetchone()["total"]

        return {
            "status": status or "All",
            "total_applications": total
        }

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Database error while counting applications"
        )

    finally:
        conn.close()

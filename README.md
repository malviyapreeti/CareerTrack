# CareerTrack – Job Application Management System

CareerTrack is a full-stack web application designed to help users manage and track their job applications in one place.

## Features

- User Registration and Login
- Secure Password Hashing
- JWT-based Authentication
- Add Job Applications
- Delete Job Applications
- Track Application Status
- Dashboard Statistics
- SQLite Database Integration
- Protected API Endpoints

## Tech Stack

**Backend**
- Python
- FastAPI
- SQLite
- Pydantic
- JWT Authentication

**Frontend**
- HTML
- CSS
- JavaScript

**Tools**
- Git & GitHub
- VS Code
- Swagger UI

## Project Structure

```text
CareerTrack/
│
├── main.py
├── auth.py
├── career_schemas.py
├── database.py
├── .gitignore
│
└── fronend/
    ├── index.html
    ├── login.html
    ├── login.js
    ├── script.js
    └── style.css
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/malviyapreeti/CareerTrack.git
cd CareerTrack
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn pydantic
```

Install any additional dependencies required by the project.

### 3. Run the backend

```bash
uvicorn main:app --reload
```

### 4. Open API documentation

Visit:

http://127.0.0.1:8000/docs

### 5. Run the frontend

Open `fronend/login.html` using VS Code Live Server.

## Database

CareerTrack uses SQLite to store user accounts and job application records.

Each user's applications are associated with their account.

## Future Improvements

- Application Search and Filtering
- Edit Application Details
- Email Reminders
- Advanced Dashboard Analytics

## Author

**Preeti Malviya**

GitHub: [malviyapreeti](https://github.com/malviyapreeti)

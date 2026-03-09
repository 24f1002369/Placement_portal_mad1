# Placement Portal Application (MAD-I)

A professional, full-featured placement management portal built with Flask, designed for seamless interaction between Admin, Companies, and Students.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Folder Structure](#folder-structure)
- [User Roles](#user-roles)
- [Setup & Installation](#setup--installation)
- [Sample Data Loading](#sample-data-loading)
- [Usage Guide](#usage-guide)
- [Contributing](#contributing)


## Overview
This portal streamlines campus placement activities, enabling registration, drive management, analytics, and transparent communication between all stakeholders.

## Features
- Student registration and profile management
- Company registration (with admin approval)
- Placement drive creation and eligibility filtering
- Application tracking for students and companies
- Shortlisting, selection, and placement status updates
- Admin dashboard for analytics and user management
- Secure authentication and role-based access
- Resume upload and download
- Data visualization with Chart.js

## Tech Stack
- Python (Flask)
- SQLite
- Jinja2 (templating)
- Bootstrap (UI)
- Chart.js (analytics)

## Folder Structure
```
app.py                # Main Flask app
routes/               # Route handlers for admin, company, student, auth
static/               # Static files (icons, images)
templates/            # Jinja2 HTML templates (admin, company, student views)
uploads/resumes/      # Uploaded student resumes
utils/decorators.py   # Custom decorators for authentication & roles
database.py           # Database initialization & schema
```

## User Roles
- **Admin**: Approves companies, manages users, oversees drives, views analytics
- **Company**: Registers, creates drives, reviews applicants, shortlists/selects students
- **Student**: Registers, applies to drives, manages profile, uploads resume


## Setup & Installation
1. Clone the repository
2. Create a virtual environment and activate it
3. Install dependencies: `pip install -r requirements.txt`
4. Run the app: `python app.py`

## Sample Data Loading
A `load_data.py` script is provided to populate the database with sample students, companies, and placement drives for testing. Run the following command to automatically insert demo data and quickly test the application workflow:
```bash
python load_data.py
```
This will load:
- Sample student records with profiles
- Demo company accounts
- Pre-configured placement drives with eligibility criteria

## Usage Guide
- Access the portal at `http://localhost:5000`
- Register as Student or Company
- Admin approves companies and manages drives
- Companies create drives and review applicants
- Students apply to eligible drives and track status

## Contributing
Contributions are welcome! Please open issues or submit pull requests for improvements.




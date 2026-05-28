# Hostel Management System Website

A hostel management website with a Python Flask backend, HTML templates, CSS, JavaScript, and SQLite database.

## Features

- Dashboard with hostel summary
- Add and view rooms
- Register students
- Allocate and vacate rooms
- Record fee payments
- Add and resolve complaints
- Persistent SQLite storage in `hostel.db`

## Requirements

- Python 3.9 or newer
- Flask

## Project Structure

```text
Hostel_Management/
├── app.py
├── requirements.txt
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── rooms.html
│   ├── students.html
│   ├── payments.html
│   └── complaints.html
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── script.js
```

## How to Run in VS Code

Open the project folder in VS Code, then run these commands in the terminal:

```bash
pip install -r requirements.txt
```

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:8000
```

The website creates `hostel.db` automatically the first time it runs.

## Project Files

- `app.py` - Python Flask backend
- `templates/` - HTML pages
- `static/css/style.css` - Website styling
- `static/js/script.js` - Small JavaScript behavior
- `hostel.db` - SQLite database created at runtime

## Output

<img width="1919" height="906" alt="image" src="https://github.com/user-attachments/assets/edf0c3ed-dee5-426f-8286-6dd844621163" />


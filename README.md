# Scholarship Formatter (CLI + Web)

A local Python app that accepts messy scholarship text and converts it into a clean summary.

## What it extracts

- Offer Title
- Intake
- Age
- Deadline
- Scholarship
- Original Fees
- Majors
- Taught in English (Yes/No)
- Note
- Application Fees (optional, omitted when missing)

## Setup

1. Ensure Python 3 is installed.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run (Web App)

```powershell
python web_app.py
```

Open `http://127.0.0.1:5000` in your browser.

## Run (CLI)

```powershell
python app.py
```

Paste messy scholarship text, then finish input with `Ctrl+Z` and `Enter` (Windows).

## Example

### Messy input

```text
Title - Global Future Leaders Scholarship 2026
start term: Fall 2026
Applicants aged 18 to 28 only
apply by 15/07/2026
scholarship = 50% tuition waiver
tuition: USD 20,000 per year
majors: Computer Science / Business Analytics; Civil Engineering
english medium yes
important: maintain GPA 3.0+
extra text blah blah not needed
```

### Formatted output

```text
Offer Title: Global Future Leaders Scholarship 2026
Intake: Fall 2026
Age: 18-28
Deadline: 15/07/2026
Scholarship: 50% tuition waiver
Original Fees: $20,000 per year
Majors: Computer Science, Business Analytics, Civil Engineering
Taught in English: Yes
Note: maintain GPA 3.0+
```

`Application Fees` is omitted above because it was not provided in the input.

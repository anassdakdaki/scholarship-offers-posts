# Scholarship Formatter (CLI + Web)

A Python tool that turns unstructured scholarship text into consistent summaries, with a command-line interface and a Flask web editor.

The parser uses rules and regular expressions; no AI API key is required. Review parsed dates, fees, and eligibility details against the original offer before publishing.

## Project layout

- `app.py`: parsing, normalization, formatting, and CLI.
- `web_app.py`: Flask form, editable fields, and summary preview.
- `api/index.py`: WSGI entry point.

The web editor supports reviewing and editing extracted fields before copying the result.

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

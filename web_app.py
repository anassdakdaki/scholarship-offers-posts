import re

from flask import Flask, render_template_string, request

from app import FIELD_ORDER, format_output, parse_scholarship


app = Flask(__name__)

MULTILINE_FIELDS = {"Scholarship", "Majors", "Note"}


def field_to_name(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")


def collect_fields_from_form(form) -> dict:
    parsed = {}
    for label in FIELD_ORDER:
        value = form.get(field_to_name(label), "").strip()
        if value:
            parsed[label] = value
    return parsed


def build_editable_fields(parsed: dict) -> list:
    fields = []
    for label in FIELD_ORDER:
        fields.append(
            {
                "label": label,
                "name": field_to_name(label),
                "value": parsed.get(label, ""),
                "multiline": label in MULTILINE_FIELDS,
            }
        )
    return fields


PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Scholarship Formatter</title>
  <style>
    :root {
      --bg: #efefec;
      --card: #fffefb;
      --ink: #1a1a1a;
      --muted: #4a4a4a;
      --accent: #a32020;
      --line: #d6d2c8;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 15% 0%, #f8efe7 0, transparent 35%),
        radial-gradient(circle at 90% 90%, #e9efe8 0, transparent 30%),
        var(--bg);
      color: var(--ink);
      font-family: Cambria, Georgia, "Times New Roman", serif;
      min-height: 100vh;
    }
    .wrap {
      width: min(1120px, 92vw);
      margin: 48px auto;
      padding: 0 0 24px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 22px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
    }
    h1 {
      margin: 0 0 6px;
      font-size: 1.7rem;
      letter-spacing: 0.2px;
    }
    p {
      margin: 0 0 18px;
      color: var(--muted);
    }
    label {
      display: block;
      font-weight: 600;
      margin-bottom: 8px;
    }
    textarea {
      width: 100%;
      min-height: 220px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      resize: vertical;
      font: 14px/1.45 Consolas, "Courier New", monospace;
      background: #fff;
    }
    input[type="text"] {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      font: 14px/1.35 "Segoe UI", Tahoma, sans-serif;
      background: #fff;
    }
    button {
      margin-top: 14px;
      border: 0;
      border-radius: 10px;
      padding: 10px 16px;
      font-weight: 700;
      background: #165a4b;
      color: #fff;
      cursor: pointer;
    }
    button:hover { filter: brightness(1.05); }
    .actions-row {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }
    .actions-row button {
      margin-top: 0;
    }
    .btn-secondary {
      background: #b6b1a2;
      color: #1f1c15;
    }
    .btn-secondary:hover {
      filter: brightness(0.98);
    }
    .out {
      margin-top: 18px;
      border-top: 1px dashed var(--line);
      padding-top: 16px;
    }
    .edit-title {
      margin-top: 16px;
    }
    .edit-form {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px 14px;
      margin-top: 6px;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 12px;
      background: #fcfbf6;
    }
    .edit-field {
      display: block;
    }
    .edit-field.wide {
      grid-column: 1 / -1;
    }
    .edit-field label {
      margin-bottom: 5px;
      font-size: 0.92rem;
      color: #3c3a33;
    }
    .edit-form textarea {
      min-height: 96px;
      font: 13px/1.4 Consolas, "Courier New", monospace;
    }
    .edit-actions {
      grid-column: 1 / -1;
      display: flex;
      gap: 10px;
      align-items: center;
    }
    .preview-title {
      margin-top: 16px;
    }
    .ig-frame {
      width: min(100%, 720px);
      aspect-ratio: 1 / 1;
      border: 1px solid var(--line);
      border-radius: 12px;
      overflow: hidden;
      background: #f0f0ed;
      position: relative;
    }
    .ig-canvas-wrap {
      width: 100%;
      height: 100%;
      padding: 14px;
    }
    .ig-canvas {
      width: 100%;
      height: 100%;
      background: #fff;
      border: 1px solid #d0ccc0;
      color: #101010;
      padding: 26px 28px;
      overflow: hidden;
      font-family: Cambria, Georgia, "Times New Roman", serif;
    }
    .poster-top {
      display: block;
      margin-bottom: 10px;
    }
    .poster-title {
      margin: 0;
      color: var(--accent);
      font-size: 32px;
      line-height: 1.05;
      font-weight: 700;
    }
    .poster-city {
      margin-top: 6px;
      color: var(--accent);
      font-size: 20px;
      line-height: 1.2;
      font-weight: 700;
    }
    .meta {
      font-size: 16px;
      line-height: 1.45;
      margin-top: 8px;
    }
    .meta-row {
      margin: 2px 0;
    }
    .meta-row b {
      font-weight: 700;
    }
    .section {
      margin-top: 12px;
    }
    .section-title {
      color: var(--accent);
      font-size: 30px;
      line-height: 1.1;
      font-weight: 700;
      margin: 0 0 6px;
    }
    .section-label {
      color: var(--accent);
      font-weight: 700;
      margin: 7px 0 4px;
      font-size: 16px;
    }
    .content {
      font-size: 16px;
      line-height: 1.42;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }
    .sch-list {
      margin-top: 2px;
    }
    .sch-item {
      font-size: 16px;
      line-height: 1.38;
      margin: 2px 0;
    }
    .note {
      color: #a12d2d;
      font-size: 16px;
      line-height: 1.38;
      margin-top: 8px;
    }
    .majors-grid {
      margin-top: 8px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 4px 20px;
      font-size: 15px;
      line-height: 1.3;
    }
    .major-item {
      break-inside: avoid;
    }
    pre {
      margin: 0;
      padding: 12px;
      border-radius: 10px;
      border: 1px solid var(--line);
      background: #fcfbf6;
      white-space: pre-wrap;
      word-wrap: break-word;
      font: 14px/1.5 Consolas, "Courier New", monospace;
    }
    @media (max-width: 640px) {
      .ig-canvas-wrap {
        padding: 8px;
      }
      .edit-form {
        grid-template-columns: 1fr;
      }
      .ig-canvas {
        padding: 12px;
      }
      .poster-title {
        font-size: 18px;
      }
      .poster-city {
        font-size: 12px;
      }
      .meta {
        font-size: 10px;
        line-height: 1.3;
      }
      .section-title {
        font-size: 15px;
        margin-bottom: 2px;
      }
      .section-label {
        font-size: 10px;
        margin: 5px 0 2px;
      }
      .content, .note {
        font-size: 10px;
        line-height: 1.3;
      }
      .sch-item {
        font-size: 10px;
        line-height: 1.3;
      }
      .majors-grid {
        font-size: 9px;
        gap: 2px 8px;
      }
    }
  </style>
</head>
<body>
  <main class="wrap">
    <section class="card">
      <h1>Scholarship Data Formatter</h1>
      <p>Paste raw scholarship text, then get a clean summary.</p>
      <form method="post">
        <input type="hidden" name="action" value="format">
        <label for="raw">Raw Scholarship Data</label>
        <textarea id="raw" name="raw" placeholder="Paste messy text here...">{{ raw_text }}</textarea>
        <div class="actions-row">
          <button type="submit">Format Data</button>
          <button id="clearRawBtn" type="button" class="btn-secondary">Clear Input</button>
        </div>
      </form>
      {% if output %}
      <section class="out">
        <label>Formatted Output</label>
        <pre>{{ output }}</pre>
        <label class="edit-title">Edit Parsed Fields</label>
        <form method="post" class="edit-form">
          <input type="hidden" name="action" value="edit">
          <textarea name="raw" style="display:none;">{{ raw_text }}</textarea>
          <input type="hidden" name="city_hidden" value="{{ parsed.get('City', '') }}">
          {% for field in editable_fields %}
            <div class="edit-field {% if field.multiline %}wide{% endif %}">
              <label for="{{ field.name }}">{{ field.label }}</label>
              {% if field.multiline %}
                <textarea id="{{ field.name }}" name="{{ field.name }}">{{ field.value }}</textarea>
              {% else %}
                <input id="{{ field.name }}" type="text" name="{{ field.name }}" value="{{ field.value }}">
              {% endif %}
            </div>
          {% endfor %}
          <div class="edit-actions">
            <button type="submit">Update Preview</button>
          </div>
        </form>
        <label class="preview-title">Instagram 1080 x 1080 Preview</label>
        <div class="ig-frame">
          <div class="ig-canvas-wrap">
            <article class="ig-canvas">
              <header class="poster-top">
                <h2 class="poster-title">{{ preview_title }}</h2>
                {% if parsed.get("City") %}<div class="poster-city">City: {{ parsed.get("City") }}</div>{% endif %}
              </header>

              <div class="meta">
                {% if parsed.get("Intake") %}<div class="meta-row"><b>Intake:</b> {{ parsed.get("Intake") }}</div>{% endif %}
                {% if parsed.get("Age") %}<div class="meta-row"><b>Age:</b> {{ parsed.get("Age") }}</div>{% endif %}
                {% if parsed.get("Deadline") %}<div class="meta-row"><b>Deadline:</b> {{ parsed.get("Deadline") }}</div>{% endif %}
              </div>

              {% if parsed.get("Scholarship") %}
              <section class="section">
                <h3 class="section-label">University Scholarship:</h3>
                {% if scholarship_items|length > 1 %}
                <div class="sch-list">
                  {% for item in scholarship_items %}
                    <div class="sch-item">- {{ item }}</div>
                  {% endfor %}
                </div>
                {% else %}
                <div class="content">{{ parsed.get("Scholarship") }}</div>
                {% endif %}
              </section>
              {% endif %}

              {% if parsed.get("Original Fees") or parsed.get("Application Fees") %}
              <section class="section">
                <h3 class="section-label">Original Fee Structure:</h3>
                {% if parsed.get("Original Fees") %}<div class="content">Tuition: {{ parsed.get("Original Fees") }}</div>{% endif %}
                {% if parsed.get("Application Fees") %}<div class="content">Application fee: {{ parsed.get("Application Fees") }}</div>{% endif %}
              </section>
              {% endif %}

              {% if parsed.get("Note") %}
              <section class="section">
                <div class="note"><b>Note:</b> {{ parsed.get("Note") }}</div>
              </section>
              {% endif %}

              {% if majors or parsed.get("Field") or parsed.get("Program") %}
              <section class="section">
                <h3 class="section-label">Majors (English-Taught):</h3>
                {% if parsed.get("Field") %}<div class="content"><b>Field:</b> {{ parsed.get("Field") }}</div>{% endif %}
                {% if parsed.get("Program") %}<div class="content"><b>Program:</b> {{ parsed.get("Program") }}</div>{% endif %}
                {% if majors %}
                <div class="majors-grid">
                  {% for item in majors %}
                    <div class="major-item">{{ item }}</div>
                  {% endfor %}
                </div>
                {% endif %}
              </section>
              {% endif %}
            </article>
          </div>
        </div>
      </section>
      {% endif %}
    </section>
  </main>
</body>
<script>
  (function () {
    var clearBtn = document.getElementById("clearRawBtn");
    var rawInput = document.getElementById("raw");
    if (!clearBtn || !rawInput) return;
    clearBtn.addEventListener("click", function () {
      rawInput.value = "";
      rawInput.focus();
    });
  })();
</script>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    raw_text = ""
    output = ""
    parsed = {}
    majors = []
    scholarship_items = []
    editable_fields = []
    preview_title = "Scholarship Offer"
    if request.method == "POST":
        action = request.form.get("action", "format")
        raw_text = request.form.get("raw", "").strip()
        if action == "edit":
            parsed = collect_fields_from_form(request.form)
            city_hidden = request.form.get("city_hidden", "").strip()
            if city_hidden:
                parsed["City"] = city_hidden
        elif raw_text:
            parsed = parse_scholarship(raw_text)

    if parsed:
        output = format_output(parsed)
        preview_title = parsed.get("Offer Title", "Scholarship Offer")
        scholarship_raw = parsed.get("Scholarship", "")
        scholarship_items = [s.strip().strip(".") for s in re.split(r"[;\n]+", scholarship_raw) if s.strip()]
        majors_raw = parsed.get("Majors", "")
        majors = [m.strip() for m in re.split(r"[,;\n]+", majors_raw) if m.strip()]
        program_value = parsed.get("Program", "").strip().lower()
        if program_value:
            majors = [m for m in majors if m.lower() != program_value]
        editable_fields = build_editable_fields(parsed)

    return render_template_string(
        PAGE,
        raw_text=raw_text,
        output=output,
        parsed=parsed,
        majors=majors,
        scholarship_items=scholarship_items,
        editable_fields=editable_fields,
        preview_title=preview_title,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

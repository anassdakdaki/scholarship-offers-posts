import re
import sys
from typing import Dict, List, Optional


FIELD_ORDER = [
    "Offer Title",
    "Intake",
    "Age",
    "Deadline",
    "Scholarship",
    "Original Fees",
    "Field",
    "Program",
    "Majors",
    "Taught in English",
    "Note",
    "Application Fees",
]


FIELD_PATTERNS = {
    "Offer Title": [
        r"\boffer\s*title\b",
        r"\btitle\b",
        r"\bscholarship\s*name\b",
        r"\boffer\b",
    ],
    "Intake": [
        r"\bintake\b",
        r"\bstart\s*(?:date|term)\b",
        r"\badmission\s*term\b",
    ],
    "City": [
        r"\bcity\b",
        r"\blocation\b",
    ],
    "Age": [
        r"\bage\b",
        r"\bage\s*limit\b",
        r"\bapplicants?\s*aged\b",
    ],
    "Deadline": [
        r"\bdeadline\b",
        r"\bapply\s*by\b",
        r"\bapplication\s*deadline\b",
        r"\blast\s*date\b",
    ],
    "Scholarship": [
        r"\bscholarship\b",
        r"\bwaiver\b",
        r"\bdiscount\b",
        r"\bgrant\b",
    ],
    "Original Fees": [
        r"\boriginal\s*fees?\b",
        r"\btuition\s*fees?\b",
        r"\btuition\b",
        r"\bcost\b",
    ],
    "Field": [
        r"\bfield\b",
    ],
    "Program": [
        r"\bprogram\s*name\b",
    ],
    "Majors": [
        r"\bmajors?\b",
        r"\bcourses?\b",
    ],
    "Taught in English": [
        r"\btaught\s*in\s*english\b",
        r"\bteaching\s*language\b",
        r"\blanguage\b",
        r"\benglish\s*medium\b",
        r"\bin\s*english\b",
    ],
    "Note": [
        r"\bnote\b",
        r"\bremarks?\b",
        r"\bimportant\b",
        r"\bconditions?\b",
    ],
    "Application Fees": [
        r"\bapplication\s*fees?\b",
        r"\bapp(?:lication)?\s*fee\b",
        r"\bprocessing\s*fee\b",
    ],
}

FIELD_LABEL_PREFIXES = {
    "Offer Title": [
        "offer title",
        "scholarship name",
        "title",
    ],
    "Intake": [
        "intake",
        "start term",
        "admission term",
    ],
    "City": [
        "city",
        "location",
    ],
    "Age": [
        "age (years old)",
        "age limit",
        "age",
    ],
    "Deadline": [
        "application deadline",
        "deadline",
        "apply by",
        "last date",
    ],
    "Scholarship": [
        "scholarship type",
        "scholarship",
        "waiver",
        "grant",
    ],
    "Original Fees": [
        "original tuition fee",
        "original tuition",
        "original fees",
        "original fee structure",
        "tuition fee",
        "tuition",
        "university fees",
    ],
    "Field": [
        "field",
    ],
    "Program": [
        "program name",
    ],
    "Majors": [
        "majors (english-taught)",
        "majors",
    ],
    "Taught in English": [
        "taught in english",
        "teaching language",
        "english medium",
        "language",
    ],
    "Note": [
        "special notes",
        "notes",
        "note",
        "remarks",
    ],
    "Application Fees": [
        "application fee",
        "application fees",
        "processing fee",
    ],
}

SECTION_BREAKERS = (
    "application requirements",
    "application documents",
    "fee structure",
    "university fees",
    "program details",
    "basic information",
    "eduprchina",
)


def normalize_spaces(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text).strip()


def normalize_lines(text: str) -> List[str]:
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [normalize_spaces(line) for line in raw.split("\n")]
    return [line for line in lines if line]


def normalize_bool_english(value: str) -> str:
    low = value.lower()
    if low in ("yes", "y", "true"):
        return "Yes"
    if low in ("no", "n", "false"):
        return "No"

    yes_tokens = ["english", "english medium", "in english", "available in english", "taught in english"]
    no_tokens = ["not in english", "non-english", "no english", "chinese only"]
    for token in yes_tokens:
        if token in low:
            return "Yes"
    for token in no_tokens:
        if token in low:
            return "No"
    return value


def clean_value(value: str) -> str:
    v = normalize_spaces(value)
    v = re.sub(r"^[\-\:\;\,\.\)\(\?\u2022\uFF1A]+", "", v).strip()
    return v


def extract_money_tokens(value: str) -> List[str]:
    text = re.sub(r"\([^)]*\)", " ", value)
    text = normalize_spaces(text)
    return re.findall(
        r"(?:[$\u00A5\u20AC\u00A3]\s*)?\d[\d,]*(?:\.\d{1,2})?(?:\s*[A-Za-z]{2,8})?(?:/[A-Za-z]{1,8})?",
        text,
    )


def is_zero_fee_token(token: str) -> bool:
    num = re.sub(r"[^\d.]", "", token)
    if not num:
        return False
    try:
        return float(num) == 0.0
    except ValueError:
        return False


def extract_money_token(value: str, prefer_non_zero: bool = False) -> str:
    tokens = [normalize_spaces(t) for t in extract_money_tokens(value) if normalize_spaces(t)]
    if not tokens:
        return normalize_spaces(value)
    if prefer_non_zero:
        for tok in tokens:
            if not is_zero_fee_token(tok):
                return tok
    return tokens[0]


def should_skip_candidate(field: str, value: str, source_line: str) -> bool:
    low_val = normalize_spaces(value).lower().strip(":")
    low_line = source_line.lower()

    if field == "Scholarship":
        if re.match(r"^\s*scholarship\s*(policy|duration|information)\b", low_line):
            return True
        if re.match(r"^\s*(first|second|third)[-\s]?class\s+scholarship\b", low_line):
            return True
        if not low_val:
            return True
        if low_val in ("policy", "information", "duration", "type"):
            return True
        if low_val.startswith("policy") or low_val.startswith("information"):
            return True

    if field == "Original Fees":
        if "after scholarship" in low_line:
            return True

    if field == "Note":
        if low_val in ("s", "note", "notes"):
            return True

    return False


def should_replace_existing(field: str, existing: str, new: str, source_line: str) -> bool:
    if not existing:
        return True

    if field == "Original Fees":
        if is_zero_fee_token(existing) and not is_zero_fee_token(new):
            return True
        if "original tuition" in source_line.lower() and not is_zero_fee_token(new):
            return True
        return False

    if field == "Scholarship":
        existing_low = existing.lower()
        new_low = new.lower()
        noise = ("policy", "information", "duration")
        if any(existing_low.startswith(n) for n in noise) and not any(new_low.startswith(n) for n in noise):
            return True
        if any(new_low.startswith(n) for n in noise):
            return False
        return len(new) >= len(existing)

    if field == "Note":
        return len(new) > len(existing)

    return True


def extract_from_prefix_labels(line: str) -> Optional[tuple]:
    low = line.lower().strip()
    for canonical, labels in FIELD_LABEL_PREFIXES.items():
        for label in sorted(labels, key=len, reverse=True):
            if low.startswith(label):
                value = clean_value(line[len(label) :])
                if value:
                    return canonical, value
    return None


def likely_is_title(line: str) -> bool:
    return bool(
        re.search(r"(scholarship|grant|waiver|bursary|offer|engineering|business|science|economics|trade|commerce)", line, flags=re.IGNORECASE)
    )


def extract_from_key_value(line: str) -> Optional[tuple]:
    # Support separators like ":" "-" "=>" "="
    m = re.match(r"^\s*([A-Za-z][A-Za-z /()\-]+?)\s*(?::|=>|=|\-)\s*(.+)$", line)
    if not m:
        return None
    key = normalize_spaces(m.group(1))
    val = clean_value(m.group(2))
    for canonical, patterns in FIELD_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, key, flags=re.IGNORECASE):
                # Prevent "Application fee" keys from being captured as original fees.
                if canonical == "Original Fees" and re.search(
                    r"\b(application|app|processing)\b", key, flags=re.IGNORECASE
                ):
                    continue
                return canonical, val
    return None


def extract_from_free_text(lines: List[str], fields: Dict[str, str]) -> None:
    blob = " ".join(lines)

    if "Deadline" not in fields:
        m = re.search(
            r"\b(?:deadline|apply by|application deadline|last date)\s*(?:is|:)?\s*([A-Za-z]{3,9}\s+\d{1,2},?\s*\d{4}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            blob,
            flags=re.IGNORECASE,
        )
        if m:
            fields["Deadline"] = normalize_spaces(m.group(1))

    if "Age" not in fields:
        m = re.search(
            r"\b(?:age(?:\s*limit)?|applicants?\s*aged)\s*(?:is|:|between|from)?\s*(\d{1,2}\s*(?:-|to)\s*\d{1,2}|\d{1,2}\+?)",
            blob,
            flags=re.IGNORECASE,
        )
        if m:
            fields["Age"] = normalize_spaces(m.group(1)).replace(" to ", "-")

    if "Application Fees" not in fields:
        m = re.search(
            r"\b(?:application|app(?:lication)?|processing)\s*fee(?:s)?\s*(?:is|:|=)?\s*([^\n]{0,30}?(?:[$\u00A5\u20AC\u00A3]\s*)?\d[\d,]*(?:\.\d{1,2})?\s*[A-Za-z]{0,8})",
            blob,
            flags=re.IGNORECASE,
        )
        if m:
            fields["Application Fees"] = extract_money_token(m.group(1), prefer_non_zero=True)

    if "Taught in English" not in fields:
        if re.search(r"\b(taught in english|english medium|in english)\b", blob, flags=re.IGNORECASE):
            fields["Taught in English"] = "Yes"
        elif re.search(r"\b(not taught in english|non-english|no english)\b", blob, flags=re.IGNORECASE):
            fields["Taught in English"] = "No"
        elif re.search(r"\bteaching\s*language\s*:?\s*english\b", blob, flags=re.IGNORECASE):
            fields["Taught in English"] = "Yes"

    if "Scholarship" not in fields and re.search(r"\bself[-\s]?financed\b", blob, flags=re.IGNORECASE):
        fields["Scholarship"] = "Self-financed"


def extract_note_from_lines(lines: List[str], fields: Dict[str, str]) -> None:
    if "Note" in fields:
        return
    for idx, line in enumerate(lines):
        if re.match(r"^(special\s*notes?|notes?)\b", line, flags=re.IGNORECASE):
            captured = []
            rest = re.sub(r"^(special\s*notes?|notes?)\s*[:\-]?\s*", "", line, flags=re.IGNORECASE)
            if rest:
                captured.append(rest)
            for nxt in lines[idx + 1 : idx + 6]:
                if any(nxt.lower().startswith(token) for token in SECTION_BREAKERS):
                    break
                if re.match(r"^(majors?|field|program details|basic information)\b", nxt, flags=re.IGNORECASE):
                    break
                captured.append(nxt)
            if captured:
                fields["Note"] = normalize_spaces(" ".join(captured))
                return


def extract_scholarship_policy_summary(lines: List[str]) -> str:
    start_idx = -1
    for idx, line in enumerate(lines):
        if re.match(r"^scholarship\s*policy\b", line, flags=re.IGNORECASE):
            start_idx = idx
            break
    if start_idx == -1:
        return ""

    picked: List[str] = []
    for nxt in lines[start_idx + 1 : start_idx + 20]:
        low = nxt.lower()
        if any(low.startswith(token) for token in SECTION_BREAKERS):
            break
        if re.match(r"^(application requirements|applicant requirements|application documents|fee structure|special notes?)\b", low):
            break

        cleaned = clean_value(re.sub(r"^\d+\s*[-.)]\s*", "", nxt))
        if not cleaned:
            continue
        if cleaned.rstrip(":").lower() in ("scholarships", "scholarship", "scholarship policy"):
            continue
        if cleaned.endswith(":") and len(cleaned.split()) <= 2:
            continue
        if re.search(r"original\s+tuition", cleaned, flags=re.IGNORECASE):
            continue
        if re.search(r"(first[-\s]?class|second[-\s]?class|third[-\s]?class|waiver|free tuition|stipend|scholarship)", cleaned, flags=re.IGNORECASE):
            picked.append(cleaned)

    # Keep a concise, deduplicated summary.
    unique: List[str] = []
    for item in picked:
        if item not in unique:
            unique.append(item)
    return "; ".join(unique[:3])


def infer_full_tuition_coverage(lines: List[str]) -> bool:
    for line in lines:
        low = line.lower()
        if "tuition fee after scholarship" in low and re.search(r"\b0(?:\.0+)?\s*rmb/year\b", low):
            return True
        if re.search(r"\btuition\s*fee\b", low) and re.search(r"\b0(?:\.0+)?\s*rmb/year\b", low):
            tokens = extract_money_tokens(line)
            if any(not is_zero_fee_token(t) for t in tokens):
                return True
        if re.search(r"(100%\s*tuition\s*fee\s*waiver|free\s*tuition\s*fee)", low):
            return True
    return False


def enrich_scholarship_field(lines: List[str], fields: Dict[str, str]) -> None:
    blob = " ".join(lines)
    existing = normalize_spaces(fields.get("Scholarship", ""))

    type_match = re.search(r"\bscholarship\s*type\s*([A-Za-z0-9]+)\b", blob, flags=re.IGNORECASE)
    type_value = f"Type {type_match.group(1).upper()}" if type_match else ""
    if re.match(r"^type\s+[A-Za-z0-9]+$", existing, flags=re.IGNORECASE):
        type_value = existing

    policy_summary = extract_scholarship_policy_summary(lines)
    full_waiver = infer_full_tuition_coverage(lines)

    parts: List[str] = []
    if existing and existing.lower() == "self-financed":
        fields["Scholarship"] = "Self-financed"
        return

    if type_value:
        parts.append(type_value)
    elif existing and existing.lower() not in ("policy", "information"):
        parts.append(existing)

    if policy_summary:
        parts.append(policy_summary)
    elif full_waiver:
        parts.append("Full tuition fee waiver")

    deduped: List[str] = []
    for p in parts:
        p = normalize_spaces(p).strip(";")
        if p and p not in deduped:
            deduped.append(p)

    if deduped:
        fields["Scholarship"] = "; ".join(deduped)


def post_process(fields: Dict[str, str], lines: List[str]) -> Dict[str, str]:
    output = dict(fields)

    if "Offer Title" not in output:
        for line in lines:
            if likely_is_title(line) and len(line.split()) <= 14:
                output["Offer Title"] = line
                break
        if "Offer Title" not in output and lines:
            output["Offer Title"] = lines[0]

    if "Taught in English" in output:
        output["Taught in English"] = normalize_bool_english(output["Taught in English"])

    if "City" in output:
        output["City"] = normalize_spaces(output["City"]).strip("-: ")

    if "Field" in output:
        output["Field"] = normalize_spaces(output["Field"]).strip("-: ")

    if "Program" in output:
        output["Program"] = normalize_spaces(output["Program"]).strip("-: ")

    if "Majors" in output:
        majors = re.split(r"[;,/|]+", output["Majors"])
        majors = [normalize_spaces(m) for m in majors if normalize_spaces(m)]
        output["Majors"] = ", ".join(majors)
        if (
            output["Majors"].lower() in ("engineering", "science", "business")
            and "Offer Title" in output
            and re.search(r"(engineering|science|business|technology|arts)", output["Offer Title"], flags=re.IGNORECASE)
        ):
            output["Majors"] = output["Offer Title"]

    if "Original Fees" in output:
        output["Original Fees"] = output["Original Fees"].replace("US$", "$").replace("USD", "$")
        output["Original Fees"] = re.sub(r"^\$\s+", "$", output["Original Fees"])
        output["Original Fees"] = extract_money_token(output["Original Fees"], prefer_non_zero=True)

    if "Application Fees" in output:
        output["Application Fees"] = extract_money_token(output["Application Fees"], prefer_non_zero=True)

    if "Offer Title" in output:
        output["Offer Title"] = re.sub(r"\bself[-\s]?financed\b", "", output["Offer Title"], flags=re.IGNORECASE)
        output["Offer Title"] = normalize_spaces(output["Offer Title"]).strip("-: ")

    if "Program" not in output and "Offer Title" in output:
        output["Program"] = output["Offer Title"]

    return output


def parse_scholarship(raw_text: str) -> Dict[str, str]:
    fields: Dict[str, str] = {}
    lines = normalize_lines(raw_text)

    for line in lines:
        kv = extract_from_key_value(line)
        if not kv:
            kv = extract_from_prefix_labels(line)
        if kv:
            key, value = kv
            if key == "Taught in English":
                value = normalize_bool_english(value)
            elif key in ("Original Fees", "Application Fees"):
                value = extract_money_token(value, prefer_non_zero=True)

            if should_skip_candidate(key, value, line):
                continue

            if key in fields and not should_replace_existing(key, fields[key], value, line):
                continue
            fields[key] = value

    extract_from_free_text(lines, fields)
    extract_note_from_lines(lines, fields)
    enrich_scholarship_field(lines, fields)

    if "Offer Title" not in fields and lines:
        first_line = lines[0]
        if len(first_line.split()) <= 8 and not re.search(r"\b(program|id|fee|intake|deadline)\b", first_line, flags=re.IGNORECASE):
            fields["Offer Title"] = first_line

    if "Majors" not in fields and "Program" in fields:
        fields["Majors"] = fields["Program"]
    elif "Majors" not in fields and "Offer Title" in fields:
        if re.search(r"(engineering|science|business|technology|arts|economics|trade|commerce)", fields["Offer Title"], flags=re.IGNORECASE):
            fields["Majors"] = fields["Offer Title"]

    return post_process(fields, lines)


def format_output(fields: Dict[str, str]) -> str:
    rows = []
    for key in FIELD_ORDER:
        if key not in fields:
            continue
        if key == "Application Fees" and not fields.get(key):
            continue
        rows.append(f"{key}: {fields[key]}")
    return "\n".join(rows)


def main() -> None:
    print("Paste messy scholarship data. Press Ctrl+Z then Enter (Windows) to finish:\n")
    raw = sys.stdin.read()
    if not raw.strip():
        print("No input received.")
        return
    parsed = parse_scholarship(raw)
    print("\nFormatted Output:\n")
    print(format_output(parsed))


if __name__ == "__main__":
    main()


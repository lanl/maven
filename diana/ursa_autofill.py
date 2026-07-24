import json
import re
from copy import deepcopy
from typing import Any

from diana.ursa_utils import run_ursa_agent


AGENT_META_COLUMNS = ["agent_meta", "user_clarifications"]

THEME_TO_FIELDS: dict[str, list[str]] = {
    "purpose_and_use": ["s2.1", "s6.1", "s6.3", "s6.5"],
    "composition_and_structure": [
        "s3.1",
        "s3.2",
        "s3.3",
        "s3.4",
        "s3.5",
        "s3.6",
        "s3.7",
        "s3.8",
        "s3.9",
        "s6.4",
        "s6.7",
    ],
    "ownership_funding_initiative": [
        "s1.3",
        "s1.4",
        "s2.2",
        "s2.3",
        "s2.4",
        "s2.5",
        "s8.1",
        "s8.2",
    ],
    "provenance_and_review": [
        "s4.1",
        "s4.2",
        "s4.3",
        "s4.4",
        "s4.5",
        "s4.6",
        "s4.7",
        "s4.8",
        "s4.9",
        "s4.10",
        "s4.11",
        "s4.12",
        "s4.13",
        "s4.14",
        "s5.4",
    ],
    "restrictions_distribution_licensing": [
        "s1.1",
        "s3.10",
        "s3.11",
        "s3.12",
        "s6.2",
        "s7.1",
        "s7.2",
        "s7.3",
        "s7.4",
        "s7.5",
        "s7.6",
        "s7.7",
        "s8.5",
    ],
    "maintenance_and_lifecycle": [
        "s8.3",
        "s8.4",
        "s8.5",
        "s8.6",
        "s8.7",
        "s8.8",
        "s6.6",
    ],
}

THEME_TO_PROMPT: dict[str, str] = {
    "purpose_and_use": "Dataset purpose and intended use: describe why the dataset was created, " +
                       "the main scientific or operational goals, current and intended uses, and " +
                       "whether it has been used or prepared for AI workflows.",
    "composition_and_structure": "Dataset composition and structure: describe what each instance " +
                                 "represents, approximate size, labels or targets, missingness, " +
                                 "relationships, quality issues, and whether the dataset links to " +
                                 "external resources.",
    "ownership_funding_initiative": "Ownership, funding, and initiative: identify the creating " +
                                    "team, institutional ownership, the best contacts, funding sources, " +
                                    "facility proposal or campaign identifiers, and any larger " +
                                    "initiative or program this dataset belongs to.",
    "provenance_and_review": "Collection, provenance, and review history: explain how the data were " +
                             "acquired, what facilities or instruments were involved, who collected " +
                             "them, the timeframe, sampling method, and any ethical, safety, " +
                             "cybersecurity, or export-control reviews.",
    "restrictions_distribution_licensing": "Restrictions, distribution, and licensing: describe " +
                                           "confidentiality, proprietary or export-control restrictions, " +
                                           "third-party dependencies, distribution channels and timing, " +
                                           "DOI or repository links, and licensing or terms-of-use requirements.",
    "maintenance_and_lifecycle": "Maintenance and lifecycle: describe who maintains the dataset, how it is " +
                                 "supported, update cadence, errata, retention limits, support for older " +
                                 "versions, obsolescence expectations, tutorials, and how outside " +
                                 "contributors can extend it.",
}

FIELD_TO_THEMES: dict[str, list[str]] = {}
for _theme, _fields in THEME_TO_FIELDS.items():
    for _field in _fields:
        FIELD_TO_THEMES.setdefault(_field, []).append(_theme)


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _safe_json_loads(value: Any, default: Any) -> Any:
    if not isinstance(value, str) or not value.strip():
        return deepcopy(default)
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return deepcopy(default)


def load_agent_meta(row: dict[str, Any]) -> dict[str, Any]:
    meta = _safe_json_loads(row.get("agent_meta", ""), {})
    meta.setdefault("fields", {})
    meta.setdefault("followup_questions", [])
    meta.setdefault("history", [])
    meta.setdefault("themes", {})
    return meta


def dump_agent_meta(meta: dict[str, Any]) -> str:
    return json.dumps(meta, indent=2, sort_keys=True)


def build_question_catalog(
    sections: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    catalog: dict[str, dict[str, Any]] = {}
    for section in sections:
        for question in section["questions"]:
            catalog[question["id"]] = {
                "label": question.get("label", question["id"]),
                "required": question.get("required", True),
                "section_idx": section["section_idx"],
                "type": question.get("type", "text"),
            }
    return catalog


def _compose_intake_context(row: dict[str, Any]) -> str:
    ordered_fields = [
        ("project_name", "Project Title"),
        ("short_project_title", "Short Project Title"),
        ("ald", "ALD"),
        ("primary_contact", "Primary Contact Person"),
        ("data_owner", "Data Owner"),
        ("project_description", "Verbose project description"),
        ("context_files_text", "Context Files Text"),
        ("data_composition", "Verbose data composition"),
        ("project_url", "Project URLs and identifiers"),
    ]
    parts = []
    for key, label in ordered_fields:
        value = row.get(key, "")
        if _has_text(value):
            parts.append(f"{label}: {str(value).strip()}")
    return "\n".join(parts)


def _base_payload() -> dict[str, Any]:
    return {
        "fields": {},
        "followup_questions": [],
        "notes": [],
        "source": "heuristic",
    }


def _field(
    answer: str = "",
    *,
    status: str,
    confidence: str,
    rationale: str,
    source: str,
) -> dict[str, str]:
    return {
        "answer": answer.strip(),
        "status": status,
        "confidence": confidence,
        "rationale": rationale,
        "source": source,
    }


def _field_from_text(
    answer: str,
    *,
    rationale: str,
    confidence: str = "medium",
    empty_status: str = "needs_user",
    source: str = "heuristic",
) -> dict[str, str]:
    answer = answer.strip()
    return _field(
        answer,
        status="filled" if answer else empty_status,
        confidence=confidence if answer else "low",
        rationale=rationale if answer else "No supporting evidence is available yet.",
        source=source,
    )


def _pick_line(value: str, *, fallback: str = "") -> str:
    value = value.strip()
    if not value:
        return fallback
    lines = [line.strip("- ").strip()
             for line in value.splitlines() if line.strip()]
    return lines[0] if lines else fallback


def _join_nonempty(parts: list[str], sep: str = " ") -> str:
    return sep.join(part.strip() for part in parts if part and part.strip())


def _normalize_theme_key(key: str) -> str:
    stripped = key.strip()
    if stripped in THEME_TO_PROMPT:
        return stripped
    for theme, prompt in THEME_TO_PROMPT.items():
        if stripped == prompt:
            return theme
    lowered = stripped.lower()
    for theme, prompt in THEME_TO_PROMPT.items():
        if lowered == prompt.lower():
            return theme
        if theme.replace("_", " ") in lowered:
            return theme
    return stripped


def _normalize_clarifications(clarifications: dict[str, str] | None,) -> dict[str, dict[str, str]]:
    normalized: dict[str, dict[str, str]] = {}
    for key, answer in (clarifications or {}).items():
        if not _has_text(answer):
            continue
        theme = _normalize_theme_key(key)
        normalized[theme] = {
            "question": THEME_TO_PROMPT.get(theme, key),
            "answer": answer.strip(),
        }
    return normalized


def _clarification_blob(theme_answers: dict[str, dict[str, str]]) -> str:
    parts = []
    for theme, item in theme_answers.items():
        title = THEME_TO_PROMPT.get(theme, item["question"])
        parts.append(f"{title}\nAnswer: {item['answer']}")
    return "\n\n".join(parts)


def _build_context(row: dict[str, Any], theme_answers: dict[str, dict[str, str]]) -> dict[str, str]:
    project_description = str(row.get("project_description", "") or "").strip()
    data_composition = str(row.get("data_composition", "") or "").strip()
    project_url = str(row.get("project_url", "") or "").strip()
    ownership_parts = [
        f"Primary Contact Person: {row['primary_contact'].strip()}" if _has_text(
            row.get("primary_contact", "")) else "",
        f"Data Owner: {row['data_owner'].strip()}" if _has_text(
            row.get("data_owner", "")) else "",
        f"ALD: {row['ald'].strip()}" if _has_text(row.get("ald", "")) else "",
        project_description,
    ]
    facility_parts = [
        f"Context files text: {row['context_files_text'].strip()}" if _has_text(
            row.get("context_files_text", "")) else "",
        project_description,
    ]
    governance_parts = [
        project_description,
        theme_answers.get("ownership_funding_initiative",
                          {}).get("answer", ""),
        theme_answers.get(
            "restrictions_distribution_licensing", {}).get("answer", ""),
        theme_answers.get("maintenance_and_lifecycle", {}).get("answer", ""),
    ]
    distribution_parts = [
        project_url,
        project_description,
        theme_answers.get(
            "restrictions_distribution_licensing", {}).get("answer", ""),
        theme_answers.get("purpose_and_use", {}).get("answer", ""),
    ]
    data_shape_parts = [
        data_composition,
        project_description,
        theme_answers.get("composition_and_structure", {}).get("answer", ""),
        theme_answers.get("purpose_and_use", {}).get("answer", ""),
        theme_answers.get("provenance_and_review", {}).get("answer", ""),
    ]
    return {
        "ownership_context": _join_nonempty(ownership_parts, sep=" "),
        "facility_context": _join_nonempty(facility_parts, sep=" "),
        "governance_context": _join_nonempty(governance_parts, sep="\n\n"),
        "distribution_context": _join_nonempty(distribution_parts, sep="\n\n"),
        "data_shape_context": _join_nonempty(data_shape_parts, sep="\n\n"),
    }


def _theme_status(
    theme: str,
    payload_fields: dict[str, dict[str, str]],
    existing_answers: dict[str, dict[str, str]],
) -> dict[str, Any]:
    fields = THEME_TO_FIELDS[theme]
    unresolved = []
    low_conf = []
    for qid in fields:
        field = payload_fields.get(qid, {})
        if field.get("status") in {"needs_user", "unknown"}:
            unresolved.append(qid)
        if field.get("confidence") == "low":
            low_conf.append(qid)
    return {
        "question": THEME_TO_PROMPT[theme],
        "fields": fields,
        "unresolved_fields": unresolved,
        "low_confidence_fields": low_conf,
        "answered": theme in existing_answers,
    }


def _extract_numbers(text: str) -> str:
    """Extract numerical information from text (counts, sizes, dates, ranges)."""
    if not text:
        return ""
    # Find patterns like "10,000", "~5000", "approximately 1000", "1.5M", etc.
    patterns = [
        r'(?:approximately|about|~|roughly)?\s*[\d,]+(?:\.\d+)?(?:\s*[KMBkmb])?(?:\s+(?:samples|instances|records|files|measurements|observations))?',
        # years/date ranges
        r'\d{4}(?:-\d{4})?(?:\s+(?:through|to|-)?\s+\d{4})?',
        r'(?:between|from)?\s*\d+\s*(?:to|and|-)\s*\d+',  # ranges
    ]
    numbers = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        numbers.extend(matches)
    return " ".join(numbers[:3]) if numbers else ""


def _extract_contacts(text: str) -> str:
    """Extract names and email addresses from text, discarding verbose descriptions."""
    if not text:
        return ""

    # Pattern for email addresses
    emails = re.findall(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

    # Pattern for names (capitalized words, 2-4 words typically)
    # Look for patterns like "John Doe" or "Jane Smith (jane@example.com)"
    name_patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b',  # Capitalized names
        r'\b[A-Z]{2,4}\b',  # Initials like "CWJ"
    ]

    names = []
    for pattern in name_patterns:
        matches = re.findall(pattern, text)
        names.extend(matches)

    # Combine names with emails if both exist
    if names and emails:
        # Try to pair them
        result = []
        for i in range(max(len(names), len(emails))):
            name = names[i] if i < len(names) else ""
            email = emails[i] if i < len(emails) else ""
            if name and email:
                result.append(f"{name} ({email})")
            elif name:
                result.append(name)
            elif email:
                result.append(email)
        return ", ".join(result[:3])  # Limit to 3 contacts
    elif emails:
        return ", ".join(emails[:3])
    elif names:
        return ", ".join(names[:3])

    return ""


def _extract_entities(text: str, entity_type: str = "all") -> str:
    """Extract named entities: institutions, people, instruments, facilities, DOIs, LA-URs."""
    if not text:
        return ""

    entities = []

    if entity_type in {"all", "institution"}:
        # Match university/lab/institution patterns
        inst_patterns = [
            r'(?:Los Alamos National Laboratory|LANL)',
            r'(?:National\s+\w+\s+(?:Laboratory|Lab|Center))',
            r'(?:University of \w+)',
            r'\b[A-Z][a-z]+\s+(?:University|Institute|Laboratory|Lab)\b',
        ]
        for pattern in inst_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

    if entity_type in {"all", "instrument"}:
        # Match instrument/equipment patterns
        inst_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z0-9-]+\s+(?:spectrometer|microscope|detector|sensor)\b',
            r'(?:XRD|SEM|TEM|NMR|FTIR|UV-Vis)\s+(?:spectrometer|system|instrument)?',
        ]
        for pattern in inst_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)

    if entity_type in {"all", "grant", "funding"}:
        # Enhanced grant/funding patterns with agency names
        grant_patterns = [
            # Federal agencies with program offices
            r'(?:U\.S\.\s+)?Department of Energy(?:,?\s+Office of [^,\.]+)?(?:,?\s+[^,\.]+\s+program)?',
            r'(?:National Science Foundation|NSF)(?:\s+[A-Z][a-z]+\s+(?:Division|Program))?',
            r'(?:National Institutes of Health|NIH)(?:\s+[A-Z]{2,})?',
            r'(?:DARPA|NASA|NOAA|EPA)(?:\s+[A-Z][a-z]+\s+(?:Program|Office))?',
            # Award/Contract numbers
            r'Award\s+(?:Number\s+)?[A-Z0-9-]+',
            r'(?:Grant|Contract)\s+(?:Number\s+|#)?[A-Z0-9-]+',
            r'DE-[A-Z]{2}\d{2}-\d{2}[A-Z]{2}\d{5}',  # DOE contract format
            r'[A-Z]{2,4}\d{2}-\d{4,7}[A-Z]{2}',  # Generic lab contract
            # LDRD and internal programs
            r'LDR[DR](?:\s+program)?(?:\s+(?:under\s+)?project(?:\s+number)?\s+\d+)?',
        ]
        for pattern in grant_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

    if entity_type in {"all", "doi", "url"}:
        # DOI and repository URL patterns
        url_patterns = [
            r'(?:https?://)?(?:dx\.)?doi\.org/[^\s,]+',
            r'doi:\s*[^\s,]+',
            r'(?:https?://)?(?:www\.)?zenodo\.org/[^\s,]+',
            r'(?:https?://)?(?:www\.)?figshare\.com/[^\s,]+',
            r'(?:https?://)?(?:www\.)?dryad\.org/[^\s,]+',
            r'(?:https?://)?github\.com/[^\s,]+',
        ]
        for pattern in url_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

    if entity_type in {"all", "la-ur"}:
        # LA-UR release numbers
        laur_patterns = [
            r'LA-UR-\d{2}-\d{4,5}',
            r'LA-UR\s+\d{2}-\d{4,5}',
        ]
        for pattern in laur_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

    return ", ".join(set(entities[:5])) if entities else ""


def _extract_sentences_with_keywords(text: str, keywords: list[str], max_sentences: int = 2) -> str:
    """Extract sentences containing specific keywords."""
    if not text or not keywords:
        return ""

    sentences = re.split(r'[.!?]+', text)
    relevant = []

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', sentence, re.IGNORECASE):
                relevant.append(sentence)
                break
        if len(relevant) >= max_sentences:
            break

    return ". ".join(relevant) + "." if relevant else ""


def _smart_extract_for_field(qid: str, all_text: str, theme_text: str = "") -> tuple[str, str, str]:
    """
    Intelligently extract relevant information for a specific field.
    Returns: (extracted_text, confidence, rationale)
    """
    combined = f"{all_text}\n{theme_text}".strip()

    # Section 3: Composition
    if qid == "s3.1":  # What instances represent
        keywords = ["instance", "record", "sample", "measurement",
                    "observation", "image", "document", "represent"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        if extract:
            return extract, "medium", "Extracted sentences describing instance types"
        return "", "low", "No clear instance description found"

    elif qid == "s3.2":  # How many instances
        numbers = _extract_numbers(combined)
        if numbers:
            return numbers, "high", "Extracted numerical counts from source"
        return "", "low", "No instance counts found"

    elif qid == "s3.3":  # Sample or complete set
        keywords = ["sample", "subset", "complete",
                    "representative", "population", "coverage"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted sampling information" if extract else "No sampling details found"

    elif qid == "s3.4":  # Data content per instance
        keywords = ["format", "structure", "feature", "column",
                    "field", "raw", "processed", "CSV", "JSON", "HDF5"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted data format description" if extract else "No format details found"

    elif qid == "s3.5":  # Labels/targets
        keywords = ["label", "target", "ground truth",
                    "annotation", "class", "category", "supervised"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted label information" if extract else "No label information found"

    elif qid == "s3.6":  # Missing information
        keywords = ["missing", "incomplete", "unavailable",
                    "redacted", "omitted", "excluded"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted missingness details" if extract else "No missingness information"

    elif qid == "s3.7":  # Relationships
        keywords = ["relationship", "link", "connection",
                    "network", "graph", "edge", "interaction"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted relationship information" if extract else "No relationship details"

    elif qid == "s3.8":  # Bias/imbalance
        keywords = ["bias", "imbalance", "skew",
                    "distribution", "unbalanced", "representative"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted bias information" if extract else "No bias details found"

    elif qid == "s3.9":  # Errors/noise
        keywords = ["error", "noise", "quality", "artifact",
                    "redundancy", "duplicate", "accuracy"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted error information" if extract else "No error details found"

    # Section 2: Motivation
    elif qid == "s2.2":  # Who created
        entities = _extract_entities(combined, "institution")
        if entities:
            return entities, "high", "Extracted institution names"
        keywords = ["team", "group", "laboratory",
                    "department", "created by", "developed by"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted creator information" if extract else "No creator details found"

    elif qid == "s2.3":  # Funding
        grants = _extract_entities(combined, "grant")
        if grants:
            return grants, "high", "Extracted grant/funding identifiers"
        keywords = ["fund", "grant", "contract", "support", "sponsor", "award"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted funding information" if extract else "No funding details found"

    elif qid == "s2.4":  # Facility/campaign
        keywords = ["facility", "campaign", "proposal",
                    "experiment", "beamline", "instrument"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted facility information" if extract else "No facility details found"

    # Section 4: Collection
    elif qid == "s4.1":  # Acquisition method
        keywords = ["acquire", "collect", "measure", "record",
                    "capture", "generate", "obtain", "method"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted acquisition method" if extract else "No acquisition details found"

    elif qid == "s4.2":  # Instruments
        instruments = _extract_entities(combined, "instrument")
        if instruments:
            return instruments, "high", "Extracted instrument names"
        keywords = ["instrument", "equipment", "apparatus",
                    "sensor", "detector", "spectrometer"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted instrument information" if extract else "No instrument details found"

    elif qid == "s4.7":  # Timeframe
        dates = _extract_numbers(combined)  # Will catch year patterns
        if dates and re.search(r'\d{4}', dates):
            return dates, "high", "Extracted temporal information"
        keywords = ["year", "period", "timeframe",
                    "duration", "between", "from", "to"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted timeframe" if extract else "No timeframe found"

    # Section 5: Preprocessing
    elif qid == "s5.1":  # Preprocessing steps
        keywords = ["preprocess", "clean", "filter", "normalize",
                    "transform", "quality control", "validation"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted preprocessing details" if extract else "No preprocessing details found"

    elif qid == "s5.2":  # Raw data retention
        keywords = ["raw", "original", "unprocessed",
                    "retain", "archive", "preserve"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        return extract, "low", "Extracted raw data info" if extract else "No raw data retention info"

    elif qid == "s5.3":  # Software availability
        keywords = ["software", "code", "script", "tool",
                    "pipeline", "available", "repository"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted software info" if extract else "No software availability info"

    elif qid == "s5.4":  # Base dataset lineage
        keywords = ["based on", "derived from", "extension", "subset",
                    "extracted from", "parent dataset", "source dataset"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted lineage info" if extract else "No base dataset mentioned"

    # Section 4 additional fields
    elif qid == "s4.3":  # Current data generation
        keywords = ["currently", "ongoing", "data rate", "frequency", "cadence",
                    "generate", "produced", "per day", "per month", "continuous"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted ongoing generation info" if extract else "No current generation details"

    elif qid == "s4.4":  # Future data generation access
        keywords = ["future", "request", "proposal", "access", "timeline",
                    "process", "how to", "allocation", "beamtime"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted future access info" if extract else "No future access details"

    elif qid == "s4.5":  # Sampling strategy
        keywords = ["sample", "sampling", "selection", "strategy", "random",
                    "deterministic", "probabilistic", "criteria"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted sampling details" if extract else "No sampling strategy found"

    elif qid == "s4.6":  # Personnel and compensation
        keywords = ["collect", "team", "personnel", "staff", "student",
                    "contractor", "crowd", "compensat", "paid"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted personnel info" if extract else "No personnel details"

    elif qid == "s4.8":  # Ethical review
        keywords = ["ethical", "IRB", "review", "ethics", "approval",
                    "institutional review board", "human subjects"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted ethical review info" if extract else "No ethical review mentioned"

    elif qid == "s4.9":  # Safety/cybersecurity reviews
        keywords = ["safety", "security", "cyber", "export control",
                    "classification", "review", "cleared", "approved"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted safety review info" if extract else "No safety reviews mentioned"

    # Section 6: Uses
    elif qid == "s6.2":  # Repository links
        urls = _extract_entities(combined, "url")
        keywords = ["repository", "papers",
                    "publications", "citations", "uses"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        if urls:
            return f"{extract} {urls}".strip(), "high", "Extracted repository URLs"
        return extract, "low", "Extracted repository info" if extract else "No repository mentioned"

    elif qid == "s6.3":  # Future uses and limitations
        keywords = ["could be used", "future", "potential", "application",
                    "should not", "limitation", "restriction", "appropriate for"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted future use info" if extract else "No future use details"

    elif qid == "s6.5":  # AI-readiness
        keywords = ["AI", "machine learning", "ML", "trained", "model",
                    "ready", "format", "tensor", "numpy", "pandas"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted AI-readiness info" if extract else "No AI-readiness details"

    elif qid == "s6.7":  # Partitioning recommendations
        keywords = ["partition", "split", "train", "test", "validation",
                    "development", "hold-out", "cross-validation", "fold"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted partitioning info" if extract else "No partitioning guidance"

    # Section 7: Distribution
    elif qid == "s7.3":  # Distribution timing
        dates = _extract_numbers(combined)
        keywords = ["available", "released", "published", "when", "date",
                    "planned", "expected", "already", "currently"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        if dates and re.search(r'\d{4}', dates):
            extract = f"{extract} {dates}".strip()
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted timing info" if extract else "No timing details"

    elif qid == "s7.4":  # License/ToU
        keywords = ["license", "terms", "copyright", "IP", "intellectual property",
                    "CC-BY", "MIT", "Apache", "proprietary", "citation required"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        urls = _extract_entities(combined, "url")
        if "license" in urls.lower():
            extract = f"{extract} {urls}".strip()
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted license info" if extract else "No license details"

    elif qid == "s7.6": # classification
        keywords = ["classification"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted classification" if extract else "No classification level"

    elif qid == "s7.7":  # License and reuse requirements
        keywords = ["license", "reuse", "require", "must", "attribution",
                    "derivative", "commercial", "non-commercial"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted reuse requirements" if extract else "No reuse details"

    # Section 8: Maintenance
    elif qid == "s8.3":  # Erratum
        keywords = ["erratum", "errata", "correction", "error report",
                    "known issue", "bug tracker"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        urls = _extract_entities(combined, "url")
        if "issue" in urls.lower() or "erratum" in urls.lower():
            extract = f"{extract} {urls}".strip()
        return extract, "low", "Extracted erratum info" if extract else "No erratum mentioned"

    elif qid == "s8.4":  # Update cadence
        keywords = ["update", "maintain", "refresh", "cadence", "frequency",
                    "monthly", "quarterly", "annually", "continuous"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        conf = "medium" if extract else "low"
        return extract, conf, "Extracted update info" if extract else "No update cadence"

    elif qid == "s8.6":  # Older version support
        keywords = ["older", "previous", "version", "archive", "legacy",
                    "deprecated", "supported", "maintained"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted version support info" if extract else "No version support details"

    elif qid == "s8.7":  # Obsolescence
        keywords = ["obsolete", "expir", "shelf life", "validity",
                    "useful", "deprecat", "end of life"]
        extract = _extract_sentences_with_keywords(combined, keywords, 1)
        return extract, "low", "Extracted obsolescence info" if extract else "No obsolescence details"

    elif qid == "s8.8":  # Contributions
        keywords = ["contribute", "extend", "augment", "add", "submit",
                    "pull request", "mechanism", "process"]
        extract = _extract_sentences_with_keywords(combined, keywords, 2)
        return extract, "low", "Extracted contribution info" if extract else "No contribution process"

    # Default: return empty with guidance
    return "", "low", f"No specific extraction logic for {qid}"


def heuristic_autofill(
    row: dict[str, Any],
    sections: list[dict[str, Any]],
    clarifications: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = _base_payload()
    theme_answers = _normalize_clarifications(clarifications)
    context = _build_context(row, theme_answers)
    purpose = theme_answers.get("purpose_and_use", {}).get("answer", "")
    composition = theme_answers.get(
        "composition_and_structure", {}).get("answer", "")
    ownership = theme_answers.get(
        "ownership_funding_initiative", {}).get("answer", "")
    provenance = theme_answers.get(
        "provenance_and_review", {}).get("answer", "")
    restrictions = theme_answers.get(
        "restrictions_distribution_licensing", {}).get("answer", "")
    lifecycle = theme_answers.get(
        "maintenance_and_lifecycle", {}).get("answer", "")
    project_name = str(row.get("project_name", "") or "").strip()
    project_description = str(row.get("project_description", "") or "").strip()
    data_composition = str(row.get("data_composition", "") or "").strip()
    project_url = str(row.get("project_url", "") or "").strip()

    if not purpose:
        purpose = project_description
    if not composition:
        composition = _join_nonempty(
            [data_composition, project_description], sep="\n\n")
    if not restrictions:
        restrictions = _join_nonempty(
            [project_url, data_composition], sep="\n\n")

    ownership_context = context["ownership_context"]
    facility_context = context["facility_context"]
    # governance_context = context["governance_context"]

    # Enhanced DOI/URL extraction
    all_source_text = _join_nonempty(
        [project_url, restrictions, composition], sep="\n\n")
    doi_extract = _extract_entities(all_source_text, "doi")
    if doi_extract:
        payload["fields"]["s1.1"] = _field_from_text(
            doi_extract,
            rationale="Extracted DOI or repository URL using pattern matching",
            confidence="high")
    else:
        payload["fields"]["s1.1"] = _field_from_text(
            _pick_line(project_url, fallback=_pick_line(restrictions)),
            rationale="Citation or access-link information is inferred from the verbose URL field and the restrictions and distribution clarification bundle.",
            empty_status="needs_user",
            confidence="low",
        )
    # s1.2 - Optional field, leave empty
    payload["fields"]["s1.2"] = _field_from_text(
        "",
        rationale="Datasheet citation field left empty (optional field).",
        empty_status="unknown",
        confidence="low",
    )

    # s1.3 - Extract contact from app_contact only
    app_contact = str(row.get("primary_contact", "") or "").strip()
    detective_contacts = _extract_contacts(app_contact)
    payload["fields"]["s1.3"] = _field_from_text(
        detective_contacts if detective_contacts else app_contact,
        rationale="Data detective contact extracted from App Contact Person field.",
        empty_status="needs_user",
        confidence="high" if detective_contacts else "medium",
    )

    # s1.4 - Extract contacts from data_owner only (no governance context)
    steward_contacts_text = str(row.get("data_owner", "") or "").strip()
    steward_contacts = _extract_contacts(steward_contacts_text)
    payload["fields"]["s1.4"] = _field_from_text(
        steward_contacts if steward_contacts else steward_contacts_text,
        rationale="Data steward contacts extracted from Metadata Team and DSI Contact Person fields.",
        empty_status="needs_user",
        confidence="high" if steward_contacts else "medium",
    )

    # s1.5 - Populate table with today's date and author from app_contact
    from datetime import date
    author_name = _extract_contacts(app_contact) or app_contact or "Unknown"
    # Extract just the name without email if present
    if "(" in author_name:
        author_name = author_name.split("(")[0].strip()

    s15_table = [{
        "version": "1.0",
        "date": date.today().strftime("%Y-%m-%d"),
        "author": author_name,
        "description": "Initial datasheet version"
    }]
    payload["fields"]["s1.5"] = _field(
        json.dumps(s15_table),
        status="filled",
        confidence="high",
        rationale="Generated datasheet version table with current date and author from App Contact Person.",
        source="heuristic",
    )

    # Section 2: Extract specific information from descriptions

    # s2.1 - Extract PURPOSE sentences (scientific objective, not funding)
    # Split description into paragraphs to avoid funding acknowledgments
    desc_paragraphs = [p.strip()
                       for p in project_description.split('\n\n') if p.strip()]

    # Focus on first paragraphs (usually contain scientific purpose)
    # Skip acknowledgment paragraphs (typically contain "supported by", "funded by")
    purpose_text = ""
    for para in desc_paragraphs[:3]:  # Check first 3 paragraphs
        # Skip if this is a funding/acknowledgment paragraph
        if re.search(r'\b(supported by|funded by|based upon work|award number|grant|contract)\b', para, re.IGNORECASE):
            continue
        purpose_text = para
        break

    if not purpose_text and purpose:
        purpose_text = purpose
    elif not purpose_text and desc_paragraphs:
        purpose_text = desc_paragraphs[0]  # Fallback to first paragraph

    # Extract key sentences about purpose, objectives, and methodology
    purpose_keywords = ["purpose", "goal", "objective", "designed", "test", "examine",
                        "investigate", "demonstrate", "show that", "capability", "task"]
    purpose_sentences = []

    for sentence in re.split(r'[.!?]+', purpose_text):
        sentence = sentence.strip()
        if not sentence:
            continue
        # Include sentences with purpose keywords OR sentences about methodology/task
        has_keyword = any(re.search(r'\b' + kw + r'\b', sentence,
                          re.IGNORECASE) for kw in purpose_keywords)
        has_method = re.search(
            r'\b(data|analyze|using|machine learning|experiment|test)\b', sentence, re.IGNORECASE)

        if has_keyword or (has_method and len(purpose_sentences) > 0):
            purpose_sentences.append(sentence)
            if len(purpose_sentences) >= 3:  # Limit to 3 key sentences
                break

    purpose_extract = ". ".join(purpose_sentences) + \
        "." if purpose_sentences else purpose_text

    payload["fields"]["s2.1"] = _field_from_text(
        purpose_extract,
        rationale="Extracted scientific purpose, objectives, and methodology from project description (excluding funding acknowledgments).",
        confidence="medium" if purpose_sentences else "low",
    )

    # s2.2 - Extract TEAM/INSTITUTION (organizational unit + institution)
    # Look for organizational codes (e.g., "CLES EES 17") or division names
    all_ownership_text = _join_nonempty(
        [ownership_context, ownership, project_description], sep="\n\n")

    # Pattern for organizational units: letters/numbers + "at" + institution
    org_pattern = r'\b([A-Z]{2,}(?:\s+[A-Z]{2,})?(?:\s+\d+)?)\s+at\s+(Los Alamos National Laboratory|LANL)'
    org_match = re.search(org_pattern, all_ownership_text, re.IGNORECASE)

    if org_match:
        team_extract = f"{org_match.group(1)} at {org_match.group(2)}"
        conf = "high"
    else:
        # Fallback to institution extraction
        team_extract = _extract_entities(all_ownership_text, "institution")
        if not team_extract:
            extract, conf, rat = _smart_extract_for_field(
                "s2.2", all_ownership_text, ownership)
            team_extract = extract
            conf = conf if extract else "low"
        else:
            conf = "medium"

    payload["fields"]["s2.2"] = _field_from_text(
        team_extract,
        rationale="Extracted team organizational unit and institution from project context.",
        confidence=conf,
        empty_status="needs_user",
    )

    # s2.3 - Extract FUNDING (agencies and award numbers only)
    funding_extract = _extract_entities(
        _join_nonempty([all_ownership_text, ownership], sep="\n\n"), "funding")

    if not funding_extract:
        extract, conf, rat = _smart_extract_for_field(
            "s2.3", all_ownership_text, ownership)
        funding_extract = extract
        conf = conf if extract else "low"
    else:
        conf = "high"

    payload["fields"]["s2.3"] = _field_from_text(
        funding_extract,
        rationale="Extracted funding sources and award identifiers.",
        confidence=conf,
        empty_status="needs_user",
    )

    # s2.4 - Detect user facility and ask for clarification if found
    facility_keywords = ["user facility", "scientific user facility", "facility proposal",
                         "beamtime", "beam time", "proposal number"]
    has_facility = any(re.search(r'\b' + kw + r'\b', _join_nonempty(
        [facility_context, project_description, ownership], sep="\n\n"), re.IGNORECASE)
        for kw in facility_keywords)

    if has_facility:
        # Extract facility/proposal details
        extract, conf, rat = _smart_extract_for_field(
            "s2.4", facility_context, ownership)
        payload["fields"]["s2.4"] = _field_from_text(
            extract if extract else "Data may have been collected at a scientific user facility",
            rationale="Detected potential user facility involvement. User clarification recommended.",
            confidence="medium" if extract else "low",
            empty_status="needs_user",
        )
        # Add follow-up question if not already answered
        facility_question = "Was this dataset created at a scientific user facility? If yes, please provide facility name, proposal number, and any relevant campaign identifiers."
        if facility_question not in payload.get("followup_questions", []):
            payload.setdefault("followup_questions", []
                               ).append(facility_question)
    else:
        payload["fields"]["s2.4"] = _field_from_text(
            "",
            rationale="No user facility involvement detected. Field left empty.",
            confidence="medium",
            empty_status="unknown",
        )

    # s2.5 - Extract INITIATIVE (program membership)
    initiative_keywords = ["program", "initiative", "campaign", "project", "effort",
                           "collaboration", "consortium", "part of", "under"]
    initiative_extract = _extract_sentences_with_keywords(
        ownership, initiative_keywords, 2)

    payload["fields"]["s2.5"] = _field_from_text(
        initiative_extract,
        rationale="Extracted initiative membership from ownership clarification.",
        confidence="medium" if initiative_extract else "low",
        empty_status="unknown",
    )
    # s2.6 - Additional comments, leave empty for user input
    payload["fields"]["s2.6"] = _field_from_text(
        "",
        rationale="Additional comments field left empty for user to manually add context.",
        empty_status="unknown",
        confidence="low",
    )

    # Section 3: Use smart extraction for composition fields
    all_composition_text = _join_nonempty(
        [data_composition, project_description], sep="\n\n")

    for qid in ["s3.1", "s3.2", "s3.3", "s3.4", "s3.5", "s3.6", "s3.7", "s3.8", "s3.9"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_composition_text, composition)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="needs_user",
        )
    payload["fields"]["s3.10"] = _field_from_text(
        restrictions,
        rationale="External dependencies and access-link details are inferred from the restrictions and distribution clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )
    payload["fields"]["s3.11"] = _field_from_text(
        restrictions,
        rationale="Confidentiality and controlled-access information are inferred from the restrictions and distribution clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )
    payload["fields"]["s3.12"] = _field_from_text(
        restrictions,
        rationale="Restriction and distribution language supplies export-control and legal-combination details.",
        confidence="low",
        empty_status="unknown",
    )
    payload["fields"]["s3.13"] = _field_from_text(
        composition,
        rationale="Subpopulation details are expected from the composition clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )
    payload["fields"]["s3.14"] = _field_from_text(
        restrictions,
        rationale="Identifiability risks are expected from the restrictions and distribution clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )
    payload["fields"]["s3.15"] = _field_from_text(
        restrictions,
        rationale="Sensitive-data details are expected from the restrictions and distribution clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )
    # s3.16 - Additional comments, leave empty for user input
    payload["fields"]["s3.16"] = _field_from_text(
        "",
        rationale="Additional comments field left empty for user to manually add context.",
        confidence="low",
        empty_status="unknown",
    )

    # Section 4: Use smart extraction for collection/provenance fields
    all_provenance_text = _join_nonempty(
        [facility_context, provenance], sep="\n\n")

    # Core collection fields with smart extraction
    for qid in ["s4.1", "s4.2", "s4.3", "s4.5", "s4.6", "s4.7"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_provenance_text, provenance)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="needs_user",
        )

    # Future access field (s4.4) - often empty, set to unknown
    extract, conf, rat = _smart_extract_for_field(
        "s4.4", all_provenance_text, provenance)
    payload["fields"]["s4.4"] = _field_from_text(
        extract,
        rationale=rat,
        confidence=conf,
        empty_status="unknown",
    )

    # Review/ethics fields (s4.8, s4.9) - use smart extraction
    for qid in ["s4.8", "s4.9"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_provenance_text, provenance)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="unknown",
        )

    # Direct vs third-party, notice, consent fields (s4.10-s4.13) - typically empty
    for qid in ["s4.10", "s4.11", "s4.12", "s4.13", "s4.14"]:
        payload["fields"][qid] = _field_from_text(
            "",
            rationale=f"No {qid} information found in provenance context.",
            confidence="low",
            empty_status="unknown",
        )

    # s4.15 - Additional comments, leave empty to avoid redundancy
    payload["fields"]["s4.15"] = _field_from_text(
        "",
        rationale="Additional comments field left empty to avoid redundancy with specific collection fields.",
        confidence="low",
        empty_status="unknown",
    )

    # Section 5: Use smart extraction for preprocessing fields
    for qid in ["s5.1", "s5.2", "s5.3", "s5.4"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_provenance_text, provenance)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="needs_user" if qid in [
                "s5.1", "s5.4"] else "unknown",
        )

    # s5.5 - Additional comments, leave empty to avoid redundancy
    payload["fields"]["s5.5"] = _field_from_text(
        "",
        rationale="Additional preprocessing comments left empty to avoid redundancy with specific preprocessing fields.",
        confidence="low",
        empty_status="unknown",
    )

    # Section 6: Uses - combine purpose and lifecycle context
    all_use_text = _join_nonempty(
        [purpose, project_url, lifecycle], sep="\n\n")

    payload["fields"]["s6.1"] = _field_from_text(
        purpose,
        rationale="Prior or intended uses come from the purpose and intended use clarification bundle.",
    )

    # Use smart extraction for specific use fields
    for qid in ["s6.2", "s6.3", "s6.5", "s6.7"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_use_text, _join_nonempty([purpose, composition], sep="\n\n"))
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="unknown" if qid in [
                "s6.2", "s6.7"] else "needs_user",
        )

    payload["fields"]["s6.4"] = _field_from_text(
        composition,
        rationale="Risks from composition or collection are expected from the composition clarification bundle.",
        confidence="low",
    )
    payload["fields"]["s6.6"] = _field_from_text(
        _join_nonempty([project_url, lifecycle], sep="\n\n"),
        rationale="Tutorials and support information are inferred from the verbose URL field and the maintenance and lifecycle clarification bundle.",
        confidence="low",
        empty_status="unknown",
    )

    # s6.8 - Additional comments, leave empty to avoid redundancy
    payload["fields"]["s6.8"] = _field_from_text(
        "",
        rationale="Additional use-case comments left empty to avoid redundancy with specific use fields.",
        confidence="low",
        empty_status="unknown",
    )

    payload["fields"]["s7.1"] = _field_from_text(
        restrictions,
        rationale="Third-party distribution details come from the restrictions and distribution clarification bundle.",
        confidence="low",
    )
    # Enhanced distribution/DOI extraction for s7.2
    distribution_text = _join_nonempty(
        [project_url, restrictions, composition], sep="\n\n")
    dist_doi = _extract_entities(distribution_text, "doi")
    if dist_doi:
        payload["fields"]["s7.2"] = _field_from_text(
            f"Publicly available via: {dist_doi}",
            rationale="Extracted repository URL or DOI using pattern matching",
            confidence="high")
    else:
        payload["fields"]["s7.2"] = _field_from_text(
            distribution_text,
            rationale="Distribution channels, DOI, or repository links come from the verbose URL field and the restrictions and distribution clarification bundle.",
            confidence="low",
        )
    # Use smart extraction for distribution timing and license fields
    all_distribution_text = _join_nonempty(
        [project_url, project_description, restrictions], sep="\n\n")

    for qid in ["s7.3", "s7.4", "s7.7"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_distribution_text, restrictions)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="unknown" if qid == "s7.3" else "needs_user",
        )

    payload["fields"]["s7.5"] = _field_from_text(
        restrictions,
        rationale="Third-party restriction details come from the restrictions and distribution clarification bundle.",
        confidence="low",
    )

    # Enhanced LA-UR detection for s7.6
    laur_extract = _extract_entities(
        _join_nonempty([restrictions, ownership, project_description], sep="\n\n"), "la-ur")
    if laur_extract:
        payload["fields"]["s7.6"] = _field_from_text(
            f"Public release approved: {laur_extract}",
            rationale="Detected LA-UR release number indicating public release approval",
            confidence="high")
        # Add follow-up about data access since LA-UR indicates public release
        if "restrictions_distribution_licensing" not in [q.split(":")[0] for q in payload.get("followup_questions", [])]:
            payload["followup_questions"].insert(
                0, THEME_TO_PROMPT["restrictions_distribution_licensing"])
    else:
        payload["fields"]["s7.6"] = _field_from_text(
            restrictions,
            rationale="Export-control and classification details come from the restrictions and distribution clarification bundle.",
            confidence="low",
        )

    # s7.8 - Additional comments, leave empty to avoid redundancy
    payload["fields"]["s7.8"] = _field_from_text(
        "",
        rationale="Additional distribution comments left empty to avoid redundancy with specific distribution fields.",
        confidence="low",
        empty_status="unknown",
    )

    # Section 8: Maintenance - combine ownership and lifecycle context
    all_maintenance_text = _join_nonempty(
        [ownership_context, ownership, lifecycle], sep="\n\n")

    # s8.1, s8.2 - Contact fields, extract contact names and emails only
    ownership_contacts = _extract_contacts(all_maintenance_text)
    payload["fields"]["s8.1"] = _field_from_text(
        ownership_contacts,
        rationale="Extracted contact names and emails for maintenance ownership from Section 0 contacts and clarifications.",
        confidence="medium" if ownership_contacts else "low",
        empty_status="needs_user",
    )
    payload["fields"]["s8.2"] = _field_from_text(
        ownership_contacts,
        rationale="Extracted contact path from Section 0 ownership contacts and clarifications.",
        confidence="medium" if ownership_contacts else "low",
        empty_status="needs_user",
    )

    # Use smart extraction for specific maintenance fields
    for qid in ["s8.3", "s8.4", "s8.6", "s8.7", "s8.8"]:
        extract, conf, rat = _smart_extract_for_field(
            qid, all_maintenance_text, lifecycle)
        payload["fields"][qid] = _field_from_text(
            extract,
            rationale=rat,
            confidence=conf,
            empty_status="unknown" if qid in [
                "s8.3", "s8.6", "s8.7"] else "needs_user",
        )

    # s8.5 - Retention limits (combine restrictions and lifecycle)
    retention_text = _join_nonempty([restrictions, lifecycle], sep="\n\n")
    extract, conf, rat = _smart_extract_for_field(
        "s8.5", retention_text, lifecycle)
    payload["fields"]["s8.5"] = _field_from_text(
        extract,
        rationale=rat,
        confidence=conf,
        empty_status="unknown",
    )

    # s8.9 - Additional comments, leave empty to avoid redundancy
    payload["fields"]["s8.9"] = _field_from_text(
        "",
        rationale="Additional maintenance comments left empty to avoid redundancy with specific maintenance fields.",
        confidence="low",
        empty_status="unknown",
    )

    if project_name:
        payload["notes"].append(f"Project context: {project_name}")
    if theme_answers:
        payload["notes"].append("Bundled clarification answers were applied.")
    payload["followup_questions"] = build_followup_questions(
        row, payload, sections)
    payload["themes"] = {
        theme: _theme_status(theme, payload["fields"], theme_answers)
        for theme in THEME_TO_FIELDS
    }
    return payload


def _build_ursa_prompt(
    row: dict[str, Any],
    sections: list[dict[str, Any]],
    clarifications: dict[str, str] | None,
) -> str:
    catalog = build_question_catalog(sections)
    theme_answers = _normalize_clarifications(clarifications)
    targets = []
    for qid, meta in catalog.items():
        if meta["section_idx"] == 0:
            continue
        themes = ",".join(FIELD_TO_THEMES.get(qid, []))
        detail = f" themes={themes}" if themes else ""
        if meta["type"] == "table":
            targets.append(
                f"{qid} ({meta['type']},{'required' if meta['required'] else 'optional'}{detail})")
        else:
            targets.append(
                f"{qid} ({'required' if meta['required'] else 'optional'}{detail}): {meta['label']}")

    clarification_blob = _clarification_blob(theme_answers)

    return (
        "You are a scientist or engineer working at Los Alamos National Laboratory completing a datasheet for scientific datasets. "
        "The input may come from peer-reviewed manuscripts (abstracts, methods, acknowledgments), "
        "technical reports, experiment documentation, or project summaries.\n\n"

        "# CRITICAL PARSING RULES\n\n"

        "1. EXTRACT SPECIFIC INFORMATION: Each question requires targeted, specific information. "
        "Do NOT copy entire paragraphs verbatim. Instead, identify and extract only the relevant facts.\n\n"

        "2. EACH ANSWER MUST BE UNIQUE: Every field should have a distinct answer tailored to that question. "
        "If multiple questions relate to similar themes, rephrase and focus each answer appropriately.\n\n"

        "3. PARSE BY DOCUMENT STRUCTURE: Identify where information appears in the source:\n"
        "   - Abstract/Summary → purpose (s2.1), intended use (s6.1)\n"
        "   - Methods section → data collection (s4.1, s4.2), preprocessing (s5.1)\n"
        "   - Data description → composition (s3.1-3.9), structure, formats\n"
        "   - Acknowledgments → funding (s2.3), institutions (s2.2)\n"
        "   - References/URLs → citations (s1.1), licenses (s7.4, s7.7)\n\n"

        "4. FIELD-SPECIFIC EXTRACTION EXAMPLES:\n"
        "   - s1.4 (data steward): Extract data steward information from SECTION 0 INTAKE's value for the 'data owner' key.\n"
        "   - s3.1 (what instances represent): Extract ONLY entity types, e.g., 'spectroscopic measurements of materials' not full description\n"
        "   - s3.2 (instance count): Extract ONLY numbers/approximations, e.g., '~10,000 samples' not methodological context\n"
        "   - s3.4 (data content): Extract ONLY format/structure, e.g., 'CSV files with 50 features per row' not motivation\n"
        "   - s4.1 (acquisition method): Extract ONLY collection process, e.g., 'automated sensor readings' not purpose\n"
        "   - s4.2 (instruments): Extract ONLY equipment names, e.g., 'Bruker XRD spectrometer' not full protocol\n"
        "   - s2.3 (funding): Extract ONLY grant info, e.g., 'NSF Grant #12345, DOE Contract DE-AC52' not team details\n"
        "   - s7.6 (data classification): Extract classification from SECTION 0 INTAKE's value for the 'classification' key.\n"
        "   - s8.2 (data owner contact): Extract from SECTION 0 INTAKE's value for the 'primary_contact' key if contact details specified.\n\n"

        "5. ANTI-REPETITION CHECKS:\n"
        "   - If composition fields (s3.1-s3.16) start looking identical, you're copying too much\n"
        "   - If collection fields (s4.1-s4.15) repeat the same text, extract more specifically\n"
        "   - Section 3 should describe DATA CONTENT, not methodology or purpose\n"
        "   - Section 4 should describe COLLECTION PROCESS, not data characteristics\n\n"

        "6. CONFIDENCE SCORING:\n"
        "   - HIGH: Extracted specific fact directly stated (number, institution name, instrument model)\n"
        "   - MEDIUM: Inferred from context with reasonable certainty\n"
        "   - LOW: Uncertain extraction or broad inference; prefer 'needs_user' status\n\n"

        "7. STATUS ASSIGNMENT:\n"
        "   - 'filled': Confident answer extracted from source material\n"
        "   - 'needs_user': Insufficient evidence in source, user clarification required\n"
        "   - 'unknown': Field not applicable or no relevant information available\n\n"

        "# EXAMPLE TRANSFORMATION\n\n"
        "BAD (verbatim copying):\n"
        "  s3.1: 'This dataset contains spectroscopic measurements collected at LANL for machine learning applications...'\n"
        "  s3.2: 'This dataset contains spectroscopic measurements collected at LANL for machine learning applications...'\n"
        "  s3.4: 'This dataset contains spectroscopic measurements collected at LANL for machine learning applications...'\n\n"

        "GOOD (targeted extraction):\n"
        "  s3.1: 'Spectroscopic measurement records, each representing X-ray diffraction patterns from material samples'\n"
        "  s3.2: 'Approximately 12,000 measurement instances across 150 material types'\n"
        "  s3.4: 'Raw spectroscopic data as HDF5 files containing intensity arrays (2048 channels) and metadata'\n\n"

        "# CLARIFICATION DECOMPOSITION\n\n"
        "CRITICAL: Thematic clarifications contain information for MULTIPLE fields. You MUST decompose them.\n\n"

        "Example clarification (ownership/funding theme):\n"
        "  'This material is based upon work supported by the U.S. Department of Energy, Office of Science, "
        "Office of Basic Energy Sciences, Geosciences program under Award Number LANL0123 to support CWJ. "
        "Research was supported by LDRD program under project number 20203210ER.'\n\n"

        "DECOMPOSE TO:\n"
        "  s2.2 (team): 'Christopher W Johnson (Los Alamos National Laboratory)'\n"
        "  s2.3 (funding): 'U.S. Department of Energy, Office of Science, Office of Basic Energy Sciences, "
        "Geosciences program, Award Number LANL0123; LANL LDRD program, project 20203210ER'\n"
        "  s1.3 (detective): 'Christopher W Johnson (contact email if provided)'\n\n"

        "Example clarification (composition theme):\n"
        "  'Data is DAS records from lab experiments to estimate permeability from flow noise. Size is about 50 Gb. "
        "Format is float64 in HDF5. Labels are flow rates. No preprocessing. No known errors. "
        "Data at https://doi.org/10.5281/zenodo.15360514'\n\n"

        "DECOMPOSE TO:\n"
        "  s3.1 (instances): 'DAS records from laboratory experiments to estimate permeability from flow noise'\n"
        "  s3.2 (count): 'Approximately 50 GB of data'\n"
        "  s3.4 (format): 'float64 arrays stored in HDF5 format'\n"
        "  s3.5 (labels): 'Flow rates included in HDF5 organization'\n"
        "  s5.1 (preprocessing): 'No preprocessing performed on raw data'\n"
        "  s3.9 (errors): 'No known errors or quality issues'\n"
        "  s1.1 (citation): 'https://doi.org/10.5281/zenodo.15360514'\n"
        "  s7.2 (distribution): 'Publicly available via Zenodo at https://doi.org/10.5281/zenodo.15360514'\n\n"

        "DECOMPOSITION RULES:\n"
        "1. Parse clarifications sentence-by-sentence to identify which field each piece answers\n"
        "2. Extract ONLY relevant portions - DO NOT copy entire clarification text\n"
        "3. Rewrite appropriately (e.g., 'Size is 50 Gb' → 'Approximately 50 GB' for s3.2)\n"
        "4. Route information to ALL applicable fields - one clarification often answers 5-10 questions\n"
        "5. DOIs/URLs populate: s1.1 (citation), s7.2 (distribution), s6.2 (papers)\n"
        "6. Funding with agency + award goes to s2.3 (keep both sponsor name AND number)\n"
        "7. Team/contact names go to s2.2, s1.3, s1.4, s8.1, s8.2 as appropriate\n"
        "8. LA-UR numbers indicate public release - populate s7.6 and generate follow-up about data access\n\n"

        "# YOUR TASK\n\n"
        "Parse the Section 0 intake and clarifications below. Extract specific, targeted information for each field. "
        "Ensure every answer is unique and addresses only that specific question.\n\n"

        "Return JSON only with this shape:\n"
        "{\n"
        '  "fields": {\n'
        '    "s2.1": {"answer": "...", "status": "filled|needs_user|unknown", "confidence": "high|medium|low", "rationale": "..."}\n'
        "  },\n"
        '  "followup_questions": ["..."],\n'
        '  "themes": {"purpose_and_use": {"unresolved_fields": ["s2.1"]}}\n'
        "}\n\n"
        "# THEME PROMPTS\n\n"
        + "\n".join(f"- {theme}: {prompt}" for theme,
                    prompt in THEME_TO_PROMPT.items())
        + "\n\n# TARGET FIELDS\n\n"
        + "\n".join(targets)
        + "\n\n# SECTION 0 INTAKE\n\n"
        + _compose_intake_context(row)
        + ("\n\n# THEMATIC CLARIFICATIONS\n\n" +
           clarification_blob if clarification_blob else "")
    )


def _run_ursa_autofill(
    *,
    diana_dir: str,
    row: dict[str, Any],
    sections: list[dict[str, Any]],
    clarifications: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run metadata extraction using ChatAgent with conversation state.
    Maintains context across initial autofill and follow-up clarifications.
    """
    # Build extraction prompt with original context + any clarifications
    user_prompt = _build_ursa_prompt(row, sections, clarifications)

    payload = run_ursa_agent(diana_dir, user_prompt)

    # Ensure required structure
    payload.setdefault("fields", {})
    payload.setdefault("followup_questions", [])
    payload.setdefault("themes", {})
    payload["source"] = "ursa_chat_agent"

    # Normalize field metadata
    for field in payload["fields"].values():
        field.setdefault("confidence", "low")
        field.setdefault("rationale", "")
        field.setdefault("source", "ursa_chat_agent")

    return payload


def merge_autofill_result(
    row: dict[str, Any],
    payload: dict[str, Any],
    section_questions: list[dict[str, str]],
    *,
    previous_meta: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    previous_meta = previous_meta or {}
    previous_fields = previous_meta.get("fields", {})
    updates: dict[str, Any] = {}
    merged_meta = deepcopy(previous_meta) if previous_meta else {}
    merged_meta.setdefault("fields", {})
    merged_meta.setdefault("history", [])
    merged_meta.setdefault("themes", {})

    for qid, field in payload.get("fields", {}).items():
        answer = str(field.get("answer", "") or "").strip()
        status = str(field.get("status", "unknown") or "unknown")
        current_value = str(row.get(qid, "") or "").strip()
        previous_answer = str(
            previous_fields.get(qid, {}).get("answer", "") or ""
        ).strip()
        should_write = False

        if status == "filled" and answer:
            if not current_value:
                should_write = True
            elif previous_answer and current_value == previous_answer:
                should_write = True

        if should_write:
            updates[qid] = answer

        question = next((s["label"] for s in section_questions if s["id"] == qid), None)
        merged_meta["fields"][qid] = {
            "question": question,
            "answer": answer,
            "status": status,
            "confidence": field.get("confidence", "low"),
            "rationale": field.get("rationale", ""),
            "source": field.get("source", payload.get("source", "heuristic")),
            "themes": FIELD_TO_THEMES.get(qid, []),
            "applied": should_write,
            "current_value_preserved": bool(current_value and not should_write),
        }

    merged_meta["followup_questions"] = payload.get("followup_questions", [])
    merged_meta["last_source"] = payload.get("source", "heuristic")
    merged_meta["themes"] = payload.get("themes", {})
    merged_meta["history"].append(
        {
            "source": payload.get("source", "heuristic"),
            "notes": payload.get("notes", []),
            "followup_count": len(payload.get("followup_questions", [])),
            "themes": sorted(payload.get("themes", {}).keys()),
        }
    )
    updates["agent_meta"] = dump_agent_meta(merged_meta)
    return updates, merged_meta


def build_followup_questions(
    row: dict[str, Any],
    payload: dict[str, Any],
    sections: list[dict[str, Any]],
    *,
    limit: int = 6,
) -> list[str]:
    del sections
    existing_answers = _normalize_clarifications(
        _safe_json_loads(row.get("user_clarifications", ""), {})
    )
    payload_fields = payload.get("fields", {})
    has_project_description = _has_text(row.get("project_description", ""))
    has_data_composition = _has_text(row.get("data_composition", ""))
    has_project_url = _has_text(row.get("project_url", ""))
    theme_priority = [
        "ownership_funding_initiative",
        "purpose_and_use",
        "composition_and_structure",
        "provenance_and_review",
        "restrictions_distribution_licensing",
        "maintenance_and_lifecycle",
    ]

    selected: list[str] = []
    for theme in theme_priority:
        status = _theme_status(theme, payload_fields, existing_answers)
        if status["answered"] and not status["unresolved_fields"]:
            continue
        if theme == "purpose_and_use" and has_project_description and not status["unresolved_fields"]:
            continue
        if theme == "composition_and_structure" and has_data_composition and not status["unresolved_fields"]:
            continue
        if theme == "restrictions_distribution_licensing" and has_project_url and not status["unresolved_fields"]:
            continue
        needs_prompt = bool(
            status["unresolved_fields"]
            or (status["low_confidence_fields"] and not status["answered"])
        )
        if needs_prompt:
            selected.append(THEME_TO_PROMPT[theme])
        if len(selected) >= limit:
            break
    return selected


def summarize_autofill(
    payload: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, list[dict[str, str]]]:
    catalog = build_question_catalog(sections)
    summary = {"filled": [], "needs_user": [],
               "unknown": [], "low_confidence": []}
    for qid, field in payload.get("fields", {}).items():
        item = {
            "qid": qid,
            "label": catalog.get(qid, {}).get("label", qid),
            "answer": str(field.get("answer", "") or ""),
            "confidence": str(field.get("confidence", "low") or "low"),
            "rationale": str(field.get("rationale", "") or ""),
            "themes": ", ".join(FIELD_TO_THEMES.get(qid, [])),
        }
        status = str(field.get("status", "unknown") or "unknown")
        summary.setdefault(status, []).append(item)
        if item["confidence"] == "low":
            summary["low_confidence"].append(item)
    return summary


def run_initial_autofill(
    diana_dir: str,
    intake_row: dict[str, Any],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        return _run_ursa_autofill(
            diana_dir=diana_dir,
            row=intake_row,
            sections=sections,
        )
    except Exception as exc:
        payload = heuristic_autofill(intake_row, sections)
        payload["notes"].append(f"URSA fallback used: {exc}")
        return payload


def run_followup_autofill(
    diana_dir: str,
    updated_row: dict[str, Any],
    clarifications: dict[str, str],
    sections: list[dict[str, Any]],
) -> dict[str, Any]:
    try:
        return _run_ursa_autofill(
            diana_dir=diana_dir,
            row=updated_row,
            sections=sections,
            clarifications=clarifications,
        )
    except Exception as exc:
        payload = heuristic_autofill(
            updated_row,
            sections,
            clarifications=clarifications,
        )
        payload["notes"].append(f"URSA fallback used: {exc}")
        return payload

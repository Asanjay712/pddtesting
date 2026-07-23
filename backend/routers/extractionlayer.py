import io
import logging
import re
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── PDF / DOCX extractors ──────────────────────────────────────────────────────
try:
    from pdfminer.high_level import extract_text as pdf_extract_text
    HAS_PDFMINER = True
except ImportError:
    logger.warning("pdfminer.six not installed. Run `pip install pdfminer.six`.")
    HAS_PDFMINER = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    logger.warning("python-docx not installed. Run `pip install python-docx`.")
    HAS_DOCX = False

# ── Lightweight dictionary/keyword NER (replaces GLiNER / transformers) ──────
# CHANGE FROM ORIGINAL:
#   The old pipeline loaded GLiNER ("urchade/gliner_mediumv2.1") or, as a
#   fallback, a HuggingFace transformer ("d4data/biomedical-ner-all"). Both
#   need torch + transformer weights resident in memory (roughly 1-2+ GB),
#   which does not fit inside Render's 512MB free/starter instances.
#
#   This version uses `flashtext` (pure Python, Aho-Corasick string matching,
#   no model weights, a few hundred KB, extremely fast — O(n) over the text
#   regardless of dictionary size) to match against curated medical term
#   lists. If flashtext isn't installed, it falls back to plain regex
#   word-boundary matching (slower, but still zero-model-weight).
#
#   Trade-off: this is deterministic dictionary matching, not zero-shot ML
#   NER — it will only catch terms that are in MEDICAL_TERMS below. It won't
#   generalize to novel phrasing the way GLiNER could. Extend MEDICAL_TERMS
#   with more terms any time you find real reports missing entities.
try:
    from flashtext import KeywordProcessor
    HAS_FLASHTEXT = True
except ImportError:
    HAS_FLASHTEXT = False
    logger.warning(
        "flashtext not installed — falling back to slower regex matching. "
        "Run `pip install flashtext` (tiny, pure-Python, no ML weights) for best speed."
    )

# ── Medical abbreviation expansion ────────────────────────────────────────────
MEDICAL_ABBREVIATIONS = {
    r"\bHTN\b": "Hypertension",
    r"\bSOB\b": "Shortness of breath",
    r"\bpt\b":  "patient",
    r"\bRx\b":  "Prescription",
    r"\bDx\b":  "Diagnosis",
    r"\bTx\b":  "Treatment",
    r"\bHx\b":  "History",
    r"\bc/o\b": "complains of",
    r"\bN/V\b": "Nausea and Vomiting",
    r"\bDOB\b": "Date of Birth",
}

# ── Curated medical term dictionary ───────────────────────────────────────────
# Label per category matches what _categorize_entities() below expects.
# Extend these lists as you discover missing terms in real reports —
# this is the main lever for recall now that there's no ML model.
MEDICAL_TERMS: Dict[str, List[str]] = {
    "SYMPTOM": [
        "fever", "cough", "headache", "nausea", "vomiting", "dizziness",
        "fatigue", "chest pain", "shortness of breath", "abdominal pain",
        "back pain", "sore throat", "diarrhea", "constipation", "rash",
        "swelling", "chills", "weakness", "numbness", "blurred vision",
        "palpitations", "loss of appetite", "difficulty breathing",
        "joint pain", "muscle pain", "night sweats", "weight loss",
        "confusion", "irritability", "insomnia",
    ],
    "DIAGNOSIS": [
        "hypertension", "diabetes", "diabetes mellitus", "type 2 diabetes",
        "asthma", "pneumonia", "bronchitis", "covid-19", "influenza",
        "migraine", "anemia", "obesity", "depression", "anxiety",
        "arthritis", "osteoarthritis", "rheumatoid arthritis", "copd",
        "gerd", "hypothyroidism", "hyperthyroidism",
        "urinary tract infection", "sinusitis", "viral infection",
        "bacterial infection", "myocardial infarction", "stroke",
        "sepsis", "chronic kidney disease", "hyperlipidemia",
        "atrial fibrillation", "congestive heart failure",
    ],
    "MEDICATION": [
        "amoxicillin", "ibuprofen", "acetaminophen", "paracetamol",
        "metformin", "lisinopril", "atorvastatin", "aspirin",
        "omeprazole", "albuterol", "insulin", "azithromycin",
        "prednisone", "levothyroxine", "losartan", "metoprolol",
        "hydrochlorothiazide", "gabapentin", "sertraline", "warfarin",
        "amlodipine", "simvastatin", "clopidogrel", "furosemide",
        "montelukast", "cetirizine", "ciprofloxacin", "doxycycline",
    ],
    "PROCEDURE": [
        "mri brain", "ct scan", "x-ray", "ultrasound", "biopsy",
        "endoscopy", "colonoscopy", "ecg", "ekg", "echocardiogram",
        "blood test", "urinalysis", "mammogram", "ct chest",
        "mri spine", "ct abdomen", "physical therapy", "surgery",
        "catheterization", "dialysis", "vaccination", "blood transfusion",
        "chest x-ray", "abdominal ultrasound", "stress test",
    ],
    "LAB_FINDING": [
        "elevated wbc", "high blood sugar", "elevated glucose",
        "low hemoglobin", "elevated creatinine", "elevated bilirubin",
        "low platelet count", "elevated troponin", "elevated crp",
        "abnormal ecg", "elevated cholesterol", "low potassium",
        "elevated liver enzymes", "elevated hba1c", "low sodium",
        "elevated white blood cell count", "positive covid test",
    ],
}


class MedicalReportExtractor:
    def __init__(self):
        logger.info("MedicalReportExtractor initializing (lightweight dictionary NER).")
        self._keyword_processor = self._build_keyword_processor()

    # ------------------------------------------------------------------
    # Build the flashtext KeywordProcessor once, at construction time.
    # This is cheap (a dict of a few hundred short strings) — no model
    # download, no GPU/CPU warm-up, negligible memory (a few hundred KB).
    # ------------------------------------------------------------------
    def _build_keyword_processor(self):
        if not HAS_FLASHTEXT:
            return None
        kp = KeywordProcessor(case_sensitive=False)
        self._term_to_label: Dict[str, str] = {}
        for label, terms in MEDICAL_TERMS.items():
            for term in terms:
                kp.add_keyword(term)
                self._term_to_label[term.lower()] = label
        return kp

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def process_document(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Extract → section-detect → expand abbrevs → NER → categorize.
        Returns empty categories if nothing could be extracted — never fake data.
        """
        full_text = self._extract_text(file_bytes, content_type, filename)

        if not full_text.strip():
            logger.warning(f"No text could be extracted from '{filename}'.")
            return self._empty_result()

        sections      = self._detect_sections(full_text)
        expanded_text = self._expand_abbreviations(full_text)
        entities      = self._extract_entities(expanded_text)
        categorized   = self._categorize_entities(entities)
        categorized["detected_sections"] = sections
        return categorized

    # ------------------------------------------------------------------
    # Empty result — honest "nothing found", no fake data
    # ------------------------------------------------------------------
    @staticmethod
    def _empty_result() -> Dict[str, Any]:
        return {
            "symptoms":          [],
            "diagnosis":         [],
            "procedures":        [],
            "medications":       [],
            "lab_findings":      [],
            "confidence_scores": {},
            "detected_sections": {},
        }

    # ------------------------------------------------------------------
    # Text extraction
    # ------------------------------------------------------------------
    def _extract_text(self, file_bytes: bytes, content_type: str, filename: str) -> str:
        fname_lower = filename.lower()
        ct_lower    = (content_type or "").lower()

        is_pdf  = "pdf" in ct_lower or fname_lower.endswith(".pdf")
        is_docx = ("wordprocessingml" in ct_lower or "msword" in ct_lower
                   or fname_lower.endswith(".docx") or fname_lower.endswith(".doc"))
        is_txt  = "text/plain" in ct_lower or fname_lower.endswith(".txt")

        if is_pdf:
            return self._extract_pdf(file_bytes)
        elif is_docx:
            return self._extract_docx(file_bytes)
        elif is_txt:
            return self._decode_txt(file_bytes)
        else:
            logger.warning(f"Unknown content type '{content_type}' for '{filename}'. Trying PDF then txt.")
            text = self._extract_pdf(file_bytes)
            return text if text.strip() else self._decode_txt(file_bytes)

    def _extract_pdf(self, file_bytes: bytes) -> str:
        if not HAS_PDFMINER:
            logger.error("pdfminer.six is not installed — cannot extract PDF text.")
            return ""
        try:
            text = pdf_extract_text(io.BytesIO(file_bytes))
            logger.info(f"PDF text extracted: {len(text)} characters.")
            return text or ""
        except Exception as e:
            logger.error(f"pdfminer extraction failed: {e}")
            return ""

    def _extract_docx(self, file_bytes: bytes) -> str:
        if not HAS_DOCX:
            logger.error("python-docx is not installed — cannot extract DOCX text.")
            return ""
        try:
            doc  = DocxDocument(io.BytesIO(file_bytes))
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            logger.info(f"DOCX text extracted: {len(text)} characters.")
            return text
        except Exception as e:
            logger.error(f"python-docx extraction failed: {e}")
            return ""

    def _decode_txt(self, file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="replace")

    # ------------------------------------------------------------------
    # Section detection
    # ------------------------------------------------------------------
    def _detect_sections(self, text: str) -> Dict[str, str]:
        sections: Dict[str, List[str]] = {}
        current = "General"
        sections[current] = []
        headers = [
            "DIAGNOSIS", "MEDICATIONS", "ALLERGIES", "LABORATORY RESULTS",
            "HISTORY OF PRESENT ILLNESS", "ASSESSMENT", "PLAN",
        ]
        for line in text.split("\n"):
            lu = line.strip().upper()
            matched = False
            for h in headers:
                if lu.startswith(h):
                    current = h
                    sections[current] = []
                    matched = True
                    break
            if not matched and line.strip():
                sections[current].append(line.strip())
        return {k: " ".join(v) for k, v in sections.items() if v}

    def _expand_abbreviations(self, text: str) -> str:
        for abbr, exp in MEDICAL_ABBREVIATIONS.items():
            text = re.sub(abbr, exp, text, flags=re.IGNORECASE)
        return text

    # ------------------------------------------------------------------
    # Entity validation — blocks noise before it reaches the graph
    # ------------------------------------------------------------------
    @staticmethod
    def _is_valid_entity(text: str) -> bool:
        """
        Rejects tokens that cannot be real medical entities:
          - purely numeric strings, including with separators (e.g. "8192", "23-27", "2179")
          - fewer than 3 characters
          - >50% digits
        """
        import re as _re
        text = text.strip()
        if len(text) < 3:
            return False
        stripped = _re.sub(r"[\s\-/.,:]", "", text)
        if not stripped or stripped.isdigit():
            return False
        if sum(c.isdigit() for c in text) / len(text) > 0.5:
            return False
        return True

    # ------------------------------------------------------------------
    # NER — lightweight dictionary/keyword matching (no model weights)
    # ------------------------------------------------------------------
    def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        if HAS_FLASHTEXT and self._keyword_processor is not None:
            return self._extract_entities_flashtext(text)
        return self._extract_entities_regex(text)

    def _extract_entities_flashtext(self, text: str) -> List[Dict[str, Any]]:
        """
        flashtext.extract_keywords() runs a single Aho-Corasick pass over the
        text — O(len(text)), independent of dictionary size — and is not
        sensitive to word count the way a transformer forward pass is. This
        is the main "process a bit faster" win: no batching, no tokenizer,
        no model inference, just string scanning.
        """
        try:
            matches = self._keyword_processor.extract_keywords(text)
        except Exception as e:
            logger.error(f"flashtext extraction failed: {e}")
            return []

        entities = []
        seen = set()
        for match in matches:
            key = match.lower()
            if key in seen:
                continue
            if not self._is_valid_entity(match):
                continue
            label = self._term_to_label.get(key)
            if not label:
                continue
            seen.add(key)
            entities.append({
                "text":             match.title() if match.islower() else match,
                "label":            label,
                "confidence_score": 92.0,  # deterministic dictionary match
            })
        logger.info(f"Dictionary NER (flashtext) extracted {len(entities)} entities.")
        return entities

    def _extract_entities_regex(self, text: str) -> List[Dict[str, Any]]:
        """Fallback when flashtext isn't installed — plain word-boundary regex."""
        entities = []
        seen = set()
        for label, terms in MEDICAL_TERMS.items():
            for term in terms:
                pattern = r"\b" + re.escape(term) + r"\b"
                if re.search(pattern, text, flags=re.IGNORECASE):
                    key = term.lower()
                    if key in seen or not self._is_valid_entity(term):
                        continue
                    seen.add(key)
                    entities.append({
                        "text":             term.title(),
                        "label":            label,
                        "confidence_score": 88.0,
                    })
        logger.info(f"Dictionary NER (regex fallback) extracted {len(entities)} entities.")
        return entities

    # ------------------------------------------------------------------
    # Categorize
    # ------------------------------------------------------------------
    def _categorize_entities(self, entities: List[Dict[str, Any]]) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "symptoms":          [],
            "diagnosis":         [],
            "procedures":        [],
            "medications":       [],
            "lab_findings":      [],
            "confidence_scores": {},
        }
        seen: set = set()
        for ent in entities:
            label = ent.get("label", "")
            text  = ent.get("text",  "")
            score = ent.get("confidence_score", 0.0)
            if text in seen:
                continue
            seen.add(text)
            out["confidence_scores"][text] = score

            if label == "SYMPTOM":
                out["symptoms"].append(text)
            elif label == "DIAGNOSIS":
                out["diagnosis"].append(text)
            elif label == "MEDICATION":
                out["medications"].append(text)
            elif label == "PROCEDURE":
                out["procedures"].append(text)
            elif label == "LAB_FINDING":
                out["lab_findings"].append(text)
            # unknown labels are dropped — not silently dumped into lab_findings
        return out
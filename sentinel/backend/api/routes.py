from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.trust_models import InvestigationRequest, TrustedResponse
from services.evidence.retrieval import retrieve_and_answer
from services.trust.guardrail import check_injection
from services.trust.contradiction import ContradictionDetector
from services.trust.fact_check import extract_claims, verify_claims
from services.trust.trust_score import build_trusted_response

router = APIRouter()

_DATA_DIR   = Path(__file__).resolve().parent.parent.parent.parent / "data" / "case-files"
_DEFAULT_CF = str(_DATA_DIR / "millbrook_arson_2019.txt")

_CASE_FILES = {
    "millbrook_arson_2019":      str(_DATA_DIR / "millbrook_arson_2019.txt"),
    "millbrook_arson_corrupted": str(_DATA_DIR / "millbrook_arson_corrupted.txt"),
}

_detector = ContradictionDetector()


@router.post("/query", response_model=TrustedResponse)
async def query(request: InvestigationRequest) -> TrustedResponse:
    # ── Milestone 7: Prompt injection guard ──────────────────────────────────
    if check_injection(request.question):
        return TrustedResponse(
            status  = "INJECTION_DETECTED",
            message = "Query rejected: prompt injection pattern detected.",
            question = request.question,
        )

    # ── Resolve case file ─────────────────────────────────────────────────────
    if request.case_file:
        case_file = _CASE_FILES.get(request.case_file, str(_DATA_DIR / request.case_file))
    else:
        case_file = _DEFAULT_CF

    if not Path(case_file).exists():
        raise HTTPException(status_code=404, detail=f"Case file not found: {case_file}")

    try:
        # ── Milestone 2: Evidence Retrieval Service ───────────────────────────
        answer, evidence_pages, retrieval_confidence = retrieve_and_answer(
            request.question, case_file
        )

        # ── Milestone 4: Contradiction detection ─────────────────────────────
        contradiction_report = _detector.detect(evidence_pages)

        # ── Milestones 5 & 6: Claim extraction + fact checking ───────────────
        claims      = extract_claims(answer)
        fact_report = verify_claims(claims, evidence_pages)

        # TF-IDF cosine scores sit in [0.1, 0.3]; semantic embeddings (sentence-
        # transformers) sit in [0.5, 0.9].  Normalise so the trust formula is
        # calibrated correctly.  A TF-IDF score >= 0.25 maps to 1.0 (strong match).
        normalised_rc = min(1.0, retrieval_confidence / 0.25)

        return build_trusted_response(
            question             = request.question,
            answer               = answer,
            evidence_pages       = evidence_pages,
            contradiction_report = contradiction_report,
            fact_report          = fact_report,
            retrieval_confidence = normalised_rc,
        )

    except Exception as exc:
        return TrustedResponse(
            status   = "ERROR",
            message  = str(exc),
            question = request.question,
        )

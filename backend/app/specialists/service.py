"""Shared Phase 8–11 specialist analysis boundary.

Specialist capabilities have dedicated analysis types and contracts, but share
the Phase-3 media ownership boundary and the Phase-4 asynchronous result
shape. Provider payloads are retained as immutable, provenance-bearing result
data; no specialist result silently edits canonical pet facts.
"""
import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from threading import RLock
from uuid import uuid4

from app.media.service import MediaError


class SpecialistStatus(StrEnum):
    QUEUED = "QUEUED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    DELETED = "DELETED"


SPECIALIST_TYPES = {
    "DOG_INITIAL_SCAN",
    "DOG_DENTAL_CHECK",
    "DOG_FECES_CHECK",
    "DOG_BODY_CHECK",
}

INITIAL_SCAN_FIELDS = {
    "COAT_COLOR", "COAT_PATTERN", "COAT_LENGTH", "APPARENT_SIZE_CATEGORY",
    "MORPHOLOGY_DESCRIPTION", "POSSIBLE_BREED_TYPE", "LIFE_STAGE_APPEARANCE",
    "DISTINGUISHING_FEATURES", "PROFILE_PHOTO_SUGGESTION",
}
INITIAL_SCAN_CAPTURE_STEPS = (
    {"step_id": "FACE_VIEW", "purpose": "FACE_VIEW", "required": True, "instruction": "Capture the dog's face in even light."},
    {"step_id": "FULL_BODY_SIDE", "purpose": "FULL_BODY_SIDE", "required": True, "instruction": "Capture one clear full-body side view."},
    {"step_id": "FULL_BODY_STANDING", "purpose": "FULL_BODY_STANDING", "required": False, "instruction": "Optional: capture the dog standing naturally."},
    {"step_id": "TOP_VIEW", "purpose": "TOP_VIEW", "required": False, "instruction": "Optional: capture a top view."},
    {"step_id": "DISTINGUISHING_MARKS", "purpose": "DISTINGUISHING_MARKS", "required": False, "instruction": "Optional: capture distinctive markings."},
)
DENTAL_CAPTURE_STEPS = (
    {"step_id": "FRONT_TEETH", "purpose": "FRONT_TEETH", "required": True, "instruction": "Use bright, even light and show the teeth and gumline clearly."},
    {"step_id": "LEFT_SIDE_TEETH", "purpose": "LEFT_SIDE_TEETH", "required": True, "instruction": "Capture the left side only if the dog remains comfortable."},
    {"step_id": "RIGHT_SIDE_TEETH", "purpose": "RIGHT_SIDE_TEETH", "required": True, "instruction": "Capture the right side only if the dog remains comfortable."},
    {"step_id": "UPPER_VISIBLE_TEETH", "purpose": "UPPER_VISIBLE_TEETH", "required": False, "instruction": "Optional: capture only what is naturally visible."},
    {"step_id": "LOWER_VISIBLE_TEETH", "purpose": "LOWER_VISIBLE_TEETH", "required": False, "instruction": "Optional: capture only what is naturally visible."},
    {"step_id": "AREA_OF_CONCERN", "purpose": "AREA_OF_CONCERN", "required": False, "instruction": "Optional: capture an area of concern without forcing the mouth open."},
)
INITIAL_SCAN_FEATURE_FLAGS = {
    "COAT_COLOR": "dog_initial_scan_coat_color_enabled",
    "COAT_PATTERN": "dog_initial_scan_coat_pattern_enabled",
    "COAT_LENGTH": "dog_initial_scan_coat_length_enabled",
    "APPARENT_SIZE_CATEGORY": "dog_initial_scan_size_category_enabled",
    "MORPHOLOGY_DESCRIPTION": "dog_initial_scan_morphology_enabled",
    "POSSIBLE_BREED_TYPE": "dog_initial_scan_breed_suggestion_enabled",
    "LIFE_STAGE_APPEARANCE": "dog_initial_scan_life_stage_enabled",
    "DISTINGUISHING_FEATURES": "dog_initial_scan_distinguishing_features_enabled",
    "PROFILE_PHOTO_SUGGESTION": "dog_initial_scan_profile_photo_enabled",
}
FORBIDDEN_INITIAL_FIELDS = {
    "EXACT_AGE", "EXACT_WEIGHT", "NEUTERED", "SPAYED", "GENETIC_ANCESTRY",
    "DIAGNOSIS", "HEALTH_CONDITION",
}
FORBIDDEN_CLAIMS = {
    "diagnosis", "diagnose", "periodontal stage", "periodontal_stage", "pocket depth", "pocket_depth", "root damage", "root_damage",
    "bone loss", "bone_loss", "pulp vitality", "pulp_vitality", "abscess", "parasite", "infection", "dehydration",
    "no dental disease", "disease ruled out", "clear of disease", "stage ",
    "medication", "prescription", "antibiotic", "dose ", "give dewormer", "exact_age", "exact_weight",
}
DENTAL_FINDING_TYPES = {
    "CALCULUS_LIKE_DEPOSIT", "GINGIVAL_REDNESS", "GINGIVAL_SWELLING", "VISIBLE_BLEEDING",
    "RECESSION_LIKE_APPEARANCE", "VISIBLE_TOOTH_DAMAGE", "VISIBLE_TOOTH_DISCOLORATION",
    "MISSING_TOOTH_LIKE_APPEARANCE", "LESION_LIKE_AREA", "FOREIGN_MATERIAL_LIKE_AREA",
    "OTHER_VISIBLE_ORAL_FINDING",
}
DENTAL_EVIDENCE_REASONS = {"BLUR", "LOW_LIGHT", "GLARE", "TOO_FAR", "GUM_LINE_NOT_VISIBLE", "TEETH_NOT_VISIBLE", "VIEW_BLOCKED", "MOTION", "INSUFFICIENT_VIEWS", "TARGET_AMBIGUOUS", "OTHER"}
DENTAL_SAFETY_STATES = ("NORMAL_INFORMATION", "MONITOR", "PROFESSIONAL_REVIEW_RECOMMENDED", "PROMPT_VETERINARY_CONTACT", "URGENT_VETERINARY_CONTACT")
DENTAL_URGENT_INPUTS = {"FACIAL_SWELLING_REPORTED", "DIFFICULTY_BREATHING_REPORTED", "HEAVY_ONGOING_BLEEDING_REPORTED"}
DENTAL_PROMPT_INPUTS = {"ACTIVE_BLEEDING_VISIBLE", "MARKED_SWELLING_VISIBLE", "MAJOR_TOOTH_DAMAGE_VISIBLE", "PAINFUL_HANDLING_REPORTED", "EATING_DIFFICULTY_REPORTED"}
FECES_FINDING_TYPES = {"MUCUS_LIKE", "FRESH_RED_BLOOD_LIKE", "DARK_BLACK_TAR_LIKE", "FOREIGN_MATERIAL_LIKE", "WORM_SEGMENT_LIKE", "OTHER_VISIBLE_FINDING"}
FECES_EVIDENCE_REASONS = {"BLUR", "LOW_LIGHT", "GLARE", "TOO_FAR", "SAMPLE_NOT_VISIBLE", "SAMPLE_PARTIALLY_BLOCKED", "MULTIPLE_SAMPLES", "TARGET_AMBIGUOUS", "INSUFFICIENT_COVERAGE", "OTHER"}
FECES_VISUAL_RISK = {"LOW_VISIBLE_CONCERN", "MILD", "MODERATE", "HIGH", "INSUFFICIENT_EVIDENCE"}
FECES_SAFETY_STATES = ("NORMAL_INFORMATION", "MONITOR", "PROFESSIONAL_REVIEW_RECOMMENDED", "PROMPT_VETERINARY_CONTACT", "URGENT_VETERINARY_CONTACT")
BODY_OBSERVATION_TYPES = {"WAIST_DEFINITION_VISIBLE", "ABDOMINAL_TUCK_VISIBLE", "RIB_OUTLINE_VISIBLE", "SPINAL_OUTLINE_VISIBLE", "HIP_BONE_OUTLINE_VISIBLE", "GENERAL_BODY_CONTOUR", "LEFT_RIGHT_ASYMMETRY_VISIBLE", "POSTURE_NOTE", "OTHER_VISIBLE_BODY_OBSERVATION"}
BODY_CONDITION_CATEGORIES = {"LEAN_APPEARANCE", "BALANCED_APPEARANCE", "ROUNDED_APPEARANCE", "UNCERTAIN"}
BODY_CAPTURE_STEPS = (
    {"step_id": "SIDE_STANDING", "purpose": "SIDE_STANDING", "required": True, "instruction": "Capture the dog standing naturally from the side."},
    {"step_id": "TOP_STANDING", "purpose": "TOP_STANDING", "required": True, "instruction": "Capture a top view without changing the dog's posture."},
    {"step_id": "FRONT_STANDING", "purpose": "FRONT_STANDING", "required": False, "instruction": "Optional: capture a front view for visible symmetry."},
)
FECES_FRESHNESS_STATES = {"FRESH_BEFORE_DISPOSAL", "NOT_FRESH", "UNKNOWN"}
FECES_CONSISTENCY_STATES = {"HARD_DRY", "FORMED", "SOFT_FORMED", "UNFORMED", "WATERY", "UNCERTAIN"}
FECES_VISIBLE_STATES = {"OBSERVED", "NOT_OBSERVED", "NOT_ASSESSABLE"}
FECES_CONTEXT_FIELDS = {"repeated_stools", "duration_category", "vomiting", "marked_lethargy", "collapse", "unable_to_keep_water_down", "reduced_eating", "known_foreign_material_ingestion", "free_text_context"}
FECES_FORBIDDEN_TEXT = ("giardia", "parasite", "parasites", "roundworm", "tapeworm", "hookworm", "whipworm", "coccidia", "worm species", "parasite identified", "parasite-free", "no parasites", "bacterial infection", "viral infection", "occult blood", "microbiome", "dysbiosis", "pancreatic disease", "hepatic disease", "internal-organ", "dehydrated", "dehydration", "give dewormer", "use antibiotic", "antibiotic", "dose ", "caused by", "definitely due to", "this proves", "nothing is wrong")
BODY_FORBIDDEN_TEXT = ("pregnant", "not pregnant", "body fat", "body-fat", "bcs ", "obese", "obesity", "underweight due", "muscle wasting", "cachexia", "malnutrition", "hypothyroidism", "exact age", "neutered", "spayed", "diagnos", "definitely", "certainly", "100%", "purebred")


@dataclass
class SpecialistAnalysis:
    id: str
    owner_user_id: str
    animal_id: str
    analysis_type: str
    media_asset_ids: list[str]
    status: SpecialistStatus = SpecialistStatus.COMPLETED
    result: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    deleted_at: datetime | None = None


@dataclass
class InitialScanCandidate:
    id: str
    analysis_id: str
    owner_user_id: str
    animal_id: str
    field_type: str
    candidate_value: str
    evidence_quality: str = "UNSPECIFIED"
    provenance_status: str = "AI_SUGGESTED"
    status: str = "PENDING_REVIEW"
    review_action: str | None = None
    reviewed_value: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    reviewed_at: datetime | None = None


@dataclass(frozen=True)
class InitialScanReview:
    id: str
    candidate_id: str
    owner_user_id: str
    action: str
    value: str | None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class SpecialistError(ValueError):
    pass


class SpecialistService:
    def __init__(self, pets, media, store=None, clock=None, release_flags=None, credits=None):
        self.pets, self.media, self.store = pets, media, store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.analyses: dict[str, SpecialistAnalysis] = {}
        self.candidates: dict[str, InitialScanCandidate] = {}
        self.candidate_reviews: list[InitialScanReview] = []
        self.pending_requests: dict[str, dict] = {}
        self.idempotency: dict[tuple[str, str], str] = {}
        self.lock = RLock()
        self.release_flags = release_flags or {}
        self.credits = credits
        self._hydrate()

    def _hydrate(self):
        """Reload specialist analyses after API/worker restart."""
        if not self.store or not hasattr(self.store, "all"):
            return
        def rows(collection):
            try:
                return self.store.all(collection)
            except Exception:  # noqa: BLE001 - transient durable outage must not crash startup
                return []

        for data in rows("specialist_analyses"):
            try:
                raw = dict(data)
                raw["status"] = SpecialistStatus(raw.get("status", SpecialistStatus.COMPLETED))
                for key in ("created_at", "updated_at", "deleted_at"):
                    value = raw.get(key)
                    if value is not None and not isinstance(value, datetime):
                        raw[key] = datetime.fromisoformat(str(value))
                item = SpecialistAnalysis(**{k: raw[k] for k in SpecialistAnalysis.__dataclass_fields__ if k in raw})
                self.analyses[item.id] = item
                if item.status == SpecialistStatus.QUEUED:
                    self.pending_requests[item.id] = {
                        "media_asset_ids": item.media_asset_ids,
                        "capture_manifest": item.provenance.get("capture_manifest"),
                        "owner_context": item.provenance.get("owner_context"),
                    }
            except (KeyError, TypeError, ValueError):
                continue
        for data in rows("initial_scan_candidates"):
            try:
                raw = dict(data)
                for key in ("created_at", "reviewed_at"):
                    value = raw.get(key)
                    if value is not None and not isinstance(value, datetime):
                        raw[key] = datetime.fromisoformat(str(value))
                item = InitialScanCandidate(**{k: raw[k] for k in InitialScanCandidate.__dataclass_fields__ if k in raw})
                self.candidates[item.id] = item
            except (KeyError, TypeError, ValueError):
                continue
        for data in rows("initial_scan_candidate_reviews"):
            try:
                raw = dict(data)
                raw["action"] = str(raw["action"])
                if raw.get("created_at") is not None and not isinstance(raw["created_at"], datetime):
                    raw["created_at"] = datetime.fromisoformat(str(raw["created_at"]))
                self.candidate_reviews.append(InitialScanReview(**{
                    k: raw[k] for k in InitialScanReview.__dataclass_fields__ if k in raw
                }))
            except (KeyError, TypeError, ValueError):
                continue

    def _save(self, collection, value):
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw(collection, value.id, asdict(value))

    def _pet(self, owner, pet_id, analysis_type=None):
        pet = self.pets.get(owner, pet_id)
        if not pet:
            raise SpecialistError("SPECIALIST_PET_NOT_FOUND")
        if str(getattr(pet, "species", "")).upper() != "DOG":
            raise SpecialistError({"DOG_INITIAL_SCAN": "DOG_INITIAL_SCAN_SPECIES_INVALID", "DOG_DENTAL_CHECK": "DENTAL_CHECK_NOT_AVAILABLE_FOR_SPECIES", "DOG_FECES_CHECK": "FECES_CHECK_NOT_AVAILABLE_FOR_SPECIES", "DOG_BODY_CHECK": "BODY_CHECK_NOT_AVAILABLE_FOR_SPECIES"}.get(analysis_type, (analysis_type or "SPECIALIST") + "_SPECIES_INVALID"))
        return pet

    def _owned(self, owner, analysis_id):
        item = self.analyses.get(analysis_id)
        if not item and self.store and hasattr(self.store, "all"):
            self._hydrate()
            item = self.analyses.get(analysis_id)
        if not item or item.owner_user_id != owner or item.deleted_at:
            raise SpecialistError("SPECIALIST_NOT_FOUND")
        return item

    def _validate_media(self, owner, animal_id, media_ids, analysis_type):
        if not media_ids:
            raise SpecialistError(analysis_type + "_MEDIA_REQUIRED")
        if len(media_ids) > 8:
            raise SpecialistError(analysis_type + "_TOO_MANY_IMAGES")
        try:
            resolved = self.media.resolve_ai_media(owner, media_ids, animal_id)
        except MediaError as exc:
            raise SpecialistError(analysis_type + "_MEDIA_UNSUPPORTED") from exc
        if any(item.get("kind") != "IMAGE" for item in resolved):
                raise SpecialistError(analysis_type + "_MEDIA_UNSUPPORTED")

    @staticmethod
    def _validate_capture_manifest(analysis_type, body, media_ids):
        manifest = body.get("capture_manifest") or {}
        if analysis_type == "DOG_FECES_CHECK":
            freshness = str(manifest.get("freshness_confirmation", body.get("freshness_confirmation", "UNKNOWN"))).upper()
            if freshness not in FECES_FRESHNESS_STATES:
                raise SpecialistError("FECES_CHECK_CAPTURE_INVALID")
            if freshness != "FRESH_BEFORE_DISPOSAL":
                raise SpecialistError("FECES_CHECK_SAMPLE_NOT_FRESH")
            if manifest and manifest.get("producer_confirmation") is False:
                raise SpecialistError("FECES_CHECK_CAPTURE_INVALID")
            if manifest and manifest.get("multi_dog_environment") is True and manifest.get("target_dog_confirmed") is not True:
                raise SpecialistError("FECES_CHECK_PRODUCER_UNCONFIRMED")
            if manifest and manifest.get("whole_sample_coverage") is False:
                raise SpecialistError("FECES_CHECK_EVIDENCE_INSUFFICIENT")
            context = body.get("owner_context") or {}
            unknown = set(context) - FECES_CONTEXT_FIELDS
            if unknown:
                raise SpecialistError("FECES_CHECK_CONTEXT_INVALID")
        if analysis_type == "DOG_BODY_CHECK" and manifest:
            steps = {str(x.get("step_id")) for x in manifest.get("steps", []) if isinstance(x, dict)}
            if not {"SIDE_STANDING", "TOP_STANDING"}.issubset(steps):
                raise SpecialistError("BODY_CHECK_CAPTURE_INCOMPLETE")
        if not media_ids:
            raise SpecialistError(analysis_type + "_MEDIA_REQUIRED")

    @staticmethod
    def _guardrail_result(analysis_type, result):
        source = dict(result or {})
        if analysis_type == "DOG_DENTAL_CHECK":
            terms = FORBIDDEN_CLAIMS
        elif analysis_type == "DOG_FECES_CHECK":
            terms = FECES_FORBIDDEN_TEXT
        else:
            terms = BODY_FORBIDDEN_TEXT
        def safe_text(value):
            text = re.sub(r"[_-]+", " ", str(value or "").lower())
            text = re.sub(r"\s+", " ", text).strip()
            normalized_terms = (re.sub(r"[_-]+", " ", term.lower()) for term in terms)
            return not any(term in text for term in normalized_terms)
        unsafe_string = False
        for key in ("observations", "uncertainties", "limitations", "recommended_actions", "areas_not_assessable", "areas_not_assessed", "posture_notes"):
            original = list(source.get(key, []) or [])
            source[key] = [x for x in original if safe_text(x)]
            unsafe_string = unsafe_string or len(source[key]) != len(original)
        if isinstance(source.get("visible_findings"), list):
            source["visible_findings"] = [x for x in source["visible_findings"] if isinstance(x, dict) and safe_text(x.get("statement"))]
        for key, value in list(source.items()):
            if isinstance(value, str) and not safe_text(value):
                source[key] = "[FILTERED_BY_SPECIALIST_GUARDRAIL]"
                unsafe_string = True
        if unsafe_string:
            source["guardrail_status"] = "RESTRICTED"
        source.setdefault("limitations", []).append("Provider language was filtered through the specialist safety guardrail.")
        return source

    def _validate_release(self, analysis_type):
        flag = {"DOG_INITIAL_SCAN": "dog_initial_scan_enabled", "DOG_DENTAL_CHECK": "dog_dental_check_enabled", "DOG_FECES_CHECK": "dog_feces_check_enabled", "DOG_BODY_CHECK": "dog_body_check_enabled"}.get(analysis_type)
        public_flag = {"DOG_INITIAL_SCAN": "dog_initial_scan_public_enabled", "DOG_DENTAL_CHECK": "dog_dental_check_public_enabled", "DOG_FECES_CHECK": "dog_feces_check_public_enabled", "DOG_BODY_CHECK": "dog_body_check_public_enabled"}.get(analysis_type)
        certificate_flag = {"DOG_INITIAL_SCAN": "dog_initial_scan_evaluation_certificate_id", "DOG_DENTAL_CHECK": "dog_dental_check_evaluation_certificate_id", "DOG_FECES_CHECK": "dog_feces_check_evaluation_certificate_id", "DOG_BODY_CHECK": "dog_body_check_evaluation_certificate_id"}.get(analysis_type)
        certificate_id = self.release_flags.get(certificate_flag) if self.release_flags and certificate_flag else None
        certificate_pending = not isinstance(certificate_id, str) or not certificate_id.strip() or certificate_id.strip().upper() == "PENDING"
        if flag and self.release_flags and (not self.release_flags.get(flag, False) or not self.release_flags.get(public_flag, False) or certificate_pending):
            raise SpecialistError({"DOG_INITIAL_SCAN": "DOG_INITIAL_SCAN_NOT_AVAILABLE", "DOG_DENTAL_CHECK": "DENTAL_CHECK_NOT_AVAILABLE", "DOG_FECES_CHECK": "FECES_CHECK_NOT_AVAILABLE", "DOG_BODY_CHECK": "BODY_CHECK_NOT_AVAILABLE"}.get(analysis_type, analysis_type + "_NOT_AVAILABLE"))

    def _validate_funding(self, owner, analysis_type, body, billing_exempt=False):
        if billing_exempt or not self.credits:
            return None
        reservation_id = body.get("funding_reservation_id")
        if not reservation_id:
            raise SpecialistError({"DOG_INITIAL_SCAN": "DOG_INITIAL_SCAN_FUNDING_REQUIRED", "DOG_DENTAL_CHECK": "DENTAL_CHECK_FUNDING_REQUIRED", "DOG_FECES_CHECK": "FECES_CHECK_FUNDING_REQUIRED", "DOG_BODY_CHECK": "BODY_CHECK_FUNDING_REQUIRED"}[analysis_type])
        reservation = self.credits.reservations.get(reservation_id)
        expected = "AI_PHOTO_STANDARD" if analysis_type == "DOG_INITIAL_SCAN" else "AI_SPECIALIST_STANDARD"
        if not reservation or reservation.user_id != owner or str(reservation.status) != "RESERVED" or str(reservation.operation_type) != expected:
            raise SpecialistError("SPECIALIST_FUNDING_INVALID")
        return reservation_id

    @staticmethod
    def _evidence_quality(value):
        return str(value or "UNSPECIFIED").upper() if str(value or "UNSPECIFIED").upper() in {"GOOD", "PARTIAL", "INSUFFICIENT", "UNSPECIFIED"} else "UNSPECIFIED"

    @staticmethod
    def _dental_safety(body, result):
        context = {str(x).upper() for x in (body.get("owner_context") or body.get("safety_inputs") or [])}
        candidates = {str(x).upper() for x in (result.get("red_flags") or [])}
        signals = context | candidates
        if signals & DENTAL_URGENT_INPUTS:
            return "URGENT_VETERINARY_CONTACT"
        if signals & DENTAL_PROMPT_INPUTS:
            return "PROMPT_VETERINARY_CONTACT"
        if result.get("visible_findings"):
            return "PROFESSIONAL_REVIEW_RECOMMENDED"
        if result.get("evidence_quality") == "INSUFFICIENT":
            return "MONITOR"
        return "NORMAL_INFORMATION"

    @classmethod
    def _normalize_initial_result(cls, result):
        source = dict(result or {})
        forbidden = ("exact age", "exact weight", "neutered", "spayed", "sterilized", "genetic ancestry", "diagnos", "healthy", "unhealthy", "purebred", "genetically", "breed certainty", "definitely a", "certainly a", "100%")
        def allowed(value):
            return not any(term in str(value or "").lower() for term in forbidden)
        candidates = source.get("profile_candidates", source.get("candidates", []))
        rejected_candidate_text = any(
            isinstance(candidate, dict)
            and any(not allowed(candidate.get(key)) for key in ("candidate_value", "display_value", "evidence_notes"))
            for candidate in (candidates or [])
        )
        candidates = [candidate for candidate in (candidates or []) if isinstance(candidate, dict) and str(candidate.get("field_type", "")) in INITIAL_SCAN_FIELDS and str(candidate.get("field_type", "")) not in FORBIDDEN_INITIAL_FIELDS and allowed(candidate.get("candidate_value")) and allowed(candidate.get("display_value")) and allowed(candidate.get("evidence_notes"))]
        normalized = {
            "result_version": str(source.get("result_version", "1.0.0")),
            "evidence_quality": cls._evidence_quality(source.get("evidence_quality")),
            "quality_reasons": list(source.get("quality_reasons", source.get("evidence_quality_reasons", [])) or []),
            "profile_candidates": list(candidates or []),
            "visible_distinguishing_features": [x for x in (source.get("visible_distinguishing_features", []) or []) if allowed(x)],
            "limitations": [x for x in (source.get("limitations", []) or []) if allowed(x)],
            "recapture_suggestions": list(source.get("recapture_suggestions", []) or []),
        }
        if rejected_candidate_text or any(not allowed(value) for value in source.values() if isinstance(value, str)):
            normalized["guardrail_status"] = "RESTRICTED"
        normalized["limitations"] = list(dict.fromkeys(normalized["limitations"] + ["This scan provides visual profile candidates only; it is not identity, medical, or breed-certification evidence."]))
        return normalized

    @classmethod
    def _normalize_dental_result(cls, body, result, release_flags=None):
        source = dict(result or {})
        findings = []
        for raw in source.get("visible_findings", []) or []:
            finding_type = str(raw.get("finding_type", "")) if isinstance(raw, dict) else ""
            finding_flag = {"CALCULUS_LIKE_DEPOSIT": "dog_dental_check_calculus_like_enabled", "GINGIVAL_REDNESS": "dog_dental_check_gingival_redness_enabled", "GINGIVAL_SWELLING": "dog_dental_check_swelling_enabled", "VISIBLE_BLEEDING": "dog_dental_check_bleeding_enabled", "RECESSION_LIKE_APPEARANCE": "dog_dental_check_recession_like_enabled", "VISIBLE_TOOTH_DAMAGE": "dog_dental_check_tooth_damage_enabled", "VISIBLE_TOOTH_DISCOLORATION": "dog_dental_check_discoloration_enabled", "MISSING_TOOTH_LIKE_APPEARANCE": "dog_dental_check_missing_tooth_like_enabled", "LESION_LIKE_AREA": "dog_dental_check_lesion_like_enabled", "FOREIGN_MATERIAL_LIKE_AREA": "dog_dental_check_foreign_material_like_enabled"}.get(finding_type)
            if not isinstance(raw, dict) or finding_type not in DENTAL_FINDING_TYPES or (finding_flag and release_flags and not release_flags.get(finding_flag, False)):
                continue
            findings.append({
                "id": str(raw.get("id") or uuid4()),
                "finding_type": str(raw["finding_type"]),
                "statement": str(raw.get("statement", "Visible oral finding."))[:500],
                "severity_descriptor": raw.get("severity_descriptor"),
                "confidence": str(raw.get("confidence", "UNSPECIFIED")),
                "source_media_ids": list(raw.get("source_media_ids", []) or []),
                "source_regions": list(raw.get("source_regions", []) or []),
                "location_descriptor": raw.get("location_descriptor"),
            })
        normalized = {
            "result_version": str(source.get("result_version", "1.0.0")),
            "evidence_quality": cls._evidence_quality(source.get("evidence_quality")),
            "evidence_quality_reasons": [x for x in (source.get("evidence_quality_reasons", []) or []) if str(x) in DENTAL_EVIDENCE_REASONS],
            "visible_findings": findings,
            "areas_not_assessed": list(source.get("areas_not_assessed", []) or []),
            "red_flags": [str(x).upper() for x in (source.get("red_flags", []) or [])],
            "recommended_actions": list(source.get("recommended_actions", []) or []),
            "limitations": list(source.get("limitations", []) or []),
        }
        normalized["safety"] = cls._dental_safety(body, normalized)
        normalized["limitations"] = list(dict.fromkeys(normalized["limitations"] + ["This is a visible-only oral observation and cannot assess hidden dental disease, roots, bone, pulp, or periodontal stage."]))
        return normalized

    @classmethod
    def _normalize_feces_result(cls, body, result, release_flags=None):
        source = dict(result or {})
        findings = []
        for raw in source.get("visible_findings", []) or []:
            finding_type = str(raw.get("finding_type", "")) if isinstance(raw, dict) else ""
            finding_flag = {"MUCUS_LIKE": "dog_feces_check_mucus_like_enabled", "FRESH_RED_BLOOD_LIKE": "dog_feces_check_fresh_red_blood_like_enabled", "DARK_BLACK_TAR_LIKE": "dog_feces_check_dark_black_tarry_like_enabled", "FOREIGN_MATERIAL_LIKE": "dog_feces_check_foreign_material_like_enabled", "WORM_SEGMENT_LIKE": "dog_feces_check_worm_segment_like_enabled"}.get(finding_type)
            if not isinstance(raw, dict) or finding_type not in FECES_FINDING_TYPES or (finding_flag and release_flags and not release_flags.get(finding_flag, False)):
                continue
            state = str(raw.get("state", "OBSERVED"))
            state = state if state in FECES_VISIBLE_STATES else "NOT_ASSESSABLE"
            statement = str(raw.get("statement", "Visible stool appearance."))[:500]
            # NOT_OBSERVED is a visual observation, never proof of absence.
            # Replace provider wording that could overclaim (especially for
            # worm-like findings) with a sanctioned observation statement.
            if state == "NOT_OBSERVED" and finding_type == "WORM_SEGMENT_LIKE":
                lower_statement = statement.lower()
                if not any(term in lower_statement for term in ("not observed", "not seen", "not visible")):
                    statement = "Worm-segment-like material was not observed in the visible sample."
            findings.append({"id": str(raw.get("id") or uuid4()), "finding_type": str(raw["finding_type"]), "state": state, "statement": statement, "confidence": str(raw.get("confidence", "UNSPECIFIED")), "source_media_ids": list(raw.get("source_media_ids", []) or []), "source_region": raw.get("source_region"), "lighting_caveat": raw.get("lighting_caveat")})
        context = body.get("owner_context") or {}
        flags = {str(x).upper() for x in (source.get("red_flags", []) or [])}
        for field_name, flag_name in (("collapse", "COLLAPSE"), ("unable_to_keep_water_down", "UNABLE_TO_KEEP_WATER_DOWN"), ("marked_lethargy", "MARKED_LETHARGY"), ("vomiting", "REPEATED_VOMITING"), ("reduced_eating", "REDUCED_EATING"), ("repeated_stools", "REPEATED_STOOLS")):
            if str(context.get(field_name, False)).lower() == "true" or context.get(field_name) is True:
                flags.add(flag_name)
        finding_types = {x["finding_type"] for x in findings}
        if flags & {"COLLAPSE", "UNABLE_TO_KEEP_WATER_DOWN"} or "DARK_BLACK_TAR_LIKE" in finding_types:
            safety = "URGENT_VETERINARY_CONTACT"
        elif flags & {"MARKED_LETHARGY", "REPEATED_VOMITING", "SUBSTANTIAL_FRESH_RED_BLOOD_LIKE"} or "FRESH_RED_BLOOD_LIKE" in finding_types:
            safety = "PROMPT_VETERINARY_CONTACT"
        elif findings or context:
            safety = "PROFESSIONAL_REVIEW_RECOMMENDED"
        else:
            safety = "NORMAL_INFORMATION"
        quality = cls._evidence_quality(source.get("capture_quality", source.get("evidence_quality")))
        consistency = str(source.get("consistency", "UNCERTAIN"))
        if release_flags and not release_flags.get("dog_feces_check_consistency_enabled", False):
            consistency = "UNCERTAIN"
        appearance = str(source.get("visible_appearance", "NOT_ASSESSABLE")) if not release_flags or release_flags.get("dog_feces_check_color_observation_enabled", False) else "NOT_ASSESSABLE"
        return {"result_version": str(source.get("result_version", "1.0.0")), "capture_quality": quality, "consistency": consistency if consistency in FECES_CONSISTENCY_STATES else "UNCERTAIN", "visible_appearance": appearance, "visible_findings": findings, "observations": list(source.get("observations", []) or []), "uncertainties": list(source.get("uncertainties", []) or []), "areas_not_assessable": list(source.get("areas_not_assessable", []) or []) + ["A photo cannot test microscopic parasites, infection, occult blood, microbiome composition, internal-organ disease, or definitive cause."], "visual_risk": str(source.get("visual_risk", "INSUFFICIENT_EVIDENCE")) if str(source.get("visual_risk", "INSUFFICIENT_EVIDENCE")) in FECES_VISUAL_RISK else "INSUFFICIENT_EVIDENCE", "red_flags": sorted(flags), "recommended_actions": list(source.get("recommended_actions", []) or []), "limitations": list(source.get("limitations", []) or []) + ["Visible stool appearance is not laboratory testing and cannot establish or exclude disease."], "safety": safety, "provenance": {"owner_context": "OWNER_REPORTED", "source_media_ids": list(body.get("media_asset_ids") or body.get("source_media_ids") or [])}, "longitudinal_comparison": None}

    @classmethod
    def _normalize_body_result(cls, body, result, release_flags):
        source = dict(result or {})
        observations = []
        for raw in source.get("observations", []) or []:
            if not isinstance(raw, dict) or str(raw.get("observation_type", "")) not in BODY_OBSERVATION_TYPES:
                continue
            observations.append({"id": str(raw.get("id") or uuid4()), "observation_type": str(raw["observation_type"]), "statement": str(raw.get("statement", "Visible body observation."))[:500], "confidence": str(raw.get("confidence", "UNSPECIFIED")), "source_media_ids": list(raw.get("source_media_ids", []) or []), "source_regions": list(raw.get("source_regions", []) or [])})
        category = str(source.get("body_condition_category", "UNCERTAIN"))
        if not release_flags.get("dog_body_condition_category_enabled", False):
            category = "UNCERTAIN"
        estimate = None
        if release_flags.get("dog_body_ai_weight_estimate_enabled", False) and isinstance(source.get("ai_weight_estimate"), dict):
            raw = source["ai_weight_estimate"]
            estimate = {"estimate_type": str(raw.get("estimate_type", "RANGE")), "estimated_value": raw.get("estimated_value"), "estimated_range": raw.get("estimated_range"), "unit": str(raw.get("unit", "UNKNOWN")), "confidence": str(raw.get("confidence", "UNSPECIFIED")), "source_class": "AI_ESTIMATED", "source_media_ids": list(raw.get("source_media_ids", []) or []), "calibration_version": str(raw.get("calibration_version", "UNSPECIFIED")), "limitations": list(raw.get("limitations", []) or []) + ["PETi estimate — not a measured weight"]}
        source_media_ids = list(body.get("media_asset_ids") or body.get("source_media_ids") or [])
        reasons = list(source.get("evidence_quality_reasons", source.get("quality_reasons", [])) or [])
        result = {"result_version": str(source.get("result_version", "1.0.0")), "evidence_quality": cls._evidence_quality(source.get("evidence_quality")), "evidence_quality_reasons": reasons, "body_observations": observations, "observations": observations, "waist_definition": str(source.get("waist_definition", "NOT_ASSESSABLE")), "abdominal_tuck": str(source.get("abdominal_tuck", "NOT_ASSESSABLE")), "rib_outline": str(source.get("rib_outline", "NOT_ASSESSABLE")), "body_condition_category": category if category in BODY_CONDITION_CATEGORIES else "UNCERTAIN", "posture_notes": list(source.get("posture_notes", []) or []), "uncertainties": list(source.get("uncertainties", []) or []), "areas_not_assessable": list(source.get("areas_not_assessable", []) or []), "limitations": list(source.get("limitations", []) or []) + ["This is visible body-contour assistance, not a scale, body-fat analyzer, or diagnosis."], "recommended_actions": list(source.get("recommended_actions", []) or []), "safety": source.get("safety") or {"state": "NORMAL_INFORMATION"}, "provenance": {"source_media_ids": source_media_ids, "weight_source_class": "AI_ESTIMATED" if estimate else None}, "ai_weight_estimate": estimate, "longitudinal_comparison": None}
        return result

    @staticmethod
    def _safe_result(analysis_type, result):
        result = dict(result or {})
        serialized = str(result).lower()
        if any(term in serialized for term in FORBIDDEN_CLAIMS):
            result["guardrail_status"] = "RESTRICTED"
            result["limitations"] = list(dict.fromkeys(list(result.get("limitations", [])) + ["PETi cannot diagnose or infer hidden medical facts from images."]))
        result.setdefault("evidence_quality", "UNSPECIFIED")
        result.setdefault("evidence_quality_reasons", [])
        result.setdefault("uncertainties", [])
        result.setdefault("recommended_actions", ["Seek veterinary advice for health concerns."])
        result.setdefault("limitations", ["This is visual assistance, not a diagnosis or substitute for veterinary care."])
        result["analysis_type"] = analysis_type
        return result

    def create(self, owner, pet_id, analysis_type, body, idempotency_key=None, billing_exempt=False):
        if analysis_type not in SPECIALIST_TYPES:
            raise SpecialistError("SPECIALIST_TYPE_UNSUPPORTED")
        self._validate_release(analysis_type)
        pet = self._pet(owner, pet_id, analysis_type)
        media_ids = list(body.get("media_asset_ids") or body.get("source_media_ids") or [])
        self._validate_media(owner, pet_id, media_ids, analysis_type)
        self._validate_capture_manifest(analysis_type, body, media_ids)
        fingerprint = hashlib.sha256(repr((analysis_type, pet_id, media_ids, body.get("result"), body.get("candidates"))).encode()).hexdigest()
        if idempotency_key and (owner, idempotency_key) in self.idempotency:
            existing = self.analyses[self.idempotency[(owner, idempotency_key)]]
            if existing.provenance.get("request_fingerprint") != fingerprint:
                raise SpecialistError("IDEMPOTENCY_KEY_REUSED_WITH_DIFFERENT_REQUEST")
            return existing
        funding_id = self._validate_funding(owner, analysis_type, body, billing_exempt)
        has_provider_result = body.get("result") is not None
        if analysis_type == "DOG_INITIAL_SCAN" and has_provider_result:
            result = self._normalize_initial_result(body.get("result"))
        elif analysis_type == "DOG_DENTAL_CHECK" and has_provider_result:
            result = self._normalize_dental_result(body, self._guardrail_result(analysis_type, body.get("result")), self.release_flags)
        elif analysis_type == "DOG_FECES_CHECK" and has_provider_result:
            result = self._normalize_feces_result(body, self._guardrail_result(analysis_type, body.get("result")), self.release_flags)
        elif analysis_type == "DOG_BODY_CHECK" and has_provider_result:
            result = self._normalize_body_result(body, self._guardrail_result(analysis_type, body.get("result")), self.release_flags)
        else:
            result = {"analysis_type": analysis_type, "result_status": "PENDING_PROVIDER_RESULT"}
        now = self.clock()
        capability_pack_version = "UNSPECIFIED"
        species_registry = getattr(self.pets, "species", None)
        if species_registry:
            pack = species_registry.get_capability_pack(getattr(pet, "species", "DOG"))
            capability_pack_version = getattr(pack, "version", "UNSPECIFIED") if pack else "UNSPECIFIED"
        provider_name = body.get("provider", "FAKE")
        provider_model = body.get("provider_model", "specialist-fake-v1")
        analysis = SpecialistAnalysis(
            str(uuid4()), owner, pet_id, analysis_type, media_ids,
            status=SpecialistStatus.COMPLETED if has_provider_result else SpecialistStatus.QUEUED,
            result=result,
            provenance={"source_media_ids": media_ids, "provider": provider_name, "provider_model": provider_model, "provider_config_version": body.get("provider_config_version", "local-v1"),
                        "prompt_version": body.get("prompt_version", "1.0.0"),
                        "schema_version": body.get("schema_version", "1.0.0"),
                        "guardrail_version": body.get("guardrail_version", "1.0.0"),
                        "safety_version": body.get("safety_version", "1.0.0"),
                        "preparation_version": body.get("preparation_version", "1.0.0"),
                        "capability_pack_version": capability_pack_version,
                        "evaluation_certificate_id": body.get("evaluation_certificate_id", self.release_flags.get({"DOG_INITIAL_SCAN": "dog_initial_scan_evaluation_certificate_id", "DOG_DENTAL_CHECK": "dog_dental_check_evaluation_certificate_id", "DOG_FECES_CHECK": "dog_feces_check_evaluation_certificate_id", "DOG_BODY_CHECK": "dog_body_check_evaluation_certificate_id"}.get(analysis_type), "PENDING")),
                        "operation_type": "AI_PHOTO_STANDARD" if analysis_type == "DOG_INITIAL_SCAN" else "AI_SPECIALIST_STANDARD",
                        "funding_reservation_id": body.get("funding_reservation_id"),
                        "funding_source_summary": "ADMIN_EXEMPT" if billing_exempt else "CREDIT_RESERVATION",
                        "capture_manifest": body.get("capture_manifest"),
                        "owner_context": body.get("owner_context"),
                        "request_fingerprint": fingerprint},
            created_at=now, updated_at=now,
        )
        self.pending_requests[analysis.id] = dict(body)
        if funding_id and has_provider_result:
            try:
                self.credits.consume(funding_id, f"specialist-{analysis.id}")
            except Exception as exc:
                raise SpecialistError("SPECIALIST_FUNDING_CONSUME_FAILED") from exc
        self.analyses[analysis.id] = analysis
        self._save("specialist_analyses", analysis)
        if idempotency_key:
            self.idempotency[(owner, idempotency_key)] = analysis.id
        if analysis_type == "DOG_INITIAL_SCAN":
            self._create_initial_candidates(analysis, body.get("candidates", []) or result.get("profile_candidates", []))
        return analysis

    def complete_task(self, owner, analysis_id, result, provider="GEMINI", provider_model="cloud-specialist"):
        """Complete a queued specialist task exactly once per analysis.

        Cloud Tasks may redeliver a request while the first delivery is still
        committing.  Serialize the terminal transition, funding consumption,
        candidate creation, and durable write so the second delivery observes
        COMPLETED instead of consuming the reservation again.
        """
        with self.lock:
            return self._complete_task(owner, analysis_id, result, provider, provider_model)

    def complete_task_internal(self, analysis_id, result, provider="GEMINI", provider_model="cloud-specialist"):
        """Complete a persisted analysis using its stored owner scope.

        Internal task payloads identify an analysis, never an authoritative
        owner.  The owner is resolved from the persisted analysis before the
        normal owner/media/funding checks run.
        """
        with self.lock:
            analysis = self.analyses.get(analysis_id)
            if not analysis and self.store and hasattr(self.store, "all"):
                self._hydrate()
                analysis = self.analyses.get(analysis_id)
            if not analysis or analysis.deleted_at:
                raise SpecialistError("SPECIALIST_NOT_FOUND")
            return self._complete_task(analysis.owner_user_id, analysis_id, result, provider, provider_model)

    def _complete_task(self, owner, analysis_id, result, provider="GEMINI", provider_model="cloud-specialist"):
        analysis = self._owned(owner, analysis_id)
        if analysis.status == SpecialistStatus.COMPLETED:
            return analysis
        body = self.pending_requests.get(analysis_id, {"media_asset_ids": analysis.media_asset_ids, "capture_manifest": analysis.provenance.get("capture_manifest"), "owner_context": analysis.provenance.get("owner_context")})
        body["result"] = result
        body["provider"] = provider
        body["provider_model"] = provider_model
        if analysis.analysis_type == "DOG_INITIAL_SCAN":
            normalized = self._normalize_initial_result(result)
        elif analysis.analysis_type == "DOG_DENTAL_CHECK":
            normalized = self._normalize_dental_result(body, self._guardrail_result(analysis.analysis_type, result), self.release_flags)
        elif analysis.analysis_type == "DOG_FECES_CHECK":
            normalized = self._normalize_feces_result(body, self._guardrail_result(analysis.analysis_type, result), self.release_flags)
        elif analysis.analysis_type == "DOG_BODY_CHECK":
            normalized = self._normalize_body_result(body, self._guardrail_result(analysis.analysis_type, result), self.release_flags)
        else:
            normalized = self._safe_result(analysis.analysis_type, result)
        funding_id = analysis.provenance.get("funding_reservation_id")
        if funding_id and self.credits:
            try:
                self.credits.consume(funding_id, f"specialist-{analysis.id}")
            except Exception as exc:
                raise SpecialistError("SPECIALIST_FUNDING_CONSUME_FAILED") from exc
        analysis.result = normalized
        analysis.status = SpecialistStatus.COMPLETED
        analysis.updated_at = self.clock()
        analysis.provenance.update({"provider": provider, "provider_model": provider_model})
        if analysis.analysis_type == "DOG_INITIAL_SCAN":
            self._create_initial_candidates(analysis, body.get("candidates", []) or normalized.get("profile_candidates", []))
        self._save("specialist_analyses", analysis)
        self.pending_requests.pop(analysis_id, None)
        return analysis

    def _create_initial_candidates(self, analysis, raw_candidates):
        for raw in raw_candidates:
            field_type = str(raw.get("field_type", ""))
            if field_type not in INITIAL_SCAN_FIELDS or field_type in FORBIDDEN_INITIAL_FIELDS:
                continue
            flag = INITIAL_SCAN_FEATURE_FLAGS.get(field_type)
            if flag and self.release_flags and not self.release_flags.get(flag, False):
                continue
            value = str(raw.get("candidate_value", "")).strip()
            if not value:
                continue
            item = InitialScanCandidate(str(uuid4()), analysis.id, analysis.owner_user_id, analysis.animal_id,
                field_type, value, raw.get("evidence_quality", "UNSPECIFIED"), created_at=self.clock())
            self.candidates[item.id] = item
            self._save("initial_scan_candidates", item)

    def list(self, owner, pet_id, analysis_type):
        self._pet(owner, pet_id)
        return sorted((x for x in self.analyses.values() if x.owner_user_id == owner and x.animal_id == pet_id and x.analysis_type == analysis_type and not x.deleted_at), key=lambda x: x.created_at, reverse=True)

    def get(self, owner, analysis_id):
        return self._owned(owner, analysis_id)

    def get_by_id_internal(self, analysis_id):
        item = self.analyses.get(analysis_id)
        if not item and self.store and hasattr(self.store, "all"):
            self._hydrate()
            item = self.analyses.get(analysis_id)
        if not item or item.deleted_at:
            raise SpecialistError("SPECIALIST_NOT_FOUND")
        return item

    def candidates_for(self, owner, analysis_id):
        self._owned(owner, analysis_id)
        return [x for x in self.candidates.values() if x.owner_user_id == owner and x.analysis_id == analysis_id]

    def review_initial_candidate(self, owner, candidate_id, action, value=None):
        item = self.candidates.get(candidate_id)
        if not item or item.owner_user_id != owner:
            raise SpecialistError("INITIAL_SCAN_CANDIDATE_NOT_FOUND")
        if item.status != "PENDING_REVIEW":
            raise SpecialistError("INITIAL_SCAN_CANDIDATE_ALREADY_REVIEWED")
        if action not in {"confirm", "correct", "reject", "skip"}:
            raise SpecialistError("INITIAL_SCAN_PROFILE_VALUE_INVALID")
        pet = self._pet(owner, item.animal_id, "DOG_INITIAL_SCAN")
        profile_attributes = {
            "COAT_COLOR": "coat_color", "COAT_PATTERN": "coat_pattern", "COAT_LENGTH": "coat_length",
            "POSSIBLE_BREED_TYPE": "possible_breed_type", "LIFE_STAGE_APPEARANCE": "life_stage_appearance",
            "MORPHOLOGY_DESCRIPTION": "morphology_description", "DISTINGUISHING_FEATURES": "distinguishing_features",
        }
        profile_attribute = profile_attributes.get(item.field_type)
        server_value = getattr(pet, profile_attribute, None) if profile_attribute else None
        if action == "confirm" and server_value and str(server_value).strip() != item.candidate_value:
            raise SpecialistError("INITIAL_SCAN_PROFILE_CONFLICT")
        if action == "correct" and not str(value or "").strip():
            raise SpecialistError("INITIAL_SCAN_PROFILE_VALUE_INVALID")
        item.status = {"confirm": "CONFIRMED", "correct": "CORRECTED", "reject": "REJECTED", "skip": "SKIPPED"}[action]
        item.provenance_status = {
            "confirm": "USER_CONFIRMED",
            "correct": "USER_CORRECTED",
            "reject": "AI_SUGGESTED",
            "skip": "AI_SUGGESTED",
        }[action]
        item.review_action = action.upper(); item.reviewed_value = str(value).strip() if action == "correct" else None; item.reviewed_at = self.clock()
        if action in {"confirm", "correct"} and profile_attribute and hasattr(self.pets, "update_profile_fields"):
            reviewed_value = item.reviewed_value or item.candidate_value
            updated = self.pets.update_profile_fields(
                owner, item.animal_id, {item.field_type: reviewed_value},
                "USER_CONFIRMED" if action == "confirm" else "USER_CORRECTED",
            )
            if updated is None:
                raise SpecialistError("INITIAL_SCAN_PET_NOT_FOUND")
        review = InitialScanReview(str(uuid4()), item.id, owner, action.upper(), item.reviewed_value or item.candidate_value, self.clock())
        self.candidate_reviews.append(review)
        self._save("initial_scan_candidate_reviews", review)
        self._save("initial_scan_candidates", item)
        return item

    def delete(self, owner, analysis_id):
        item = self._owned(owner, analysis_id)
        funding_id = item.provenance.get("funding_reservation_id")
        if funding_id and self.credits:
            reservation = self.credits.reservations.get(funding_id)
            if reservation and str(reservation.status) == "RESERVED":
                self.credits.release(funding_id, "SPECIALIST_DELETED_BEFORE_PROVIDER")
        item.deleted_at = self.clock(); item.status = SpecialistStatus.DELETED; item.updated_at = item.deleted_at
        self._save("specialist_analyses", item)
        return item

    def comparison(self, owner, analysis_id):
        current = self._owned(owner, analysis_id)
        if current.analysis_type == "DOG_FECES_CHECK" and self.release_flags and not self.release_flags.get("dog_feces_longitudinal_compare_enabled", False):
            raise SpecialistError("FECES_CHECK_COMPARISON_NOT_AVAILABLE")
        if current.analysis_type == "DOG_BODY_CHECK" and self.release_flags and not self.release_flags.get("dog_body_longitudinal_compare_enabled", False):
            raise SpecialistError("BODY_CHECK_COMPARISON_NOT_AVAILABLE")
        prior = [x for x in self.list(owner, current.animal_id, current.analysis_type) if x.id != current.id and x.created_at < current.created_at]
        if not prior:
            return {"status": "NOT_COMPARABLE", "reason": "NO_PRIOR_COMPATIBLE_RESULT", "current_analysis_id": current.id}
        previous = prior[0]
        if current.analysis_type != "DOG_BODY_CHECK":
            return {"status": "NOT_COMPARABLE", "reason": "SPECIALIST_COMPARISON_REQUIRES_REVIEWED_EVIDENCE", "current_analysis_id": current.id, "prior_analysis_id": previous.id}
        current_manifest = current.provenance.get("capture_manifest") or {}
        prior_manifest = previous.provenance.get("capture_manifest") or {}
        current_steps = {str(x.get("step_id")) for x in current_manifest.get("steps", []) if isinstance(x, dict)}
        prior_steps = {str(x.get("step_id")) for x in prior_manifest.get("steps", []) if isinstance(x, dict)}
        if not {"SIDE_STANDING", "TOP_STANDING"}.issubset(current_steps & prior_steps):
            return {"status": "NOT_COMPARABLE", "reason": "STANDARDIZED_CAPTURE_REQUIRED", "current_analysis_id": current.id, "prior_analysis_id": previous.id}
        current_types = {x.get("observation_type") for x in current.result.get("observations", [])}
        prior_types = {x.get("observation_type") for x in previous.result.get("observations", [])}
        current_category = current.result.get("body_condition_category")
        prior_category = previous.result.get("body_condition_category")
        if current_category == prior_category and current_types == prior_types:
            label = "STABLE"
        elif current_category in {"ROUNDED_APPEARANCE"} and prior_category in {"LEAN_APPEARANCE", "BALANCED_APPEARANCE"}:
            label = "WORSENED"
        elif current_category in {"LEAN_APPEARANCE"} and prior_category in {"ROUNDED_APPEARANCE", "BALANCED_APPEARANCE"}:
            label = "IMPROVED"
        elif current_types - prior_types:
            label = "NEW"
        elif prior_types - current_types:
            label = "IMPROVED"
        else:
            label = "NOT_COMPARABLE"
        return {"status": label, "comparison_domain": "VISIBLE_BODY_APPEARANCE", "current_analysis_id": current.id, "prior_analysis_id": previous.id, "limitations": ["This comparison describes visible appearance only and does not indicate disease progression."]}

    @staticmethod
    def public(value):
        return asdict(value)

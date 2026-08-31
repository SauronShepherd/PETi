"""Phase 14 privacy export and account-deletion orchestration."""
from dataclasses import asdict
from datetime import UTC, datetime
from threading import RLock

from .lifecycle import (
    AccountDeletionJob,
    DeletionDependencyResolver,
    DeletionPlan,
    DeletionResidualVerifier,
    DeletionTaskGate,
    MediaStorageResidualInventory,
    OwnerCollectionResidualInventory,
)


class PrivacyError(ValueError):
    pass


class PrivacyService:
    def __init__(self, pets, media, phase6, records=None, specialists=None, reports=None, users=None, credits=None, premium=None, operations=None, care_advanced=None, collaboration=None, future=None, portability=None, memory=None, agents=None, store=None, clock=None):
        self.pets, self.media, self.phase6 = pets, media, phase6
        self.records, self.specialists, self.reports, self.users = records, specialists, reports, users
        self.credits, self.premium, self.operations = credits, premium, operations
        self.care_advanced = care_advanced
        self.collaboration = collaboration
        self.future = future
        self.portability = portability
        self.memory = memory
        self.agents = agents
        self.lab = None
        self.store = store
        self.clock = clock or (lambda: datetime.now(UTC))
        self.deletion_planner = DeletionDependencyResolver()
        # All locally dispatched work must observe the same account freeze as
        # the deletion state machine. Cloud adapters can share this boundary
        # when they are wired into the deployed task handler.
        self.deletion_task_gate = DeletionTaskGate()
        inventory = {}
        metadata_store = getattr(media, "metadata_store", None)
        storage = getattr(media, "storage", None)
        if metadata_store is not None and storage is not None:
            inventory["media_objects"] = MediaStorageResidualInventory(metadata_store, storage)
        phase6_store = getattr(phase6, "store", None)
        if phase6_store is not None:
            for collection in ("measurements", "care_items", "care_occurrences", "device_registrations"):
                inventory[collection] = OwnerCollectionResidualInventory(phase6_store, collection)
        for domain, repository in (("pets", pets),):
            if hasattr(repository, "list_owned"):
                inventory[domain] = lambda owner, repo=repository: sum(
                    1 for item in repo.list_owned(owner) if not getattr(item, "deleted_at", None)
                )
        for domain, repository, collection in (
            ("records", records, "documents"),
            ("analyses", specialists, "analyses"),
            ("weekly_reports", reports, "reports"),
        ):
            values = getattr(repository, collection, None) if repository else None
            if isinstance(values, dict):
                inventory[domain] = lambda owner, values=values: sum(
                    1 for item in values.values()
                    if getattr(item, "owner_user_id", None) == owner and not getattr(item, "deleted_at", None)
                )
        if self.care_advanced:
            inventory["advanced_care_records"] = lambda owner: sum(
                1 for item in self.care_advanced.records.values()
                if item.owner_user_id == owner and not item.deleted_at
            )
        if self.collaboration:
            inventory["collaboration_memberships"] = lambda owner: sum(
                1 for item in self.collaboration.memberships.values()
                if (item.owner_user_id == owner or item.member_user_id == owner)
                and item.status != "REVOKED"
            )
        if self.future:
            inventory["future_domain_items"] = lambda owner: sum(
                1 for item in self._future_owner_items(self.future, owner)
            )
        if self.portability:
            inventory["portability_share_grants"] = lambda owner: sum(
                1 for item in self.portability.shares.values()
                if item.owner_user_id == owner and not item.revoked_at
            )
        if self.memory:
            inventory["personal_pet_memories"] = lambda owner: sum(
                1 for item in self.memory.memories.values() if item.owner_user_id == owner
            )
        if self.agents:
            inventory.update(self._agent_residual_inventory(self.agents))
        if self.operations:
            inventory["support_cases"] = lambda owner: sum(
                1 for item in self.operations.support.values()
                if item.owner_user_id == owner
            )
        self.deletion_verifier = DeletionResidualVerifier(inventory)
        self.deletion_jobs: dict[tuple[str, str], AccountDeletionJob] = {}
        self._deletion_lock = RLock()
        self._hydrate_deletion_jobs()

    @staticmethod
    def _agent_residual_inventory(agents):
        def owned_run_ids(owner):
            return {item.id for item in agents.runs.values() if item.owner_user_id == owner}

        return {
            "agent_sessions": lambda owner: sum(1 for item in agents.sessions.values() if item.owner_user_id == owner),
            "agent_runs": lambda owner: len(owned_run_ids(owner)),
            "agent_context_requests": lambda owner: sum(1 for item in agents.context_requests.values() if item.get("run_id") in owned_run_ids(owner)),
            "agent_actions": lambda owner: sum(1 for item in agents.actions.values() if item.get("run_id") in owned_run_ids(owner)),
        }

    @staticmethod
    def _future_owner_items(future, owner):
        if hasattr(future, "owner_items"):
            return future.owner_items(owner)
        return [item for item in future.items.values() if item.owner_user_id == owner and not item.deleted_at]

    def attach_agents(self, agents) -> None:
        """Attach the agent domain and include it in residual verification."""
        self.agents = agents
        self.deletion_verifier.inventory.update(self._agent_residual_inventory(agents))

    def attach_operations(self, operations) -> None:
        """Attach operational account data to residual verification."""
        self.operations = operations
        self.deletion_verifier.inventory["support_cases"] = lambda owner: sum(
            1 for item in operations.support.values()
            if item.owner_user_id == owner
        )

    def attach_lab(self, repository) -> None:
        """Attach personal Lab records to export, deletion and residual verification."""
        self.lab = repository
        for domain, getter in (
            ("lab_responses", repository.list_responses),
            ("lab_feedback", repository.list_feedback),
            ("lab_run_traces", repository.list_runs),
            ("lab_safety_reports", repository.list_safety_reports),
            ("lab_outcomes", repository.list_outcomes),
            ("lab_step_traces", repository.list_steps),
            ("lab_model_calls", repository.list_model_calls),
            ("lab_tool_calls", repository.list_tool_calls),
            ("lab_safety_decisions", repository.list_safety_decisions),
            ("lab_evidence_usage", repository.list_evidence_usage),
        ):
            self.deletion_verifier.inventory[domain] = lambda owner, getter=getter: sum(
                1 for item in getter() if getattr(item, "owner_user_id", None) == owner
            )

    def _hydrate_deletion_jobs(self) -> None:
        if not self.store or not hasattr(self.store, "all"):
            return
        try:
            rows = self.store.all("privacy_deletion_jobs")
        except Exception:  # noqa: BLE001 - unavailable state must not authorize deletion completion
            rows = []
        for row in rows:
            try:
                plan_data = row["plan"]
                plan = DeletionPlan(
                    plan_data["owner_user_id"], plan_data["entities"],
                    plan_data["idempotency_key"], plan_data.get("dependencies", {}),
                )
                job = AccountDeletionJob(plan, residual_verifier=self.deletion_verifier, task_gate=self.deletion_task_gate)
                job.state = row["state"]
                job.completed = list(row.get("completed", []))
                self.deletion_jobs[(plan.owner_user_id, plan.idempotency_key)] = job
            except (KeyError, TypeError, ValueError):
                continue

    def _save_deletion_job(self, job: AccountDeletionJob) -> None:
        if self.store and hasattr(self.store, "put_raw"):
            self.store.put_raw(
                "privacy_deletion_jobs",
                f"{job.plan.owner_user_id}:{job.plan.idempotency_key}",
                {**job.snapshot(), "plan": asdict(job.plan)},
            )

    def export(self, owner):
        pets = self.pets.list(owner)
        pet_ids = {x.id for x in pets}
        payload = {
            "export_version": "1.0.0",
            "generated_at": self.clock(),
            "provenance_policy": "Each exported record retains its canonical domain identifiers and source references when the domain provides them.",
            "pets": [asdict(x) for x in pets],
            "measurements": [asdict(x) for x in self.phase6.measurements.values() if x.owner_user_id == owner and x.animal_id in pet_ids and not x.deleted_at],
            "care": [asdict(x) for x in self.phase6.care.values() if x.owner_user_id == owner and x.animal_id in pet_ids and not x.deleted_at],
            "media": [asdict(x) for x in self.media.list_owned(owner)],
        }
        if hasattr(self.phase6, "occurrences"):
            payload["care_occurrences"] = [
                asdict(x) for x in self.phase6.occurrences.values()
                if x.owner_user_id == owner and x.animal_id in pet_ids
            ]
        if hasattr(self.phase6, "notification_preferences"):
            preferences = self.phase6.notification_preferences.get(owner)
            payload["notification_preferences"] = [asdict(preferences)] if preferences else []
        if self.specialists:
            payload["specialist_analyses"] = [asdict(x) for x in self.specialists.analyses.values() if x.owner_user_id == owner and not x.deleted_at]
        if self.credits:
            payload["credit_grants"] = [asdict(x) for x in self.credits.grants.values() if x.user_id == owner]
            payload["credit_ledger"] = [asdict(x) for x in self.credits.ledger if x.user_id == owner]
            payload["credit_reservations"] = [asdict(x) for x in self.credits.reservations.values() if x.user_id == owner]
        if self.premium:
            payload["premium_entitlements"] = [self.premium.public(x) for x in self.premium.entitlements.values() if x.owner_user_id == owner]
        if self.records:
            payload["records"] = [asdict(x) for x in self.records.documents.values() if x.owner_user_id == owner and not x.deleted_at]
            payload["candidate_facts"] = [asdict(x) for x in self.records.candidates.values() if x.owner_user_id == owner]
            payload["documented_facts"] = [asdict(x) for x in self.records.facts.values() if x.owner_user_id == owner and not x.deleted_at]
        if self.reports:
            payload["weekly_reports"] = [asdict(x) for x in self.reports.reports.values() if x.owner_user_id == owner and not x.deleted_at]
        if self.operations:
            payload["support_cases"] = [asdict(x) for x in self.operations.support.values() if x.owner_user_id == owner]
        if self.care_advanced:
            payload["advanced_care_records"] = [asdict(x) for x in self.care_advanced.records.values() if x.owner_user_id == owner and not x.deleted_at]
        if self.collaboration:
            payload["collaboration_memberships"] = [asdict(x) for x in self.collaboration.memberships.values() if x.owner_user_id == owner or x.member_user_id == owner]
        if self.future:
            payload["future_domain_items"] = [self.future.public(x) for x in self._future_owner_items(self.future, owner)]
        if self.portability:
            payload["portability_share_grants"] = []
            for grant in self.portability.shares.values():
                if grant.owner_user_id == owner and not grant.revoked_at:
                    exported_grant = asdict(grant)
                    exported_grant.pop("token_digest", None)
                    payload["portability_share_grants"].append(exported_grant)
        if self.memory:
            payload["personal_pet_memories"] = [asdict(x) for x in self.memory.memories.values() if x.owner_user_id == owner]
        if self.agents:
            owned_run_ids = {x.id for x in self.agents.runs.values() if x.owner_user_id == owner and not x.deleted_at}
            payload["agent_sessions"] = [asdict(x) for x in self.agents.sessions.values() if x.owner_user_id == owner]
            payload["agent_runs"] = [asdict(x) for x in self.agents.runs.values() if x.owner_user_id == owner and not x.deleted_at]
            payload["agent_context_requests"] = [x for x in self.agents.context_requests.values() if x.get("run_id") in owned_run_ids]
            payload["agent_actions"] = [x for x in self.agents.actions.values() if x.get("run_id") in owned_run_ids]
        if self.lab:
            payload["lab_responses"] = [x.public() for x in self.lab.list_responses() if x.owner_user_id == owner and not x.deleted_at]
            payload["lab_feedback"] = [x.public() for x in self.lab.list_feedback() if x.owner_user_id == owner and not x.removed_at]
            payload["lab_outcomes"] = [x.public() for x in self.lab.list_outcomes() if x.owner_user_id == owner and not x.removed_at]
            # Internal prompts, comments, costs, reviewer identity and audit events are intentionally excluded.
        domains = [key for key, value in payload.items() if isinstance(value, list)]
        payload["export_manifest"] = {
            "owner_user_id": owner,
            "domains": sorted(domains),
            "record_counts": {key: len(payload[key]) for key in sorted(domains)},
            "canonical_identifiers_preserved": True,
        }
        return payload

    def export_pet(self, owner, pet_id):
        """Return only pet-scoped material for a portability package."""
        if not isinstance(pet_id, str) or not pet_id:
            raise ValueError("PET_NOT_FOUND")
        payload = self.export(owner)
        pets = [pet for pet in payload.get("pets", []) if pet.get("id") == pet_id]
        if not pets:
            raise ValueError("PET_NOT_FOUND")
        scoped = {}
        for key, value in payload.items():
            if not isinstance(value, list):
                continue
            if key == "pets":
                scoped[key] = pets
                continue
            scoped[key] = [
                row for row in value
                if isinstance(row, dict)
                and (row.get("pet_id") == pet_id or row.get("animal_id") == pet_id)
            ]
        scoped["export_version"] = payload["export_version"]
        scoped["generated_at"] = payload["generated_at"]
        scoped["provenance_policy"] = payload["provenance_policy"]
        return scoped

    def _perform_delete_account(self, owner, plan):
        """Execute domain deletion adapters; caller owns confirmation/idempotency."""
        self.deletion_task_gate.freeze(owner)
        ordered_domains = self.deletion_planner.ordered_domains(plan)
        domains = set(ordered_domains)
        deleted = {"pets": 0, "media": 0, "records": 0, "facts": 0, "analyses": 0, "reports": 0}
        if hasattr(self.phase6, "remove_device_registrations"):
            deleted["device_registrations"] = self.phase6.remove_device_registrations(owner)
        if self.users and hasattr(self.users, "tombstone"):
            self.users.tombstone(owner)
        for pet in list(self.pets.list(owner)):
            if "records" in domains and self.records:
                for document in list(self.records.documents.values()):
                    if document.owner_user_id == owner and document.animal_id == pet.id and not document.deleted_at:
                        try: self.records.delete(owner, document.id, confirm_dependencies=True); deleted["records"] += 1
                        except Exception:  # noqa: BLE001, S110
                            pass
            if "analyses" in domains and self.specialists:
                for analysis in list(self.specialists.analyses.values()):
                    if analysis.owner_user_id == owner and analysis.animal_id == pet.id and not analysis.deleted_at:
                        self.specialists.delete(owner, analysis.id); deleted["analyses"] += 1
            if "reports" in domains and self.reports:
                for report in self.reports.reports.values():
                    if report.owner_user_id == owner and report.animal_id == pet.id and getattr(report, "deleted_at", None) is None:
                        # Reports are retained only as an auditable tombstone in
                        # the local store; they must not remain visible/exportable.
                        report.deleted_at = self.clock()
                        if self.reports.store and hasattr(self.reports.store, "put_raw"):
                            self.reports.store.put_raw("weekly_reports", report.id, asdict(report))
                        deleted["reports"] += 1
            if "media" in domains:
                for media in list(self.media.list_owned(owner)):
                    if media.animal_id == pet.id:
                        try: self.media.delete(owner, media.id); deleted["media"] += 1
                        except Exception:  # noqa: BLE001, S110
                            pass
            if "pets" in domains and self.pets.delete(owner, pet.id): deleted["pets"] += 1
        # Do not make deletion completeness depend on a healthy pet foreign
        # key.  Imports, legacy rows, and partially-created records can be
        # owner-scoped without a currently visible pet; those rows still
        # belong to the account and must be processed by the same plan.
        if "records" in domains and self.records:
            for document in list(self.records.documents.values()):
                if document.owner_user_id == owner and not document.deleted_at:
                    try:
                        self.records.delete(owner, document.id, confirm_dependencies=True)
                        deleted["records"] += 1
                    except Exception:  # noqa: BLE001, S110
                        pass
        if "analyses" in domains and self.specialists:
            for analysis in list(self.specialists.analyses.values()):
                if analysis.owner_user_id == owner and not analysis.deleted_at:
                    self.specialists.delete(owner, analysis.id)
                    deleted["analyses"] += 1
        if "reports" in domains and self.reports:
            for report in self.reports.reports.values():
                if report.owner_user_id == owner and getattr(report, "deleted_at", None) is None:
                    report.deleted_at = self.clock()
                    if self.reports.store and hasattr(self.reports.store, "put_raw"):
                        self.reports.store.put_raw("weekly_reports", report.id, asdict(report))
                    deleted["reports"] += 1
        if "media" in domains:
            for media in list(self.media.list_owned(owner)):
                try:
                    self.media.delete(owner, media.id)
                    deleted["media"] += 1
                except Exception:  # noqa: BLE001, S110
                    pass
        if "records" in domains and self.records:
            now = self.clock()
            for candidate in self.records.candidates.values():
                if candidate.owner_user_id == owner and candidate.status.name != "REJECTED":
                    candidate.status = type(candidate.status).REJECTED
                    candidate.reviewed_at = now
                    self.records._save("candidate_facts", candidate)
            for fact in self.records.facts.values():
                if fact.owner_user_id == owner and not fact.deleted_at:
                    fact.deleted_at = now
                    fact.updated_at = now
                    self.records._save("documented_facts", fact)
        if "measurements" in domains and hasattr(self.phase6, "remove_owner_data"):
            # Phase 6 owns both canonical measurements and the care/notification
            # graph.  Delegate the complete owner-scoped purge so occurrences
            # cannot survive after their parent care item is removed.
            self.phase6.remove_owner_data(owner)
        elif "measurements" in domains:
            for item in self.phase6.measurements.values():
                if item.owner_user_id == owner and not item.deleted_at:
                    item.deleted_at = self.clock(); self.phase6._persist("measurements", item)
        now = self.clock()
        if self.care_advanced and "records" in domains:
            for item in self.care_advanced.records.values():
                if item.owner_user_id == owner and not item.deleted_at:
                    item.deleted_at = now; item.updated_at = now; item.status = "DELETED"
                    if getattr(self.care_advanced, "store", None) and hasattr(self.care_advanced.store, "put"):
                        self.care_advanced.store.put("care_records", item)
        if self.collaboration:
            for item in self.collaboration.memberships.values():
                if (item.owner_user_id == owner or item.member_user_id == owner) and item.status != "REVOKED":
                    item.status = "REVOKED"
                    if getattr(self.collaboration, "store", None) and hasattr(self.collaboration.store, "put"):
                        self.collaboration.store.put("collaboration_memberships", item)
        if self.future:
            if hasattr(self.future, "delete_owner"):
                self.future.delete_owner(owner, now)
            else:
                for item in self._future_owner_items(self.future, owner):
                    item.deleted_at = now; item.updated_at = now; item.status = "DELETED"
        if self.portability:
            for item in self.portability.shares.values():
                if item.owner_user_id == owner and not item.revoked_at:
                    item.revoked_at = now
                    if getattr(self.portability, "store", None) and hasattr(self.portability.store, "put"):
                        self.portability.store.put("portability_share_grants", item)
        if self.memory:
            self.memory.delete_owner(owner)
        if self.agents:
            owned_run_ids = {x.id for x in self.agents.runs.values() if x.owner_user_id == owner}
            for session_id, session in list(self.agents.sessions.items()):
                if session.owner_user_id == owner:
                    self.agents.sessions.pop(session_id, None)
                    if self.agents.store and hasattr(self.agents.store, "delete"):
                        self.agents.store.delete("agent_sessions", session_id)
            for run_id, run in list(self.agents.runs.items()):
                if run.owner_user_id == owner:
                    self.agents.runs.pop(run_id, None)
                    if self.agents.store and hasattr(self.agents.store, "delete"):
                        self.agents.store.delete("agent_runs", run_id)
            for collection, values in (("agent_context_requests", self.agents.context_requests), ("agent_actions", self.agents.actions)):
                for item_id, item in list(values.items()):
                    if item.get("run_id") in owned_run_ids:
                        values.pop(item_id, None)
                        if self.agents.store and hasattr(self.agents.store, "delete"):
                            self.agents.store.delete(collection, item_id)
        if self.operations:
            for case_id, case in list(self.operations.support.items()):
                if case.owner_user_id == owner:
                    self.operations.support.pop(case_id, None)
                    if getattr(self.operations, "store", None) and hasattr(self.operations.store, "delete"):
                        self.operations.store.delete("support_cases", case_id)
        if self.lab:
            deleted["lab"] = sum(self.lab.delete_owner_lab_data(owner).values())
        return {"status": "DELETED", "deleted": deleted, "completed_at": self.clock()}

    def delete_account(self, owner, confirm=False, idempotency_key=None):
        with self._deletion_lock:
            return self._delete_account(owner, confirm, idempotency_key)

    def _delete_account(self, owner, confirm=False, idempotency_key=None):
        if not confirm:
            raise PrivacyError("ACCOUNT_DELETE_CONFIRMATION_REQUIRED")
        key = idempotency_key or f"account-delete:{owner}"
        job_key = (owner, key)
        job = self.deletion_jobs.get(job_key)
        if job and job.state == "COMPLETE":
            return {"status": "DELETED", "job": job.snapshot(), "idempotent_replay": True}
        plan = self.deletion_planner.plan(owner, key)
        if not job:
            job = AccountDeletionJob(
                plan,
                residual_verifier=self.deletion_verifier,
                task_gate=self.deletion_task_gate,
            )
            self.deletion_jobs[job_key] = job
            self._save_deletion_job(job)
        # Drive the safety-critical front of the state machine before any
        # destructive adapter runs: freeze the account, then cancel locally
        # registered queued work. Provider-specific cancellation is supplied
        # by the deployed queue adapter, while this boundary remains safe in
        # memory and in tests.
        if job.state == "FREEZE_ACCOUNT":
            job.run_once()
            self._save_deletion_job(job)
        if job.state == "CANCEL_QUEUED_WORK":
            job.run_once()
            self._save_deletion_job(job)
        result = self._perform_delete_account(owner, plan)
        # In-memory adapters expose their remaining entities directly; cloud
        # adapters must supply an equivalent residual count during reconciliation.
        remaining = {
            "pets": len(self.pets.list(owner)),
            "media": len(self.media.list_owned(owner)),
            "records": sum(1 for x in getattr(self.records, "documents", {}).values() if x.owner_user_id == owner and not x.deleted_at),
            "measurements": sum(1 for x in self.phase6.measurements.values() if x.owner_user_id == owner and not x.deleted_at),
        }
        job.completed.extend(["DELETE_DERIVED_DATA", "DELETE_CANONICAL_DATA", "DELETE_OBJECTS"])
        job.state = "VERIFY_NO_RESIDUAL_DATA"
        verification = self.deletion_verifier.verify(owner, remaining)
        if verification["verified"]:
            job.completed.append("VERIFY_NO_RESIDUAL_DATA")
            job.state = "COMPLETE"
        else:
            job.state = "FAILED_RETRYABLE"
        self._save_deletion_job(job)
        return {**result, "job": job.snapshot(), "verification": verification}

    def deletion_status(self, owner, idempotency_key):
        job = self.deletion_jobs.get((owner, idempotency_key))
        if not job:
            raise PrivacyError("DELETION_JOB_NOT_FOUND")
        return job.snapshot()

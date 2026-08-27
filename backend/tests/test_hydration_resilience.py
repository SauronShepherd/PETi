from app.advertising.service import RewardService
from app.agents.contracts import AgentOrchestrator
from app.billing.premium import PremiumService
from app.credits.service import CreditService
from app.media.service import MediaService
from app.phase6 import Phase6Service
from app.records.vault import RecordVaultService
from app.reports.service import WeeklyReportService
from app.specialists.service import SpecialistService


class UnavailableStore:
    @staticmethod
    def list_all(_collection):
        raise RuntimeError("temporary outage")

    def list_all_assets(self):
        raise RuntimeError("temporary outage")

    def list_all_sessions(self):
        raise RuntimeError("temporary outage")


class MalformedAgentStore:
    @staticmethod
    def all(collection):
        return ["not-an-agent-row"] if collection.startswith("agent_") else []


class Pets:
    @staticmethod
    def get(_owner, _pet_id):
        return object()


def test_credit_hydration_does_not_crash_when_journal_is_unavailable():
    assert CreditService(persistence=UnavailableStore()).grants == {}


def test_media_hydration_does_not_crash_when_metadata_is_unavailable():
    service = MediaService(Pets(), metadata_store=UnavailableStore())
    assert service.assets == {} and service.sessions == {}


def test_agent_specialist_and_report_hydration_do_not_crash_on_store_outage():
    pets = Pets()
    assert AgentOrchestrator(store=UnavailableStore()).runs == {}
    assert SpecialistService(pets, [], store=UnavailableStore()).analyses == {}
    assert WeeklyReportService(pets, [], store=UnavailableStore()).reports == {}


def test_agent_hydration_skips_malformed_context_rows():
    assert AgentOrchestrator(store=MalformedAgentStore()).context_requests == {}


def test_phase6_hydration_does_not_crash_when_store_is_unavailable():
    service = Phase6Service(UnavailableStore())
    assert service.measurements == {} and service.care == {} and service.idempotency == {}


def test_phase6_hydration_skips_non_mapping_rows():
    class Store:
        @staticmethod
        def all(_collection):
            return ["malformed-row"]

    service = Phase6Service(Store())
    assert service.measurements == {} and service.care == {}


def test_records_and_premium_hydration_fail_closed_on_store_outage():
    assert RecordVaultService(Pets(), object(), store=UnavailableStore()).documents == {}
    assert PremiumService(store=UnavailableStore()).entitlements == {}


def test_reward_hydration_does_not_crash_when_journal_is_unavailable():
    assert RewardService(object(), store=UnavailableStore()).intents == {}

import pytest

from infinity_army_acquisition.history_reconcile import CODEONE_REVIEW, select_identity


def row(**changes):
    return {"edition": "n4", "factionFolder": "winterfor", "factionId": None,
            "identityStatus": "unresolved-folder", "commonMembershipIds": [106],
            "issues": [], **changes}


def evidence(**changes):
    return {"historicalCandidateIds": [106], "proposedFactionId": 106, "gitMatch": True,
            "firstObservation": {"commit": "fixture", "folderCandidateIds": [106]}, **changes}


def test_historical_slug_corroborated_by_membership():
    assert select_identity(row(), evidence(), set()) == (106, "inferred-historical-folder-and-membership")


def test_exact_alias_requires_prior_assignment():
    ev = evidence(firstObservation={"commit": "fixture", "folderCandidateIds": [998, 999]},
                  historicalCandidateIds=[998], proposedFactionId=998)
    assert select_identity(row(commonMembershipIds=[998, 999]), ev, {998}) == (
        998, "inferred-historical-byte-alias")
    assert select_identity(row(), ev, set()) == (None, "candidate-needs-review")
    assert select_identity(row(), ev, {999}) == (None, "conflicting-assigned-alias")


def test_codeone_exception_is_scoped_to_reviewed_observation():
    r = row(edition="codeone", factionFolder="nomads", commonMembershipIds=[],
            identityStatus="conflicting-memberships")
    ev = evidence(historicalCandidateIds=[10501], proposedFactionId=10501,
                  firstObservation={"commit": next(iter(CODEONE_REVIEW)), "folderCandidateIds": [10501]})
    assert select_identity(r, ev, set()) == (10501, "inferred-reviewed-codeone-endpoint")
    assert select_identity(row(**{**r, "factionFolder": "aleph"}), ev, set())[0] is None
    ev["firstObservation"]["commit"] = "unreviewed"
    assert select_identity(r, ev, set())[0] is None


@pytest.mark.parametrize("candidate", [None, 106])
def test_ambiguous_historical_evidence_stays_unresolved(candidate):
    assert select_identity(row(), evidence(historicalCandidateIds=[106, 107],
                                           proposedFactionId=candidate), set()) == (None, "unresolved")


def test_prior_assignment_conflict_fails_closed():
    assert select_identity(row(factionId=107), evidence(), set()) == (None, "conflicting-historical-candidate")

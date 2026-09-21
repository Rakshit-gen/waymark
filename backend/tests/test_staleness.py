from backend.agents.staleness import StalenessChecker


def test_flags_retired_entities_only():
    checker = StalenessChecker()
    flags = checker.run(["Jenkins", "Postgres"], retired_names={"Jenkins"})
    assert len(flags) == 1
    assert flags[0]["entity"] == "Jenkins"
    assert "retired" in flags[0]["reason"]


def test_no_flags_when_nothing_retired():
    checker = StalenessChecker()
    assert checker.run(["Postgres"], retired_names={"Jenkins"}) == []


def test_no_entities_means_no_flags():
    checker = StalenessChecker()
    assert checker.run([], retired_names={"Jenkins"}) == []

import pandas as pd

from roster_catalog import (clean_name, display_name, find_catalog_player,
                            handwritten_id, resolve_roster_ids)


def test_names_can_be_entered_without_stats():
    catalog = {"2544": "LeBron James", "203999": "Nikola Jokic"}
    assert find_catalog_player("lebron james", catalog) == "2544"
    assert find_catalog_player("Brand New Rookie", catalog) == "custom:Brand New Rookie"
    assert display_name("custom:Brand New Rookie", catalog) == "Brand New Rookie"


def test_name_normalization():
    assert clean_name("Nikola Jokić") == clean_name("Nikola Jokic")
    assert clean_name("Karl-Anthony Towns") == clean_name("Karl Anthony Towns")


def test_manual_names_resolve_when_data_later_loaded():
    raw = pd.DataFrame({"PLAYER_ID": ["101", "102"],
                        "PLAYER_NAME": ["Nikola Jokic", "LeBron James"]})
    result = resolve_roster_ids(["custom:Nikola Jokić", "102", "custom:Unknown"],
                                ["custom:Nikola Jokić"], raw)
    assert result == (["101", "102"], ["101"], ["custom:Unknown"])


def test_no_stats_never_block_roster_entry():
    result = resolve_roster_ids(["custom:Brand New Rookie"], [], None)
    assert result == ([], [], ["custom:Brand New Rookie"])

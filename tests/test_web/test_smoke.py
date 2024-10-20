from pathlib import Path

import pytest

from cs_wayback_machine.web.deps import (
    get_parser_result_file_path,
    get_parser_result_updated_date_file_path,
)

pytestmark = pytest.mark.picodi_override(
    [
        (
            get_parser_result_file_path,
            lambda: Path(__file__).parent / "rosters.jsonlines",
        ),
        (get_parser_result_updated_date_file_path, lambda: None),
    ]
)


@pytest.fixture()
async def entities_ids(client):
    response = await client.get("/api/entities")
    assert response.status_code == 200
    results = response.json()
    assert results, results
    assert len(results) < 1000
    return results


@pytest.fixture()
def team_ids(entities_ids):
    return [entity_id for entity_id in entities_ids if entity_id.startswith("team:")]


@pytest.fixture()
def player_ids(entities_ids):
    return [entity_id for entity_id in entities_ids if entity_id.startswith("player:")]


async def test_request_main_page(client):
    result = await client.get("/", params={"q": ""}, follow_redirects=True)

    assert result.status_code == 200
    assert "search" in result.text


async def test_request_teams(subtests, client, team_ids):
    for team_id in team_ids:
        with subtests.test(msg="request team page", team_id=team_id):
            result = await client.get(
                "/goto/", params={"q": team_id}, follow_redirects=True
            )

            assert result.status_code == 200
            assert "/teams/" in result.url.path
            assert "liquipedia" in result.text


async def test_request_players(subtests, client, player_ids):
    for player_id in player_ids:
        with subtests.test(msg="request player page", player_id=player_id):
            result = await client.get(
                "/goto/", params={"q": player_id}, follow_redirects=True
            )

            assert result.status_code == 200
            assert "/players/" in result.url.path
            assert "List of Teams" in result.text

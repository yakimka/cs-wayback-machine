from dataclasses import dataclass
from datetime import date, timedelta

from cs_wayback_machine.date_util import DateRange
from cs_wayback_machine.entities import Roster, RosterPlayer


@dataclass(order=True)
class Event:
    date: date
    action: str  # 'start' or 'end'
    player: RosterPlayer


def create_rosters(players: list[RosterPlayer]) -> list[Roster]:
    # Collect events
    events_by_date: dict[date, list[Event]] = {}
    for player in players:
        start_event_date = player.active_period.start
        end_event_date = player.active_period.end
        start_event = Event(date=start_event_date, action="start", player=player)
        end_event = Event(date=end_event_date, action="end", player=player)
        events_by_date.setdefault(start_event_date, []).append(start_event)
        events_by_date.setdefault(end_event_date, []).append(end_event)

    # Sort dates
    sorted_dates = sorted(events_by_date.keys())

    active_players = set()
    previous_active_players: set[RosterPlayer] | None = None
    current_period_start: date | None = None
    rosters = []

    for event_date in sorted_dates:
        events = events_by_date[event_date]
        # Process events
        for event in events:
            if event.action == "start":
                active_players.add(event.player)
            elif event.action == "end":
                active_players.remove(event.player)

        # After processing events, check if active_players changed
        if active_players != previous_active_players:
            if previous_active_players is not None:
                roster_period_end = event_date - timedelta(days=1)
                assert current_period_start is not None
                roster_period = DateRange(
                    start=current_period_start, end=roster_period_end
                )
                roster = Roster(
                    players=list(previous_active_players),
                    active_period=roster_period,
                )
                rosters.append(roster)
            current_period_start = event_date
            previous_active_players = active_players.copy()

    # Handle the last roster if active_players is not empty
    if previous_active_players and active_players:
        roster_period_end = max(
            player.active_period.end for player in previous_active_players
        )
        assert current_period_start is not None
        roster_period = DateRange(start=current_period_start, end=roster_period_end)
        roster = Roster(
            players=list(previous_active_players), active_period=roster_period
        )
        rosters.append(roster)

    return rosters

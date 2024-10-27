from __future__ import annotations

from typing import TYPE_CHECKING

from picodi import Provide, inject

from cs_wayback_machine.deps import get_rosters_storage
from cs_wayback_machine.web.presenters import GlobalDataDTO, present_global_data

if TYPE_CHECKING:
    from cs_wayback_machine.storage import RosterStorage


@inject
def get_global_data(
    rosters_storage: RosterStorage = Provide(get_rosters_storage),
) -> GlobalDataDTO:
    return present_global_data(rosters_storage)

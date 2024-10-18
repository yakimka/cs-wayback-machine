from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

import scrapy

if TYPE_CHECKING:
    from collections.abc import Generator

    from scrapy.http import Response


class TeamsSpider(scrapy.Spider):
    name = "teamsspider"
    start_urls = ["https://liquipedia.net/counterstrike/index.php?title=Category:Teams"]

    def parse(self, response: Response, **kwargs: Any) -> Generator:
        teams = response.css("#mw-pages .mw-content-ltr a::attr(href)").getall()
        yield from response.follow_all(teams, callback=self.parse_teams)

        next_page = response.css('#mw-pages a:contains("next page")::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_teams(self, response: Response) -> Generator:
        team_name = response.css("#firstHeading span::text").get()
        roster_section = response.css("#Player_Roster").xpath(
            "../following-sibling::div"
        )
        tab_names = self._extract_cs_names(roster_section)
        roster_cards = roster_section.css(".roster-card")
        for card_id, item in enumerate(roster_cards, start=1):
            for row in item.css("tr.Player"):
                parent_content_el = row.xpath(
                    r'ancestor::*[re:test(@class, "content\d+")][1]'
                )
                content_class = parent_content_el.xpath("@class").get()
                game_version: str | None = None
                if content_class is not None:
                    if match := re.search(r"content(\d+)", content_class):
                        game_version = tab_names.get(match.group(1))
                else:
                    versions = self._extract_cs_version_from_infobox(response)
                    if len(versions) == 1:
                        game_version = versions[0]
                    else:
                        game_version = None

                extracted_dates = self._extract_dates(row)
                player_url = row.css("td.ID a::attr(href)").get()
                player_url = (
                    response.urljoin(player_url) if player_url is not None else None
                )
                flag_url = row.css("td.ID .flag img::attr(src)").get()
                flag_name = row.css("td.ID .flag img::attr(title)").get("").strip()
                position = row.css("td.Position i::text").get("").strip()
                full_name = row.css("td.Name .LargeStuff::text").get("").strip()
                new_team = (
                    row.css("td.NewTeam .team-template-text a::text").get("").strip()
                )
                team_slug = self._extract_name_from_url(response.url)
                player_id = row.css("td.ID a::text").get().strip()
                player_slug = self._extract_name_from_url(player_url) or ""
                yield {
                    "team_name": team_name,
                    "team_url": response.url,
                    "team_full_name": self._clean_text(team_slug or ""),
                    "team_slug": team_slug,
                    "game_version": game_version,
                    "card_id": card_id,
                    "player_id": player_id,
                    "player_url": player_url,
                    "player_full_id": self._clean_text(player_slug) or player_id,
                    "player_slug": player_slug,
                    "position": position or None,
                    "is_captain": row.css('td.ID i[title="Captain"]').get() is not None,
                    "flag_name": flag_name or None,
                    "flag_url": (
                        response.urljoin(flag_url) if flag_url is not None else None
                    ),
                    "full_name": full_name or None,
                    "new_team": new_team or None,
                    **extracted_dates,
                }

    def _extract_dates(self, node: Response) -> dict[str, str]:
        dates = node.css("td.Date")
        dates_parsed = {}
        for date_el in dates:
            date_type = date_el.css(".MobileStuffDate::text").get()
            date_type = (
                date_type.lower().replace(" ", "_").replace(":", "").strip().strip("_")
            )
            date_value = date_el.css("i::text").get("").strip()
            if not date_value:
                date_value = date_el.css("i abbr::text").get("").strip()
            dates_parsed[date_type] = date_value or None

        raw_dates = {}
        for date_type, value in dates_parsed.items():
            if value is not None:
                raw_dates[f"{date_type}_raw"] = value
                if "?" in value[:4] or value == "-":
                    dates_parsed[date_type] = None
                    continue
                # Fix for 2015-??-??1, 2013-??-02-??, etc
                if len(value) > 4 and value[5] == "?":
                    value = value[:4]
                value = value.replace("?", "").replace("X", "").rstrip("-")
                if len(value) < 4:
                    continue
                parts = value[:10].split("-")
                if "leave" in date_type or "inactive" in date_type:
                    parts.extend(["12", "31"])
                else:
                    parts.extend(["01", "01"])
                dates_parsed[date_type] = "-".join(parts[:3])

        return dates_parsed | raw_dates

    def _extract_cs_names(self, node: Response) -> dict[str, str]:
        tabs = node.css(".nav-tabs li")
        tab_names = {}
        for tab in tabs:
            classes = tab.css("::attr(class)").get("")
            if match := re.search(r"tab(\d+)", classes):
                num = match.group(1)
                if num not in tab_names:
                    text = "".join(tab.xpath(".//text()").getall()).strip()
                    if text.startswith("CS"):
                        tab_names[num] = text
        return tab_names

    def _extract_cs_version_from_infobox(self, response: Response) -> list[str]:
        games_element = response.css('div.infobox-description:contains("Games:")')
        parent_div = games_element.xpath("./parent::div")
        return parent_div.css("a ::text").getall()

    def _extract_name_from_url(self, url: str) -> str | None:
        if not url or "action=edit" in url:
            return None
        return url.split("/")[-1].replace("_", " ")

    def _clean_text(self, text: str) -> str:
        return unquote(text.strip().replace("_", " "))

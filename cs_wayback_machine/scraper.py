from __future__ import annotations

import re
from datetime import date
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, unquote, urlparse

import scrapy
from scrapy.crawler import CrawlerProcess

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

    from scrapy.http import Response


class TeamsSpider(scrapy.Spider):
    name = "teamsspider"
    start_urls = ["https://liquipedia.net/counterstrike/index.php?title=Category:Teams"]

    def parse(self, response: Response, **kwargs: Any) -> Generator:
        teams = response.css("#mw-pages .mw-content-ltr a::attr(href)").getall()
        for team in teams:
            if "User:" in team:
                continue
            yield response.follow(team, callback=self.parse_teams)

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
        for item in roster_cards:
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

                player_url = self._extract_text(
                    row.css("td.ID a::attr(href)"), nullable=True
                )
                if player_url is not None:
                    player_url = response.urljoin(player_url)
                team_slug = self._extract_name_from_url(response.url)
                player_id = self._extract_text(row.css("td.ID a::text"))
                player_slug = self._extract_name_from_url(player_url) or ""
                extracted_dates = self._extract_dates(row)
                yield {
                    "team_unique_name": self._clean_text(team_slug or ""),
                    "team_name": team_name,
                    "team_url": response.url,
                    "player_unique_id": self._clean_text(
                        player_slug or player_id or ""
                    ),
                    "game_version": game_version,
                    "player_id": player_id,
                    "full_name": self._extract_text(
                        row.css("td.Name .LargeStuff::text"), nullable=True
                    ),
                    "player_url": player_url,
                    "is_captain": row.css('td.ID i[title="Captain"]').get() is not None,
                    "position": self._extract_text(
                        row.css("td.Position i::text"), nullable=True
                    ),
                    "flag_name": self._extract_text(
                        row.css("td.ID .flag img::attr(title)"), nullable=True
                    ),
                    "has_invalid_dates": (
                        not extracted_dates
                        or any(key.endswith("_raw") for key in extracted_dates)
                    ),
                    **extracted_dates,
                }

    def _extract_text(self, node: Any, *, nullable: bool = False) -> str | None:
        text = node.get("").strip()
        if nullable:
            return text or None
        return text

    def _extract_dates(self, node: Response) -> dict[str, str | None]:
        dates = node.css("td.Date")
        dates_parsed: dict[str, str | None] = {}
        for date_el in dates:
            date_type_raw = date_el.css(".MobileStuffDate::text").get()
            date_value_raw = date_el.css("i::text").get("")
            if not date_value_raw:
                date_value_raw = date_el.css("i abbr::text").get("")

            date_parser = DateParser(date_type_raw, date_value_raw)
            date_type, date_val, date_raw = date_parser.parse()
            if date_type is None:
                continue
            dates_parsed[date_type] = date_val.isoformat() if date_val else None
            if date_raw is not None:
                dates_parsed[f"{date_type}_raw"] = date_raw

        return dates_parsed

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

    def _extract_name_from_url(self, url: str | None) -> str | None:
        if not url:
            return None
        if "action=edit" in url:
            parsed_url = urlparse(url)
            return parse_qs(parsed_url.query)["title"][0]
        return url.split("/")[-1].replace("_", " ")

    def _clean_text(self, text: str) -> str:
        return unquote(text.strip().replace("_", " "))


class DateParser:
    def __init__(self, date_type: str, date_value: str) -> None:
        self._date_type_raw = date_type
        self._date_value_raw = date_value
        self._date_type: str | None = None
        self._date_value: date | None = None

    def parse(self) -> tuple[str | None, date | None, str | None]:
        self._date_type_raw = self._date_type_raw.strip()
        self._date_value_raw = self._date_value_raw.strip()

        self._parse_date_type()
        if not self._date_type:
            return None, None, None
        date_fixed = self._parse_date_value()

        date_value_raw = None
        empty_value = not self._date_value and not self._date_value_raw
        if ("join" in self._date_type or "leave" in self._date_type) and empty_value:
            date_value_raw = "unknown"
        elif not self._date_value or date_fixed:
            date_value_raw = self._date_value_raw or None

        return self._date_type, self._date_value, date_value_raw

    def _parse_date_type(self) -> None:
        date_type = self._date_type_raw.lower().replace(" ", "_")
        parsed = date_type.replace(":", "")
        if parsed in ["join_date", "leave_date", "inactive_date"]:
            self._date_type = parsed

    def _parse_date_value(self) -> bool:
        if self._date_type is None:
            raise RuntimeError("Date type must be parsed first")

        text = self._date_value_raw[:10].lower()
        if date := self._parse_date(text):
            self._date_value = date
            return False

        fixed_date = self._try_to_fix_date(text, to_start="join" in self._date_type)
        if fixed_date is None:
            return False
        if date := self._parse_date(fixed_date):
            self._date_value = date
            return True
        return False

    def _parse_date(self, value: str) -> date | None:
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    def _try_to_fix_date(self, value: str, *, to_start: bool) -> str | None:
        year = value[:4]
        if len(year) < 4:
            return None
        try:
            int(year)
        except ValueError:
            return None

        if len(value) > 4 and not value[5].isdigit():
            value = value[:4]
        value = "".join(char for char in value if char.isdigit() or char == "-")
        value = value.rstrip("-")

        parts = value.split("-")
        if to_start:
            parts.extend(["01", "01"])
        else:
            parts.extend(["12", "31"])
        return "-".join(parts[:3])


def create_crawler_process(*, result_path: str | Path, email: str) -> CrawlerProcess:
    return CrawlerProcess(
        settings={
            "FEEDS": {
                str(result_path): {"format": "jsonlines"},
            },
            "BOT_NAME": "teamsscrapper",
            "USER_AGENT": f"CsWaybackMachineBot/0.1.0 ({email})",
            "ROBOTSTXT_OBEY": False,
            "CLOSESPIDER_ERRORCOUNT": 1,
            "DOWNLOAD_DELAY": 1,
            "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
            "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
            "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
            "FEED_EXPORT_ENCODING": "utf-8",
        }
    )

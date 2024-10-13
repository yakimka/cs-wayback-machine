import re

import scrapy


class TeamsSpider(scrapy.Spider):
    name = "teamsspider"
    start_urls = ["https://liquipedia.net/counterstrike/index.php?title=Category:Teams"]

    def parse(self, response, **kwargs):
        teams = response.css("#mw-pages .mw-content-ltr a::attr(href)").getall()
        yield from response.follow_all(teams, callback=self.parse_teams)

        next_page = response.css('#mw-pages a:contains("next page")::attr(href)').get()
        if next_page is not None:
            yield response.follow(next_page, callback=self.parse)

    def parse_teams(self, response):
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
                if content_class is not None:
                    match = re.search(r"content(\d+)", content_class)
                    n_value = match.group(1)
                    game_version = tab_names.get(n_value)
                else:
                    versions = self._extract_cs_version_from_infobox(response)
                    if len(versions) == 1:
                        game_version = versions[0]
                    else:
                        game_version = None

                dates = row.css("td.Date")
                dates_parsed = {}
                for date_el in dates:
                    date_type = date_el.css(".MobileStuffDate::text").get()
                    date_type = (
                        date_type.lower()
                        .replace(" ", "_")
                        .replace(":", "")
                        .strip()
                        .strip("_")
                    )
                    dates_parsed[date_type] = date_el.css("i::text").get()
                player_url = row.css("td.ID a::attr(href)").get()
                flag_url = row.css("td.ID .flag img::attr(src)").get()
                yield {
                    "team_name": team_name,
                    "team_url": response.url,
                    "game_version": game_version,
                    "player_id": row.css("td.ID a::text").get(),
                    "player_url": (
                        response.urljoin(player_url) if player_url is not None else None
                    ),
                    "is_captain": row.css('td.ID i[title="Captain"]').get() is not None,
                    "flag_name": row.css("td.ID .flag img::attr(title)").get(),
                    "flag_url": (
                        response.urljoin(flag_url) if flag_url is not None else None
                    ),
                    "position": row.css("td.Position i::text").get(),
                    "full_name": row.css("td.Name .LargeStuff::text").get(),
                    "join_date": dates_parsed.get("join_date"),
                    "inactive_date": dates_parsed.get("inactive_date"),
                    "leave_date": dates_parsed.get("leave_date"),
                    "new_team": row.css("td.NewTeam .team-template-text a::text").get(),
                }

    def _extract_cs_names(self, node):
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

    def _extract_cs_version_from_infobox(self, response):
        games_element = response.css('div.infobox-description:contains("Games:")')
        parent_div = games_element.xpath("./parent::div")
        game_titles = parent_div.css("a ::text").getall()
        return game_titles

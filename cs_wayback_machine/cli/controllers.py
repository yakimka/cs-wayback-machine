from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from picodi import Provide, inject

from cs_wayback_machine.scraper import TeamsSpider, create_crawler_process
from cs_wayback_machine.web.deps import get_settings

if TYPE_CHECKING:
    from cs_wayback_machine.settings import Settings


@dataclass
class Result:
    message: str
    exit_code: int = 0


@inject
def scrape_liquidpedia_and_replace_result(
    settings: Settings = Provide(get_settings),
) -> Result:
    settings.parser_results_path.mkdir(parents=False, exist_ok=True)
    tmp_file = settings.parser_results_path / "rosters.inprogress.jsonlines"

    process = create_crawler_process(
        result_path=tmp_file, email=settings.email_for_scrapper_useragent
    )
    crawler = process.create_crawler(TeamsSpider)
    process.crawl(crawler)
    process.start()

    if crawler.stats.get_value("downloader/exception_count"):
        return Result("Error occurred during the scraping", 1)

    result_file_path = str(settings.parser_result_file_path)
    shutil.move(result_file_path, result_file_path + ".bak")
    shutil.move(tmp_file, result_file_path)
    with open(settings.parser_result_updated_date_file_path, "w") as f:
        f.write(date.today().isoformat())

    return Result("Scraping finished")

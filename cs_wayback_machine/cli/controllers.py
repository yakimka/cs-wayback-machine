from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

from picodi import Provide, inject

from cs_wayback_machine.deps import get_settings
from cs_wayback_machine.scraper import TeamsSpider, create_crawler_process

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
    tmp_file.unlink(missing_ok=True)

    process = create_crawler_process(
        result_path=tmp_file, email=settings.email_for_scrapper_useragent
    )
    crawler = process.create_crawler(TeamsSpider)
    process.crawl(crawler)
    process.start(install_signal_handlers=False)
    errors_count = crawler.stats.get_value("downloader/exception_count")
    process.stop()

    if errors_count:
        return Result("Error occurred during the scraping", 1)

    if tmp_file.stat().st_size == 0:
        return Result("Scraping resulted in empty file", 1)

    parser_result_file_path = settings.parser_result_file_path
    if parser_result_file_path.exists():
        shutil.move(parser_result_file_path, f"{parser_result_file_path}.bak")
    shutil.move(tmp_file, parser_result_file_path)
    with open(settings.parser_result_updated_date_file_path, "w") as f:
        f.write(date.today().isoformat())

    return Result("Scraping finished")

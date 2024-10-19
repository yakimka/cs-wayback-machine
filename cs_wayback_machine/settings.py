from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dynaconf import Dynaconf

BASE_DIR = Path(__file__).resolve().parent


settings = Dynaconf(
    envvar_prefix="CSWM",
    settings_files=[BASE_DIR / "settings.yaml"],
    environments=True,
    load_dotenv=True,
)


@dataclass
class Settings:
    email_for_scrapper_useragent: str
    parser_results_path: Path

    @classmethod
    def create_from_config(cls) -> Settings:
        parser_results_path = settings.parser_results_path
        if parser_results_path is None:
            raise ValueError("parser_results_path is not set in the config")
        if not parser_results_path.startswith("/"):
            parser_results_path = BASE_DIR / parser_results_path
        return cls(
            email_for_scrapper_useragent=settings.email_for_scrapper_useragent,
            parser_results_path=Path(parser_results_path),
        )

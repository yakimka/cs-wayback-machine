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
    parser_result_file_path: Path

    @classmethod
    def create_from_config(cls) -> Settings:
        parser_result_file_path = settings.parser_result_file_path
        if parser_result_file_path is None:
            raise ValueError("parser_result_file_path is not set in the config")
        if not parser_result_file_path.startswith("/"):
            parser_result_file_path = BASE_DIR / parser_result_file_path
        return cls(
            email_for_scrapper_useragent=settings.email_for_scrapper_useragent,
            parser_result_file_path=Path(parser_result_file_path),
        )

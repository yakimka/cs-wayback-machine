# Counter-Strike Wayback Machine

[![Build Status](https://github.com/yakimka/cs-wayback-machine/actions/workflows/workflow-ci.yml/badge.svg?branch=main&event=push)](https://github.com/yakimka/cs-wayback-machine/actions/workflows/workflow-ci.yml)
[![Codecov](https://codecov.io/gh/yakimka/cs-wayback-machine/branch/main/graph/badge.svg)](https://codecov.io/gh/yakimka/cs-wayback-machine)

[Demo site](https://cs-wayback-machine.yakimka.me/)

A Service for Viewing Historical Data on Counter-Strike Players and Teams

This service allows you to explore team rosters during different time periods,
view the teammates of a specific professional player, and more.

## Used Technologies

- [Starlette](https://www.starlette.io/) (Python web framework)
- [Picodi](https://github.com/yakimka/picodi) (lightweight Python DI library)
- [DuckDB](https://duckdb.org/)
- [Scrapy](https://scrapy.org/) (for parsing data from Liquipedia)
- [Liquipedia.net](https://liquipedia.net/)
- [Awesomplete](https://projects.verou.me/awesomplete/)
- [PicoCSS](https://picocss.com/)

## Docker images

Docker images (amd64 and arm64) are available on [Docker Hub](https://hub.docker.com/r/yakimka/cs-wayback-machine).

## Development

### Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Copy the example settings file and configure your settings:
   ```bash
   cp cs_wayback_machine/settings.example.yaml cs_wayback_machine/settings.yaml
   ```
3. Build the Docker images:
   ```bash
   docker-compose build
   ```
4. Start the service:
   ```bash
   docker-compose up
   ```

### Making Changes

1. List available `make` commands:
   ```bash
   make help
   ```
2. Check code style with:
   ```bash
   make lint
   ```
3. Run tests using:
   ```bash
   make test
   ```
4. Manage dependencies via Poetry:
   ```bash
   make poetry args="<poetry-args>"
   ```
   - For example: `make poetry args="add requests"`

5. For local CI debugging:
   ```bash
   make run-ci
   ```

#### Pre-commit Hooks

We use [pre-commit](https://pre-commit.com/) for linting and formatting:
- It runs inside a Docker container by default.
- Optionally, set up hooks locally:
  ```bash
  pre-commit install
  ```

#### Mypy

We use [mypy](https://mypy.readthedocs.io/en/stable/) for static type checking.

It is configured for strictly typed code, so you may need to add type hints to your code.
But don't be very strict, sometimes it's better to use `Any` type.

Also, if you don't feel comfortable with that strictness,
you can disable some checks in the [pyproject.toml](pyproject.toml) in `tool.mypy` section:
- `disallow_untyped_calls = false`
- `disallow_untyped_decorators = false`
- `disallow_untyped_defs = false`

## Available CLI Commands

Project CLI commands are available in the `cs_wayback_machine.cli` module.
List of available commands you can see if you run `python -m cs_wayback_machine.cli --help` command.

### update_database

Command for updating the database with new data from Liquipedia. This command is starting
Scrapy spider for parsing data from Liquipedia and updating the database.

Can also be used like cron job with `--schedule` option.

## License

[MIT](https://github.com/yakimka/cs-wayback-machine/blob/main/LICENSE)


## Credits

This project was generated with [`yakimka/cookiecutter-pyproject`](https://github.com/yakimka/cookiecutter-pyproject).

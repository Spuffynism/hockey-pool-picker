# 🏒 hockey pool picker

This is a tool to pick an optimal hockey team alignment for competing in [LaPresse's hockey pool](https://poolhockey.lapresse.ca/index.php) using [OR-Tools's CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver). It handles trades as the season progresses, and different strategies to evaluate players' value.

Data for this project is sourced from:
- [Hockey Reference](https://www.hockey-reference.com/), for player and game statistics across seasons
- [CapFriendly](https://www.capfriendly.com/), for player cap hits across seasons

> [!NOTE]
> I've intentionally left out the crawled or downloaded data to avoid any legal issues. Feel free to use the crawlers here or manually download the data.

## Usage

### Running the solver

```shell
uv run src/main.py
```

### Crawling

The Hockey Reference and CapFriendly crawlers are ran with:

```shell
uv run src/hockey_pool_picker/crawl.py
```

## Linting

```shell
uv run ruff format . src
uv run ruff check --fix . src
```
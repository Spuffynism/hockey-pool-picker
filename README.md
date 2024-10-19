# 🏒 hockey pool picker

This is a tool to pick an optimal hockey team alignment for competing in [Marqueur's hockey pool](https://www.marqueur.com/hockey/mbr/games/masterpool/index.php) using [OR-Tools's CP-SAT solver](https://developers.google.com/optimization/cp/cp_solver). It handles trades as the season progresses, and different strategies to evaluate players' value.

Data for this project is sourced from:
- [Hockey Reference](https://www.hockey-reference.com/), for player and game statistics across seasons.
- [Puckpedia](https://puckpedia.com/), for player statistics and cap hits across seasons.
- [Marqueur](https://www.marqueur.com/), for player cap hits across seasons.

> [!NOTE]
> I've intentionally left out the crawled or downloaded data to avoid any legal issues. Feel free to use the crawlers here or manually download the data.

## Usage

### Running the solver

```shell
uv run src/hockey_pool_picker/backtest.py
```

### Picking a pool for 

```shell
uv run src/hockey_pool_picker/pick_pool.py
```

### Crawling

The Hockey Reference, and Marqueur crawlers are ran with:

```shell
uv run src/hockey_pool_picker/crawl.py
```

### Testing

```shell
pytest
```

### Linting and formatting

```shell
uv run ruff format src
uv run ruff check --fix src
```
# 🏒 hockey pool picker

This is a tool to pick an optimal hockey team alignment for competing in [LaPresse's hockey pool](https://poolhockey.lapresse.ca/index.php). It handles trades as the season progresses, and different strategies to evaluate players' value.

Data for this project is sourced from:
- [Hockey-Reference.com](https://www.hockey-reference.com/), for player and game statistics across seasons
- [CapFriendly](https://www.capfriendly.com/), for player cap hits across seasons

> [!NOTE]
> I've intentionally left out the crawled or downloaded data to avoid any legal issues. Feel free to use the crawlers here or manually download the data.

## Usage

### Setup

```shell
make boostrap
```

### Running the solver

```shell
make run
```

### Crawling

All crawlers have a main function that can be run directly. For example:

```shell
python3 source/capfriendly.py
```

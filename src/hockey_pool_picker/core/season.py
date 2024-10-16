SEASONS_CAP_HIT = {
    2020: 81_500_000,
    2021: 81_500_000,
    2022: 82_500_000,
    2023: 83_500_000,
    2024: 88_000_000,
}


class Season:
    def __init__(self, start: int):
        self.start = start
        self.end = start + 1

    def next(self):
        return Season(self.end)

    def __str__(self):
        return f"{self.start}-{self.end}"

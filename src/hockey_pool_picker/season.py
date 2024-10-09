class Season:
    def __init__(self, start: int):
        self.start = start
        self.end = start + 1

    def next(self):
        return Season(self.end)

    def __str__(self):
        return f"{self.start}-{self.end}"

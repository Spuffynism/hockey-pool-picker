import pandas as pd
from unidecode import unidecode

# good is from hockey reference because it's where we get the stats
# bad is from cap friendly because it's where we get the cap hit
# bad -> good
corrections = {
    "Mitchell Marner": "Mitch Marner",
    "Evgeni Dadonov": "Evgenii Dadonov",
    "Maxime Comtois": "Max Comtois",
    "Zachary Sanford": "Zach Sanford",
    "Samuel Blais": "Sammy Blais",
    "Nicholas Paul": "Nick Paul",
    "Patrick Maroon": "Pat Maroon",
    "Joseph Veleno": "Joe Veleno",
    "Matthew Boldy": "Matt Boldy",
    "Nick Abruzzese": "Nicholas Abruzzese",
    "Matt Nieto": "Matthew Nieto",
    "Alexander Chmelevski": "Sasha Chmelevski",
    "Benjamin Jones": "Ben Jones",
    "Zach Senyshyn": "Zachary Senyshyn",
    "Tim Gettinger": "Timothy Gettinger",
    "Michael Vecchione": "Mike Vecchione",
    "Alex True": "Alexander True",
    "Nick Merkley": "Nicholas Merkley",
    "Nicolas Petan": "Nic Petan",
    "Max Willman": "Maxwell Willman",
    "Matt Dumba": "Mathew Dumba",
    "Michael Matheson": "Mike Matheson",
    "Christopher Tanev": "Chris Tanev",
    "Joshua Morrissey": "Josh Morrissey",
    "Joshua Brown": "Josh Brown",
    "Matthew Benning": "Matt Benning",
    "Jacob Christiansen": "Jake Christiansen",
    "Ronnie Attard": "Ronald Attard",
    "Cam York": "Cameron York",
    "Cal Foote": "Callan Foote",
    "Jon Merrill": "Jonathon Merrill",
    "Daniel Renouf": "Dan Renouf",
    "Zachary Werenski": "Zach Werenski",
    "Zackary Hayes": "Zack Hayes",
    "Nikita Okhotiuk": "Nikita Okhotyuk",
    "Cal Petersen": "Calvin Petersen",
    "Samuel Montembeault": "Sam Montembeault",
    "Zach Sawchenko": "Zachary Sawchenko",
    "Will Cuylle": "William Cuylle",
    "Will Bitten": "William Bitten",
    "Maxence Guenette": "Max Guenette",
    "Nick Perbix": "Nicklaus Perbix",
    "David Gust": "Dave Gust",
    "Jacob Lucchini": "Jake Lucchini",
}

RETIRED_PLAYERS = [
    "Thomas Hodges",  # emergency goaltender
    "Matthew Berlin",  # emergency goaltender
    "Jett Alexander",  # emergency goaltender
]

PLAYER_TYPES = ["forward", "defender", "goalie"]


def normalize_name(name):
    accents_removed = unidecode(name)
    to_normalize = (
        corrections[accents_removed]
        if accents_removed in corrections
        else accents_removed
    )

    return "".join(filter(str.isalpha, to_normalize.lower()))


def massage_players(df):
    return df[df["games_played"] > 0]


def inner_merge_dropping_duplicates(left, right, column):
    df = pd.merge(left, right, how="inner", on=[column], suffixes=("", "_y"))
    return df.drop(df.filter(regex="_y$").columns, axis=1)

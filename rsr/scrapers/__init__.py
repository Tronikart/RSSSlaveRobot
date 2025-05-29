"""
Webcomic scrapers for the RSS Slave Bot

This package contains all the individual scrapers for different webcomics.
Each scraper is responsible for fetching and posting updates from a specific webcomic.
"""

# Import all scrapers for registration
# As new scrapers are implemented, add them here
from rsr.scrapers.xkcd import XkcdScraper
from rsr.scrapers.oatmeal import OatmealScraper
from rsr.scrapers.pbf import PbfScraper
from rsr.scrapers.warandpeas import WarAndPeasScraper
from rsr.scrapers.sarahsscribbles import SarahsScribblesScraper
from rsr.scrapers.explosm import ExplosmScraper
from rsr.scrapers.efc import EfcScraper
from rsr.scrapers.loadingartist import LoadingArtistScraper
from rsr.scrapers.optipess import OptipessScraper
from rsr.scrapers.piecomic import PieComicScraper
from rsr.scrapers.pdl import PoorlyDrawnLinesScraper
from rsr.scrapers.nerfnow import NerfNowScraper
from rsr.scrapers.theodd1sout import TheOdd1sOutScraper
from rsr.scrapers.skeletonclaw import SkeletonClawScraper
from rsr.scrapers.somethingpositive import SomethingPositiveScraper
from rsr.scrapers.safelyendangered import SafelyEndangeredScraper
from rsr.scrapers.falseknees import FalseKneesScraper

# List of active scrapers to run
active_scrapers = [
    XkcdScraper,
    OatmealScraper,
    PbfScraper,
    WarAndPeasScraper,
    SarahsScribblesScraper,
    ExplosmScraper,
    EfcScraper,
    LoadingArtistScraper,
    OptipessScraper,
    PieComicScraper,
    PoorlyDrawnLinesScraper,
    NerfNowScraper,
    TheOdd1sOutScraper,
    SkeletonClawScraper,
    SomethingPositiveScraper,
    SafelyEndangeredScraper,
    FalseKneesScraper,
    # Add more scrapers here as they're implemented
] 
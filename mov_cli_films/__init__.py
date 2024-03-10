from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mov_cli.plugins import PluginHookData

from .vadapav import *
from .vidsrcto import *

plugin: PluginHookData = {
    "version": 1, 
    "scrapers": {
        "DEFAULT": VidSrcToScraper, 
        "vadapav": VadapavScraper,
        "vidsrcto": VidSrcToScraper
    }
}

__version__ = "1.1.1"
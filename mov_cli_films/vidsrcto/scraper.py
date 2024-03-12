from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Iterable

if TYPE_CHECKING:
    from typing import Dict, Any, Literal, Optional

    from mov_cli import Config
    from mov_cli.http_client import HTTPClient

from mov_cli import utils
from mov_cli.scraper import Scraper
from mov_cli import Series, Movie, Metadata, MetadataType
from mov_cli.errors import MovCliException

import re
import base64
from urllib.parse import unquote
from .ext import VidPlay

__all__ = ("VidSrcToScraper", )

class IMDbSerial:
    def __init__(self, data):
        self.i: Dict[Any] = data["i"]
        self.id: str = data["id"]
        self.l: str = data["l"]
        self.qid: str = data["qid"]
        self.rank: int = data["rank"]
        self.s: str = data["s"]
        self.y: int = data["y"]

class VidSrcToScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient) -> None:
        self.base_url = "https://vidsrc.to"
        self.media_imdb = "https://v2.sg.media-imdb.com/suggestion/{}/{}.json"
        self.season_imdb = "https://www.imdb.com/_next/data/{}/title/{}/episodes.json"
        self.sources = "https://vidsrc.to/ajax/embed/episode/{}/sources"
        self.source = "https://vidsrc.to/ajax/embed/source/{}"
        super().__init__(config, http_client)

    def search(self, query: str, limit: int = 10) -> Iterable[Metadata]:
        metadata_list = []

        added = 0

        results = self.http_client.get(self.media_imdb.format(query[0], query)).json()["d"][:limit]

        for result in results:
            if added == limit:
                break

            if not "qid" in result:
                continue

            if result["qid"] not in ["movie", "tvSeries"]:
                continue

            result = IMDbSerial(result)

            metadata_list.append(
                Metadata(
                    id = result.id,
                    title = result.l,
                    type = MetadataType.MOVIE if result.qid == "movie" else MetadataType.SERIES,
                    year = result.y,
                    #extra_func = extra_metadata(result)
                )
            )

            added += 1

        return metadata_list
    
    def scrape_metadata_episodes(self, metadata: Metadata) -> Dict[int, int] | Dict[None, Literal[1]]:
        _dict = {}

        imdb = self.http_client.get("https://imdb.com/", redirect=True).text

        buildId = re.findall(r"\"buildId\":\"(.*?)\"", imdb)[0]

        url = self.season_imdb.format(buildId, metadata.id)

        imdb = self.http_client.get(url).json()

        seasons = imdb["pageProps"]["contentData"]["section"]["seasons"]

        for season in seasons:
            if not season["value"].isdigit():
                continue

            ps = self.http_client.get(url + "?season=" + season["value"]).json()

            _dict[int(season["value"])] = len(ps["pageProps"]["contentData"]["section"]["episodes"]["items"])
        
        return _dict
    
    def __deobf(self, encoded_url: str) -> str | bool:
        # This file is based on https://github.com/Ciarands/vidsrc-to-resolver/blob/dffa45e726a4b944cb9af0c9e7630476c93c0213/vidsrc.py#L16
        # Thanks to @Ciarands!
        standardized_input = encoded_url.replace('_', '/').replace('-', '+')
        binary_data = base64.b64decode(standardized_input)

        key_bytes = bytes("8z5Ag5wgagfsOuhz", 'utf-8')
        s = bytearray(range(256))
        j = 0

        for i in range(256):
            j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
            s[i], s[j] = s[j], s[i]

        decoded = bytearray(len(binary_data))
        i = 0
        k = 0

        for index in range(len(binary_data)):
            i = (i + 1) & 0xff
            k = (k + s[i]) & 0xff
            s[i], s[k] = s[k], s[i]
            t = (s[i] + s[k]) & 0xff

            if isinstance(binary_data[index], str):
                decoded[index] = ord(binary_data[index]) ^ s[t]
            elif isinstance(binary_data[index], int):
                decoded[index] = binary_data[index] ^ s[t]
            else:
                decoded = False

        return unquote(decoded.decode("utf-8"))

    def scrape(self, metadata: Metadata, episode: Optional[utils.EpisodeSelector] = None) -> Series | Movie:
        media_type = "tv" if metadata.type == MetadataType.SERIES else "movie"
        url = f"{self.base_url}/embed/{media_type}/{metadata.id}"

        if metadata.type == MetadataType.SERIES:
            url += f"/{episode.season}/{episode.episode}"
        
        vidsrc = self.http_client.get(url)

        soup = self.soup(vidsrc)

        id = soup.find('a', {'data-id': True}).get("data-id", None)

        if not id:
            raise NoDataId(metadata)
    
        sources = self.http_client.get(self.sources.format(id)).json()

        vidplay_id = None

        for source in sources["result"]:
            if source["title"] == "Vidplay":
                vidplay_id = source["id"]

        if not vidplay_id:
            raise NoSources(metadata)
        
        get_source = self.http_client.get(self.source.format(vidplay_id)).json()["result"]["url"]

        vidplay_url = self.__deobf(get_source)

        vidplay = VidPlay(self.http_client)

        url = vidplay.resolve_source(vidplay_url)[0]

        if metadata.type == MetadataType.SERIES:
            return Series(
                url,
                metadata.title,
                "",
                episode.episode,
                episode.season,
                None
            )

        return Movie(
            url,
            metadata.title,
            "",
            metadata.year,
            None
        )

class NoDataId(MovCliException):
    """Raised when scraper couldn't find DataId."""
    def __init__(self, metadata: Metadata) -> None:
        super().__init__(
            f"Did not find any DataId while scraping {metadata.title}"
        )


class NoSources(MovCliException):
    """Raised when scraper couldn't find supported sources."""
    def __init__(self, metadata: Metadata) -> None:
        super().__init__(
            f"Did not find any supported sources while scraping {metadata.title}"
        )

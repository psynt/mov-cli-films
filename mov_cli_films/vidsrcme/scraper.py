from __future__ import annotations
from typing import TYPE_CHECKING, Dict, Iterable

if TYPE_CHECKING:
    from typing import Dict, Any, Literal, Optional

    from mov_cli import Config
    from mov_cli.http_client import HTTPClient

import re

from mov_cli import utils
from mov_cli.scraper import Scraper
from mov_cli import Series, Movie, Metadata, MetadataType
import base64


__all__ = ("VidSrcMeScraper",)

class IMDbSerial:
    def __init__(self, data):
        self.id: str = data["id"]
        self.l: str = data["l"]
        self.qid: str = data["qid"]
        self.rank: int = data["rank"]
        self.s: str = data["s"]
        self.year: Optional[int] = data.get("y")
        self.image: Optional[Dict[Any]] = data.get("i")

class VidSrcMeScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient) -> None:
        self.base_url = "https://vidsrc.net"
        self.media_imdb = "https://v2.sg.media-imdb.com/suggestion/{}/{}.json"
        self.season_imdb = "https://www.imdb.com/_next/data/{}/title/{}/episodes.json"
        super().__init__(config, http_client)

    def search(self, query: str, limit: int = 10) -> Iterable[Metadata]:
        metadata_list = []

        added = 0

        results = self.http_client.get(self.media_imdb.format(query[0], query)).json()["d"][:limit]

        for result in results:
            if added == limit:
                break

            if result.get("qid") not in ["movie", "tvSeries"]:
                continue

            result = IMDbSerial(result)

            metadata_list.append(
                Metadata(
                    id = result.id,
                    title = result.l,
                    type = MetadataType.MOVIE if result.qid == "movie" else MetadataType.SERIES,
                    year = result.year,
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
            print(season)
            if not season["value"].isdigit():
                continue

            ps = self.http_client.get(url + "?season=" + season["value"]).json()

            _dict[int(season["value"])] = len(ps["pageProps"]["contentData"]["section"]["episodes"]["items"])
        
        return _dict
    
    def __deobfstr(self, hash, index):
        result = ""
        for i in range(0, len(hash), 2):
            j = hash[i:i+2]
            result += chr(int(j, 16) ^ ord(index[i // 2 % len(index)]))
        return result
    
    def __extraction(self, script):
        file_section = re.findall(r"file:\"#9(.*?)\"", script)[0]

        based64 = re.sub('/@#@\\S+?=?=', '', file_section)

        decoded_video = base64.b64decode(based64)

        return decoded_video.decode()

    def scrape(self, metadata: Metadata, episode: Optional[utils.EpisodeSelector] | None = None) -> Series | Movie:
        if episode is None:
            episode = utils.EpisodeSelector()

        type = "movie" if metadata.type == MetadataType.MOVIE else "tv"

        url_const = f"{self.base_url}/embed/{type}/{metadata.id}"

        if metadata.type == MetadataType.SERIES:
            url_const += f"/{episode.season}-{episode.episode}" 

        vidsrc = self.http_client.get(url_const)

        iframeurl = "https:" + self.soup(vidsrc).select("iframe#player_iframe")[0]["src"]

        doc = self.http_client.get(iframeurl, headers={"Referer": vidsrc})

        doc = self.soup(doc)

        index = doc.select("body")[0]["data-i"]
        hash = doc.select("div#hidden")[0]["data-h"]

        srcrcp = "https:" + self.__deobfstr(hash, index).replace("vidsrc.stream", "vidsrc.net")

        prourl = self.http_client.get(srcrcp, headers={"Referer": "https://vidsrc.stream/"}).headers["Location"]

        prorcp = self.http_client.get(prourl, headers={"Referer": "https://vidsrc.stream/"})

        prorcp = self.soup(prorcp)

        scripts = prorcp.findAll("script")

        for script in scripts:
            if "Playerjs" in script.text:
                player = script.text
                break
        
        url = self.__extraction(player)

        if metadata.type == MetadataType.MOVIE:
            return Movie(
                url,
                metadata.title,
                "https://vidsrc.stream/",
                metadata.year,
                None
            )

        return Series(
            url,
            metadata.title,
            "https://vidsrc.stream/",
            episode.episode,
            episode.season,
            None
        )

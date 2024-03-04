from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Optional, Dict

    from mov_cli import Config
    from mov_cli.http_client import HTTPClient

import re

from mov_cli import utils
from mov_cli.scraper import Scraper
from mov_cli import Series, Movie, Metadata, MetadataType

__all__ = ("VadapavScraper",)

class VadapavSerial:
    def __init__(self, data):
        self.id: str = data["id"]
        self.name: str = data["name"]
        self.dir: bool = data["dir"]
        self.parent: str = data["parent"]
        self.mtime: str = data["mtime"]

class VadapavScraper(Scraper):
    def __init__(self, config: Config, http_client: HTTPClient) -> None:
        self.base_url = "https://vadapav.mov"
        super().__init__(config, http_client)

    def search(self, query: str, limit: int = 10) -> List[Metadata]:
        results = self.__results(query, limit)
        return results

    def scrape(self, metadata: Metadata, episode: Optional[utils.EpisodeSelector] = None) -> Series | Movie:
        if episode is None:
            episode = utils.EpisodeSelector()

        if metadata.type == MetadataType.MOVIE:
            files = self.http_client.get(f"{self.base_url}/api/d/{metadata.id}").json()["data"]["files"]

            for file in files:
                file = VadapavSerial(file)
                if not file.dir:
                    id = file.id
                    break

            url = "https://vadapav.mov/f/" + id

            return Movie(
                url,
                title = metadata.title,
                referrer = self.base_url,
                year = metadata.year,
                subtitles = None
            )

        season = episode.season - 1

        season_id = self.http_client.get(f"{self.base_url}/api/d/{metadata.id}").json()["data"]["files"][season]["id"]

        episode_ids = self.http_client.get(f"{self.base_url}/api/d/{season_id}").json()["data"]["files"]

        for epi in episode_ids:
            epi = VadapavSerial(epi)
            if episode.episode <= 9: 
                if f"E0{episode.episode}" in epi.name:
                    id = epi.id
            else:    
                if f"E{episode.episode}" in epi.name:
                    id = epi.id

        url = "https://vadapav.mov/f/" + id

        print(url)

        return Series(
            url,
            title = metadata.title,
            referrer = self.base_url,
            episode = episode,
            season = episode.season,
            subtitles = None
        )

    def __results(self, query: str, limit: int = None) -> List[Metadata]:
        metadata_list = []

        items = self.http_client.get(f"{self.base_url}/api/s/{query}").json()["data"]

        for item in items:
            item = VadapavSerial(item)
            id = item.id
            title = item.name
            year = re.findall("\((\d{4})\)", item.name)

            year = year[0] if year else None

            print(year)

            type = MetadataType.SERIES if self.http_client.get(f"{self.base_url}/api/d/{id}").json()["data"]["files"][0]["name"].__contains__("Season") else MetadataType.MOVIE

            metadata_list.append(
                Metadata(
                    id = id,
                    title = title,
                    type = type,
                    year = year,

                    # extra_func = lambda: ExtraMetadata() TODO: Add ExtraMetadata
                )
            )


        return metadata_list

    def scrape_metadata_episodes(self, metadata: Metadata) -> Dict[int, int]:
        files = self.http_client.get(f"{self.base_url}/api/d/{metadata.id}").json()["data"]["files"]

        _dict = {} 

        for i in range(len(files)):

            _i = files[i]["id"]

            file = len(
                self.http_client.get(f"{self.base_url}/api/d/{_i}").json()["data"]["files"]
            )

            _dict[i + 1] = file

        return _dict
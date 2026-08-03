"""Pluggable fetchers for candidate scheme records.

A "fetcher" just has to return a list of raw dicts — whatever shape the
source gives you. The mapper (mapper.py) is responsible for turning that
into Setu's scheme schema, so adding a new source means writing a new
fetcher, not touching the rest of the pipeline.

DataGovInFetcher targets the Open Government Data (OGD) Platform India's
real, documented REST API (api.data.gov.in/resource/{resource_id}) — but
you have to supply your own resource_id. We deliberately don't ship a
hardcoded default: data.gov.in hosts thousands of unrelated datasets, and
guessing/hardcoding a resource_id we haven't ourselves verified as a live,
correct scholarship/pension dataset would repeat the exact mistake this
project spent a full audit fixing (unverified data presented as trustworthy).
Browse https://www.data.gov.in/keywords/Scholarship (or similar) yourself,
open a dataset, and copy its resource_id from the API section of that page.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import requests


class SchemeFetcher(ABC):
    @abstractmethod
    def fetch(self) -> list[dict[str, Any]]:
        """Return a list of raw candidate records, in whatever shape the source uses."""
        raise NotImplementedError


class DataGovInFetcher(SchemeFetcher):
    """Fetches records from a specific data.gov.in (OGD Platform India) resource.

    Requires:
      - DATA_GOV_IN_API_KEY env var — free, instant self-registration at
        https://www.data.gov.in/user/register (no approval wait).
      - resource_id — the dataset's resource UUID, found on the dataset's
        page under "API" (e.g. https://www.data.gov.in/resource/<uuid>).
    """

    BASE_URL = "https://api.data.gov.in/resource"

    def __init__(self, resource_id: str, api_key: str | None = None, limit: int = 100):
        self.resource_id = resource_id
        self.api_key = api_key or os.environ.get("DATA_GOV_IN_API_KEY")
        self.limit = limit
        if not self.api_key:
            raise ValueError(
                "No data.gov.in API key found. Set DATA_GOV_IN_API_KEY, or register "
                "for a free key at https://www.data.gov.in/user/register"
            )

    def fetch(self) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/{self.resource_id}"
        params = {"api-key": self.api_key, "format": "json", "limit": self.limit}
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("records", [])


class LocalSampleFetcher(SchemeFetcher):
    """Reads candidate records from a local JSON file.

    Useful for testing the mapper/validation/dedup pipeline without any
    network access, or for manually pasting in scheme data you found via
    your own research (e.g. copied from a government portal you read
    yourself) instead of going through an API at all.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def fetch(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

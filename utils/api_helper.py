"""
Cricbuzz API helper with API-first access and fallback caching.

Runtime API cache:
    data/api_cache/

This folder is used for application-level API fallback data.

Configuration sources:
- Local development: project-level .env
- Streamlit Community Cloud: st.secrets
- Environment variables take precedence when both are available

Deployment note:
- data/api_cache/ is writable during the current Streamlit runtime.
- Streamlit Cloud storage is ephemeral, so runtime cache changes should not
  be treated as permanent storage across app restarts.
- Any cache files committed with the project are available as initial
  fallback data after deployment.

Cache behavior:
- The API is ALWAYS tried first.
- If the API succeeds, the fresh response is returned and cached.
- If the API fails, the most recent cached response is returned.
- Cache files are never automatically deleted.
- Refresh TTL controls when a fresh API request is attempted; it does
  NOT prevent an older cached response from being used as a fallback.
- Fallback cache retention is 30 days.
- Live matches: refresh target every 8 hours
- Recent matches: refresh target every 24 hours
- Player rankings/statistics: refresh target every 30 days
- Series data: refresh target every 30 days
- Player data: refresh target every 30 days

This means:

    API available
        -> fresh API data
        -> save response to data/api_cache/

    API unavailable / quota exhausted
        -> use cached API response

    API unavailable + no usable cache
        -> return an error

The cache is intentionally retained for the runtime. This module does not provide
automatic cache-clearing behavior and never deletes old cache files.
"""

import hashlib
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    import streamlit as st
except Exception:
    st = None


# Configuration

BASE_DIR = Path(__file__).resolve().parent.parent

# Load the project-level .env explicitly for local development.
# On Streamlit Community Cloud, secrets are supplied through st.secrets.
load_dotenv(BASE_DIR / ".env")


def _get_config_value(name: str, default: str = "") -> str:
    """Read configuration from environment variables, then Streamlit secrets."""

    # Environment variables are checked first so local/system configuration
    # remains explicit and predictable.
    value = os.getenv(name, "").strip()

    if value:
        return value

    # Streamlit Cloud secrets are available through st.secrets.
    if st is not None:
        try:
            secret_value = st.secrets.get(name, default)

            if secret_value is not None:
                return str(secret_value).strip()
        except Exception:
            # This also covers running the helper outside Streamlit or when
            # no secrets.toml is configured.
            pass

    return default


CACHE_DIR = BASE_DIR / "data" / "api_cache"

try:
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )
except OSError:
    # The application can still use already-existing cache files or API data.
    # Individual cache writes are already treated as non-critical operations.
    pass


API_KEY = _get_config_value(
    "CRICBUZZ_API_KEY",
).strip()

# GitHub persistent cache configuration.
GITHUB_TOKEN = _get_config_value("GITHUB_TOKEN").strip()
GITHUB_REPO = _get_config_value("GITHUB_REPO").strip()
GITHUB_BRANCH = _get_config_value("GITHUB_BRANCH", "main").strip()
GITHUB_CACHE_PATH = _get_config_value(
    "GITHUB_CACHE_PATH",
    "data/api_cache",
).strip().strip("/")

API_HOST = _get_config_value(
    "CRICBUZZ_API_HOST",
    "cricbuzz-cricket.p.rapidapi.com",
).strip()

BASE_URL = f"https://{API_HOST}"

GITHUB_API_URL = "https://api.github.com"

HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": API_HOST,
}


# Cache policy

TTL_SECONDS = {
    # Freshness target before another API request is attempted.
    "live": 60 * 60 * 8,

    # Recent match data can be refreshed every 24 hours.
    "recent": 60 * 60 * 24,

    # Rankings/statistics can be refreshed every 30 days.
    "stats": 60 * 60 * 24 * 30,

    # Series information can be refreshed every 30 days.
    "series": 60 * 60 * 24 * 30,

    # Player information can be refreshed every 30 days.
    "player": 60 * 60 * 24 * 30,

    # Default refresh target.
    "default": 60 * 60 * 24,
}

# Maximum age for fallback data.
#
# This is intentionally separate from TTL_SECONDS.
#
# Example:
#   live cache is 15 minutes old
#   live TTL is 2 minutes
#   API fails
#
# The cache is still usable as a fallback because it is inside the
# 30-day fallback retention period.
FALLBACK_RETENTION_SECONDS = 60 * 60 * 24 * 30


# Cache helpers

def _cache_key(
    endpoint: str,
    params: dict,
) -> Path:
    """
    Create a stable cache filename from the endpoint and parameters.

    The same API request always maps to the same JSON file.
    """

    raw = (
        endpoint
        + json.dumps(
            params,
            sort_keys=True,
            separators=(",", ":"),
        )
    )

    digest = hashlib.md5(
        raw.encode("utf-8")
    ).hexdigest()

    return CACHE_DIR / f"{digest}.json"


def _read_cache(
    cache_file: Path,
):
    """
    Read a cached JSON response.

    Returns None if the cache does not exist or cannot be read.
    """

    if not cache_file.exists():
        return None

    try:
        with cache_file.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        return data

    except (
        OSError,
        json.JSONDecodeError,
        TypeError,
    ):
        return None


def _write_cache(
    cache_file: Path,
    data: dict,
):
    """
    Save a successful API response.

    The cache file is replaced only for this exact API request.

    No other cache files are touched.
    """

    temporary_file = cache_file.with_suffix(".tmp")

    try:
        with temporary_file.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_file.replace(cache_file)

    except (
        OSError,
        TypeError,
        ValueError,
    ):
        # Cache failure must never break the application.
        try:
            if temporary_file.exists():
                temporary_file.unlink()
        except OSError:
            pass


def _cache_age_seconds(
    cache_file: Path,
):
    """
    Return the age of a cache file in seconds.

    Returns None if the file cannot be inspected.
    """

    try:
        return max(
            0,
            time.time() - cache_file.stat().st_mtime,
        )

    except OSError:
        return None


def _is_fresh(
    cache_file: Path,
    category: str,
):
    """
    Determine whether a cache is fresh according to its refresh TTL.

    Fresh cache is useful for avoiding unnecessary API calls, but this
    function is deliberately NOT used as the API-failure fallback test.
    """

    age = _cache_age_seconds(cache_file)

    if age is None:
        return False

    ttl = TTL_SECONDS.get(
        category,
        TTL_SECONDS["default"],
    )

    return age < ttl


def _is_valid_fallback(
    cache_file: Path,
):
    """
    Determine whether a cached response can still be used as fallback.

    Fallback retention is 30 days regardless of the category TTL.
    """

    if not cache_file.exists():
        return False

    age = _cache_age_seconds(cache_file)

    if age is None:
        return False

    return age <= FALLBACK_RETENTION_SECONDS


def _decorate_response(
    data: dict,
    source: str,
    cache_file: Path,
):
    """
    Add non-invasive metadata describing where the response came from.

    Existing API fields remain unchanged.

    Pages can inspect:
        _data_source
        _cache_age_seconds
        _cache_is_fallback
    """

    if not isinstance(data, dict):
        return data

    result = dict(data)

    result["_data_source"] = source

    cache_age = _cache_age_seconds(cache_file)

    if cache_age is not None:
        result["_cache_age_seconds"] = int(cache_age)

    result["_cache_is_fallback"] = source == "cache"

    return result


# GitHub persistent cache

def _github_enabled() -> bool:
    """Return True when GitHub cache persistence is configured."""
    return bool(GITHUB_TOKEN and GITHUB_REPO and GITHUB_BRANCH)


def _github_headers() -> dict:
    """Build headers for GitHub's REST API."""
    return {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    }


def _github_file_path(cache_file: Path) -> str:
    """Convert a local cache file into a repository-relative path."""
    try:
        relative = cache_file.relative_to(CACHE_DIR)
    except ValueError:
        relative = Path(cache_file.name)

    relative_path = str(relative).replace("\\", "/").lstrip("/")
    return (
        f"{GITHUB_CACHE_PATH}/{relative_path}"
        if GITHUB_CACHE_PATH
        else relative_path
    )


def _github_file_url(repo_path: str) -> str:
    """Build the GitHub Contents API URL for a repository file."""
    return (
        f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/"
        f"{repo_path.lstrip('/')}"
    )


def _github_get_file(repo_path: str):
    """Return (decoded_content, sha) for a GitHub file, or None."""
    if not _github_enabled():
        return None

    try:
        response = requests.get(
            _github_file_url(repo_path),
            headers=_github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=10,
        )

        if response.status_code != 200:
            return None

        payload = response.json()
        if not isinstance(payload, dict):
            return None

        encoded = payload.get("content")
        sha = payload.get("sha")

        if not encoded or not sha:
            return None

        import base64

        content = base64.b64decode(
            encoded.replace("\n", "")
        ).decode("utf-8")

        return content, sha

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        UnicodeDecodeError,
    ):
        return None


def _github_write_file(cache_file: Path, data: dict) -> bool:
    """
    Create or update a cache file in GitHub.

    No GitHub failure is allowed to interrupt the dashboard.
    """
    if not _github_enabled():
        return False

    repo_path = _github_file_path(cache_file)

    try:
        import base64

        content = json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        )

        encoded_content = base64.b64encode(
            content.encode("utf-8")
        ).decode("ascii")

        existing = _github_get_file(repo_path)

        # Do not create a commit when the file already contains
        # exactly the same cache data.
        if existing is not None:
            existing_content, sha = existing
            if existing_content == content:
                return True
        else:
            sha = None

        payload = {
            "message": f"Update API cache: {cache_file.name}",
            "content": encoded_content,
            "branch": GITHUB_BRANCH,
        }

        if sha:
            payload["sha"] = sha

        response = requests.put(
            _github_file_url(repo_path),
            headers=_github_headers(),
            json=payload,
            timeout=15,
        )

        return response.status_code in {200, 201}

    except (
        requests.RequestException,
        ValueError,
        TypeError,
        OSError,
    ):
        return False


def _github_read_cache(cache_file: Path):
    """
    Read JSON cache from GitHub and restore it to local runtime cache.

    Returns a dictionary or None.
    """
    if not _github_enabled():
        return None

    result = _github_get_file(
        _github_file_path(cache_file)
    )

    if result is None:
        return None

    content, _ = result

    try:
        data = json.loads(content)

        if not isinstance(data, dict):
            return None

        try:
            cache_file.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            cache_file.write_text(
                content,
                encoding="utf-8",
            )
        except OSError:
            pass

        return data

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return None


def _persist_cache_to_github(
    cache_file: Path,
    data: dict,
) -> None:
    """Best-effort GitHub persistence for successful API data."""
    _github_write_file(
        cache_file,
        data,
    )


# API request

def _request_api(
    endpoint: str,
    params: dict = None,
):
    """
    Make one live API request.

    Returns:
        dict: successful API response
        None: API/network/HTTP/JSON failure
    """

    if not API_KEY:
        return None

    params = params or {}

    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        if not isinstance(data, dict):
            return None

        return data

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        return None


# Main API function

def fetch_or_cache(
    endpoint: str,
    params: dict = None,
    category: str = "default",
) -> dict:
    """
    Fetch API data with fallback caching.

    IMPORTANT:
        The API is always tried first.

    Behavior:

    1. Check whether a cache exists.
    2. Attempt the live API.
    3. If the API succeeds:
           - return fresh API data
           - replace the cache for this request
    4. If the API fails:
           - return cached data when it is <= 30 days old
    5. If neither is available:
           - return an error dictionary

    The category TTL is a refresh target only. It does not make the
    cached response unusable as a fallback.
    """

    params = params or {}

    cache_file = _cache_key(
        endpoint,
        params,
    )

    cached_data = _read_cache(
        cache_file
    )

    # Streamlit Cloud can restart with an empty local filesystem.
    # Restore the persistent GitHub cache when no local copy exists.
    if cached_data is None:
        cached_data = _github_read_cache(
            cache_file
        )

    # API FIRST
    #
    # We deliberately attempt the API even when a cache exists.
    # This guarantees that a working API always provides fresh data.
    api_data = _request_api(
        endpoint,
        params=params,
    )

    if api_data is not None:
        _write_cache(
            cache_file,
            api_data,
        )

        # Persist fresh API data so the cache survives Streamlit Cloud
        # runtime restarts.
        _persist_cache_to_github(
            cache_file,
            api_data,
        )

        return _decorate_response(
            api_data,
            source="api",
            cache_file=cache_file,
        )

    # API failed.
    #
    # Use the previous successful response as persistent fallback.
    if (
        cached_data is not None
        and _is_valid_fallback(cache_file)
    ):
        return _decorate_response(
            cached_data,
            source="cache",
            cache_file=cache_file,
        )

    # No API and no valid cache.
    if not API_KEY:
        return {
            "error": (
                "No CRICBUZZ_API_KEY configured and "
                "no valid cached API data is available."
            ),
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    return {
        "error": (
            "Cricbuzz API is currently unavailable or the "
            "API quota may be exhausted, and no valid cached "
            "API data is available."
        ),
        "_data_source": "none",
        "_cache_is_fallback": False,
    }


# Cache information

def get_cache_directory():
    """
    Return the application API cache directory.
    """

    return CACHE_DIR


def get_cache_age(
    endpoint: str,
    params: dict = None,
):
    """
    Return the age of a specific request cache in seconds.

    Returns None when no cache exists.
    """

    params = params or {}

    cache_file = _cache_key(
        endpoint,
        params,
    )

    return _cache_age_seconds(
        cache_file
    )


def is_cache_available(
    endpoint: str,
    params: dict = None,
):
    """
    Return True when a valid fallback cache exists.
    """

    params = params or {}

    cache_file = _cache_key(
        endpoint,
        params,
    )

    return _is_valid_fallback(
        cache_file
    )


# Cricbuzz API endpoints

def _safe_filename_part(value: str) -> str:
    """
    Convert a match/series/team name into a Windows-safe filename part.
    """

    value = str(value or "").strip()

    replacements = {
        "\\": "-",
        "/": "-",
        ":": "-",
        "*": "-",
        "?": "",
        '"': "",
        "<": "(",
        ">": ")",
        "|": "-",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    # Keep filenames readable and avoid accidental trailing dots/spaces.
    value = " ".join(value.split()).strip(" .")

    return value or "Unknown"


def _extract_recent_matches(data: dict):
    """
    Extract individual match dictionaries from a Cricbuzz response.

    Cricbuzz can nest matches under structures such as:
        typeMatches -> seriesMatches -> seriesAdWrapper -> matches

    The traversal is recursive so future response-shape changes do not
    require another cache redesign.
    """

    matches = []
    seen_ids = set()

    def walk(value):
        if isinstance(value, dict):
            # A real match object normally contains matchInfo.
            if isinstance(value.get("matchInfo"), dict):
                match_id = _get_match_id(value)

                if match_id is not None:
                    match_id = str(match_id)

                    if match_id not in seen_ids:
                        seen_ids.add(match_id)
                        matches.append(value)

                    return

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)

    return matches


def _get_match_id(match: dict):
    """
    Return the Cricbuzz match ID from a match dictionary.
    """

    info = match.get("matchInfo", {})

    if not isinstance(info, dict):
        return None

    return (
        info.get("matchId")
        or info.get("matchID")
        or match.get("matchId")
        or match.get("matchID")
    )


def _get_match_cache_filename(match: dict):
    """
    Build the human-readable recent-match cache filename.

    Format:

        <series name>_<team 1> vs <team 2>_<match_id>.json

    Example:

        European T20 Premier League 2026_Dublin Guardians vs
        Amsterdam Flames_123456.json
    """

    info = match.get("matchInfo", {})

    if not isinstance(info, dict):
        info = {}

    series_name = (
        info.get("seriesName")
        or info.get("seriesDesc")
        or "Unknown Series"
    )

    team1 = info.get("team1", {})
    team2 = info.get("team2", {})

    if not isinstance(team1, dict):
        team1 = {}

    if not isinstance(team2, dict):
        team2 = {}

    team1_name = (
        team1.get("teamName")
        or team1.get("shortName")
        or team1.get("teamSName")
        or "Unknown Team 1"
    )

    team2_name = (
        team2.get("teamName")
        or team2.get("shortName")
        or team2.get("teamSName")
        or "Unknown Team 2"
    )

    match_id = _get_match_id(match) or "unknown_id"

    return (
        f"{_safe_filename_part(series_name)}_"
        f"({_safe_filename_part(team1_name)}_vs_"
        f"{_safe_filename_part(team2_name)})_"
        f"{_safe_filename_part(match_id)}.json"
    )


def _write_recent_match_caches(data: dict):
    """
    Save every match returned by the recent-matches API as an individual
    human-readable JSON cache file.

    The complete match object is retained, including matchInfo and
    matchScore, so it can be reused later without another API request.
    """

    matches = _extract_recent_matches(data)

    for match in matches:
        filename = _get_match_cache_filename(match)
        cache_file = CACHE_DIR / filename
        temporary_file = cache_file.with_suffix(".tmp")

        try:
            with temporary_file.open(
                "w",
                encoding="utf-8",
            ) as file:
                json.dump(
                    match,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            temporary_file.replace(cache_file)

            # Persist the readable recent-match cache in GitHub.
            _persist_cache_to_github(
                cache_file,
                match,
            )

        except (OSError, TypeError, ValueError):
            try:
                if temporary_file.exists():
                    temporary_file.unlink()
            except OSError:
                pass

    return len(matches)


def _find_recent_match_cache(match_id: str):
    """
    Find an individually cached recent match by Cricbuzz match ID.

    This scans only the human-readable recent-match cache filenames.
    It does not delete or modify anything.
    """

    if not match_id:
        return None

    match_id = str(match_id)

    try:
        for cache_file in CACHE_DIR.glob("*.json"):
            # Leaderboard files and hashed API cache files do not need to
            # be opened unless their filename could contain this ID.
            if not cache_file.name.endswith(f"_{match_id}.json"):
                continue

            data = _read_cache(cache_file)

            if isinstance(data, dict):
                cached_id = _get_match_id(data)

                if str(cached_id) == match_id:
                    return cache_file, data

    except OSError:
        return None

    # Local cache may be empty after a Streamlit Cloud restart.
    if _github_enabled():
        try:
            response = requests.get(
                f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/"
                f"{GITHUB_CACHE_PATH}",
                headers=_github_headers(),
                params={"ref": GITHUB_BRANCH},
                timeout=10,
            )

            if response.status_code == 200:
                items = response.json()

                if isinstance(items, list):
                    suffix = f"_{match_id}.json"

                    for item in items:
                        if not isinstance(item, dict):
                            continue

                        name = str(item.get("name", ""))
                        if not name.endswith(suffix):
                            continue

                        download_url = item.get("download_url")
                        if not download_url:
                            continue

                        content_response = requests.get(
                            download_url,
                            headers=_github_headers(),
                            timeout=10,
                        )

                        if content_response.status_code != 200:
                            continue

                        data = content_response.json()

                        if isinstance(data, dict):
                            return Path(name), data

        except (
            requests.RequestException,
            ValueError,
            TypeError,
        ):
            pass

    return None


def list_recent_match_cache_files():
    """
    Return all individually cached recent-match files.

    Files are sorted newest-first by modification time.
    """

    try:
        files = list(
            CACHE_DIR.glob("*_*.json")
        )

        files = [
            file
            for file in files
            if not file.name.startswith("top player leaderboard_")
            and not file.name.startswith("Top_leaderboard_")
        ]

        return sorted(
            files,
            key=lambda file: file.stat().st_mtime,
            reverse=True,
        )

    except OSError:
        return []


def get_recent_match_by_id(match_id: str):
    """
    Retrieve one previously cached recent match by match ID.

    This is intended as a fast local lookup for future application
    features and avoids needing to know the generated filename.
    """

    found = _find_recent_match_cache(match_id)

    if found is None:
        return {
            "error": (
                f"No cached recent match was found for match ID "
                f"{match_id}."
            ),
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    cache_file, data = found

    result = dict(data)
    result["_data_source"] = "cache"
    result["_cache_is_fallback"] = True

    age = _cache_age_seconds(cache_file)

    if age is not None:
        result["_cache_age_seconds"] = int(age)

    return result


def get_recent_matches():
    """
    Get recent matches.

    API is always tried first.

    On successful API retrieval:
        1. The normal aggregate recent-matches response is cached.
        2. Every individual match is also saved as a readable file:

           <series>_<team1> vs <team2>_<match_id>.json

    Example:

        European T20 Premier League 2026_Dublin Guardians vs
        Amsterdam Flames_123456.json

    Individual match files are persistent and are never automatically
    deleted.

    If the API fails, the normal aggregate hashed cache remains the
    fallback for up to 30 days.
    """

    data = fetch_or_cache(
        "/matches/v1/recent",
        category="recent",
    )

    if not isinstance(data, dict):
        return data

    # Only create/refresh the readable individual match files when the
    # response actually came from the live API. Cached fallback data
    # should not be treated as newly fetched data.
    if data.get("_data_source") == "api":
        _write_recent_match_caches(data)

    return data


def get_live_matches():
    """
    Get currently listed live matches.

    API is always tried first.

    If the API fails, the last successful live-match response is
    used as fallback for up to 30 days.

    The application should label cached live data as cached/stale
    rather than presenting it as guaranteed current live data.
    """

    return fetch_or_cache(
        "/matches/v1/live",
        category="live",
    )


def get_match_scorecard(
    match_id: str,
):
    """
    Get a match scorecard.

    Scorecards use the live refresh category.

    A successful scorecard response is also retained as fallback
    for up to 30 days.
    """

    if not match_id:
        return {
            "error": "A valid match_id is required.",
            "_data_source": "none",
        }

    return fetch_or_cache(
        f"/mcenter/v1/{match_id}/scard",
        category="live",
    )


def _leaderboard_cache_file(match_type: str) -> Path:
    """
    Return the human-readable persistent cache file for a player leaderboard.

    Examples:
        data/api_cache/Top_leaderboard_ODI.json
        data/api_cache/Top_leaderboard_Test.json
        data/api_cache/Top_leaderboard_T20.json
    """

    filename_map = {
        "odi": "Top_leaderboard_ODI.json",
        "test": "Top_leaderboard_Test.json",
        "t20": "Top_leaderboard_T20.json",
    }
    return CACHE_DIR / filename_map.get(
        str(match_type).lower().strip(),
        f"Top_leaderboard_{str(match_type).upper()}.json",
    )


def _read_leaderboard_cache(match_type: str):
    """
    Read the combined leaderboard cache for one format.

    The cache can contain both:
        - batsmen
        - bowlers

    This lets the batting and bowling API responses live in the same
    human-readable format-specific cache file.
    """

    cache_file = _leaderboard_cache_file(match_type)

    if not cache_file.exists():
        return None

    try:
        with cache_file.open("r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return None

        return data

    except (OSError, json.JSONDecodeError, TypeError):
        return None


def _write_leaderboard_cache(
    match_type: str,
    cached_data: dict,
):
    """
    Save one format's player leaderboard without removing the other
    leaderboard type already stored in the same file.
    """

    cache_file = _leaderboard_cache_file(match_type)
    temporary_file = cache_file.with_suffix(".tmp")

    try:
        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(
                cached_data,
                file,
                ensure_ascii=False,
                indent=2,
            )

        temporary_file.replace(cache_file)

    except (OSError, TypeError, ValueError):
        try:
            if temporary_file.exists():
                temporary_file.unlink()
        except OSError:
            pass


def _leaderboard_cache_age_seconds(match_type: str):
    """
    Return the age of the format-specific leaderboard cache.
    """

    return _cache_age_seconds(
        _leaderboard_cache_file(match_type)
    )


def _decorate_leaderboard_component(
    data: dict,
    source: str,
    match_type: str,
):
    """
    Add the same source metadata used by the rest of the API helper.
    """

    if not isinstance(data, dict):
        return data

    result = dict(data)
    result["_data_source"] = source

    age = _leaderboard_cache_age_seconds(match_type)

    if age is not None:
        result["_cache_age_seconds"] = int(age)

    result["_cache_is_fallback"] = source == "cache"

    return result


def _get_top_player_ranking(
    match_type: str,
    ranking_type: str,
):
    """
    Get one player ranking and persist it in the format-specific
    human-readable leaderboard cache.

    Cache files:
        Top_leaderboard_ODI.json
        Top_leaderboard_Test.json
        Top_leaderboard_T20.json

    The API is always attempted first.

    If the API succeeds:
        - the fresh component is returned
        - the component is saved into its format cache

    If the API fails:
        - the cached component is returned when it is within the
          30-day fallback retention period

    Existing cached batting/bowling data in the same file is preserved.
    """

    match_type = str(match_type).lower().strip()

    if match_type == "t20i":
        api_format = "t20"
    elif match_type in {
        "odi",
        "test",
        "t20",
    }:
        api_format = match_type
    else:
        return {
            "error": (
                "Unsupported match type. "
                "Use ODI, Test, or T20."
            ),
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    if ranking_type not in {"batsmen", "bowlers"}:
        return {
            "error": "Unsupported player ranking type.",
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    endpoint = f"/stats/v1/rankings/{ranking_type}"
    params = {
        "formatType": api_format,
    }

    # API FIRST
    api_data = _request_api(
        endpoint,
        params=params,
    )

    cache_file = _leaderboard_cache_file(api_format)
    cached_file_data = _read_leaderboard_cache(api_format)

    if api_data is not None:
        # Preserve the other ranking type already stored in this file.
        combined_cache = {}

        if isinstance(cached_file_data, dict):
            combined_cache.update(cached_file_data)

        combined_cache[ranking_type] = api_data
        combined_cache["_format"] = api_format
        combined_cache["_updated_at"] = int(time.time())

        _write_leaderboard_cache(
            api_format,
            combined_cache,
        )

        # Persist the combined leaderboard cache in GitHub.
        _persist_cache_to_github(
            cache_file,
            combined_cache,
        )

        return _decorate_leaderboard_component(
            api_data,
            source="api",
            match_type=api_format,
        )

    # API failed. Use the requested component from the persistent
    # format-specific leaderboard cache.
    if (
        isinstance(cached_file_data, dict)
        and ranking_type in cached_file_data
        and _is_valid_fallback(cache_file)
    ):
        cached_component = cached_file_data[ranking_type]

        if isinstance(cached_component, dict):
            return _decorate_leaderboard_component(
                cached_component,
                source="cache",
                match_type=api_format,
            )

    if not API_KEY:
        return {
            "error": (
                "No CRICBUZZ_API_KEY configured and no valid "
                f"{ranking_type} leaderboard cache is available "
                f"for {api_format.upper()}."
            ),
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    return {
        "error": (
            "Cricbuzz API is currently unavailable or the API quota "
            "may be exhausted, and no valid "
            f"{ranking_type} leaderboard cache is available "
            f"for {api_format.upper()}."
        ),
        "_data_source": "none",
        "_cache_is_fallback": False,
    }


def get_top_player_leaderboard(
    match_type: str = "odi",
):
    """
    Get both batting and bowling leaderboards for ODI, Test, or T20.

    Each format is stored in exactly one human-readable cache file:

        data/api_cache/Top_leaderboard_ODI.json
        data/api_cache/Top_leaderboard_Test.json
        data/api_cache/Top_leaderboard_T20.json

    The API is attempted first for both ranking endpoints.

    If one endpoint is unavailable, its previously cached component is
    used when valid. This means a partial API failure does not discard
    the other ranking data.
    """

    match_type = str(match_type).lower().strip()

    if match_type == "t20i":
        api_format = "t20"
    elif match_type in {"odi", "test", "t20"}:
        api_format = match_type
    else:
        return {
            "error": (
                "Unsupported match type. "
                "Use ODI, Test, or T20."
            ),
            "_data_source": "none",
            "_cache_is_fallback": False,
        }

    batsmen = _get_top_player_ranking(
        api_format,
        "batsmen",
    )

    bowlers = _get_top_player_ranking(
        api_format,
        "bowlers",
    )

    result = {
        "format": api_format,
        "batsmen": batsmen,
        "bowlers": bowlers,
        "_cache_file": str(
            _leaderboard_cache_file(api_format)
        ),
    }

    sources = {
        batsmen.get("_data_source"),
        bowlers.get("_data_source"),
    }

    if "api" in sources:
        result["_data_source"] = "api"
    elif "cache" in sources:
        result["_data_source"] = "cache"
    else:
        result["_data_source"] = "none"

    result["_cache_is_fallback"] = (
        result["_data_source"] == "cache"
    )

    if "api" not in sources and "cache" not in sources:
        result["error"] = (
            "Top player leaderboard data is unavailable "
            f"for {api_format.upper()}."
        )

    return result


def fetch_all_top_player_leaderboards():
    """
    Fetch ODI, Test, and T20 batting + bowling leaderboards.

    Successful API responses are persisted to:

        data/api_cache/Top_leaderboard_ODI.json
        data/api_cache/Top_leaderboard_Test.json
        data/api_cache/Top_leaderboard_T20.json

    Returns a dictionary keyed by format.
    """

    results = {}

    for match_type in ("odi", "test", "t20"):
        results[match_type] = get_top_player_leaderboard(
            match_type
        )

    return results


def get_top_batsmen(
    match_type: str = "odi",
):
    """
    Get current batting rankings.

    Supported formats:
        ODI
        Test
        T20
        T20I

    The response is persisted in:
        Top_leaderboard_ODI.json
        Top_leaderboard_Test.json
        Top_leaderboard_T20.json
    """

    return _get_top_player_ranking(
        match_type,
        "batsmen",
    )


def get_top_bowlers(
    match_type: str = "odi",
):
    """
    Get current bowling rankings.

    Supported formats:
        ODI
        Test
        T20
        T20I

    The response is persisted in:
        Top_leaderboard_ODI.json
        Top_leaderboard_Test.json
        Top_leaderboard_T20.json
    """

    return _get_top_player_ranking(
        match_type,
        "bowlers",
    )


def get_series_list(
    year: int = 2024,
):
    """
    Get international series information.

    API is always tried first.

    The successful response is retained for up to 30 days
    as fallback.
    """

    return fetch_or_cache(
        "/series/v1/international",
        params={
            "year": year,
        },
        category="series",
    )

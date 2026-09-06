# API Configuration

## 1. Purpose

The API layer supplies live/current cricket information while the SQLite database provides the historical analytical layer.

The application keeps API request logic centralized in the API helper rather than scattering direct HTTP calls across the Streamlit pages.

## 2. API Host

The configured Cricbuzz API host is:

```text
cricbuzz-cricket.p.rapidapi.com
```

## 3. Required Environment Variables

Create `.env`:

```env
CRICBUZZ_API_KEY=your_rapidapi_key
CRICBUZZ_API_HOST=cricbuzz-cricket.p.rapidapi.com
```

The API key must be obtained from the relevant RapidAPI account/subscription.

## 4. Optional GitHub Configuration

If the repository/cache workflow requires GitHub access, use the project's expected variables:

```env
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_username/your_repository
GITHUB_BRANCH=main
GITHUB_CACHE_PATH=data/api_cache
```

Only configure variables that are actually used by the current application.

## 5. Security

Never place secrets directly in source code.

Bad:

```python
API_KEY = "real-secret"
```

Preferred:

```python
import os

API_KEY = os.getenv("CRICBUZZ_API_KEY")
```

Never commit:

```text
.env
```

or real tokens.

## 6. API Data Flow

```text
Streamlit page
      |
      v
API helper
      |
      v
Cricbuzz API
      |
      +----> successful response
      |
      +----> persistent cache
```

## 7. Persistent Cache

API responses are stored in:

```text
data/api_cache/
```

The cache is used to reduce unnecessary repeated requests and improve resilience.

## 8. Fallback Strategy

Where implemented by the relevant application flow:

```text
1. Live API
      ↓
2. Persistent API cache
      ↓
3. Historical SQLite data
```

The historical database is particularly important for analytics that do not require real-time information.

## 9. API Source Transparency

The UI should distinguish fresh/live data from cached data where that distinction affects freshness.

Cached information should not be presented as live information.

## 10. Troubleshooting

### Authentication failure

Check:

```text
CRICBUZZ_API_KEY
```

### Host failure

Check:

```text
CRICBUZZ_API_HOST
```

### Rate limit

Check the API provider's current request allowance.

### Empty response

Inspect the endpoint response and confirm that the requested data exists.

### API unavailable

Check `data/api_cache/` and the relevant historical SQLite tables.

## 11. Development Rules

- Centralize API requests in the API helper.
- Avoid duplicate API calls.
- Reuse valid cache data where appropriate.
- Keep secrets outside source control.
- Test both successful and failed API scenarios.
- Keep API behavior separate from historical SQL analytics.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Build a new Home Assistant HACS custom integration called `eagent-dienlucvn` that connects to Vietnam's national EVN electricity API at `https://gateway.dienluc.vn/api/`.

Key differences from the reference integration (`sample/nestup_evn/`):
- **Simplified config flow**: only Username + Password + Customer ID — no region selection
- **Single unified API**: uses the national `gateway.dienluc.vn` eAgent API instead of 5 separate regional endpoints
- **Sensor scope**: only expose sensors that have data available from this API (drop sensors not supported)

## API Reference

The HAR capture in `data_request/eagent.vn_v3.har` documents the full API. Key endpoints under `https://gateway.dienluc.vn/api/`:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `sso/auth/login/` | POST | Login — password is **plaintext base64-encoded** before sending; response contains JWT |
| `estore/electric/subscribe/getList/` | POST | List customer accounts |
| `estore/electric/bill/getLastBill/` | POST | Most recent bill |
| `estore/electric/bill/getCustomerBill/` | POST | Bill history by month |
| `electric-indicators/indicator/getListNumeIndicator/` | POST | Daily readings (only last 10 days available) |

All endpoints after login require the JWT from the auth response as `Authorization: Bearer <token>`.

## Reference Integration

`sample/nestup_evn/custom_components/nestup_evn/` is the reference to adapt from:

- **`__init__.py`** — async setup/unload, forwards to sensor platform
- **`const.py`** — domain, sensor IDs, pricing tiers, scan interval (3 hours default)
- **`types.py`** — `Area` dataclass, `EVNSensorEntityDescription` with value extractor lambdas, sensor tuple definitions
- **`config_flow.py`** — multi-step UI setup; the new version should collapse to a single step (user/password/customer ID)
- **`nestup_evn.py`** — main API client class (`EVNAPI`); each EVN region currently has its own login and data-fetch method — replace with a single set targeting `gateway.dienluc.vn`
- **`sensor.py`** — `EVNDevice` (coordinator wrapper) and `EVNSensor` (entity); creates one entity per sensor description per customer account

## Development Workflow

No build step. This is a standard Home Assistant custom component:

1. Place the finished `custom_components/eagent_dienlucvn/` directory into the Home Assistant `custom_components/` folder. The domain **must** be `eagent_dienlucvn` (set in `manifest.json` and `const.py`) — do not reuse `nestup_evn` or any sensor/entity IDs from the sample.
2. Restart Home Assistant, then add the integration via **Settings → Integrations → Add Integration**.

CI validation (once `.github/workflows/` is set up) uses:
- `hacs/action` — validates HACS metadata (`hacs.json`)
- `home-assistant/actions/hassfest` — validates HA manifest and component structure

## Architecture Notes

- All I/O must be **async** (`aiohttp.ClientSession`, never `requests`).
- The coordinator pattern (`DataUpdateCoordinator`) in `sensor.py` handles polling; the API client in the main module should only fetch and parse — no scheduling.
- SSL: `gateway.dienluc.vn` may need a custom `ssl.SSLContext` (see `nestup_evn.py` for the pattern used by the reference).
- Vietnamese electricity cost calculation uses tiered pricing; keep `VIETNAM_ECOST_STAGES` from `const.py` if cost sensors are included.
- `evn_branches.json` in the reference maps branch codes to names for auto-detecting region — not needed in the new integration since region selection is removed.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Home Assistant HACS custom integration (`eagent_dienlucvn`) that polls Vietnam's national EVN electricity API at `https://gateway.dienluc.vn/api/`. The integration is complete and deployed; `sample/nestup_evn/` is the original reference and is no longer the source of truth.

## Development Workflow

No build step. Validate syntax with:
```bash
python3 -c "import ast; ast.parse(open('custom_components/eagent_dienlucvn/<file>.py').read())"
```

Deploy by copying `custom_components/eagent_dienlucvn/` into the HA `custom_components/` folder, then restarting HA. Add via **Settings → Integrations → Add Integration → eAgent Điện lực Việt Nam**.

CI (`.github/workflows/`) uses `hacs/action` and `home-assistant/actions/hassfest`.

## API Endpoints

All under `https://gateway.dienluc.vn/api/`, POST, JSON body. Full request/response samples in `data_request/eagent.vn_v3.har`.

| Endpoint | Auth | Purpose |
|----------|------|---------|
| `sso/auth/login/` | — | Password is **plaintext base64-encoded**; returns JWT + `expiredAt` |
| `estore/electric/subscribe/getList/` | Bearer | List subscriptions; used in config flow to resolve `merchantCode` from `customerCode` |
| `estore/electric/bill/getLastBill/` | Bearer | Most recent bill (QR code, amounts, indexes) |
| `estore/electric/bill/getCustomerBill/` | Bearer | `responseCode: "0023"` = no debt / paid; `"0000"` = has debt |
| `estore/electric/bill/getListByCustomer/` | Bearer | Full bill history + `electricCustomer` info (name, address, phone, station) |
| `electric-indicators/indicator/getListNumeIndicator/` | Bearer | Daily meter readings, last 10 days only |

## Architecture

### Data flow
```
ConfigFlow → resolves merchantCode from subscriptions API → stores in config entry
sensor.py async_setup_entry → EVNDevice + DataUpdateCoordinator (polls every N hours)
EVNDevice._async_update → EAgentAPI.request_update → 4 parallel API calls
→ _format_result → flat dict keyed by sensor ID
→ EVNSensor.native_value + extra_state_attributes read from that dict
```

### Sensor data model
Each sensor ID in the flat data dict maps to a sub-dict:
- `"value"` — the sensor state (required)
- `"info"` — consumed by `dynamic_name` or `dynamic_icon` (not exported as attribute)
- any other keys — automatically exported as `extra_state_attributes`

Additionally, `ID_INDICATORS_HISTORY` and `ID_BILL_HISTORY` are dict-keyed entries (not sensors) that hold list values; sensors reference them via `history_key` on their `EVNSensorEntityDescription` and the list is appended as `"history"` in attributes.

### Key design decisions
- `merchant_code` is **never entered by the user** — it is resolved automatically during config flow by matching `customerCode` in the subscriptions list.
- Token expiry is parsed from the API's `expiredAt` field (`"HH:MM:SS DD/MM/YYYY"`) using `python_dateutil`. Tokens are refreshed 60 s before expiry.
- `econ_total_old` ("Chỉ số đầu kỳ") = `last_bill.newIndex` — the meter reading at the END of the last billed period, which is the START of the current unbilled period.
- `econ_monthly` = current meter reading (`indicators[-1].index`) − `econ_total_old`.
- Tiered pricing (`VIETNAM_ECOST_STAGES` in `const.py`) + 8 % VAT applies to all `ecost_*` sensors.

### Sensor → attribute mapping (notable)
| Sensor key | Extra attributes |
|------------|-----------------|
| `payment_status` | `customer_name`, `address`, `phone`, `meter`, `station`, `new_code` |
| `bill_amount` | `period`, `issue_date`, `from_date`, `to_date`, `consumption_kwh`, `amount_before_tax`, `tax`, `bill_type`, `order_code`, `bank`, `qr_code`, + `history` list |
| `econ_total_new` | `meter_no`, + `history` list (10 days of `{date, index, consumption}`) |

## Config Entry Data

Stored keys: `username`, `password`, `customer_code`, `merchant_code`, `scan_interval` (hours, 1–24, default 3).

`merchant_code` is the EVN branch code (e.g. `"ETLP"`) — required on every API call after login. It is resolved once at setup and never shown to the user.

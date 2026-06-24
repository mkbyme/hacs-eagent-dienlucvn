"""eAgent EVN API client."""

import base64
from datetime import datetime, timedelta
import json
import logging
import time
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import (
    async_create_clientsession,
    async_get_clientsession,
)

from .const import (
    CONF_EMPTY,
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_UNKNOWN,
    CONF_SUCCESS,
    ID_BILL_AMOUNT,
    ID_BILL_HISTORY,
    ID_ECON_DAILY_NEW,
    ID_ECON_DAILY_OLD,
    ID_ECON_MONTHLY,
    ID_ECON_TOTAL_NEW,
    ID_ECON_TOTAL_OLD,
    ID_ECOST_DAILY_NEW,
    ID_ECOST_DAILY_OLD,
    ID_ECOST_MONTHLY,
    ID_FROM_DATE,
    ID_INDICATORS_HISTORY,
    ID_LATEST_UPDATE,
    ID_PAYMENT_STATUS,
    ID_TO_DATE,
    RESP_CODE_NO_DEBT,
    RESP_CODE_SUCCESS,
    STATUS_PAID,
    STATUS_UNPAID,
    URL_BILL_LIST,
    URL_CUSTOMER_BILL,
    URL_INDICATORS,
    URL_LAST_BILL,
    URL_LOGIN,
    URL_SUBSCRIBE_LIST,
    VIETNAM_ECOST_STAGES,
    VIETNAM_ECOST_VAT,
)

_LOGGER = logging.getLogger(__name__)

_BASE_HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "vi-VN,vi;q=0.9",
    "Content-Type": "application/json; charset=utf-8",
    "Origin": "https://eagent.vn",
    "Referer": "https://eagent.vn/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
}


class EAgentAPI:
    def __init__(self, hass: HomeAssistant, is_new_session=False):
        self.hass = hass
        self._session = (
            async_create_clientsession(hass)
            if is_new_session
            else async_get_clientsession(hass)
        )
        self._access_token = None
        self._token_expiry = 0.0

    def _is_token_expired(self) -> bool:
        return time.time() >= self._token_expiry - 60

    def _auth_headers(self) -> dict:
        headers = dict(_BASE_HEADERS)
        if self._access_token:
            headers["Authorization"] = f"Bearer {self._access_token}"
        return headers

    async def login(self, username: str, password: str) -> str:
        """Login and store JWT. Password is base64-encoded before sending."""
        password_b64 = base64.b64encode(password.encode()).decode()

        try:
            resp = await self._session.post(
                url=URL_LOGIN,
                json={"username": username, "password": password_b64},
                headers=_BASE_HEADERS,
            )
        except Exception as e:
            _LOGGER.error("Login connection error: %s", e)
            return CONF_ERR_CANNOT_CONNECT

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return status

        if resp_json.get("responseCode") != RESP_CODE_SUCCESS:
            return CONF_ERR_INVALID_AUTH

        data = resp_json.get("responseData", {})
        self._access_token = data.get("accessToken")

        # Parse token expiry from "expiredAt": "10:20:02 24/06/2026"
        expired_at_str = data.get("expiredAt", "")
        try:
            from dateutil import parser as dp
            self._token_expiry = dp.parse(expired_at_str, dayfirst=True).timestamp()
        except Exception:
            self._token_expiry = time.time() + 1800

        return CONF_SUCCESS

    async def get_subscriptions(self, username: str) -> dict:
        """Return list of customer subscriptions for this account."""
        try:
            resp = await self._session.post(
                url=URL_SUBSCRIBE_LIST,
                json={"username": username, "status": 1},
                headers=self._auth_headers(),
            )
        except Exception as e:
            _LOGGER.error("Get subscriptions error: %s", e)
            return {"status": CONF_ERR_CANNOT_CONNECT}

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return {"status": status}

        if resp_json.get("responseCode") != RESP_CODE_SUCCESS:
            return {"status": CONF_ERR_UNKNOWN}

        return {"status": CONF_SUCCESS, "data": resp_json.get("responseData", [])}

    async def request_update(
        self,
        username: str,
        password: str,
        customer_code: str,
        merchant_code: str,
    ) -> dict[str, Any]:
        """Fetch all sensor data and return a formatted dict."""
        if self._is_token_expired():
            login_result = await self.login(username, password)
            if login_result != CONF_SUCCESS:
                return {"status": CONF_ERR_INVALID_AUTH}

        today = datetime.now()
        from_date = (today - timedelta(days=10)).strftime("%d/%m/%Y")
        to_date = today.strftime("%d/%m/%Y")

        indicators = await self._get_indicators(
            merchant_code, customer_code, from_date, to_date
        )
        if indicators.get("status") != CONF_SUCCESS:
            return {"status": indicators["status"]}

        last_bill = await self._get_last_bill(merchant_code, customer_code)
        customer_bill = await self._get_customer_bill(merchant_code, customer_code)
        bill_list = await self._get_bill_list(merchant_code, customer_code)

        return _format_result(
            indicators["data"],
            last_bill.get("data"),
            customer_bill.get("data"),
            bill_list.get("data", []),
            bill_list.get("customer", {}),
        )

    async def _get_indicators(
        self,
        merchant_code: str,
        customer_code: str,
        from_date: str,
        to_date: str,
    ) -> dict:
        try:
            resp = await self._session.post(
                url=URL_INDICATORS,
                json={
                    "merchantCode": merchant_code,
                    "customerCode": customer_code,
                    "fromDate": from_date,
                    "toDate": to_date,
                },
                headers=self._auth_headers(),
            )
        except Exception as e:
            _LOGGER.error("Get indicators error: %s", e)
            return {"status": CONF_ERR_CANNOT_CONNECT}

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return {"status": status}

        if resp_json.get("responseCode") != RESP_CODE_SUCCESS:
            _LOGGER.error("Indicators API error: %s", resp_json.get("responseMessage"))
            return {"status": CONF_ERR_UNKNOWN}

        return {"status": CONF_SUCCESS, "data": resp_json.get("responseData", [])}

    async def _get_last_bill(self, merchant_code: str, customer_code: str) -> dict:
        try:
            resp = await self._session.post(
                url=URL_LAST_BILL,
                json={"merchantCode": merchant_code, "customerCode": customer_code},
                headers=self._auth_headers(),
            )
        except Exception as e:
            _LOGGER.error("Get last bill error: %s", e)
            return {"status": CONF_ERR_CANNOT_CONNECT}

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return {"status": status}

        return {"status": CONF_SUCCESS, "data": resp_json.get("responseData")}

    async def _get_customer_bill(self, merchant_code: str, customer_code: str) -> dict:
        try:
            resp = await self._session.post(
                url=URL_CUSTOMER_BILL,
                json={"merchantCode": merchant_code, "customerCode": customer_code},
                headers=self._auth_headers(),
            )
        except Exception as e:
            _LOGGER.error("Get customer bill error: %s", e)
            return {"status": CONF_ERR_CANNOT_CONNECT}

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return {"status": status}

        # Keep full response; responseCode indicates debt status
        return {"status": CONF_SUCCESS, "data": resp_json}

    async def _get_bill_list(self, merchant_code: str, customer_code: str) -> dict:
        try:
            resp = await self._session.post(
                url=URL_BILL_LIST,
                json={"merchantCode": merchant_code, "customerCode": customer_code},
                headers=self._auth_headers(),
            )
        except Exception as e:
            _LOGGER.error("Get bill list error: %s", e)
            return {"status": CONF_ERR_CANNOT_CONNECT, "data": []}

        status, resp_json = await _process_response(resp)
        if status != CONF_SUCCESS:
            return {"status": status, "data": []}

        if resp_json.get("responseCode") != RESP_CODE_SUCCESS:
            _LOGGER.warning("Bill list API: %s", resp_json.get("responseMessage"))
            return {"status": CONF_ERR_UNKNOWN, "data": []}

        resp_data = resp_json.get("responseData", {})
        return {
            "status": CONF_SUCCESS,
            "data": resp_data.get("electricBillList", []),
            "customer": resp_data.get("electricCustomer", {}),
        }


async def _process_response(resp) -> tuple:
    if resp.status == 401:
        return CONF_ERR_INVALID_AUTH, {"status": CONF_ERR_INVALID_AUTH}

    if resp.status != 200:
        _LOGGER.error("HTTP error %s", resp.status)
        return CONF_ERR_CANNOT_CONNECT, {"status": CONF_ERR_CANNOT_CONNECT}

    try:
        text = await resp.text()
        data = json.loads(text, strict=False)
        state = CONF_SUCCESS if data else CONF_EMPTY
        return state, data
    except Exception as e:
        _LOGGER.error("JSON parse error: %s", e)
        return CONF_ERR_UNKNOWN, {"status": CONF_ERR_UNKNOWN}


def _format_result(
    indicators: list,
    last_bill: dict | None,
    customer_bill: dict | None,
    bill_list: list | None = None,
    electric_customer: dict | None = None,
) -> dict[str, Any]:
    """Build the sensor data dict from raw API responses."""
    if not indicators:
        return {"status": CONF_ERR_UNKNOWN}

    time_obj = datetime.now()

    latest = indicators[-1]
    previous = indicators[-2] if len(indicators) > 1 else {}

    econ_total_new = round(float(latest.get("index", 0)), 2)
    econ_daily_new = round(float(latest.get("numeIndex", 0)), 2)
    econ_daily_old = round(float(previous.get("numeIndex", 0)), 2)

    def _parse_date(s: str):
        try:
            return datetime.strptime(s, "%d/%m/%Y").date()
        except Exception:
            return time_obj.date()

    to_date = _parse_date(latest.get("readAt", ""))
    prev_date = _parse_date(previous.get("readAt", ""))

    def _date_label(d) -> str:
        if d == time_obj.date():
            return "hôm nay"
        if d == (time_obj - timedelta(days=1)).date():
            return "hôm qua"
        if d == (time_obj - timedelta(days=2)).date():
            return "hôm kia"
        return f'ngày {d.strftime("%d/%m")}'

    # Pull values from last bill
    econ_total_old = 0.0
    from_date_str = time_obj.replace(day=1).strftime("%d/%m/%Y")
    bill_amount = 0

    if last_bill:
        try:
            econ_total_old = round(float(last_bill.get("newIndex", 0)), 2)
        except (ValueError, TypeError):
            econ_total_old = 0.0
        from_date_str = last_bill.get("fromDate", from_date_str)
        bill_amount = last_bill.get("amount", 0)

    econ_monthly = round(econ_total_new - econ_total_old, 2) if econ_total_old else 0.0

    # Payment status from getCustomerBill responseCode
    payment_status = STATUS_PAID
    if customer_bill and customer_bill.get("responseCode") != RESP_CODE_NO_DEBT:
        payment_status = STATUS_UNPAID

    cust = electric_customer or {}

    return {
        "status": CONF_SUCCESS,
        ID_ECON_DAILY_NEW: {"value": econ_daily_new, "info": _date_label(to_date)},
        ID_ECOST_DAILY_NEW: {
            "value": _calc_ecost(econ_daily_new),
            "info": _date_label(to_date),
        },
        ID_ECON_DAILY_OLD: {"value": econ_daily_old, "info": _date_label(prev_date)},
        ID_ECOST_DAILY_OLD: {
            "value": _calc_ecost(econ_daily_old),
            "info": _date_label(prev_date),
        },
        ID_ECON_MONTHLY: {"value": econ_monthly},
        ID_ECOST_MONTHLY: {"value": _calc_ecost(econ_monthly)},
        ID_ECON_TOTAL_NEW: {
            "value": econ_total_new,
            "info": to_date,
            "meter_no": latest.get("meterNo", ""),
        },
        ID_ECON_TOTAL_OLD: {"value": econ_total_old},
        ID_FROM_DATE: {"value": from_date_str},
        ID_TO_DATE: {"value": latest.get("readAt", "")},
        ID_PAYMENT_STATUS: {
            "value": payment_status,
            "info": (
                "mdi:comment-alert-outline"
                if payment_status == STATUS_UNPAID
                else "mdi:comment-check-outline"
            ),
            "customer_name": cust.get("name", ""),
            "address": cust.get("address", ""),
            "phone": cust.get("phone", ""),
            "meter": cust.get("meter", ""),
            "station": cust.get("stationName", ""),
            "new_code": cust.get("newCode", ""),
        },
        ID_BILL_AMOUNT: {
            "value": str(bill_amount),
            "info": (
                "mdi:alert-circle-outline"
                if bill_amount > 0
                else "mdi:checkbox-marked-circle-outline"
            ),
            **_format_bill_attrs(last_bill),
        },
        ID_LATEST_UPDATE: {"value": time_obj.astimezone()},
        ID_INDICATORS_HISTORY: {
            "value": [
                {
                    "date": e.get("readAt", ""),
                    "index": round(float(e.get("index", 0)), 2),
                    "consumption": round(float(e.get("numeIndex", 0)), 2),
                }
                for e in indicators
            ]
        },
        ID_BILL_HISTORY: {
            "value": [_format_bill_attrs(b) for b in (bill_list or [])]
        },
    }


def _format_bill_attrs(bill: dict | None) -> dict:
    """Extract meaningful fields from a bill object."""
    if not bill:
        return {}
    return {
        "period": f"{bill.get('month', '')}/{bill.get('year', '')}",
        "issue_date": bill.get("issueDate", ""),
        "from_date": bill.get("fromDate", ""),
        "to_date": bill.get("toDate", ""),
        "old_index": int(bill.get("oldIndex", 0) or 0),
        "new_index": int(bill.get("newIndex", 0) or 0),
        "consumption_kwh": int(bill.get("nume", 0) or 0),
        "amount_before_tax": int(bill.get("amountNotTax", 0) or 0),
        "tax": int(bill.get("amountTax", 0) or 0),
        "bill_type": bill.get("typeName", ""),
        "order_code": bill.get("orderInfoCode", ""),
        "bank": bill.get("bankCode", ""),
        "qr_code": bill.get("qrCodeContent", ""),
    }


def _calc_ecost(kwh: float) -> str:
    """Calculate electricity cost using Vietnamese tiered pricing."""
    total_price = 0.0
    e_stage_list = list(VIETNAM_ECOST_STAGES.keys())

    for index, e_stage in enumerate(e_stage_list):
        if kwh < e_stage:
            break
        if e_stage == e_stage_list[-1]:
            total_price += (kwh - e_stage) * VIETNAM_ECOST_STAGES[e_stage]
        else:
            next_stage = e_stage_list[index + 1]
            total_price += (
                (next_stage - e_stage) if kwh > next_stage else (kwh - e_stage)
            ) * VIETNAM_ECOST_STAGES[e_stage]

    total_price = int(round((total_price / 100) * (100 + VIETNAM_ECOST_VAT)))
    return str(total_price)

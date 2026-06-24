"""Config flow for eAgent EVN integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from . import eagent_dienlucvn
from .const import (
    CONF_CUSTOMER_CODE,
    CONF_ERR_CANNOT_CONNECT,
    CONF_ERR_INVALID_CODE,
    CONF_ERR_UNKNOWN,
    CONF_MERCHANT_CODE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SUCCESS,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

_SETUP_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_CUSTOMER_CODE): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL_HOURS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=24)
        ),
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for eAgent EVN."""

    VERSION = 1

    def __init__(self):
        self._errors = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Single setup step: username + password + customer code + scan interval."""
        self._errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]
            customer_code = user_input[CONF_CUSTOMER_CODE].strip().upper()
            scan_interval = user_input[CONF_SCAN_INTERVAL]

            api = eagent_dienlucvn.EAgentAPI(self.hass, True)

            try:
                login_result = await api.login(username, password)
            except Exception as e:
                _LOGGER.exception("Unexpected login error: %s", e)
                self._errors["base"] = CONF_ERR_UNKNOWN
                login_result = None

            if login_result != CONF_SUCCESS:
                self._errors["base"] = login_result or CONF_ERR_UNKNOWN
            else:
                try:
                    subs = await api.get_subscriptions(username)
                except Exception as e:
                    _LOGGER.exception("Unexpected subscriptions error: %s", e)
                    subs = {"status": CONF_ERR_UNKNOWN}

                if subs["status"] != CONF_SUCCESS:
                    self._errors["base"] = CONF_ERR_CANNOT_CONNECT
                else:
                    merchant_code = None
                    for sub in subs.get("data", []):
                        if sub.get("customerCode", "").upper() == customer_code:
                            merchant_code = sub.get("merchantCode")
                            break

                    if merchant_code is None:
                        self._errors["base"] = CONF_ERR_INVALID_CODE
                    else:
                        await self.async_set_unique_id(customer_code)
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=customer_code,
                            data={
                                CONF_USERNAME: username,
                                CONF_PASSWORD: password,
                                CONF_CUSTOMER_CODE: customer_code,
                                CONF_MERCHANT_CODE: merchant_code,
                                CONF_SCAN_INTERVAL: scan_interval,
                            },
                        )

        return self.async_show_form(
            step_id="user",
            data_schema=_SETUP_SCHEMA,
            errors=self._errors,
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow to change scan interval after setup."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self._config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self._config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS),
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                        vol.Coerce(int), vol.Range(min=1, max=24)
                    ),
                }
            ),
        )

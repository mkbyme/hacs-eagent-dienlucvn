"""Setup and manage HomeAssistant sensor entities."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    DOMAIN as ENTITY_DOMAIN,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from . import eagent_dienlucvn
from .const import (
    CONF_CUSTOMER_CODE,
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_SW_VERSION,
    CONF_ERR_INVALID_AUTH,
    CONF_ERR_UNKNOWN,
    CONF_MERCHANT_CODE,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_SUCCESS,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    ID_CONNECTION_STATUS,
    ID_LATEST_UPDATE,
    STATUS_OFFLINE,
    STATUS_ONLINE,
)
from .types import EVN_SENSORS, EVNSensorEntityDescription

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Setup the sensor platform."""
    device: EVNDevice = hass.data[DOMAIN][entry.entry_id]["device"]

    async_add_entities(
        [EVNSensor(device, description, hass) for description in EVN_SENSORS]
    )


class EVNDevice:
    """Manages data fetching and coordinator for one customer account."""

    def __init__(self, dataset: dict, api: eagent_dienlucvn.EAgentAPI) -> None:
        self._name = f"{CONF_DEVICE_NAME}: {dataset[CONF_CUSTOMER_CODE]}"
        self._coordinator: DataUpdateCoordinator = None
        self.hass = api.hass
        self._username = dataset[CONF_USERNAME]
        self._password = dataset[CONF_PASSWORD]
        self._customer_code = dataset[CONF_CUSTOMER_CODE]
        self._merchant_code = dataset[CONF_MERCHANT_CODE]
        self._api = api
        self._data = {"status": "unknown"}
        self._last_success = None
        scan_hours = dataset.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_HOURS)
        self._scan_interval = timedelta(hours=scan_hours)

    async def _fetch(self) -> tuple[dict, str]:
        result = await self._api.request_update(
            self._username,
            self._password,
            self._customer_code,
            self._merchant_code,
        )

        status = result.get("status")

        if status == CONF_ERR_INVALID_AUTH:
            _LOGGER.info(
                "[EVN %s] Session expired, re-authenticating.", self._customer_code
            )
            login_state = await self._api.login(self._username, self._password)
            if login_state == CONF_SUCCESS:
                result = await self._api.request_update(
                    self._username,
                    self._password,
                    self._customer_code,
                    self._merchant_code,
                )
                status = result.get("status")

        return result, status

    async def _async_update(self):
        try:
            result, status = await self._fetch()
        except Exception as e:  # keep old data on any unexpected error
            _LOGGER.exception("[EVN %s] Unexpected error: %s", self._customer_code, e)
            status = CONF_ERR_UNKNOWN

        now = datetime.now().astimezone()

        if status == CONF_SUCCESS:
            # only replace sensor data when the fetch succeeded
            self._data = result
            self._last_success = now
            _LOGGER.info(
                "[EVN %s] Successfully fetched new data.", self._customer_code
            )
        else:
            # keep previous data so sensors retain their last known state
            _LOGGER.warning(
                "[EVN %s] Could not fetch data - status: %s, keeping previous data",
                self._customer_code,
                status,
            )

        online = status == CONF_SUCCESS
        self._data[ID_LATEST_UPDATE] = {"value": now}
        self._data[ID_CONNECTION_STATUS] = {
            "value": STATUS_ONLINE if online else STATUS_OFFLINE,
            "info": "mdi:cloud-check" if online else "mdi:cloud-off-outline",
            "last_status": status,
            "last_success": self._last_success,
        }

    async def async_create_coordinator(self, hass: HomeAssistant) -> None:
        if self._coordinator:
            return

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name=f"{DOMAIN}-{self._customer_code}",
            update_method=self._async_update,
            update_interval=self._scan_interval,
        )
        await coordinator.async_config_entry_first_refresh()
        self._coordinator = coordinator

    @property
    def coordinator(self) -> DataUpdateCoordinator:
        return self._coordinator


class EVNSensor(CoordinatorEntity, SensorEntity):
    """One sensor entity for a customer account."""

    def __init__(
        self,
        device: EVNDevice,
        description: EVNSensorEntityDescription,
        hass: HomeAssistant,
    ):
        super().__init__(device.coordinator)
        self._device = device
        self._attr_name = f"{device._name} {description.name}"
        self._unique_id = f"{device._customer_code}_{description.key}".lower()
        self._default_name = description.name
        self.entity_id = (
            f"{ENTITY_DOMAIN}.{device._customer_code}_{description.key}".lower()
        )
        self.entity_description = description

    @property
    def unique_id(self) -> str:
        return self._unique_id

    def _sensor_data(self) -> dict:
        try:
            return self.entity_description.value_fn(self._device._data) or {}
        except KeyError:
            return {}

    @property
    def native_value(self):
        data = self._sensor_data()

        if self.entity_description.dynamic_name:
            self._attr_name = f"{self._default_name} {data.get('info')}"

        if self.entity_description.dynamic_icon:
            self._attr_icon = data.get("info")

        return data.get("value")

    @property
    def extra_state_attributes(self) -> dict | None:
        data = self._sensor_data()
        # export all keys except the reserved ones used by native_value/icon/name
        attrs = {k: v for k, v in data.items() if k not in ("value", "info")}
        # append list history if configured
        history_key = self.entity_description.history_key
        if history_key and history_key in self._device._data:
            history_data = self._device._data.get(history_key, {})
            attrs["history"] = history_data.get("value", [])
        return attrs if attrs else None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            name=self._device._name,
            identifiers={(DOMAIN, self._device._customer_code)},
            manufacturer=CONF_DEVICE_MANUFACTURER,
            sw_version=CONF_DEVICE_SW_VERSION,
            model=CONF_DEVICE_MODEL,
        )

    @property
    def available(self) -> bool:
        # _data only holds the last successful fetch, so sensors stay available
        # with their old state when a later update fails
        if not self.entity_description.always_available and (
            self._device._data.get("status") != CONF_SUCCESS
        ):
            return False
        return self.native_value is not None

    @property
    def last_reset(self):
        if self.entity_description.state_class == SensorStateClass.TOTAL:
            return self._sensor_data().get("info")
        return None

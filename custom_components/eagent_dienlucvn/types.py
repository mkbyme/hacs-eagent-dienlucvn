from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy

from .const import (
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
)


@dataclass
class EVNRequiredKeysMixin:
    value_fn: Callable[[Any], float]


@dataclass
class EVNSensorEntityDescription(SensorEntityDescription, EVNRequiredKeysMixin):
    dynamic_name: None | bool = False
    dynamic_icon: None | bool = False
    history_key: str | None = None


EVN_SENSORS: tuple[EVNSensorEntityDescription, ...] = (
    # Current day
    EVNSensorEntityDescription(
        key=ID_ECON_DAILY_NEW,
        name="Sản lượng",
        icon="mdi:flash-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_DAILY_NEW],
        dynamic_name=True,
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_DAILY_NEW,
        name="Tiền điện",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_DAILY_NEW],
        dynamic_name=True,
    ),
    # Previous day
    EVNSensorEntityDescription(
        key=ID_ECON_DAILY_OLD,
        name="Sản lượng",
        icon="mdi:flash-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_DAILY_OLD],
        dynamic_name=True,
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_DAILY_OLD,
        name="Tiền điện",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_DAILY_OLD],
        dynamic_name=True,
    ),
    # Current month
    EVNSensorEntityDescription(
        key=ID_ECON_MONTHLY,
        name="Sản lượng tháng này",
        icon="mdi:flash-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_MONTHLY],
    ),
    EVNSensorEntityDescription(
        key=ID_ECOST_MONTHLY,
        name="Tiền điện tháng này",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_ECOST_MONTHLY],
    ),
    # Meter readings
    EVNSensorEntityDescription(
        key=ID_ECON_TOTAL_NEW,
        name="Chỉ số công tơ",
        icon="mdi:arrow-up-bold-box-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_TOTAL_NEW],
        history_key=ID_INDICATORS_HISTORY,
    ),
    EVNSensorEntityDescription(
        key=ID_ECON_TOTAL_OLD,
        name="Chỉ số đầu kỳ",
        icon="mdi:arrow-down-bold-box-outline",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        value_fn=lambda data: data[ID_ECON_TOTAL_OLD],
    ),
    # Dates
    EVNSensorEntityDescription(
        key=ID_FROM_DATE,
        name="Ngày đầu kỳ",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_FROM_DATE],
    ),
    EVNSensorEntityDescription(
        key=ID_TO_DATE,
        name="Ngày chốt gần nhất",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data[ID_TO_DATE],
    ),
    # Bill & payment
    EVNSensorEntityDescription(
        key=ID_PAYMENT_STATUS,
        name="Trạng thái thanh toán",
        icon="mdi:comment-question-outline",
        value_fn=lambda data: data[ID_PAYMENT_STATUS],
        dynamic_icon=True,
    ),
    EVNSensorEntityDescription(
        key=ID_BILL_AMOUNT,
        name="Tiền hóa đơn",
        icon="mdi:cash-multiple",
        native_unit_of_measurement="VNĐ",
        value_fn=lambda data: data[ID_BILL_AMOUNT],
        dynamic_icon=True,
        history_key=ID_BILL_HISTORY,
    ),
    EVNSensorEntityDescription(
        key=ID_LATEST_UPDATE,
        name="Lần cập nhật cuối",
        icon="mdi:calendar-check",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: data[ID_LATEST_UPDATE],
    ),
)

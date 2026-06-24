"""Constants for the eAgent EVN integration."""

from datetime import timedelta

DEFAULT_SCAN_INTERVAL_HOURS = 3
DEFAULT_SCAN_INTERVAL = timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS)

CONF_SCAN_INTERVAL = "scan_interval"

DOMAIN = "eagent_dienlucvn"

BASE_URL = "https://gateway.dienluc.vn/api"
URL_LOGIN = f"{BASE_URL}/sso/auth/login/"
URL_SUBSCRIBE_LIST = f"{BASE_URL}/estore/electric/subscribe/getList/"
URL_LAST_BILL = f"{BASE_URL}/estore/electric/bill/getLastBill/"
URL_CUSTOMER_BILL = f"{BASE_URL}/estore/electric/bill/getCustomerBill/"
URL_INDICATORS = f"{BASE_URL}/electric-indicators/indicator/getListNumeIndicator/"
URL_BILL_LIST = f"{BASE_URL}/estore/electric/bill/getListByCustomer/"

CONF_DEVICE_NAME = "EVN eAgent"
CONF_DEVICE_MODEL = "Vietnam EVN eAgent Monitor"
CONF_DEVICE_MANUFACTURER = "EVN"
CONF_DEVICE_SW_VERSION = "1.0.0"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_CUSTOMER_CODE = "customer_code"
CONF_MERCHANT_CODE = "merchant_code"

CONF_SUCCESS = "success"
CONF_EMPTY = "empty"
CONF_ERR_CANNOT_CONNECT = "cannot_connect"
CONF_ERR_INVALID_AUTH = "invalid_auth"
CONF_ERR_UNKNOWN = "unknown"
CONF_ERR_INVALID_CODE = "invalid_customer_code"

RESP_CODE_SUCCESS = "0000"
RESP_CODE_NO_DEBT = "0023"

ID_ECON_DAILY_NEW = "econ_daily_new"
ID_ECON_DAILY_OLD = "econ_daily_old"
ID_ECOST_DAILY_NEW = "ecost_daily_new"
ID_ECOST_DAILY_OLD = "ecost_daily_old"
ID_ECON_MONTHLY = "econ_monthly"
ID_ECOST_MONTHLY = "ecost_monthly"
ID_ECON_TOTAL_NEW = "econ_total_new"
ID_ECON_TOTAL_OLD = "econ_total_old"
ID_FROM_DATE = "from_date"
ID_TO_DATE = "to_date"
ID_PAYMENT_STATUS = "payment_status"
ID_BILL_AMOUNT = "bill_amount"
ID_LATEST_UPDATE = "latest_update"
ID_INDICATORS_HISTORY = "indicators_history"
ID_BILL_HISTORY = "bill_history"

STATUS_PAID = "Đã thanh toán"
STATUS_UNPAID = "Chưa thanh toán"

VIETNAM_ECOST_VAT = 8  # in %
VIETNAM_ECOST_STAGES = {
    # kWh : VND/kWh
    0: 1984,
    50: 2050,
    100: 2380,
    200: 2998,
    300: 3350,
    400: 3460,
}

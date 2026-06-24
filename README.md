[![hacs][hacs-badge]][hacs-repo]
[![Project Maintenance][maintenance-badge]][maintenance]

## Công cụ theo dõi điện năng tiêu thụ EVN qua eAgent dành cho HomeAssistant

> **Dựa trên** [nestup_evn](https://github.com/trvqhuy/nestup_evn) của [@trvqhuy](https://github.com/trvqhuy) — cảm ơn tác giả vì đã xây dựng nền tảng open-source cho cộng đồng HA Việt Nam.

Integration này sử dụng API quốc gia **eAgent** (`gateway.dienluc.vn`) thay vì các endpoint riêng lẻ theo vùng, cho phép theo dõi điện năng tiêu thụ trực tiếp trên UI [Home Assistant](https://www.home-assistant.io) mà không cần chọn chi nhánh EVN.

### Điểm khác biệt so với nestup_evn

| | nestup_evn | eagent_dienlucvn |
|---|---|---|
| API | 5 endpoint riêng theo vùng | 1 API quốc gia `gateway.dienluc.vn` |
| Thiết lập | Mã KH → Tài khoản → Ngày bắt đầu HĐ | Tài khoản + Mật khẩu + Mã KH (1 bước) |
| Chọn khu vực | Cần chọn chi nhánh | Tự động phát hiện qua API |
| Chu kì cập nhật | 6 giờ | 1–24 giờ (mặc định 3 giờ, tùy chỉnh được) |

### Các tính năng

1. Thiết lập **một bước duy nhất** — chỉ cần tài khoản eAgent + mã khách hàng.
2. Hỗ trợ **toàn quốc** qua API eAgent mà không phân biệt vùng miền.
3. Theo dõi **nhiều mã khách hàng** đồng thời.
4. **Chu kỳ cập nhật tùy chỉnh** từ 1 đến 24 giờ, thay đổi được sau khi cài đặt mà không cần xóa integration.
5. Tương thích với tất cả platform HA: **Core**, **Supervisor**, **Hass OS**.

### Sensors được tạo

| Sensor | Ý nghĩa | Đơn vị |
|---|---|---|
| `econ_daily_new` | Sản lượng ngày mới nhất (Dynamic Name) | kWh |
| `econ_daily_old` | Sản lượng ngày trước đó (Dynamic Name) | kWh |
| `ecost_daily_new` | Tiền điện ngày mới nhất (tham khảo) | VNĐ |
| `ecost_daily_old` | Tiền điện ngày trước đó (tham khảo) | VNĐ |
| `econ_monthly` | Sản lượng tháng hiện tại (tạm chốt) | kWh |
| `ecost_monthly` | Tiền điện tháng (tham khảo) | VNĐ |
| `econ_total_new` | Chỉ số công tơ mới nhất | kWh |
| `econ_total_old` | Chỉ số công tơ đầu kì | kWh |
| `from_date` | Ngày đầu kì hóa đơn | — |
| `to_date` | Ngày tạm chốt (cập nhật mới nhất) | — |
| `payment_status` | Tình trạng thanh toán | — |
| `bill_amount` | Số tiền hóa đơn gần nhất | VNĐ |
| `latest_update` | Thời điểm cập nhật dữ liệu lần cuối | — |

> **Lưu ý**: Các sensors tiền điện (`ecost_*`) được tính theo biểu giá bán lẻ sinh hoạt + 8% VAT, chỉ mang tính **tham khảo**.

## Yêu cầu trước khi cài đặt

### 1. Phiên bản Home Assistant: tối thiểu 2022.7.0

### 2. Tài khoản eAgent

Tải app **eAgent** hoặc đăng ký tại [eagent.vn](https://eagent.vn). Tài khoản bao gồm:
- **Tên đăng nhập**: thường là số điện thoại đăng ký với EVN.
- **Mật khẩu**: mật khẩu tài khoản eAgent.

### 3. Mã khách hàng

Mã khách hàng điện (`customerCode`) có trên hóa đơn điện hàng tháng hoặc trong app eAgent phần thông tin hợp đồng.

### 4. Loại công tơ được hỗ trợ

Chỉ hỗ trợ công tơ **điện tử đo xa ghi theo ngày**. Nếu bạn xem được **sản lượng theo ngày** trên app eAgent thì công tơ của bạn tương thích.

## Cài đặt

### Cách 1: Thêm nhanh qua HACS (khuyến nghị)

Nhấn nút bên dưới để thêm repository này vào HACS ngay lập tức:

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mkbyme&repository=hacs-eagent-dienlucvn&category=integration)

Sau khi tải xong, **khởi động lại HomeAssistant**, rồi tiến hành [Thiết lập](#thiết-lập) phía dưới.

---

Hoặc thêm thủ công:
> HACS > Integrations > ⋮ > Custom repositories > `https://github.com/mkbyme/hacs-eagent-dienlucvn` > Category: Integration

### Cách 2: Cài đặt thủ công qua Samba / SFTP

1. Tải phiên bản mới nhất từ [GitHub Releases](https://github.com/mkbyme/hacs-eagent-dienlucvn/releases).

2. Sao chép thư mục `custom_components/eagent_dienlucvn` vào thư mục `custom_components` của HomeAssistant.

    ```
    └── configuration.yaml
    └── custom_components
        └── eagent_dienlucvn
            └── __init__.py
            └── sensor.py
            └── eagent_dienlucvn.py
            └── config_flow.py
            └── const.py
            └── types.py
            └── manifest.json
            └── ...
    ```

3. Khởi động lại HomeAssistant.

## Thiết lập

Sau khi cài đặt, nhấn nút bên dưới để thêm integration trực tiếp vào HomeAssistant của bạn:

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=eagent_dienlucvn)

Hoặc tìm thủ công: **Settings > Devices & Services > Add Integration** → tìm `eAgent Điện lực Việt Nam`.

Điền thông tin trong **một bước duy nhất**:
- **Tài khoản**: số điện thoại đăng ký eAgent
- **Mật khẩu**: mật khẩu eAgent
- **Mã khách hàng**: mã khách hàng điện (ghi trên hóa đơn)
- **Chu kỳ cập nhật dữ liệu**: số giờ giữa các lần lấy dữ liệu từ API (1–24, mặc định 3)

Sau khi xác nhận, các sensors sẽ xuất hiện trong phần Devices.

### Thay đổi chu kỳ cập nhật sau khi cài đặt

Vào **Settings → Devices & Services → eAgent Điện lực Việt Nam → Configure** để chỉnh lại chu kỳ mà không cần xóa và cài lại integration.

## Home Assistant — Ví dụ Automation

Thay `{ma_khach_hang}` bằng mã khách hàng thực tế của bạn (viết thường).

```yaml
alias: Thông báo điện năng tiêu thụ mỗi ngày
mode: single

trigger:
  - platform: time
    at: "08:00:00"

condition:
  - condition: template
    value_template: >-
      {{ states('sensor.{ma_khach_hang}_to_date') == (now() - timedelta(days=1)).strftime('%d/%m/%Y') }}

action:
  - service: notify.notify
    data:
      title: Điện tiêu thụ hôm qua
      message: >
        Ngày {{ states('sensor.{ma_khach_hang}_to_date') }}:
        {{ '\n' }}- Sản lượng: {{ states('sensor.{ma_khach_hang}_econ_daily_new') }} kWh
        {{ '\n' }}- Thành tiền: {{ '{0:_.0f}'.format(states('sensor.{ma_khach_hang}_ecost_daily_new')|int).replace('_','.') }} VNĐ
        {{ '\n' }}- Sản lượng tháng: {{ states('sensor.{ma_khach_hang}_econ_monthly') }} kWh
```

## Giá bán lẻ điện (sinh hoạt, có VAT 8%)

| Bậc | Mức tiêu thụ (kWh) | Giá (VNĐ/kWh) |
|---|---|---|
| 1 | 0 – 50 | 1.984 |
| 2 | 51 – 100 | 2.050 |
| 3 | 101 – 200 | 2.380 |
| 4 | 201 – 300 | 2.998 |
| 5 | 301 – 400 | 3.350 |
| 6 | 401+ | 3.460 |

> Xem biểu giá chính thức tại [evn.com.vn](https://www.evn.com.vn/c3/evn-va-khach-hang/Bieu-gia-ban-le-dien-9-79.aspx).

## Lời cảm ơn

Integration này được xây dựng dựa trên nền tảng của **[nestup_evn](https://github.com/trvqhuy/nestup_evn)** — công trình open-source của [@trvqhuy](https://github.com/trvqhuy).

> Không có `nestup_evn`, repo này sẽ không tồn tại như một integration dành cho cộng đồng HA Việt Nam.

[hacs]: https://github.com/custom-components/hacs
[hacs-badge]: https://img.shields.io/badge/HACS-custom-0468BF.svg?style=for-the-badge
[hacs-repo]: https://github.com/mkbyme/hacs-eagent-dienlucvn
[maintenance-badge]: https://img.shields.io/badge/maintainer-%40mkbyme-F2994B?style=for-the-badge
[maintenance]: https://github.com/mkbyme

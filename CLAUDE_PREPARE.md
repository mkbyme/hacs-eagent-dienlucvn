# Khởi tạo 1 HACS cho HomeAssistant

Mục tiêu tham khảo từ `sample/nestup_evn/custom_components/nestup_evn`

Để đổi lại các ConfigFlow mới chỉ cần setup User/Password/Mã khách hàng — không cần chọn khu vực.

Với các API lấy từ `data_request/eagent.vn_v3.har`

Trong đây là record request để lấy data từ `https://gateway.dienluc.vn/api*` gồm:
- Đăng nhập: Password là dạng text encode sang base64 rồi gửi lên `sso/auth`
- Sau đó là các API lấy thông tin khách hàng, số liệu tháng hiện tại (chỉ lấy được trong 10 ngày gần nhất tính từ ngày hiện tại)
- Danh sách hóa đơn theo tháng (gồm số tiền và số điện tiêu thụ)
- Các endpoint phía sau sẽ lấy token từ response request auth qua JWT (Bearer Token header Authorization)

Tạo mới `eagent-dienlucvn` HACS để tích hợp được tài khoản qua eAgent (sử dụng API `gateway.dienluc.vn`)

Từ sample HACS tạo thành HACS mới giữ/loại bỏ các sensor không có từ số liệu API `gateway.dienluc.vn`

# FRDM-RW612: project test bằng Keil

Project µVision native cho **NXP FRDM-RW612 / RW612ETA2I**, chạy trực tiếp từ flash ngoài (XIP). Sử dụng SDK tại `D:\scs\MCUXpresso\mcuxpresso-sdk\mcuxsdk`; không cần sao chép toàn bộ SDK.

## Mở và build

1. Mở `mdk\FRDM_RW612_Test.uvmpw` hoặc `mdk\FRDM_RW612_Test.uvprojx` trong Keil µVision.
2. Chọn target **flash_debug**, compiler **Arm Compiler 6**.
3. Nhấn **F7** để build hoặc **Project → Rebuild all target files** để build lại toàn bộ.

Đã build trên máy này với **Keil MDK 5.43, Arm Compiler 6.24, NXP.RW612_DFP 25.12.00**, SDK **2026.09.00-pvw2**: **0 errors, 0 warnings**. Bộ công cụ và pack này hiện đã cài trên máy.

Build bằng PowerShell, đứng tại thư mục project:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build.ps1 -Rebuild
```

`-ExecutionPolicy Bypass` chỉ áp dụng cho tiến trình build này. Có thể bỏ `-Rebuild` để build các file đã thay đổi. Nếu Keil nằm ở chỗ khác, thêm `-KeilRoot 'D:\Keil_v5'`.

Kết quả nằm trong `mdk\Objects\`:

| File | Mục đích |
| --- | --- |
| `FRDM_RW612_Test.axf` | Nạp và debug bằng Keil |
| `FRDM_RW612_Test.hex` | Intel HEX, chứa địa chỉ nạp |
| `FRDM_RW612_Test.bin` | Binary bắt đầu tại **0x08000000**, bao gồm boot header |

Linker map: `mdk\Listings\FRDM_RW612_Test.map`. Build log: `mdk\build.log`.

## Nạp và chạy trên board

1. Nối PC với cổng **MCU-Link USB J10** trên FRDM-RW612 bằng cáp USB có truyền dữ liệu.
2. Mở COM của MCU-Link trong Tera Term/PuTTY: **115200 baud, 8 data bits, no parity, 1 stop bit, no flow control**. Tắt local echo.
3. Trong Keil, vào **Options for Target → Debug**, chọn **CMSIS-DAP ARMv8-M Debugger → Settings**, chọn MCU-Link của board và giao tiếp **SWD**. Project dùng cấu hình CMSIS-DAP từ template FRDM-RW612 của NXP, đã bỏ serial probe của template để bạn chọn probe thực tế.
4. Trong **Utilities / Flash Download**, kiểm tra có thuật toán **RW61X_FlexSPI_FRDM** tại `0x08000000` (pack còn cung cấp alias secure tại `0x18000000`). Dùng thuật toán FRDM đúng loại flash của board.
5. Chọn **Flash → Download** để nạp. Vào **Debug → Start/Stop Debug Session**, rồi nhấn **F5 / Run**. Nhấn Reset trên board để xem lại banner khi terminal đã mở.

Hướng dẫn đối chiếu của NXP: [Run a demo using Keil MDK/µVision](https://mcuxpresso.nxp.com/mcuxsdk/latest/html/boards/Wireless/frdmrw612/gettingStarted/topics/run_a_demo_using_keil__mdk_vision.html). Cổng J10 và thông số UART lấy từ `examples/_boards/frdmrw612/demo_apps/hello_world/example_board_readme.md` trong SDK đang cài.

## Chức năng test

- Khởi tạo clock, pin mux và UART theo `hello_world` cho FRDM-RW612 của SDK.
- In tên board, phiên bản SDK và `SystemCoreClock`.
- Test buffer SRAM riêng **256 byte**, ghi/đọc bốn mẫu dữ liệu. Đây là test buffer của ứng dụng, không kiểm tra toàn bộ SRAM.
- SysTick **1 ms**, in heartbeat và uptime mỗi giây.
- Nhận UART bằng polling, echo ký tự và đếm số byte nhận/lỗi RX FIFO. Đây là kiểm tra tương tác bằng terminal, không phải bài đo throughput UART.

| Phím | Chức năng |
| --- | --- |
| `?` | In trợ giúp |
| `i` | Thông tin board, clock, uptime, bộ đếm UART |
| `t` | Bật/tắt heartbeat; tắt khi muốn kiểm tra echo dễ hơn |
| `r` | Chạy lại test buffer RAM |
| Ký tự khác | Echo về terminal; Enter xuống dòng |

Ví dụ đầu ra dự kiến trên board:

```text
=== FRDM-RW612 Keil board test ===
Board: FRDM-RW612 | CPU: RW612 Cortex-M33
SDK: 2026.09.00-pvw2 | Core clock: 260000000 Hz
UART: FLEXCOMM3, 115200 baud, 8N1, no flow control
Uptime: 0 ms | RX bytes: 0 | RX FIFO errors: 0
SRAM scratch buffer (256 bytes): PASS
...
[heartbeat 1] uptime=1000 ms, rx=0, fifo_errors=0
```

Đã kiểm tra build/link và vị trí boot header/vector table; **chưa nạp hoặc xác nhận chạy trên board thật**. Banner trên là đầu ra dự kiến. Bài test hiện chưa bao gồm Wi-Fi/BLE/802.15.4.

## File để sửa và cấu hình bộ nhớ

- `source/main.c`: chương trình test và các lệnh UART.
- `board/`: bản sao board, clock, pin mux và hardware init của NXP; có thể sửa tại đây.
- `config/`: cấu hình SDK và header phiên bản, lấy từ CMake/Kconfig của SDK.
- `linker/RW612_flash.scf`: scatter file của SDK; boot header tại **0x08000000**, vector table tại **0x08001000**, code tại **0x08001400**; SRAM bắt đầu **0x20000000**, stack/heap mặc định mỗi vùng **1 KiB**.
- Các driver, startup, system và flash config tham chiếu SDK bằng đường dẫn tương đối trong `.uvprojx`. Giữ SDK tại vị trí hiện tại để build ngay.

Không dùng LED macro mẫu vì `board.h` của SDK mô tả LED đó là GPIO giả trên header. Test này quan sát kết quả qua UART.

## Tạo lại project khi chuyển SDK

Chỉ bước tạo lại cần Python, west, CMake và Ninja. Build hằng ngày trong µVision không cần các công cụ này.

```powershell
python .\tools\generate_keil.py --sdk 'D:\scs\MCUXpresso\mcuxpresso-sdk' --keil 'C:\Keil_v5'
```

Script lấy danh sách source/include/define từ cấu hình SDK `hello_world`, `frdmrw612`, `mdk`, `flash_debug`, rồi tạo project native. Script ghi đè `.uvprojx`, `.uvoptx`, `.uvmpw` và header trong `config/`; giữ các file `board/` và scatter file đã tồn tại. Nếu đổi SDK sang phiên bản khác, cần tự đối chiếu các bản sao board/scatter với SDK mới. Nếu đang mở project trong Keil, đóng trước khi tạo lại để tránh Keil ghi đè cấu hình.

Các file NXP giữ nguyên thông tin copyright và giấy phép BSD-3-Clause, xem `NXP-LICENSE.txt`.

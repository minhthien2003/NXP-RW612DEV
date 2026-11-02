# Hướng dẫn tạo project FRDM-RW612 bằng Keil thủ công

Tài liệu này hướng dẫn dựng project µVision theo đúng cách đã dùng cho `FRDM_RW612_Test`: lấy template Keil của NXP, lấy cấu hình và dependency từ ví dụ SDK, rồi thêm source và cấu hình từng mục trong Keil. Không cần chạy `generate_keil.py` để làm theo tài liệu.

Phạm vi: board **FRDM-RW612**, chip **RW612ETA2I**, ứng dụng bare-metal chạy từ flash ngoài (XIP), lấy `hello_world` làm nền. Các project Wi-Fi, BLE, FreeRTOS, TrustZone hoặc có bootloader cần lấy cấu hình từ ví dụ tương ứng.

## 1. Các đường dẫn và công cụ

| Thành phần | Giá trị đã dùng trên máy này |
| --- | --- |
| SDK workspace | `D:\scs\MCUXpresso\mcuxpresso-sdk` |
| SDK root chứa source | `D:\scs\MCUXpresso\mcuxpresso-sdk\mcuxsdk` |
| Keil | `C:\Keil_v5` — MDK 5.43 |
| Compiler | Arm Compiler 6.24, `C:\Keil_v5\ARM\ARMCLANG\bin` |
| Device pack | `C:\Keil_v5\packs\NXP\RW612_DFP\25.12.00` |
| SDK đã dùng | `2026.09.00-pvw2` |
| Project tham khảo đã build | `D:\scs\NXPProject\FRDM_RW612_Test` |

Trong tài liệu, **SDK_ROOT** là đường dẫn kết thúc bằng `mcuxsdk`. Đây chỉ là ký hiệu viết tắt trong tài liệu; Keil không tự hiểu biến `SDK_ROOT`. Khi nhập đường dẫn, thay bằng đường dẫn thực tế hoặc dùng đường dẫn tương đối.

Nếu chưa có device pack, cài RW612 DFP theo [hướng dẫn NXP](https://mcuxpresso.nxp.com/mcuxsdk/latest/html/boards/Wireless/frdmrw612/gettingStarted/topics/run_a_demo_using_keil__mdk_vision.html). Với project này, pack cung cấp nhận diện chip, thông tin debug và thuật toán nạp flash; source driver vẫn lấy từ SDK.

## 2. Hiểu các phần cần có

| Phần | Vai trò |
| --- | --- |
| `startup_RW612.S` | Vector table, Reset Handler, đưa chương trình vào C runtime |
| `system_RW612.c` | Khởi tạo hệ thống, biến và hàm cập nhật `SystemCoreClock` |
| `board.c/.h`, `clock_config.c/.h` | Cấu hình board, clock, debug UART và các hàm hỗ trợ board |
| `pin_mux.c/.h`, `hardware_init.c`, `app.h` | Pin mux và hàm `BOARD_InitHardware()` của ví dụ |
| Driver và component SDK | Hiện thực các API `CLOCK_*`, `USART_*`, `PRINTF`, v.v. |
| `flash_config.c` | Cấu hình boot flash của board |
| `RW612_flash.scf` | Scatter file, quy định vị trí boot header, vector, code, RAM, stack và heap |
| `mcux_config.h`, `mcuxsdk_version.h` | Cấu hình build SDK và thông tin phiên bản |
| `main.c` | Logic ứng dụng của bạn |

Một project cần đủ cả source, include path, macro và linker phù hợp. Thêm riêng `main.c`, `startup` và `fsl_usart.c` thường chưa đủ vì driver và board có dependency khác.

## 3. Chọn ví dụ SDK làm nền

Với bài UART cơ bản, các vị trí đã dùng là:

```text
SDK_ROOT/examples/demo_apps/hello_world/
SDK_ROOT/examples/_boards/frdmrw612/demo_apps/hello_world/
SDK_ROOT/examples/_boards/frdmrw612/
SDK_ROOT/devices/Wireless/RW/RW612/
```

`examples/demo_apps/hello_world` chứa phần ứng dụng chung. Phần dưới `_boards/frdmrw612` bổ sung cấu hình riêng cho board. Đọc `example_board_readme.md`, `prj.conf`, `CMakeLists.txt` và `reconfig.cmake` nếu có ở các thư mục liên quan.

Khi làm project khác, chọn ví dụ gần chức năng mong muốn, có hỗ trợ `frdmrw612` và toolchain `mdk`. Ví dụ cần SPI/I2C/FreeRTOS nên đối chiếu ví dụ cùng loại trong SDK để lấy đủ driver, macro, pin mux và thư viện.

### Cách lấy chính xác danh sách dependency như đã làm

Đây là bước chuẩn bị metadata của SDK, chưa tạo project Keil và chưa build firmware. Nếu chỉ dựng lại nền `hello_world` hiện tại, bạn cũng có thể dùng trực tiếp danh sách source/include ở phụ lục cuối tài liệu và copy hai header từ `FRDM_RW612_Test/config`.

Ví dụ đặt project mới tại `D:\scs\NXPProject\My_RW612_Project`. Mở PowerShell và chạy:

```powershell
$env:MDK_DIR = 'C:\Keil_v5'
Set-Location 'D:\scs\MCUXpresso\mcuxpresso-sdk\mcuxsdk'
west build -b frdmrw612 examples/demo_apps/hello_world --toolchain mdk --config flash_debug -d D:/scs/NXPProject/My_RW612_Project/.build/sdk_reference --cmake-only -- -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
```

Kết quả trong `.build/sdk_reference` của project mới:

| File | Dùng để làm gì |
| --- | --- |
| `compile_commands.json` | Mỗi entry cho biết một source và lệnh compile thực tế |
| `mcux_config.h` | Copy vào `config/` của project |
| `mcuxsdk_version.h` | Copy vào `config/` của project |
| `build.ninja` | Xem linker flags, thư viện và các bước build bổ sung |
| `.config` | Đối chiếu các lựa chọn Kconfig |

Đọc `compile_commands.json` như sau:

- Trường `file`: source cần thêm vào project; thay `hello_world.c` bằng `main.c` của bạn.
- Các tham số `-I...`: thư mục cần đưa vào Include Paths.
- Các tham số `-D...`: macro cần đưa vào Define.
- Các tham số `-include ...`: header cần ép include bằng Misc Controls.
- Các tham số CPU, FPU, ABI, ngôn ngữ và tối ưu hóa: chuyển sang thiết lập compiler tương ứng.

Để xem nhanh bằng PowerShell, thay `$metadata` theo thư mục bạn đã tạo:

```powershell
$metadata = 'D:\scs\NXPProject\My_RW612_Project\.build\sdk_reference'
$entries = Get-Content -LiteralPath "$metadata\compile_commands.json" -Raw | ConvertFrom-Json
$entries | Select-Object -ExpandProperty file
$entries[0].command
Select-String -LiteralPath "$metadata\build.ninja" -Pattern '^  LINK_FLAGS =','^  LINK_LIBRARIES ='
```

Với ví dụ phức tạp, xem nhiều entry: source C, C++, assembly hoặc một file riêng có thể có macro/flags khác nhau. Dùng **Options for File** của Keil nếu một file cần cấu hình riêng. Nếu linker dùng `.lib`, `.a`, prebuilt object hoặc bước sinh code, cần chuyển cả phần đó; không thể chỉ lấy danh sách `.c`.

## 4. Tạo cấu trúc thư mục của project mới

```text
My_RW612_Project/
    source/
        main.c
    board/
        board.c
        board.h
        clock_config.c
        clock_config.h
        pin_mux.c
        pin_mux.h
        hardware_init.c
        app.h
    config/
        mcux_config.h
        mcuxsdk_version.h
    linker/
        RW612_flash.scf
    mdk/
        My_RW612_Project.uvprojx
        My_RW612_Project.uvoptx
```

Copy thủ công:

| File nguồn trong SDK hoặc metadata | Thư mục đích |
| --- | --- |
| `SDK_ROOT/examples/_boards/frdmrw612/board.c`, `board.h` | `board/` |
| `SDK_ROOT/examples/_boards/frdmrw612/clock_config.c`, `clock_config.h` | `board/` |
| `SDK_ROOT/examples/_boards/frdmrw612/demo_apps/hello_world/pin_mux.c`, `pin_mux.h`, `hardware_init.c`, `app.h` | `board/` |
| Hai header từ metadata ở bước 3 | `config/` |
| `SDK_ROOT/devices/Wireless/RW/RW612/arm/RW612_flash.scf` | `linker/` |

Giữ copyright/license trong file NXP. Các driver, component, startup, system và flash config có thể thêm trực tiếp từ SDK để dùng chung source. Những file board/pin/clock bạn cần tùy chỉnh nên copy về project để không thay đổi SDK chung.

## 5. Lấy template Keil của NXP và mở project

Đây là cách đã dùng cho project test: bắt đầu từ template FRDM-RW612 của SDK để giữ cấu hình debug/flash của board.

1. Vào `SDK_ROOT/scripts/guigenerator/templates/mdk/app_frdmrw612/`.
2. Copy `app_frdmrw612.uvprojx` và `app_frdmrw612.uvoptx` vào `My_RW612_Project/mdk/`.
3. Đổi tên hai file thành `My_RW612_Project.uvprojx` và `My_RW612_Project.uvoptx`.
4. Mở file `.uvprojx` trong µVision. Một project đơn không bắt buộc có `.uvmpw`.
5. Trong **Manage Project Items**, giữ lại target cần dùng và đặt tên `flash_debug`. Nếu sửa XML lúc Keil đang đóng, đổi `<TargetName>` ở cả `.uvprojx` và `.uvoptx` cho khớp.
6. Trong **Options for Target → Device**, chọn **NXP → RW612ETA2I** và pack đang cài. Template SDK cũ có thể tham chiếu phiên bản pack cũ; chọn lại device/pack thay vì giữ nguyên số phiên bản của template.
7. Trong tab **Target**, chọn **Arm Compiler 6**. Project đã kiểm tra dùng bản **6.24**. Giữ chế độ MicroLIB tắt như project tham khảo.

Tên target `flash_debug` chỉ là tên. Các bước flash config, macro và scatter file dưới đây mới quyết định firmware được link để chạy từ flash.

Nếu muốn dùng **Project → New µVision Project** thay vì template: lưu project vào `mdk/`, chọn cùng device, rồi thực hiện đầy đủ các bước tiếp theo, đặc biệt cấu hình debug và flash. Khi hộp thoại quản lý component đề nghị thêm startup từ pack, không thêm trùng với `startup_RW612.S` từ SDK mà tài liệu này sử dụng.

## 6. Thêm source vào project

Tạo các group như `Application`, `Board`, `Device`, `SDK drivers`, `SDK components`, `Boot header`. Nhấp phải từng group → **Add Existing Files to Group** để thêm source.

Nguồn chính xác của nền `hello_world` đã build nằm ở **Phụ lục A**. Giữ đủ danh sách đó cho lần dựng đầu. Có 36 file compile sau khi thay `hello_world.c` bằng `main.c`.

Lưu ý khi thêm:

- Chỉ có **một** `main()`; không thêm đồng thời `hello_world.c` và `main.c` mới.
- Chỉ có **một** startup và một `system_RW612.c`; tránh vừa thêm từ pack vừa thêm từ SDK.
- File `.h` cần có trong include path; chỉ thêm `.h` vào cây project không làm compiler tự tìm thấy header.
- Trong hộp chọn file, bật hiển thị tất cả file để thấy `.S`. Giữ nguyên đuôi `.S` viết hoa và để loại file là assembly.
- Giữ `flash_config.c` đúng của **frdmrw612**.
- Các file ELS/PKC trong phụ lục là dependency của cấu hình board SDK đã dùng, kể cả khi ứng dụng chỉ in UART. Không xóa chỉ vì `main.c` không trực tiếp gọi API crypto.

## 7. Cấu hình C/C++ (AC6)

Mở **Options for Target → C/C++ (AC6)**.

### Define

Đối với nền `hello_world`, cấu hình `flash_debug` đã dùng:

```text
CPU_RW612ETA2I,RW612_SERIES,DEBUG,MCUX_META_BUILD,MCUXPRESSO_SDK,BOOT_HEADER_ENABLE=1,SDK_DEBUGCONSOLE=1
```

Giữ nguyên chữ hoa/thường. Khi dùng ví dụ SDK khác, lấy macro từ metadata của ví dụ đó; không mặc định mọi project dùng cùng danh sách.

### Include Paths

Thêm `..\board`, `..\config` và các thư mục trong **Phụ lục B**. Khi đã copy board về local, ưu tiên local board và bỏ hai đường dẫn board/demo gốc tương ứng để tránh lấy nhầm header từ SDK.

Đường dẫn tương đối tính từ thư mục `mdk/` chứa `.uvprojx`. Nếu chưa quen, dùng đường dẫn tuyệt đối qua nút chọn thư mục, build thành công rồi mới chuyển sang tương đối.

### Ngôn ngữ, kiểu dữ liệu và tối ưu

Đặt C99, short enums, short wchar và mức tối ưu `-O1` như nền SDK đã dùng; giữ debug information bật. Nếu lấy từ template thì đối chiếu các mục này với project tham khảo.

### Misc Controls

Nhập thành một dòng:

```text
-include "../config/mcux_config.h" -include "../config/mcuxsdk_version.h" -mcpu=cortex-m33+nodsp -mfpu=fpv5-sp-d16 -ffunction-sections -fdata-sections -fno-common -fno-builtin
```

Hai `-include` giúp mọi file thấy cấu hình SDK mà không phải sửa từng source. Dùng dấu `/` trong hai đường dẫn này: quá trình build trước đã gặp lỗi mất dấu `\` khi dùng đường dẫn kiểu Windows trong Misc Controls.

CPU/FPU phải khớp giữa C, assembly và linker. Nếu giao diện Keil đã sinh các tham số tương đương, kiểm tra command line để tránh có hai lựa chọn mâu thuẫn.

## 8. Cấu hình Asm

Trong **Options for Target → Asm**, chọn assembler **armclang**, hỗ trợ GNU syntax, cho các source `.S` của SDK. Project mẫu đã dùng armclang; không chuyển các file này sang legacy armasm.

**Define:**

```text
CPU_RW612ETA2I,RW612_SERIES,MCUXPRESSO_SDK
```

**Include Paths:** dùng cùng các đường dẫn như phần C.

**Misc Controls:**

```text
-include "../config/mcux_config.h" -include "../config/mcuxsdk_version.h" -mcpu=cortex-m33+nodsp -mfpu=fpv5-sp-d16
```

Giữ `.S` viết hoa để armclang xử lý C preprocessor cho source assembly. Xem [Keil: Arm Assembler](https://www.keil.com/support/man/docs/uv4/uv4_dg_adsas.asp) về lựa chọn assembler và ý nghĩa đuôi `.S`/`.s`.

## 9. Cấu hình Linker và bộ nhớ

Trong **Options for Target → Linker**:

1. Bỏ chọn **Use Memory Layout from Target Dialog**.
2. Chọn **Scatter File**: `..\linker\RW612_flash.scf`.
3. Trong **Misc Controls**, nhập:

```text
--remove --entry=Reset_Handler --strict --diag_suppress=6314 --cpu=Cortex-M33.no_dsp --fpu=FPv5-SP
```

Các tùy chọn này lấy từ cấu hình đã build. Với SDK khác, đối chiếu `LINK_FLAGS` của metadata. `--diag_suppress=6314` là lựa chọn có trong nền SDK này; không dùng thêm suppress khác để che lỗi linker chưa hiểu.

Khi dùng scatter file, file đó quyết định cách đặt các section. Xem thêm [Keil: Target và Memory Areas](https://www.keil.com/support/man/docs/uv4/uv4_dg_adstarg.asp) về quan hệ giữa bảng bộ nhớ trong Target và tùy chọn tạo scatter file.

Bản `RW612_flash.scf` đang dùng quy định:

| Vùng | Địa chỉ / kích thước |
| --- | --- |
| Boot / flash config | `0x08000000`, vùng 4 KiB |
| Vector table | `0x08001000` |
| Code chính | Bắt đầu `0x08001400` |
| SRAM | Bắt đầu `0x20000000`, vùng mặc định 0x130000 byte |
| Stack | Mặc định 0x400 byte, tăng xuống từ cuối vùng SRAM |
| Heap | Mặc định 0x400 byte |

Giữ nguyên scatter file trong lần build đầu. Nếu thêm bootloader, chuyển RAM build, bật TrustZone hoặc đổi layout, cần chọn/sửa linker theo ví dụ tương ứng và đồng bộ startup/boot config. Chỉ đổi địa chỉ IROM trong tab Target là chưa đủ khi đang dùng scatter file riêng.

## 10. Cấu hình Output, Listing và file BIN

Trong **Output**:

- Đặt tên output `My_RW612_Project`.
- Chọn thư mục output `Objects` dưới `mdk/`.
- Bật **Create Executable**, **Debug Information** và **Create HEX File**.

Trong **Listing**, bật linker map và chọn thư mục `Listings` để có thể kiểm tra địa chỉ các section.

Muốn tạo BIN, vào **User → After Build/Rebuild**, bật một lệnh và nhập:

```text
fromelf --bincombined --output=".\Objects\My_RW612_Project.bin" "#L"
```

`#L` được Keil thay bằng file executable đã link. Nếu máy không tìm thấy `fromelf`, chỉ rõ đường dẫn `C:\Keil_v5\ARM\ARMCLANG\bin\fromelf.exe` trong lệnh.

Với scatter file hiện tại, BIN bao gồm boot header và nạp từ **0x08000000**. File BIN không tự chứa địa chỉ nạp; dùng `.axf` hoặc `.hex` trong quy trình nạp tương ứng sẽ giữ thông tin địa chỉ.

## 11. Viết main.c đơn giản để kiểm tra nền

```c
#include "app.h"
#include "board.h"
#include "fsl_debug_console.h"

int main(void)
{
    BOARD_InitHardware();
    PRINTF("\r\nMy RW612 project started.\r\n");

    while (1)
    {
        char ch = GETCHAR();
        PUTCHAR(ch);
    }
}
```

`BOARD_InitHardware()` của nền này gọi khởi tạo pin, clock và debug console. Chương trình trên đợi ký tự rồi echo; `GETCHAR()` là blocking, nên chưa phù hợp cho vòng lặp cần heartbeat đồng thời. Tham khảo `FRDM_RW612_Test/source/main.c` khi cần polling UART và SysTick.

Nếu gọi trực tiếp API USART, kiểm tra kiểu macro của board. Trong SDK hiện tại `BOARD_DEBUG_UART_BASEADDR` là số nguyên địa chỉ, nên truyền con trỏ bằng cách:

```c
USART_Type *const uart = (USART_Type *)BOARD_DEBUG_UART_BASEADDR;
uint32_t flags = USART_GetStatusFlags(uart);
```

Nhớ include `fsl_usart.h` khi dùng đoạn này.

## 12. Build và kiểm tra image trước khi nạp

Chạy **Project → Rebuild all target files**. Đọc lỗi đầu tiên trong Build Output trước vì nhiều lỗi sau có thể chỉ là hệ quả.

Khi build thành công:

1. Kiểm tra có `.axf` và `.hex`; nếu thêm After Build thì có `.bin`.
2. Mở map trong `mdk/Listings`: tìm vùng `FLASH_CONFIG` ở `0x08000000`, `VECTOR_ROM` và `__Vectors` ở `0x08001000`.
3. Kiểm tra `Reset_Handler` được link vào image. Nếu có handler tự viết như `SysTick_Handler`, kiểm tra vector tham chiếu đến handler đó.
4. Kiểm tra vùng RAM, stack/heap và kích thước image đáp ứng ứng dụng.

Nền `FRDM_RW612_Test` đã được rebuild với **0 lỗi, 0 cảnh báo** trên bộ công cụ ở bước 1. Điều đó xác nhận nền build đã dùng; các bước thủ công và ứng dụng mới của bạn vẫn cần tự build và chạy kiểm tra.

## 13. Cấu hình debug và nạp FRDM-RW612

1. Nối PC với **MCU-Link USB J10** trên board bằng cáp USB có dữ liệu.
2. **Options for Target → Debug**: chọn **CMSIS-DAP ARMv8-M Debugger**, mở **Settings**, chọn probe của board và giao tiếp **SWD**.
3. Template có thể giữ tên/serial probe của NXP. Chọn lại probe thực tế; không giữ serial mẫu.
4. Trong cấu hình **Utilities / Flash Download**, chọn thuật toán **RW61X_FlexSPI_FRDM** của RW612 DFP. Địa chỉ flash dùng trong bài này là **0x08000000**; pack cũng có thuật toán alias secure `_S` tại `0x18000000`.
5. Giữ vùng RAM phục vụ flash algorithm theo template FRDM-RW612: start **0x1002C000**, size **0x8000**. Đây là RAM cho thuật toán nạp, khác với SRAM ứng dụng trong scatter file.
6. **Flash → Download**, sau đó **Start/Stop Debug Session → Run**.
7. Mở COM của MCU-Link ở **115200, 8N1, no flow control**, tắt local echo. Reset board để xem banner rồi gõ ký tự để kiểm tra echo.

Tham khảo [NXP: chạy demo bằng Keil](https://mcuxpresso.nxp.com/mcuxsdk/latest/html/boards/Wireless/frdmrw612/gettingStarted/topics/run_a_demo_using_keil__mdk_vision.html). Cổng J10 và cấu hình UART lấy từ `SDK_ROOT/examples/_boards/frdmrw612/demo_apps/hello_world/example_board_readme.md`. Tài liệu này chưa xác nhận thao tác nạp/chạy trên board thật trong phiên làm việc này.

## 14. Áp dụng cho các project khác

Khi tạo thêm ứng dụng cùng board, cùng nền bare-metal UART, bạn có thể copy project đã build, đổi tên file project/output, thay `main.c`, rồi kiểm tra lại các đường dẫn tương đối nếu vị trí thư mục thay đổi.

Khi thay chức năng nền, làm theo thứ tự:

1. Chọn ví dụ SDK cho FRDM-RW612 có chức năng gần nhất.
2. Lấy metadata `mdk` và cấu hình mong muốn; dùng thư mục build riêng cho mỗi ví dụ/toolchain/config để tránh lẫn cache.
3. So sánh source, include, define, linker, thư viện và lệnh sinh file với project hiện tại.
4. Copy pin mux/hardware init riêng của ví dụ. Kiểm tra xung clock cấp cho peripheral, reset và pin thực tế trên board.
5. Thêm đủ dependency theo metadata; giữ cấu hình riêng của từng file nếu có.
6. Build một thay đổi nhỏ trước, kiểm tra UART còn hoạt động, rồi thêm logic ứng dụng.

Ví dụ thêm I2C: cần driver đúng, các header/dependency, mux SDA/SCL, clock/reset cho FLEXCOMM và phần khởi tạo I2C; không chỉ thêm `fsl_i2c.c`. Ví dụ FreeRTOS cần thêm kernel/port/heap/config phù hợp và quản lý SysTick theo RTOS; không giữ nguyên handler SysTick bare-metal nếu nó trùng với port RTOS.

Với ví dụ Wi-Fi/BLE/Matter/TrustZone, dùng nền tương ứng của SDK và xem cả firmware nhị phân, middleware, heap/stack và layout bộ nhớ. Danh sách `hello_world` ở phụ lục là ảnh chụp cấu hình đã dùng, không phải danh sách chung cho mọi ứng dụng RW612.

## 15. Lỗi thường gặp

| Hiện tượng | Kiểm tra / cách xử lý |
| --- | --- |
| Không chọn được RW612 | Kiểm tra RW612 DFP và chọn lại device/pack |
| Không tìm thấy `fsl_*.h` | Thêm thư mục chứa header vào Include Paths; kiểm tra đường dẫn tính từ `mdk/` |
| Không tìm thấy `mcux_config.h` hoặc `mcuxsdk_version.h` | Copy từ metadata và kiểm tra hai tham số `-include` ở cả C và Asm |
| Báo thiếu `..configmcux_config.h` | Đổi đường dẫn trong Misc Controls thành `../config/mcux_config.h` |
| Assembly báo sai instruction/syntax | Kiểm tra Arm Compiler 6, armclang và giữ đuôi `.S` viết hoa |
| `Undefined symbol ...` | Tìm source/thư viện hiện thực symbol trong metadata; include header không cung cấp phần hiện thực |
| Trùng `main`, `Reset_Handler`, `SystemInit` | Xóa source bị thêm trùng từ ví dụ hoặc pack |
| Lỗi CPU/FPU/ABI không tương thích | Đồng bộ C, assembly, linker và prebuilt library theo cấu hình SDK |
| Lỗi truyền integer vào `USART_Type *` | Cast macro địa chỉ board sang `USART_Type *` như bước 11 |
| Build được nhưng không boot sau reset | Kiểm tra đúng flash config FRDM, macro `BOOT_HEADER_ENABLE`, scatter file và vị trí vector/boot header |
| Debug không thấy probe hoặc chọn nhầm probe | Kiểm tra USB J10, chọn lại CMSIS-DAP và bỏ lựa chọn serial probe mẫu |
| Nạp flash thất bại | Kiểm tra thuật toán FRDM, địa chỉ flash, RAM cho thuật toán và device pack |
| Không có log UART | Kiểm tra đúng COM MCU-Link, 115200 8N1, pin mux/clock UART, chương trình đã Run và terminal mở trước khi Reset |
| Copy project sang chỗ khác rồi thiếu source | Sửa đường dẫn source/include tương đối hoặc chọn lại file từ SDK |

## Phụ lục A. Source của nền hello_world đã dùng

Các đường dẫn có tiền tố `SDK_ROOT/` là file thêm trực tiếp từ SDK. Đường dẫn khác tính từ thư mục project mới. Thêm các file bên dưới vào group tương ứng trong Keil.

### Device

```text
SDK_ROOT/devices/Wireless/RW/RW612/system_RW612.c
SDK_ROOT/devices/Wireless/RW/RW612/arm/startup_RW612.S
```

### SDK drivers

```text
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_clock.c
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_i2s_bridge.c
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_iped.c
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_ocotp.c
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_power.c
SDK_ROOT/devices/Wireless/RW/RW612/drivers/fsl_reset.c
SDK_ROOT/drivers/common/fsl_common.c
SDK_ROOT/drivers/common/fsl_common_arm.c
SDK_ROOT/drivers/flexcomm/fsl_flexcomm.c
SDK_ROOT/drivers/flexspi/fsl_flexspi.c
SDK_ROOT/drivers/lpc_gpio/fsl_gpio.c
SDK_ROOT/drivers/cache/cache64/fsl_cache.c
SDK_ROOT/drivers/flexcomm/usart/fsl_usart.c
```

### Boot header

```text
SDK_ROOT/examples/_boards/frdmrw612/flash_config/flash_config.c
```

### Board

```text
board/board.c
board/clock_config.c
board/pin_mux.c
board/hardware_init.c
```

### SDK components

```text
SDK_ROOT/components/assert/fsl_assert.c
SDK_ROOT/components/debug_console_lite/fsl_debug_console.c
SDK_ROOT/components/misc_utilities/fsl_memcpy.S
SDK_ROOT/components/misc_utilities/fsl_memset.S
SDK_ROOT/components/str/fsl_str.c
SDK_ROOT/components/uart/fsl_adapter_usart.c
SDK_ROOT/components/els_pkc/src/comps/mcuxClBuffer/src/mcuxClBuffer.c
SDK_ROOT/components/els_pkc/src/comps/mcuxClEls/src/mcuxClEls_Common.c
SDK_ROOT/components/els_pkc/src/comps/mcuxClEls/src/mcuxClEls_GlitchDetector.c
SDK_ROOT/components/els_pkc/src/comps/mcuxClMemory/src/mcuxClMemory.c
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/src/mcuxCsslMemory_Clear.c
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/src/mcuxCsslMemory_Compare.c
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/src/mcuxCsslMemory_Copy.c
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/src/mcuxCsslMemory_Set.c
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslParamIntegrity/src/mcuxCsslParamIntegrity32.c
```

### Application

```text
source/main.c
```

## Phụ lục B. Include Paths của nền đã dùng

Nhập các đường dẫn dưới đây vào cả phần C và Asm. `SDK_ROOT` phải được thay bằng đường dẫn SDK thật; các dòng local `../board` và `../config` tính từ `mdk/`. Các thư mục ELS/PKC giữ theo dependency của SDK hiện tại.

```text
../board
../config
SDK_ROOT/devices/Wireless/RW/RW612
SDK_ROOT/devices/Wireless/RW/periph
SDK_ROOT/devices/Wireless/RW/RW612/drivers
SDK_ROOT/arch/arm/CMSIS/Core/Include
SDK_ROOT/arch/arm/CMSIS/Core/Include/m-profile
SDK_ROOT/examples/_boards/frdmrw612/flash_config
SDK_ROOT/drivers/common
SDK_ROOT/drivers/flexcomm
SDK_ROOT/drivers/flexspi
SDK_ROOT/drivers/lpc_gpio
SDK_ROOT/drivers/cache/cache64
SDK_ROOT/drivers/flexcomm/usart
SDK_ROOT/components/assert
SDK_ROOT/components/debug_console_lite
SDK_ROOT/components/str
SDK_ROOT/components/uart
SDK_ROOT/components/els_pkc
SDK_ROOT/components/els_pkc/src/comps/mcuxClBuffer/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxClBuffer/inc/internal
SDK_ROOT/components/els_pkc/src/comps/mcuxClCore/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxClEls/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxClEls/inc/internal
SDK_ROOT/components/els_pkc/src/comps/mcuxClMemory/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxClMemory/inc/internal
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslMemory/inc/internal
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslCPreProcessor/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslDataIntegrity/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslFlowProtection/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslParamIntegrity/inc
SDK_ROOT/components/els_pkc/src/comps/mcuxCsslSecureCounter/inc
SDK_ROOT/components/els_pkc/src/compiler
SDK_ROOT/components/els_pkc/src/platforms/rw61x
SDK_ROOT/components/els_pkc/src/platforms/rw61x/inc
SDK_ROOT/components/els_pkc/includes/platform/rw61x
```

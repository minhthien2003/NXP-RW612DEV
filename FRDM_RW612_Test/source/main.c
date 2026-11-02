/* SPDX-License-Identifier: BSD-3-Clause */
#include <stdbool.h>
#include <stdint.h>
#include "app.h"
#include "board.h"
#include "fsl_debug_console.h"
#include "fsl_usart.h"

static volatile uint32_t s_milliseconds;
static uint32_t s_rxCount;
static uint32_t s_rxErrors;
static bool s_heartbeatEnabled = true;

void SysTick_Handler(void)
{
    ++s_milliseconds;
}

/* Only tests this application's scratch buffer, not the entire SRAM. */
static bool TestRamBuffer(void)
{
    volatile uint32_t scratch[64];
    const uint32_t patterns[] = {0x00000000U, 0xFFFFFFFFU, 0x55555555U, 0xAAAAAAAAU};
    for (uint32_t p = 0; p < sizeof(patterns) / sizeof(patterns[0]); ++p)
    {
        for (uint32_t i = 0; i < 64U; ++i)
        {
            scratch[i] = patterns[p] ^ i;
        }
        for (uint32_t i = 0; i < 64U; ++i)
        {
            if (scratch[i] != (patterns[p] ^ i))
            {
                return false;
            }
        }
    }
    return true;
}

static void PrintInfo(void)
{
    PRINTF("\r\nBoard: %s | CPU: RW612 Cortex-M33\r\n", BOARD_NAME);
    PRINTF("SDK: %s | Core clock: %u Hz\r\n", MCUXSDK_VERSION_FULL_STR,
           (unsigned int)SystemCoreClock);
    PRINTF("UART: FLEXCOMM3, %u baud, 8N1, no flow control\r\n",
           (unsigned int)BOARD_DEBUG_UART_BAUDRATE);
    PRINTF("Uptime: %u ms | RX bytes: %u | RX FIFO errors: %u\r\n",
           (unsigned int)s_milliseconds, (unsigned int)s_rxCount, (unsigned int)s_rxErrors);
}

static void PrintHelp(void)
{
    PRINTF("\r\nKeys: ? = help, i = info, t = toggle heartbeat, r = RAM buffer test\r\n");
    PRINTF("Other characters are echoed. Disable terminal local echo.\r\n");
}

int main(void)
{
    USART_Type *const uart = (USART_Type *)BOARD_DEBUG_UART_BASEADDR;
    uint32_t lastHeartbeat = 0U;
    uint32_t heartbeatCount = 0U;

    BOARD_InitHardware();
    SystemCoreClockUpdate();
    PRINTF("\r\n=== FRDM-RW612 Keil board test ===\r\n");
    PrintInfo();
    PRINTF("SRAM scratch buffer (256 bytes): %s\r\n", TestRamBuffer() ? "PASS" : "FAIL");
    PrintHelp();

    if (SysTick_Config(SystemCoreClock / 1000U) != 0U)
    {
        PRINTF("ERROR: cannot configure 1 ms SysTick.\r\n");
        while (1) {}
    }

    while (1)
    {
        const uint32_t now = s_milliseconds;
        if ((uint32_t)(now - lastHeartbeat) >= 1000U)
        {
            lastHeartbeat = now;
            if (s_heartbeatEnabled)
            {
                PRINTF("[heartbeat %u] uptime=%u ms, rx=%u, fifo_errors=%u\r\n",
                       (unsigned int)++heartbeatCount, (unsigned int)now,
                       (unsigned int)s_rxCount, (unsigned int)s_rxErrors);
            }
        }

        const uint32_t flags = USART_GetStatusFlags(uart);
        if ((flags & kUSART_RxError) != 0U)
        {
            USART_ClearStatusFlags(uart, kUSART_RxError);
            ++s_rxErrors;
        }
        if ((flags & kUSART_RxFifoNotEmptyFlag) != 0U)
        {
            const uint8_t ch = USART_ReadByte(uart);
            ++s_rxCount;
            switch (ch)
            {
                case '?': PrintHelp(); break;
                case 'i': PrintInfo(); break;
                case 't':
                    s_heartbeatEnabled = !s_heartbeatEnabled;
                    PRINTF("\r\nHeartbeat: %s\r\n", s_heartbeatEnabled ? "ON" : "OFF");
                    break;
                case 'r':
                    PRINTF("\r\nSRAM scratch buffer (256 bytes): %s\r\n",
                           TestRamBuffer() ? "PASS" : "FAIL");
                    break;
                case '\r': PRINTF("\r\n"); break;
                case '\n': break;
                default: PUTCHAR(ch); break;
            }
        }
    }
}

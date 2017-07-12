#include <stdbool.h>
#include <stdint.h>
#include "inc/hw_memmap.h"
#include "inc/hw_types.h"
#include "driverlib/gpio.h"
#include "driverlib/rom.h"
#include "drivers/rgb.h"
#include "drivers/buttons.h"
#include "utils/uartstdio.h"
#include "led_task.h"
#include "priorities.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

// The stack size for the LED toggle task.
#define LEDTASKSTACKSIZE        128                     // Stack size in words
#define LED_ITEM_SIZE           sizeof(uint8_t)        // The item size and queue size for the LED message queue.
#define LED_QUEUE_SIZE          5
#define ui32LEDToggleDelay      250                     // Default LED toggle delay value. LED toggling frequency is twice this number.

// The queue that holds messages sent to the LED task.

xQueueHandle g_pLEDQueue;
static uint32_t g_pui32Colors[3] = {0x0000, 0x0000, 0x0000};

extern xSemaphoreHandle g_pUARTSemaphore;

// This task toggles the user selected LED at a user selected frequency. User can make the selections by pressing the left and right buttons.

static void LEDTask(void *pvParameters)
{
    portTickType ui32WakeTime;
    uint8_t i8Message;

    // Get the current tick count.

    ui32WakeTime = xTaskGetTickCount();

    // Loop forever.

    while(1)
    {
        // Read the next message, if available on queue.

        if(xQueueReceive(g_pLEDQueue, &i8Message, 0) == pdPASS)
        {
            // If received CAN msg is 0xF --> LED ON
            if(i8Message == 0xf)
            {
                    RGBEnable();
            }
            // If received CAN msg is 0 --> LED OFF
           else if (i8Message == 0x0)
                {
                    RGBDisable();
                }
        }

        vTaskDelayUntil(&ui32WakeTime, ui32LEDToggleDelay / portTICK_RATE_MS);
    }
}

// Initializes the LED task.

uint32_t LEDTaskInit(void)
{
    // Initialize the GPIOs and Timers that drive the three LEDs.

    RGBInit(1);
    RGBIntensitySet(0.3f);

    // Turn on the Red LED

    g_pui32Colors[0] = 0x8000;
    RGBColorSet(g_pui32Colors);

    // LED is Off
    RGBDisable();

    // Create a queue for sending messages to the LED task.

    g_pLEDQueue = xQueueCreate(LED_QUEUE_SIZE, LED_ITEM_SIZE);

    // Create the LED task.

    if(xTaskCreate(LEDTask, (const portCHAR *)"LED", LEDTASKSTACKSIZE, NULL, tskIDLE_PRIORITY + PRIORITY_LED_TASK, NULL) != pdTRUE)
    {
        return(1);
    }

    // Success.
    return(0);
}

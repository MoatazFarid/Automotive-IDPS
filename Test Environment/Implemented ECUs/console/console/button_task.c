#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include "inc/hw_memmap.h"
#include "inc/hw_ints.h"
#include "driverlib/gpio.h"
#include "driverlib/sysctl.h"
#include "driverlib/pin_map.h"
#include "driverlib/systick.h"
#include "driverlib/rom.h"
#include "utils/uartstdio.h"
#include "inc/hw_can.h"
#include "driverlib/can.h"
#include "inc/hw_gpio.h"
#include "drivers/buttons.h"
#include "inc/hw_types.h"
#include "priorities.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"

#define BUTTONTASKSTACKSIZE        128         // Stack size in words
extern xSemaphoreHandle g_pUARTSemaphore;

extern xQueueHandle g_pCAN0Queue;


static void ButtonTask(void *pvParameters)
{
    TickType_t xCANDelayms = pdMS_TO_TICKS(100);
    uint8_t ui8CurButtonState, ui8PrevButtonState;
    uint8_t ui8Message;

    ui8CurButtonState = ui8PrevButtonState = 0;

    uint8_t flage = 0;

    while(1)
    {

        // Poll the debounced state of the buttons.
        //
        ui8CurButtonState = ButtonsPoll(0, 0);

        // Check if previous debounced state is equal to the current state.
        //
        if(ui8CurButtonState != ui8PrevButtonState)
        {
            ui8PrevButtonState = ui8CurButtonState;

            // Check to make sure the change in state is due to button press
            // and not due to button release.
            //
            if((ui8CurButtonState & ALL_BUTTONS) != 0)
            {
                if((ui8CurButtonState & ALL_BUTTONS) == LEFT_BUTTON)
                {
                    if(flage == 0)
                    {
                        ui8Message = 0xf;
                        flage = 1;
                    }
                    else if(flage == 1)
                    {
                        ui8Message = 0x0;
                        flage = 0;
                    }

                    xSemaphoreTake(g_pUARTSemaphore, portMAX_DELAY);
                    UARTprintf("Left Button is pressed.\n");
                    xSemaphoreGive(g_pUARTSemaphore);
                }


                if(xQueueSend(g_pCAN0Queue, &ui8Message, portMAX_DELAY) != pdPASS)
                {
                    UARTprintf("\nQueue full. This should never happen.\n");
                    while(1)
                    {
                    }
                }
            }
        }
           vTaskDelay(xCANDelayms);
       }

}

uint32_t ButtonsTaskInit(void)
{

    ButtonsInit();

    if(xTaskCreate(ButtonTask, (const portCHAR *)"Button", BUTTONTASKSTACKSIZE, NULL, tskIDLE_PRIORITY + PRIORITY_BUTTON_TASK, NULL) != pdTRUE)


    {
        return(1);
    }

    //
    // Success.
    //
    return(0);

}

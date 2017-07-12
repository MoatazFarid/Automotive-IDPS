#include <can_task.h>
#include <stdbool.h>
#include <stdint.h>
#include "inc/hw_memmap.h"
#include "inc/hw_types.h"
#include "inc/hw_gpio.h"
#include "driverlib/sysctl.h"
#include "driverlib/gpio.h"
#include "driverlib/rom.h"
#include "drivers/buttons.h"
#include "utils/uartstdio.h"
#include "led_task.h"
#include "can_task.h"
#include "priorities.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "inc/hw_can.h"
#include "inc/hw_ints.h"
#include "driverlib/can.h"
#include "driverlib/interrupt.h"
#include "driverlib/pin_map.h"



#define CanDelay                25
#define CANTASKSTACKSIZE        128         // Stack size in words

volatile bool g_bRXFlag = 0;
volatile bool g_bErrFlag = 0;

extern xQueueHandle g_pLEDQueue;
extern xSemaphoreHandle g_pUARTSemaphore;

static void CANTask(void *pvParameters)
{
    tCANMsgObject sCANMessage;
    uint8_t ui8MsgData;
    //fportTickType ui16LastTime;

    sCANMessage.ui32MsgID = 0;
    sCANMessage.ui32MsgIDMask = 0;
    sCANMessage.ui32Flags = MSG_OBJ_RX_INT_ENABLE | MSG_OBJ_USE_ID_FILTER;
    sCANMessage.ui32MsgLen = 8;
    CANMessageSet(CAN0_BASE, 1, &sCANMessage, MSG_OBJ_TYPE_RX);

    TickType_t xCANDelayms = pdMS_TO_TICKS(100);

    for(;;)
   {


            // If the flag is set, that means that the RX interrupt occurred and  there is a message ready to be read from the CAN

            if(g_bRXFlag)
            {
                // Reuse the same message object that was used earlier to configure the CAN for receiving messages.
                // A buffer for storing the received data must also be provided, so set the buffer pointer
                // within the message object.

                sCANMessage.pui8MsgData = (uint8_t*) &ui8MsgData;

                // Read the message from the CAN.  Message object number 1 is used (which is not the same thing as CAN ID).
                // The interrupt clearing flag is not set because this interrupt was already cleared in the interrupt handler.

                CANMessageGet(CAN0_BASE, 1, &sCANMessage, 0);

                // Clear the pending message flag so that the interrupt handler can set it again when the next message arrives.

                g_bRXFlag = 0;

                // Check to see if there is an indication that some messages were lost.

                if(sCANMessage.ui32Flags & MSG_OBJ_DATA_LOST)
                {
                    UARTprintf("CAN message loss detected\n");
                }

                // Print out the contents of the message that was received.

                UARTprintf("ID=0x%08X data=0x", sCANMessage.ui32MsgID);


                if (sCANMessage.ui32MsgID == 0x50)
                {


                    if(xQueueSend(g_pLEDQueue, &ui8MsgData, portMAX_DELAY) != pdPASS)
                    {
                        // Error. The queue should never be full. If so print the error message on UART and wait for ever.
                        UARTprintf("\nQueue full\n");
                        while(1)
                         {
                         }
                    }

                }
            }
            vTaskDelay( xCANDelayms );

    }
  }

//*****************************************************************************
// Initializes the switch task.
//*****************************************************************************
uint32_t CANTaskInit(void)
{
    // For this example CAN0 is used with RX and TX pins on port E4 and E5. The actual port and pins used may be different on your part, consult
    // the data sheet for more information. GPIO port B needs to be enabled so these pins can be used.

    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOE);

    // Configure the GPIO pin muxing to select CAN0 functions for these pins.

    GPIOPinConfigure(GPIO_PE4_CAN0RX);
    GPIOPinConfigure(GPIO_PE5_CAN0TX);

    // Enable the alternate function on the GPIO pins.  The above step selects which alternate function is available.
    // This step actually enables the alternate function instead of GPIO for these pins.

    GPIOPinTypeCAN(GPIO_PORTE_BASE, GPIO_PIN_4 | GPIO_PIN_5);

    // The GPIO port and pins have been set up for CAN.  The CAN peripheral must be enabled.

    SysCtlPeripheralEnable(SYSCTL_PERIPH_CAN0);

    // Initialize the CAN controller

    CANInit(CAN0_BASE);

    // Set up the bit rate for the CAN bus.  This function sets up the CAN bus timing for a nominal configuration.  You can achieve more control
    // over the CAN bus timing by using the function CANBitTimingSet() instead of this one, if needed.
    // In this example, the CAN bus is set to 500 kHz.  In the function below, the call to SysCtlClockGet() or ui32SysClock is used to determine the
    // clock rate that is used for clocking the CAN peripheral.  This can be replaced with a  fixed value if you know the value of the system clock,
    // saving the extra function call.  For some parts, the CAN peripheral is clocked by a fixed 8 MHz regardless of the system clock in which case
    // the call to SysCtlClockGet() or ui32SysClock should be replaced with 8000000.  Consult the data sheet for more information about CAN
    // peripheral clocking.

    CANBitRateSet(CAN0_BASE, SysCtlClockGet(), 500000);

    // Enable interrupts on the CAN peripheral.  This example uses static allocation of interrupt handlers which means the name of the handler
    // is in the vector table of startup code.
    CANIntEnable(CAN0_BASE, CAN_INT_MASTER | CAN_INT_ERROR | CAN_INT_STATUS);

    // Enable the CAN interrupt on the processor (NVIC).

    IntEnable(INT_CAN0);

    // Enable the CAN for operation.

    CANEnable(CAN0_BASE);

    if(xTaskCreate(CANTask, (const portCHAR *)"CAN", CANTASKSTACKSIZE, NULL, tskIDLE_PRIORITY + PRIORITY_CAN_TASK, NULL) != pdTRUE)
    {
        return(1);
    }

    // Success.

    return(0);
}

void CANIntHandler(void)
{
    uint32_t ui32Status;

    // Read the CAN interrupt status to find the cause of the interrupt

    ui32Status = CANIntStatus(CAN0_BASE, CAN_INT_STS_CAUSE);

    // If the cause is a controller status interrupt, then get the status

    if(ui32Status == CAN_INT_INTID_STATUS)
    {
        // Read the controller status.  This will return a field of status error bits that can indicate various errors.  Error processing
        // is not done in this example for simplicity.  Refer to the API documentation for details about the error status bits.
        // The act of reading this status will clear the interrupt.

        ui32Status = CANStatusGet(CAN0_BASE, CAN_STS_CONTROL);

        // Set a flag to indicate some errors may have occurred.

        g_bErrFlag = 1;
    }

    // Check if the cause is message object 1, which what we are using for receiving messages.

    else if(ui32Status == 1)
    {
        // Getting to this point means that the RX interrupt occurred on message object 1, and the message reception is complete.  Clear the
        // message object interrupt.

        CANIntClear(CAN0_BASE, 1);

        // Set flag to indicate received message is pending.

        g_bRXFlag = 1;

        // Since a message was received, clear any error flags.

        g_bErrFlag = 0;
    }

    // Otherwise, something unexpected caused the interrupt.  This should never happen.

    else
    {
        // Spurious interrupt handling can go here.
    }
}

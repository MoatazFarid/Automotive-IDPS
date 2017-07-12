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
#include "inc/hw_types.h"
#include "priorities.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "semphr.h"
#include "driverlib/fpu.h"
#include "driverlib/uart.h"
#include "grlib/grlib.h"
#include "driverlib/interrupt.h"

//*****************************************************************************
//
// The stack size for the CAN sending task.
//
//*****************************************************************************
#define CANTASKSTACKSIZE        128         // Stack size in words

//*****************************************************************************
//
// The item size and queue size for the CAN message queue.
//
//*****************************************************************************

#define CAN_ITEM_SIZE           sizeof(uint8_t)        // The item size and queue size for the CAN message queue.
#define CAN_QUEUE_SIZE          10


volatile bool g_bErrFlag = 0;

static void CAN0Task(void *pvParameters);
//*****************************************************************************
//
// The queue that holds messages sent to the CAN task.
//
//*****************************************************************************
xQueueHandle g_pCAN0Queue;

void CAN0IntHandler(void)
{
    uint32_t ui32Status;

    // Read the CAN interrupt status to find the cause of the interrupt

    ui32Status = CANIntStatus(CAN0_BASE, CAN_INT_STS_CAUSE);

    // If the cause is a controller status interrupt, then get the status

    if(ui32Status == CAN_INT_INTID_STATUS)
    {

        // Read the controller status.  This will return a field of status error bits that can indicate various errors.
        //Error processing is not done in this example for simplicity.  Refer to the API documentation for details about the error status bits.
        // The act of reading this status will clear the interrupt.  If the CAN peripheral is not connected to a CAN bus with other CAN devices
        // present, then errors will occur and will be indicated in the controller status.

        ui32Status = CANStatusGet(CAN0_BASE, CAN_STS_CONTROL);

        // Set a flag to indicate some errors may have occurred.

        g_bErrFlag = 1;
    }

    // Check if the cause is message object 1, which what we are using for sending messages.

    else if(ui32Status == 1)
    {
        // Getting to this point means that the TX interrupt occurred on message object 1, and the message TX is complete.
        //Clear the message object interrupt.

        CANIntClear(CAN0_BASE, 1);

        // Since the message was sent, clear any error flags.

        g_bErrFlag = 0;
    }
}

uint32_t CAN0TaskInit(void)
{
    // CAN0 is used with RX and TX pins on port E4 and E5.
    SysCtlPeripheralEnable(SYSCTL_PERIPH_GPIOE);

    // Configure the GPIO pin muxing to select CAN0 functions for these pins.
    //This step selects which alternate function is available for these pins.
    // This is necessary if your part supports GPIO pin function muxing.

    GPIOPinConfigure(GPIO_PE4_CAN0RX);
    GPIOPinConfigure(GPIO_PE5_CAN0TX);

    // Enable the alternate function on the GPIO pins.  The above step selects which alternate function is available.
    // This step actually enables the alternate function instead of GPIO for these pins.
    // TODO: change this to match the port/pin you are using

    GPIOPinTypeCAN(GPIO_PORTE_BASE, GPIO_PIN_4 | GPIO_PIN_5);

    // The GPIO port and pins have been set up for CAN.  The CAN peripheral must be enabled.

    SysCtlPeripheralEnable(SYSCTL_PERIPH_CAN0);
    CANInit(CAN0_BASE);

    CANBitRateSet(CAN0_BASE, SysCtlClockGet(), 500000);

    // Enable interrupts on the CAN peripheral.  This example uses static allocation of interrupt handlers which means the name of the handler
    // is in the vector table of startup code.  If you want to use dynamic allocation of the vector table,
    // then you must also call CANIntRegister() there.

     //CANIntRegister(CAN0_BASE, CAN0IntHandler); // if using dynamic vectors

    CANIntEnable(CAN0_BASE, CAN_INT_MASTER | CAN_INT_ERROR | CAN_INT_STATUS);

    // Enable the CAN interrupt on the processor (NVIC).

    IntEnable(INT_CAN0);

    // Enable the CAN for operation.

     CANEnable(CAN0_BASE);


     g_pCAN0Queue = xQueueCreate(CAN_QUEUE_SIZE, CAN_ITEM_SIZE);

        //
        // Create the CAN task.
        //
        if(xTaskCreate(CAN0Task, (const portCHAR *)"CAN0", CANTASKSTACKSIZE, NULL, tskIDLE_PRIORITY + PRIORITY_CAN0_TASK, NULL) != pdTRUE)


        {
            return(1);
        }

        //
        // Success.
        //
        return(0);


}

static void CAN0Task(void *pvParameters)
{
    TickType_t xCANDelayms = pdMS_TO_TICKS(100);

    tCANMsgObject sCANMessage;

    uint8_t ui8MsgData = 0 ;

    sCANMessage.pui8MsgData = (uint8_t *)&ui8MsgData;


    // Initialize the message object that will be used for sending CAN messages.
    // The message will be 4 bytes that will contain an incrementing value.  Initially it will be set to 0.

    sCANMessage.ui32MsgID = 0x50;
    sCANMessage.ui32MsgIDMask = 0;
    sCANMessage.ui32Flags = MSG_OBJ_TX_INT_ENABLE;
    sCANMessage.ui32MsgLen = sizeof(uint8_t);

    while(1)
    {

        if(xQueueReceive(g_pCAN0Queue, &ui8MsgData, 0) == pdPASS)
        {
            sCANMessage.pui8MsgData = (uint8_t *)&ui8MsgData;

        }
        CANMessageSet(CAN0_BASE, 1, &sCANMessage, MSG_OBJ_TYPE_TX);

        //delay half second
        SysCtlDelay(8000000 / 3);

        if(g_bErrFlag)
        {
           UARTprintf(" Error - cable connected?\n");
        }
        else
        {
        }

        vTaskDelay(xCANDelayms);
    }

}



################################################################################
# Automatically-generated file. Do not edit!
################################################################################

SHELL = cmd.exe

# Each subdirectory must supply rules for building sources it contributes
drivers/buttons.obj: C:/ti/TivaWare_C_Series-2.1.2.111/examples/boards/ek-tm4c123gxl/drivers/buttons.c $(GEN_OPTS) | $(GEN_HDRS)
	@echo 'Building file: $<'
	@echo 'Invoking: ARM Compiler'
	"C:/ti/ccsv7/tools/compiler/ti-cgt-arm_16.9.0.LTS/bin/armcl" -mv7M4 --code_state=16 --float_support=FPv4SPD16 --abi=eabi -me -O2 --include_path="C:/ti/ccsv7/tools/compiler/ti-cgt-arm_16.9.0.LTS/include" --include_path="D:/workspace_v7/Lamp_freertos_final" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/examples/boards/ek-tm4c123gxl" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS/Source/include" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS/Source/portable/CCS/ARM_CM4F" --advice:power=all -g --gcc --define=ccs="ccs" --define=PART_TM4C123GH6PM --define=TARGET_IS_TM4C123_RB1 --diag_wrap=off --diag_warning=225 --display_error_number --gen_func_subsections=on --ual --preproc_with_compile --preproc_dependency="drivers/buttons.d" --obj_directory="drivers" $(GEN_OPTS__FLAG) "$<"
	@echo 'Finished building: $<'
	@echo ' '

drivers/rgb.obj: C:/ti/TivaWare_C_Series-2.1.2.111/examples/boards/ek-tm4c123gxl/drivers/rgb.c $(GEN_OPTS) | $(GEN_HDRS)
	@echo 'Building file: $<'
	@echo 'Invoking: ARM Compiler'
	"C:/ti/ccsv7/tools/compiler/ti-cgt-arm_16.9.0.LTS/bin/armcl" -mv7M4 --code_state=16 --float_support=FPv4SPD16 --abi=eabi -me -O2 --include_path="C:/ti/ccsv7/tools/compiler/ti-cgt-arm_16.9.0.LTS/include" --include_path="D:/workspace_v7/Lamp_freertos_final" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/examples/boards/ek-tm4c123gxl" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS/Source/include" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS" --include_path="C:/ti/TivaWare_C_Series-2.1.2.111/third_party/FreeRTOS/Source/portable/CCS/ARM_CM4F" --advice:power=all -g --gcc --define=ccs="ccs" --define=PART_TM4C123GH6PM --define=TARGET_IS_TM4C123_RB1 --diag_wrap=off --diag_warning=225 --display_error_number --gen_func_subsections=on --ual --preproc_with_compile --preproc_dependency="drivers/rgb.d" --obj_directory="drivers" $(GEN_OPTS__FLAG) "$<"
	@echo 'Finished building: $<'
	@echo ' '



@echo off
REM Battery Diagnostics Script for OnePlus Phone
REM Make sure ADB is in your PATH or place this script in the same folder as adb.exe

echo Starting battery diagnostics collection...
echo Timestamp: %date% %time%

REM Create timestamp for folder structure
set timestamp=%date%_%time%
set timestamp=%timestamp::=-%
set timestamp=%timestamp:.=-%
set timestamp=%timestamp: =0%

REM Create output directory structure: logs\timestamp\
set output_dir=logs\%timestamp%
if not exist "logs" mkdir logs
if not exist "%output_dir%" mkdir "%output_dir%"

echo Collecting basic battery information...
adb shell dumpsys battery > "%output_dir%\battery_basic.txt"
if %errorlevel% neq 0 (
    echo ERROR: Failed to collect basic battery info. Make sure device is connected and ADB debugging is enabled.
    pause
    exit /b 1
)

echo Collecting detailed battery statistics...
adb shell dumpsys batterystats > "%output_dir%\battery_stats.txt"
if %errorlevel% neq 0 (
    echo ERROR: Failed to collect battery statistics.
    pause
    exit /b 1
)

echo Collecting enhanced battery statistics...
adb shell dumpsys batterystats --reset > "%output_dir%\battery_stats_reset.txt"
adb shell dumpsys batterystats > "%output_dir%\battery_stats_detailed.txt"
adb shell dumpsys alarm > "%output_dir%\alarm_stats.txt"
adb shell dumpsys jobscheduler > "%output_dir%\job_scheduler.txt"

echo Collecting battery hardware information...
REM Create combined battery hardware file
echo === Battery Hardware Information === > "%output_dir%\battery_hardware.txt"
echo Timestamp: %date% %time% >> "%output_dir%\battery_hardware.txt"
echo. >> "%output_dir%\battery_hardware.txt"

REM Get power supply list for reference
echo === Available Power Supplies === >> "%output_dir%\battery_hardware.txt"
adb shell "ls /sys/class/power_supply/" >> "%output_dir%\battery_hardware.txt" 2>nul
echo. >> "%output_dir%\battery_hardware.txt"

REM Try multiple possible paths for cycle count
echo === Cycle Count === >> "%output_dir%\battery_hardware.txt"
adb shell "cat /sys/class/power_supply/battery/cycle_count 2>/dev/null || cat /sys/class/power_supply/bms/cycle_count 2>/dev/null || cat /sys/class/power_supply/battery/charge_cycle_count 2>/dev/null || echo 'Cycle count not available'" >> "%output_dir%\battery_hardware.txt"
echo. >> "%output_dir%\battery_hardware.txt"

REM Collect main battery parameters in combined file
for %%f in (capacity voltage_now temp health charge_full charge_full_design status present technology) do (
    echo === %%f === >> "%output_dir%\battery_hardware.txt"
    adb shell "cat /sys/class/power_supply/battery/%%f 2>/dev/null || echo 'File not found or no permission'" >> "%output_dir%\battery_hardware.txt"
    echo. >> "%output_dir%\battery_hardware.txt"
)

REM Try additional battery-related files that might contain useful info
echo === Additional Battery Info === >> "%output_dir%\battery_hardware.txt"
for %%f in (charge_counter charge_now current_now power_now) do (
    echo --- %%f --- >> "%output_dir%\battery_hardware.txt"
    adb shell "cat /sys/class/power_supply/battery/%%f 2>/dev/null || echo 'Not available'" >> "%output_dir%\battery_hardware.txt"
)
echo. >> "%output_dir%\battery_hardware.txt"

REM Try OnePlus/OxygenOS specific paths
echo === OnePlus Specific Battery Info === >> "%output_dir%\battery_hardware.txt"
adb shell "find /sys/class/power_supply -name '*cycle*' -type f 2>/dev/null | head -5 | while read file; do echo \"--- \$file ---\"; cat \"\$file\" 2>/dev/null || echo 'Cannot read'; done" >> "%output_dir%\battery_hardware.txt" 2>nul
echo. >> "%output_dir%\battery_hardware.txt"

echo Collecting thermal information...
adb shell dumpsys thermalservice > "%output_dir%\thermal.txt"

echo Collecting system performance metrics...
adb shell dumpsys meminfo > "%output_dir%\memory_info.txt"
adb shell dumpsys cpuinfo --verbose > "%output_dir%\cpuinfo_verbose.txt"
adb shell dumpsys procstats --hours 24 > "%output_dir%\procstats_24h.txt"
adb shell dumpsys procstats --hours 1 > "%output_dir%\procstats_1h.txt"

echo Collecting power management info...
adb shell dumpsys power > "%output_dir%\power.txt"

echo Collecting enhanced power analysis...
adb shell dumpsys power --verbose > "%output_dir%\power_verbose.txt"
adb shell dumpsys usagestats > "%output_dir%\usage_stats.txt"
adb shell dumpsys appops > "%output_dir%\app_ops.txt"
adb shell dumpsys deviceidle > "%output_dir%\device_idle.txt"

echo Collecting process and CPU information...
adb shell dumpsys cpuinfo > "%output_dir%\cpuinfo.txt"
adb shell dumpsys procstats > "%output_dir%\procstats.txt"

echo Collecting enhanced process analysis...
adb shell dumpsys activity processes > "%output_dir%\processes.txt"
adb shell dumpsys activity activities > "%output_dir%\activities.txt"
adb shell dumpsys window windows > "%output_dir%\window_manager.txt"
adb shell dumpsys activity service > "%output_dir%\service_activities.txt"

echo Collecting network and connectivity info...
adb shell dumpsys wifi > "%output_dir%\wifi.txt"
adb shell dumpsys telephony.registry > "%output_dir%\telephony.txt"
adb shell dumpsys connectivity > "%output_dir%\connectivity.txt"

echo Collecting enhanced network analysis...
adb shell dumpsys netstats > "%output_dir%\netstats.txt"
adb shell dumpsys connectivity > "%output_dir%\connectivity_detailed.txt"
adb shell dumpsys netpolicy > "%output_dir%\netpolicy.txt"
adb shell dumpsys wifi --verbose > "%output_dir%\wifi_verbose.txt"

echo Collecting device info for context...
REM Use a more comprehensive approach for device info
echo === Device Information === > "%output_dir%\device_info.txt"
echo Timestamp: %date% %time% >> "%output_dir%\device_info.txt"
echo. >> "%output_dir%\device_info.txt"

adb shell "getprop ro.product.model" > temp_model.txt
set /p device_model=<temp_model.txt
echo Model: %device_model% >> "%output_dir%\device_info.txt"
del temp_model.txt

adb shell "getprop ro.product.brand" > temp_brand.txt
set /p device_brand=<temp_brand.txt
echo Brand: %device_brand% >> "%output_dir%\device_info.txt"
del temp_brand.txt

adb shell "getprop ro.build.version.release" > temp_version.txt
set /p android_version=<temp_version.txt
echo Android Version: %android_version% >> "%output_dir%\device_info.txt"
del temp_version.txt

REM Get all relevant properties
echo. >> "%output_dir%\device_info.txt"
echo === All Relevant Properties === >> "%output_dir%\device_info.txt"
adb shell getprop | findstr /i "model product brand version build" >> "%output_dir%\device_info.txt"

echo.
echo Battery diagnostics collection completed!
echo Files saved in: %output_dir%
echo Timestamp: %timestamp%
echo.

REM List generated files
echo Generated files:
dir "%output_dir%\*.txt" /b

echo.
echo Press any key to exit...
pause >nul


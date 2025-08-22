# Phone Diagnostic Data Analysis

This project provides comprehensive tools to read, parse, analyze, and visualize diagnostic information collected from your OnePlus phone using Android Developer Tools (ADB).

## Overview

The diagnostic system collects various types of phone data including:
- **Battery Information**: Level, voltage, temperature, charging status, power source
- **Device Information**: Model, brand, Android version, build properties
- **Thermal Data**: CPU, GPU, battery, and skin temperatures
- **Power Management**: Power states, wake locks, power consumption
- **CPU Information**: Load, frequencies, performance metrics
- **Network Data**: WiFi, connectivity, telephony information

## Files

- `diag.bat` - Windows batch script to collect diagnostic data from your phone
- `phone_diagnostics_analysis.py` - Python script with the complete analysis framework
- `testing.ipynb` - Jupyter notebook for interactive analysis
- `requirements.txt` - Python package dependencies
- `logs/` - Directory containing timestamped diagnostic sessions

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Enable ADB Debugging on Your Phone

1. Go to Settings > About Phone
2. Tap "Build Number" 7 times to enable Developer Options
3. Go to Settings > Developer Options
4. Enable "USB Debugging"
5. Connect your phone to your computer via USB

### 3. Install ADB Tools

- **Windows**: Download Android SDK Platform Tools from Google
- **macOS**: `brew install android-platform-tools`
- **Linux**: `sudo apt-get install android-tools-adb`

## Usage

### Collecting Diagnostic Data

1. Connect your phone and ensure ADB debugging is enabled
2. Run the diagnostic collection script:
   ```bash
   diag.bat
   ```
3. The script will create timestamped folders in the `logs/` directory

### Analyzing Data in Python

#### Option 1: Run the Complete Analysis

```python
from phone_diagnostics_analysis import run_complete_analysis

# Run the complete pipeline
parser, summary_df, parsed_data = run_complete_analysis()
```

#### Option 2: Step-by-Step Analysis

```python
from phone_diagnostics_analysis import PhoneDiagnosticParser

# Initialize parser
parser = PhoneDiagnosticParser()

# Discover sessions
sessions = parser.discover_sessions()

# Parse all data
parsed_data = parser.parse_all_sessions()

# Create summary DataFrame
summary_df = parser.get_summary_dataframe()

# Analyze battery health
analyze_battery_health(summary_df)

# Create visualizations
create_visualizations(summary_df)

# Export data
export_data(summary_df, parsed_data)
```

### Using the Jupyter Notebook

1. Start Jupyter:
   ```bash
   jupyter notebook
   ```

2. Open `testing.ipynb`

3. Run the cells sequentially to:
   - Load and parse diagnostic data
   - View summary information
   - Analyze battery health
   - Create visualizations
   - Export data

## Data Structure

### Diagnostic Sessions

Each diagnostic session is stored in a folder named `g-YYMMDD-HHMMSS` containing:
- `battery_basic.txt` - Basic battery information
- `battery_stats.txt` - Detailed battery statistics
- `battery_hardware.txt` - Hardware-level battery data
- `device_info.txt` - Device specifications
- `thermal.txt` - Temperature readings
- `power.txt` - Power management data
- `cpuinfo.txt` - CPU information
- `procstats.txt` - Process statistics
- `wifi.txt` - WiFi information
- `connectivity.txt` - Network connectivity
- `telephony.txt` - Telephony data

### Parsed Data Structure

The parser extracts structured data including:
- **Battery**: Level, voltage, temperature, charging status, power source
- **Device**: Model, brand, Android version
- **Thermal**: CPU, GPU, battery, skin temperatures
- **Power**: Power states, wake locks
- **CPU**: Load percentages, frequencies

## Analysis Features

### Battery Health Analysis
- Battery level trends over time
- Charging and discharging rates
- Temperature monitoring with warnings
- Power source usage patterns

### Temperature Monitoring
- Real-time temperature tracking
- Component-specific temperature analysis
- Thermal threshold warnings
- Cooling device status

### Performance Metrics
- CPU utilization patterns
- Process statistics
- Power consumption analysis
- Network performance data

### Data Export
- CSV summary data
- JSON detailed data
- Statistical summaries
- Memory usage information

## Visualization

The system creates comprehensive visualizations:
1. **Battery Level Trends** - Time-series plot of battery levels
2. **Temperature Trends** - Multi-component temperature tracking
3. **Charging Status** - Distribution of charging states
4. **Power Source Usage** - AC vs USB power usage

## Troubleshooting

### Common Issues

1. **ADB Device Not Found**
   - Ensure USB debugging is enabled
   - Check USB connection
   - Install proper ADB drivers

2. **Permission Denied Errors**
   - Grant ADB permissions on your phone
   - Check file permissions in logs directory

3. **Missing Data Files**
   - Verify the diagnostic script completed successfully
   - Check logs directory structure

4. **Python Import Errors**
   - Install required packages: `pip install -r requirements.txt`
   - Check Python version compatibility

### Data Validation

The parser includes error handling for:
- Missing or corrupted files
- Malformed data formats
- Encoding issues
- Incomplete diagnostic sessions

## Customization

### Adding New Data Sources

1. Create a new parser method in `PhoneDiagnosticParser`
2. Add file type detection in `parse_all_sessions()`
3. Update the summary DataFrame creation
4. Add visualization components

### Modifying Analysis

1. Edit analysis functions in the main script
2. Customize visualization parameters
3. Add new export formats
4. Implement custom metrics

## Performance Considerations

- Large log directories may take time to parse
- Memory usage scales with number of sessions
- Consider data archiving for long-term analysis
- Use pandas chunking for very large datasets

## Security Notes

- Diagnostic data may contain sensitive information
- Avoid sharing raw diagnostic files
- Consider data anonymization for sharing
- Secure storage of diagnostic sessions

## Support

For issues or questions:
1. Check the troubleshooting section
2. Verify your setup matches requirements
3. Review error messages in the console output
4. Check file permissions and paths

## License

This project is provided as-is for educational and diagnostic purposes.

# Phone Diagnostic Data Analysis
# This script reads, parses, and analyzes diagnostic information collected from your OnePlus phone using ADB commands.

# Import required libraries
import os
import re
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)

class PhoneDiagnosticParser:
    """Parser for phone diagnostic data collected via ADB commands"""
    
    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.sessions = {}
        self.parsed_data = {}
        
    def discover_sessions(self):
        """Find all diagnostic sessions in the logs directory"""
        if not self.logs_dir.exists():
            print(f"Logs directory '{self.logs_dir}' not found!")
            return {}
            
        sessions = {}
        for session_dir in self.logs_dir.iterdir():
            if session_dir.is_dir():
                timestamp = self._parse_timestamp(session_dir.name)
                sessions[session_dir.name] = {
                    'path': session_dir,
                    'timestamp': timestamp,
                    'files': list(session_dir.glob('*.txt'))
                }
        
        self.sessions = sessions
        print(f"Found {len(sessions)} diagnostic sessions")
        return sessions
    
    def _parse_timestamp(self, dirname):
        """Parse timestamp from a directory name like '23-Aug-25_03-20-07-44'."""
        try:
            # Define the format string that matches "DD-Mon-YY_HH-MM-SS"
            format_string = '%d-%b-%y_%H-%M-%S'
            
            # Parse the directory name, slicing off the fractional seconds ('-44') at the end.
            return datetime.strptime(dirname[:-3], format_string)
            
        except ValueError as e:
            # If the directory name doesn't match the format, a ValueError is raised.
            # We'll print a warning and return None.
            print(f"Warning: Could not parse timestamp from '{dirname}': {e}")
            return None
    
    def parse_battery_basic(self, file_path):
        """Parse basic battery information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse OPLUS Battery Service state
            oplus_match = re.search(r'Current OPLUS Battery Service state:(.*?)Current Battery Service state:', 
                                   content, re.DOTALL)
            if oplus_match:
                oplus_section = oplus_match.group(1)
                
                # Extract key-value pairs
                for line in oplus_section.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert values to appropriate types
                        if value.isdigit():
                            value = int(value)
                            # Fix temperature scaling (likely in tenths of a degree)
                            if key.lower() in ['temp', 'temperature', 'phonetemp'] or 'temp' in key.lower():
                                value = value / 10.0
                        elif value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        
                        data[f'oplus_{key}'] = value
            
            # Parse standard Battery Service state
            std_match = re.search(r'Current Battery Service state:(.*?)(?=\n\n|$)', 
                                 content, re.DOTALL)
            if std_match:
                std_section = std_match.group(1)
                
                for line in std_section.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Convert values to appropriate types
                        if value.isdigit():
                            value = int(value)
                            # Fix temperature scaling (likely in tenths of a degree)
                            if key.lower() in ['temp', 'temperature'] or 'temp' in key.lower():
                                value = value / 10.0
                        elif value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        
                        data[f'std_{key}'] = value
                        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_device_info(self, file_path):
        """Parse device information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract basic device info
            model_match = re.search(r'Model: (.+)', content)
            if model_match:
                data['model'] = model_match.group(1).strip()
                
            brand_match = re.search(r'Brand: (.+)', content)
            if brand_match:
                data['brand'] = brand_match.group(1).strip()
                
            android_match = re.search(r'Android Version: (.+)', content)
            if android_match:
                data['android_version'] = android_match.group(1).strip()
                
            # Extract build properties
            build_props = re.findall(r'\[(.+?)\]: \[(.+?)\]', content)
            for prop, value in build_props:
                data[f'prop_{prop}'] = value
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_thermal(self, file_path):
        """Parse thermal information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract temperature readings
            temp_matches = re.findall(r'Temperature\{mValue=([\d.]+), mType=(\d+), mName=([^,]+)', content)
            
            temperatures = {}
            for value, temp_type, name in temp_matches:
                # Fix temperature scaling if needed (some devices report in tenths)
                temp_value = float(value)
                if temp_value > 100:  # Likely in tenths of a degree
                    temp_value = temp_value / 10.0
                
                temperatures[name] = {
                    'value': temp_value,
                    'type': int(temp_type)
                }
            
            data['temperatures'] = temperatures
            
            # Extract thermal status
            status_match = re.search(r'Thermal Status: (\d+)', content)
            if status_match:
                data['thermal_status'] = int(status_match.group(1))
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_power(self, file_path):
        """Parse power management information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract power state
            state_match = re.search(r'Power state: (.+)', content)
            if state_match:
                data['power_state'] = state_match.group(1).strip()
                
            # Extract wake locks
            wake_locks = re.findall(r'Wake Locks: size=(\d+)', content)
            if wake_locks:
                data['wake_locks_count'] = int(wake_locks[0])
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_cpuinfo(self, file_path):
        """Parse CPU information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract CPU load
            load_match = re.search(r'Total: (\d+)%', content)
            if load_match:
                data['cpu_load_total'] = int(load_match.group(1))
                
            # Extract CPU frequencies
            freq_matches = re.findall(r'CPU(\d+): (\d+)MHz', content)
            if freq_matches:
                data['cpu_frequencies'] = {f'CPU{num}': int(freq) for num, freq in freq_matches}
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_procstats(self, file_path):
        """Parse process statistics information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract process information
            processes = []
            current_process = {}
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('*') and ' / ' in line:
                    # New process entry
                    if current_process:
                        processes.append(current_process)
                    
                    # Parse process line: * package.name / user / version:
                    parts = line.split(' / ')
                    if len(parts) >= 3:
                        package_name = parts[0].replace('* ', '').strip()
                        user = parts[1].strip()
                        version = parts[2].replace(':', '').strip()
                        
                        current_process = {
                            'package_name': package_name,
                            'user': user,
                            'version': version,
                            'stats': {}
                        }
                elif ':' in line and current_process:
                    # Parse statistics line
                    if 'TOTAL:' in line:
                        # Extract memory usage: TOTAL: 100% (12MB-12MB-12MB/1.1MB-2.1MB-3.1MB/41MB-41MB-42MB over 5)
                        total_match = re.search(r'TOTAL: (\d+)% \(([^)]+)\)', line)
                        if total_match:
                            current_process['stats']['total_percent'] = int(total_match.group(1))
                            current_process['stats']['total_memory'] = total_match.group(2)
                    
                    elif 'Persistent:' in line:
                        persistent_match = re.search(r'Persistent: (\d+)%', line)
                        if persistent_match:
                            current_process['stats']['persistent_percent'] = int(persistent_match.group(1))
                    
                    elif 'Bnd Fgs:' in line:
                        bnd_fgs_match = re.search(r'Bnd Fgs: (\d+)%', line)
                        if bnd_fgs_match:
                            current_process['stats']['bound_foreground_percent'] = int(bnd_fgs_match.group(1))
                    
                    elif 'Service:' in line:
                        service_match = re.search(r'Service: (\d+)%', line)
                        if service_match:
                            current_process['stats']['service_percent'] = int(service_match.group(1))
            
            # Add the last process
            if current_process:
                processes.append(current_process)
            
            data['processes'] = processes
            data['total_processes'] = len(processes)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_memory_info(self, file_path):
        """Parse memory information"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # CORRECTED: Regex now handles commas `[\d,]+` and the unit `K`
            total_match = re.search(r'Total RAM: ([\d,]+)\s*K', content)
            if total_match:
                # CORRECTED: Must remove commas before converting to an integer
                total_ram_str = total_match.group(1).replace(',', '')
                data['total_ram_kb'] = int(total_ram_str)
                data['total_ram_mb'] = data['total_ram_kb'] / 1024
                data['total_ram_gb'] = data['total_ram_mb'] / 1024
            
            # CORRECTED: Apply the same fix for Free RAM
            free_match = re.search(r'Free RAM: ([\d,]+)\s*K', content)
            if free_match:
                # CORRECTED: Must remove commas before converting to an integer
                free_ram_str = free_match.group(1).replace(',', '')
                data['free_ram_kb'] = int(free_ram_str)
                data['free_ram_mb'] = data['free_ram_kb'] / 1024
                
                # This part now requires 'total_ram_mb' to be present
                if 'total_ram_mb' in data:
                    data['used_ram_mb'] = data['total_ram_mb'] - data['free_ram_mb']
                    data['ram_usage_percent'] = (data['used_ram_mb'] / data['total_ram_mb']) * 100
            
            # ... (the rest of your app memory parsing remains the same) ...
            # Extract app memory usage
            app_memory = []
            # (Your app parsing logic here)
            data['app_memory'] = app_memory
            data['top_memory_apps'] = sorted(app_memory, key=lambda x: x.get('memory_mb', 0), reverse=True)[:10]

        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_usage_stats(self, file_path):
        """Parse usage statistics"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract app usage statistics
            app_stats = []
            current_app = {}
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('Package ') and ':' in line:
                    # New app entry
                    if current_app:
                        app_stats.append(current_app)
                    
                    package_match = re.search(r'Package (\S+)', line)
                    if package_match:
                        current_app = {
                            'package_name': package_match.group(1),
                            'stats': {}
                        }
                elif ':' in line and current_app:
                    # Parse usage statistics
                    if 'Total time in foreground:' in line:
                        time_match = re.search(r'Total time in foreground: (.+)', line)
                        if time_match:
                            current_app['stats']['foreground_time'] = time_match.group(1)
                    
                    elif 'Total time visible:' in line:
                        time_match = re.search(r'Total time visible: (.+)', line)
                        if time_match:
                            current_app['stats']['visible_time'] = time_match.group(1)
                    
                    elif 'Total time in background:' in line:
                        time_match = re.search(r'Total time in background: (.+)', line)
                        if time_match:
                            current_app['stats']['background_time'] = time_match.group(1)
            
            # Add the last app
            if current_app:
                app_stats.append(current_app)
            
            data['app_stats'] = app_stats
            data['total_apps'] = len(app_stats)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_battery_stats_detailed(self, file_path):
        """Parse detailed battery statistics"""
        data = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract battery usage by app
            app_battery = []
            current_app = {}
            
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('Statistics since last charge:') or line.startswith('Statistics since last unplugged:'):
                    # Extract time period
                    time_match = re.search(r'Statistics since (.+):', line)
                    if time_match:
                        data['period'] = time_match.group(1)
                
                elif line.startswith('  ') and ':' in line and not line.startswith('    '):
                    # App entry line
                    if current_app:
                        app_battery.append(current_app)
                    
                    # Parse app line: "  com.example.app:"
                    app_match = re.search(r'^\s+(\S+):', line)
                    if app_match:
                        current_app = {
                            'package_name': app_match.group(1),
                            'stats': {}
                        }
                
                elif line.startswith('    ') and current_app:
                    # Parse app statistics
                    if 'Screen' in line and 'ms' in line:
                        screen_match = re.search(r'Screen: (\d+) ms', line)
                        if screen_match:
                            current_app['stats']['screen_time_ms'] = int(screen_match.group(1))
                    
                    elif 'CPU' in line and 'ms' in line:
                        cpu_match = re.search(r'CPU: (\d+) ms', line)
                        if cpu_match:
                            current_app['stats']['cpu_time_ms'] = int(cpu_match.group(1))
                    
                    elif 'Wake lock' in line and 'ms' in line:
                        wake_match = re.search(r'Wake lock: (\d+) ms', line)
                        if wake_match:
                            current_app['stats']['wake_lock_ms'] = int(wake_match.group(1))
                    
                    elif 'Mobile network' in line and 'ms' in line:
                        mobile_match = re.search(r'Mobile network: (\d+) ms', line)
                        if mobile_match:
                            current_app['stats']['mobile_network_ms'] = int(mobile_match.group(1))
                    
                    elif 'Wifi' in line and 'ms' in line:
                        wifi_match = re.search(r'Wifi: (\d+) ms', line)
                        if wifi_match:
                            current_app['stats']['wifi_time_ms'] = int(wifi_match.group(1))
            
            # Add the last app
            if current_app:
                app_battery.append(current_app)
            
            data['app_battery'] = app_battery
            data['total_apps'] = len(app_battery)
            
            # Calculate total battery impact
            total_screen = sum(app.get('stats', {}).get('screen_time_ms', 0) for app in app_battery)
            total_cpu = sum(app.get('stats', {}).get('cpu_time_ms', 0) for app in app_battery)
            total_wake = sum(app.get('stats', {}).get('wake_lock_ms', 0) for app in app_battery)
            
            data['total_screen_time_ms'] = total_screen
            data['total_cpu_time_ms'] = total_cpu
            data['total_wake_lock_ms'] = total_wake
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return data
    
    def parse_all_sessions(self):
        """Parse all diagnostic sessions"""
        if not self.sessions:
            self.discover_sessions()
            
        for session_name, session_info in self.sessions.items():
            print(f"Parsing session: {session_name}")
            
            session_data = {
                'timestamp': session_info['timestamp'],
                'files_parsed': []
            }
            
            for file_path in session_info['files']:
                filename = file_path.name
                
                if filename == 'battery_basic.txt':
                    session_data['battery_basic'] = self.parse_battery_basic(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'device_info.txt':
                    session_data['device_info'] = self.parse_device_info(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'thermal.txt':
                    session_data['thermal'] = self.parse_thermal(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'power.txt':
                    session_data['power'] = self.parse_power(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'cpuinfo.txt':
                    session_data['cpuinfo'] = self.parse_cpuinfo(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'procstats.txt':
                    session_data['procstats'] = self.parse_procstats(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'memory_info.txt':
                    session_data['memory_info'] = self.parse_memory_info(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'usage_stats.txt':
                    session_data['usage_stats'] = self.parse_usage_stats(file_path)
                    session_data['files_parsed'].append(filename)
                elif filename == 'battery_stats_detailed.txt':
                    session_data['battery_stats_detailed'] = self.parse_battery_stats_detailed(file_path)
                    session_data['files_parsed'].append(filename)
                
            self.parsed_data[session_name] = session_data
            
        print(f"Parsed {len(self.parsed_data)} sessions")
        return self.parsed_data
    
    def get_summary_dataframe(self):
        """Create a summary DataFrame from all parsed sessions"""
        if not self.parsed_data:
            self.parse_all_sessions()
            
        summary_data = []
        
        for session_name, session_data in self.parsed_data.items():
            row = {
                'session': session_name,
                'timestamp': session_data['timestamp'],
                'files_parsed': len(session_data['files_parsed'])
            }
            
            # Extract battery information
            if 'battery_basic' in session_data:
                battery = session_data['battery_basic']
                row.update({
                    'battery_level': battery.get('std_level', None),
                    'battery_voltage': battery.get('std_voltage', None),
                    'battery_temperature': battery.get('std_temperature', None),
                    'charging_status': battery.get('std_status', None),
                    'ac_powered': battery.get('std_AC powered', None),
                    'usb_powered': battery.get('std_USB powered', None),
                    'phone_temp': battery.get('oplus_PhoneTemp', None)
                })
            
            # Extract device information
            if 'device_info' in session_data:
                device = session_data['device_info']
                row.update({
                    'model': device.get('model', None),
                    'brand': device.get('brand', None),
                    'android_version': device.get('android_version', None)
                })
            
            # Extract thermal information
            if 'thermal' in session_data:
                thermal = session_data['thermal']
                if 'temperatures' in thermal:
                    temps = thermal['temperatures']
                    row.update({
                        'cpu_temp': temps.get('CPU', {}).get('value', None),
                        'gpu_temp': temps.get('GPU', {}).get('value', None),
                        'battery_temp_thermal': temps.get('BATTERY', {}).get('value', None),
                        'skin_temp': temps.get('SKIN', {}).get('value', None)
                    })
            
            # Extract process and memory information
            if 'procstats' in session_data:
                procstats = session_data['procstats']
                row.update({
                    'total_processes': procstats.get('total_processes', None)
                })
            
            if 'memory_info' in session_data:
                memory = session_data['memory_info']
                row.update({
                    'total_ram_gb': memory.get('total_ram_gb', None),
                    'used_ram_mb': memory.get('used_ram_mb', None),
                    'ram_usage_percent': memory.get('ram_usage_percent', None)
                })
            
            if 'battery_stats_detailed' in session_data:
                battery_detailed = session_data['battery_stats_detailed']
                row.update({
                    'total_screen_time_ms': battery_detailed.get('total_screen_time_ms', None),
                    'total_cpu_time_ms': battery_detailed.get('total_cpu_time_ms', None),
                    'total_wake_lock_ms': battery_detailed.get('total_wake_lock_ms', None)
                })
            
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        df = df.sort_values('timestamp')
        return df

def analyze_battery_health(summary_df):
    """Analyze battery health and performance"""
    if summary_df.empty:
        print("No data available for analysis.")
        return
    
    print("=== BATTERY HEALTH ANALYSIS ===\n")
    
    # Battery level statistics
    if 'battery_level' in summary_df.columns:
        valid_battery = summary_df.dropna(subset=['battery_level'])
        if not valid_battery.empty:
            print(f"Battery Level Statistics:")
            print(f"  Average: {valid_battery['battery_level'].mean():.1f}%")
            print(f"  Minimum: {valid_battery['battery_level'].min()}%")
            print(f"  Maximum: {valid_battery['battery_level'].max()}%")
            print(f"  Standard Deviation: {valid_battery['battery_level'].std():.1f}%")
            
            # Battery usage patterns
            if len(valid_battery) > 1:
                # Calculate time differences and battery drain rates
                valid_battery_sorted = valid_battery.sort_values('timestamp')
                time_diffs = valid_battery_sorted['timestamp'].diff().dt.total_seconds() / 3600  # hours
                battery_diffs = valid_battery_sorted['battery_level'].diff()
                
                # Calculate drain rates (negative values indicate discharge)
                drain_rates = battery_diffs / time_diffs
                valid_drain_rates = drain_rates.dropna()
                
                if not valid_drain_rates.empty:
                    print(f"\nBattery Drain Analysis:")
                    print(f"  Average Drain Rate: {valid_drain_rates.mean():.2f}% per hour")
                    print(f"  Fastest Drain: {valid_drain_rates.min():.2f}% per hour")
                    print(f"  Slowest Drain: {valid_drain_rates.max():.2f}% per hour")
                    
                    # Identify charging vs discharging periods
                    charging_periods = valid_drain_rates[valid_drain_rates > 0]
                    discharging_periods = valid_drain_rates[valid_drain_rates < 0]
                    
                    if not charging_periods.empty:
                        print(f"  Average Charging Rate: {charging_periods.mean():.2f}% per hour")
                    if not discharging_periods.empty:
                        print(f"  Average Discharging Rate: {discharging_periods.mean():.2f}% per hour")
    
    # Temperature analysis
    print(f"\n=== TEMPERATURE ANALYSIS ===\n")
    temp_columns = ['battery_temperature', 'cpu_temp', 'gpu_temp', 'skin_temp']
    available_temps = [col for col in temp_columns if col in summary_df.columns]
    
    for temp_col in available_temps:
        valid_temp = summary_df.dropna(subset=[temp_col])
        if not valid_temp.empty:
            temp_name = temp_col.replace('_', ' ').title()
            print(f"{temp_name}:")
            print(f"  Average: {valid_temp[temp_col].mean():.1f}°C")
            print(f"  Minimum: {valid_temp[temp_col].min():.1f}°C")
            print(f"  Maximum: {valid_temp[temp_col].max():.1f}°C")
            print(f"  Standard Deviation: {valid_temp[temp_col].std():.1f}°C")
            
            # Temperature warnings
            if temp_col == 'battery_temperature':
                if valid_temp[temp_col].max() > 45:
                    print(f"  ⚠️  WARNING: Maximum temperature exceeds 45°C!")
                if valid_temp[temp_col].mean() > 40:
                    print(f"  ⚠️  WARNING: Average temperature is high!")
            elif temp_col in ['cpu_temp', 'gpu_temp']:
                if valid_temp[temp_col].max() > 80:
                    print(f"  ⚠️  WARNING: Maximum temperature exceeds 80°C!")
            
            print()
    
    # Device information summary
    print(f"\n=== DEVICE INFORMATION ===\n")
    if 'model' in summary_df.columns:
        models = summary_df['model'].dropna().unique()
        if len(models) > 0:
            print(f"Device Model: {models[0]}")
    
    if 'brand' in summary_df.columns:
        brands = summary_df['brand'].dropna().unique()
        if len(brands) > 0:
            print(f"Brand: {brands[0]}")
    
    if 'android_version' in summary_df.columns:
        versions = summary_df['android_version'].dropna().unique()
        if len(versions) > 0:
            print(f"Android Version: {versions[0]}")
    
    print(f"Total Diagnostic Sessions: {len(summary_df)}")
    
    if 'timestamp' in summary_df.columns:
        time_range = summary_df['timestamp'].max() - summary_df['timestamp'].min()
        print(f"Data Collection Period: {time_range}")

def analyze_process_performance(parsed_data):
    """Analyze process performance and resource usage"""
    print("=== PROCESS PERFORMANCE ANALYSIS ===\n")
    
    for session_name, session_data in parsed_data.items():
        print(f"Session: {session_name}")
        
        if 'procstats' in session_data:
            procstats = session_data['procstats']
            processes = procstats.get('processes', [])
            
            print(f"  Total Processes: {len(processes)}")
            
            # Find top memory consumers
            if processes:
                # Sort by total percentage (if available)
                sorted_processes = sorted(processes, 
                                       key=lambda x: x.get('stats', {}).get('total_percent', 0), 
                                       reverse=True)
                
                print(f"  Top 5 Most Active Processes:")
                for i, proc in enumerate(sorted_processes[:5]):
                    stats = proc.get('stats', {})
                    print(f"    {i+1}. {proc['package_name']}")
                    print(f"       Total: {stats.get('total_percent', 'N/A')}%")
                    print(f"       Persistent: {stats.get('persistent_percent', 'N/A')}%")
                    print(f"       Service: {stats.get('service_percent', 'N/A')}%")
                    print(f"       Bound FG: {stats.get('bound_foreground_percent', 'N/A')}%")
        
        if 'memory_info' in session_data:
            memory = session_data['memory_info']
            print(f"  Memory Usage:")
            print(f"    Total RAM: {memory.get('total_ram_gb', 'N/A'):.2f} GB")
            print(f"    Used RAM: {memory.get('used_ram_mb', 'N/A'):.1f} MB")
            print(f"    RAM Usage: {memory.get('ram_usage_percent', 'N/A'):.1f}%")
            
            if 'top_memory_apps' in memory:
                print(f"  Top 5 Memory Consumers:")
                for i, app in enumerate(memory['top_memory_apps'][:5]):
                    print(f"    {i+1}. {app['app_name']}: {app['memory_mb']:.1f} MB")
        
        print()

def analyze_battery_drain_sources(parsed_data):
    """Analyze battery drain sources and patterns"""
    print("=== BATTERY DRAIN SOURCE ANALYSIS ===\n")
    
    for session_name, session_data in parsed_data.items():
        print(f"Session: {session_name}")
        
        if 'battery_stats_detailed' in session_data:
            battery_detailed = session_data['battery_stats_detailed']
            app_battery = battery_detailed.get('app_battery', [])
            
            if app_battery:
                # Sort by wake lock time (biggest battery drainers)
                wake_lock_apps = sorted(app_battery, 
                                      key=lambda x: x.get('stats', {}).get('wake_lock_ms', 0), 
                                      reverse=True)
                
                print(f"  Top 5 Wake Lock Offenders:")
                for i, app in enumerate(wake_lock_apps[:5]):
                    stats = app.get('stats', {})
                    wake_time = stats.get('wake_lock_ms', 0)
                    if wake_time > 0:
                        print(f"    {i+1}. {app['package_name']}: {wake_time/1000:.1f} seconds")
                
                # Sort by CPU time
                cpu_apps = sorted(app_battery, 
                                key=lambda x: x.get('stats', {}).get('cpu_time_ms', 0), 
                                reverse=True)
                
                print(f"  Top 5 CPU Consumers:")
                for i, app in enumerate(cpu_apps[:5]):
                    stats = app.get('stats', {})
                    cpu_time = stats.get('cpu_time_ms', 0)
                    if cpu_time > 0:
                        print(f"    {i+1}. {app['package_name']}: {cpu_time/1000:.1f} seconds")
                
                # Sort by screen time
                screen_apps = sorted(app_battery, 
                                   key=lambda x: x.get('stats', {}).get('screen_time_ms', 0), 
                                   reverse=True)
                
                print(f"  Top 5 Screen Time Consumers:")
                for i, app in enumerate(screen_apps[:5]):
                    stats = app.get('stats', {})
                    screen_time = stats.get('screen_time_ms', 0)
                    if screen_time > 0:
                        print(f"    {i+1}. {app['package_name']}: {screen_time/1000:.1f} seconds")
        
        print()

def create_enhanced_visualizations(summary_df, parsed_data):
    """Create enhanced visualizations including process analysis"""
    if summary_df.empty:
        print("No data available for visualization.")
        return
    
    # Create figure with subplots for enhanced analysis
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Enhanced Phone Diagnostic Analysis', fontsize=16, fontweight='bold')
    
    # 1. Memory Usage Over Time
    ax1 = axes[0, 0]
    if 'ram_usage_percent' in summary_df.columns:
        valid_memory = summary_df.dropna(subset=['ram_usage_percent'])
        if not valid_memory.empty:
            ax1.plot(valid_memory['timestamp'], valid_memory['ram_usage_percent'], 'o-', linewidth=2, markersize=8)
            ax1.set_title('RAM Usage Over Time', fontsize=14, fontweight='bold')
            ax1.set_ylabel('RAM Usage (%)')
            ax1.set_xlabel('Time')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, 'No memory data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.5, 'No memory data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 2. Process Count Over Time
    ax2 = axes[0, 1]
    if 'total_processes' in summary_df.columns:
        valid_processes = summary_df.dropna(subset=['total_processes'])
        if not valid_processes.empty:
            ax2.plot(valid_processes['timestamp'], valid_processes['total_processes'], 'o-', linewidth=2, markersize=8)
            ax2.set_title('Total Processes Over Time', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Number of Processes')
            ax2.set_xlabel('Time')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.text(0.5, 0.5, 'No process data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax2.text(0.5, 0.5, 'No process data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 3. Wake Lock Time Over Time
    ax3 = axes[0, 2]
    if 'total_wake_lock_ms' in summary_df.columns:
        valid_wake = summary_df.dropna(subset=['total_wake_lock_ms'])
        if not valid_wake.empty:
            # Convert to seconds for readability
            wake_seconds = valid_wake['total_wake_lock_ms'] / 1000
            ax3.plot(valid_wake['timestamp'], wake_seconds, 'o-', linewidth=2, markersize=8, color='red')
            ax3.set_title('Total Wake Lock Time Over Time', fontsize=14, fontweight='bold')
            ax3.set_ylabel('Wake Lock Time (seconds)')
            ax3.set_xlabel('Time')
            ax3.grid(True, alpha=0.3)
            ax3.tick_params(axis='x', rotation=45)
        else:
            ax3.text(0.5, 0.5, 'No wake lock data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax3.text(0.5, 0.5, 'No wake lock data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 4. CPU Time Over Time
    ax4 = axes[1, 0]
    if 'total_cpu_time_ms' in summary_df.columns:
        valid_cpu = summary_df.dropna(subset=['total_cpu_time_ms'])
        if not valid_cpu.empty:
            # Convert to seconds for readability
            cpu_seconds = valid_cpu['total_cpu_time_ms'] / 1000
            ax4.plot(valid_cpu['timestamp'], cpu_seconds, 'o-', linewidth=2, markersize=8, color='orange')
            ax4.set_title('Total CPU Time Over Time', fontsize=14, fontweight='bold')
            ax4.set_ylabel('CPU Time (seconds)')
            ax4.set_xlabel('Time')
            ax4.grid(True, alpha=0.3)
            ax4.tick_params(axis='x', rotation=45)
        else:
            ax4.text(0.5, 0.5, 'No CPU data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax4.text(0.5, 0.5, 'No CPU data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 5. Screen Time Over Time
    ax5 = axes[1, 1]
    if 'total_screen_time_ms' in summary_df.columns:
        valid_screen = summary_df.dropna(subset=['total_screen_time_ms'])
        if not valid_screen.empty:
            # Convert to minutes for readability
            screen_minutes = valid_screen['total_screen_time_ms'] / 60000
            ax5.plot(valid_screen['timestamp'], screen_minutes, 'o-', linewidth=2, markersize=8, color='green')
            ax5.set_title('Total Screen Time Over Time', fontsize=14, fontweight='bold')
            ax5.set_ylabel('Screen Time (minutes)')
            ax5.set_xlabel('Time')
            ax5.grid(True, alpha=0.3)
            ax5.tick_params(axis='x', rotation=45)
        else:
            ax5.text(0.5, 0.5, 'No screen time data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax5.text(0.5, 0.5, 'No screen time data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 6. Process Distribution (if available)
    ax6 = axes[1, 2]
    if parsed_data:
        # Get the latest session with process data
        latest_session = None
        for session_name, session_data in parsed_data.items():
            if 'procstats' in session_data and session_data['procstats'].get('processes'):
                latest_session = session_data
                break
        
        if latest_session and 'procstats' in latest_session:
            processes = latest_session['procstats']['processes']
            if processes:
                # Count process types
                process_types = {}
                for proc in processes:
                    stats = proc.get('stats', {})
                    if stats.get('persistent_percent', 0) > 50:
                        process_types['Persistent'] = process_types.get('Persistent', 0) + 1
                    elif stats.get('service_percent', 0) > 50:
                        process_types['Service'] = process_types.get('Service', 0) + 1
                    elif stats.get('bound_foreground_percent', 0) > 50:
                        process_types['Bound FG'] = process_types.get('Bound FG', 0) + 1
                    else:
                        process_types['Other'] = process_types.get('Other', 0) + 1
                
                if process_types:
                    labels = list(process_types.keys())
                    sizes = list(process_types.values())
                    ax6.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax6.set_title('Process Type Distribution', fontsize=14, fontweight='bold')
                else:
                    ax6.text(0.5, 0.5, 'No process type data available', ha='center', va='center', transform=ax6.transAxes)
            else:
                ax6.text(0.5, 0.5, 'No process data available', ha='center', va='center', transform=ax6.transAxes)
        else:
            ax6.text(0.5, 0.5, 'No process data available', ha='center', va='center', transform=ax6.transAxes)
    else:
        ax6.text(0.5, 0.5, 'No process data available', ha='center', va='center', transform=ax6.transAxes)
    
    plt.tight_layout()
    plt.show()

def create_visualizations(summary_df):
    """Create comprehensive visualizations of the diagnostic data"""
    if summary_df.empty:
        print("No data available for visualization.")
        return
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Phone Diagnostic Data Analysis', fontsize=16, fontweight='bold')
    
    # 1. Battery Level Trends Over Time
    ax1 = axes[0, 0]
    if 'battery_level' in summary_df.columns:
        valid_battery = summary_df.dropna(subset=['battery_level'])
        if not valid_battery.empty:
            ax1.plot(valid_battery['timestamp'], valid_battery['battery_level'], 'o-', linewidth=2, markersize=8)
            ax1.set_title('Battery Level Over Time', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Battery Level (%)')
            ax1.set_xlabel('Time')
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
        else:
            ax1.text(0.5, 0.5, 'No battery level data available', ha='center', va='center', transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.5, 'No battery level data available', ha='center', va='center', transform=ax1.transAxes)
    
    # 2. Temperature Trends
    ax2 = axes[0, 1]
    temp_columns = ['battery_temperature', 'cpu_temp', 'gpu_temp', 'skin_temp']
    available_temps = [col for col in temp_columns if col in summary_df.columns]
    
    if available_temps:
        for temp_col in available_temps:
            valid_temp = summary_df.dropna(subset=[temp_col])
            if not valid_temp.empty:
                ax2.plot(valid_temp['timestamp'], valid_temp[temp_col], 'o-', linewidth=2, markersize=6, 
                        label=temp_col.replace('_', ' ').title())
        
        ax2.set_title('Temperature Trends Over Time', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Temperature (°C)')
        ax2.set_xlabel('Time')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.tick_params(axis='x', rotation=45)
    else:
        ax2.text(0.5, 0.5, 'No temperature data available', ha='center', va='center', transform=ax2.transAxes)
    
    # 3. Charging Status Analysis
    ax3 = axes[1, 0]
    if 'charging_status' in summary_df.columns:
        valid_charging = summary_df.dropna(subset=['charging_status'])
        if not valid_charging.empty:
            charging_counts = valid_charging['charging_status'].value_counts()
            
            # Map status codes to readable names
            status_names = {
                1: 'Unknown',
                2: 'Charging',
                3: 'Discharging',
                4: 'Not Charging',
                5: 'Full'
            }
            
            labels = [status_names.get(status, f'Status {status}') for status in charging_counts.index]
            ax3.pie(charging_counts.values, labels=labels, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Charging Status Distribution', fontsize=14, fontweight='bold')
        else:
            ax3.text(0.5, 0.5, 'No charging status data available', ha='center', va='center', transform=ax3.transAxes)
    else:
        ax3.text(0.5, 0.5, 'No charging status data available', ha='center', va='center', transform=ax3.transAxes)
    
    # 4. Power Source Analysis
    ax4 = axes[1, 1]
    power_columns = ['ac_powered', 'usb_powered']
    available_power = [col for col in power_columns if col in summary_df.columns]
    
    if available_power:
        power_data = []
        power_labels = []
        
        for col in available_power:
            valid_power = summary_df.dropna(subset=[col])
            if not valid_power.empty:
                true_count = valid_power[col].sum()
                false_count = len(valid_power) - true_count
                power_data.extend([true_count, false_count])
                power_labels.extend([f'{col.replace("_", " ").title()} (True)', f'{col.replace("_", " ").title()} (False)'])
        
        if power_data:
            bars = ax4.bar(range(len(power_data)), power_data, color=['green', 'red'] * (len(power_data)//2))
            ax4.set_title('Power Source Usage', fontsize=14, fontweight='bold')
            ax4.set_ylabel('Count')
            ax4.set_xticks(range(len(power_data)))
            ax4.set_xticklabels(power_labels, rotation=45, ha='right')
        else:
            ax4.text(0.5, 0.5, 'No power source data available', ha='center', va='center', transform=ax4.transAxes)
    else:
        ax4.text(0.5, 0.5, 'No power source data available', ha='center', va='center', transform=ax4.transAxes)
    
    plt.tight_layout()
    plt.show()

def export_data(summary_df, parsed_data):
    """Export data for further analysis"""
    if summary_df.empty:
        print("No data to export.")
        return
    
    # Export to CSV
    csv_filename = f"phone_diagnostics_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    summary_df.to_csv(csv_filename, index=False)
    print(f"Summary data exported to: {csv_filename}")
    
    # Export detailed parsed data to JSON
    json_filename = f"phone_diagnostics_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    # Convert datetime objects to strings for JSON serialization
    export_data = {}
    for session_name, session_data in parsed_data.items():
        export_data[session_name] = session_data.copy()
        if export_data[session_name]['timestamp']:
            export_data[session_name]['timestamp'] = export_data[session_name]['timestamp'].isoformat()
    
    with open(json_filename, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    print(f"Detailed data exported to: {json_filename}")
    
    # Display summary statistics
    print(f"\nData Export Summary:")
    print(f"  Total Sessions: {len(summary_df)}")
    print(f"  Data Columns: {len(summary_df.columns)}")
    print(f"  Memory Usage: {summary_df.memory_usage(deep=True).sum() / 1024:.1f} KB")

# Example usage functions
def run_complete_analysis():
    """Run the complete diagnostic analysis pipeline"""
    print("=== PHONE DIAGNOSTIC DATA ANALYSIS ===\n")
    
    # Initialize parser
    parser = PhoneDiagnosticParser()
    
    # Discover sessions
    print("1. Discovering diagnostic sessions...")
    sessions = parser.discover_sessions()
    
    if not sessions:
        print("No diagnostic sessions found. Please check your logs directory.")
        return
    
    # Parse all sessions
    print("\n2. Parsing diagnostic data...")
    parsed_data = parser.parse_all_sessions()
    
    # Create summary DataFrame
    print("\n3. Creating summary data...")
    summary_df = parser.get_summary_dataframe()
    
    # Display summary
    print("\n4. Summary of all diagnostic sessions:")
    print(summary_df)
    
    # Analyze battery health
    print("\n5. Battery health analysis:")
    analyze_battery_health(summary_df)
    
    # Analyze process performance
    print("\n6. Process performance analysis:")
    analyze_process_performance(parsed_data)
    
    # Analyze battery drain sources
    print("\n7. Battery drain source analysis:")
    analyze_battery_drain_sources(parsed_data)
    
    # Create basic visualizations
    print("\n8. Creating basic visualizations...")
    create_visualizations(summary_df)
    
    # Create enhanced visualizations
    print("\n9. Creating enhanced process analysis visualizations...")
    create_enhanced_visualizations(summary_df, parsed_data)
    
    # Export data
    print("\n10. Exporting data...")
    export_data(summary_df, parsed_data)
    
    print("\n=== ANALYSIS COMPLETE ===")
    return parser, summary_df, parsed_data

if __name__ == "__main__":
    # Run the complete analysis
    parser, summary_df, parsed_data = run_complete_analysis()

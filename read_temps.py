import time
import csv
from yoctopuce.yocto_api import *
from yoctopuce.yocto_temperature import *
from yoctopuce.yocto_datalogger import *

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

import matplotlib.dates as mdates
from datetime import datetime

import os

os.makedirs("data", exist_ok=True)
os.makedirs("plots", exist_ok=True)

def connect_to_yocto():
    """
    Connect to Yoctopuce devices
    """
    errmsg = YRefParam()
    if YAPI.RegisterHub("usb", errmsg) != YAPI.SUCCESS:
        print("RegisterHub error:", errmsg.value)
        return False
    return True

def save_datalogger_data(sensor):
    """
    Check if the data logger is recording and save the data to a CSV file
    """
    dataLogger = sensor.get_dataLogger()
    state = dataLogger.get_recording()
    
    if state == YDataLogger.RECORDING_ON:
        logical_name = sensor.get_logicalName()
        serial = sensor.get_module().get_serialNumber()
        func_id = sensor.get_functionId()
        filename = f"data/{logical_name or serial}_{func_id}_data.csv"
        
        print(f"\t\tData logger is recording, saving data to {filename}")
        
        with open(filename, mode='w', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(["Timestamp", "Min", "Avg", "Max"])
            
            for data_set in dataLogger.get_dataSets():
                try:
                    if data_set.loadMore():
                        measures = data_set.get_measures()
                        for m in measures:
                            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(m.get_startTimeUTC()))
                            csv_writer.writerow([
                                timestamp,
                                m.get_minValue(),
                                m.get_averageValue(),
                                m.get_maxValue()
                            ])
                except Exception as e:
                    print(f"\t\tError loading measures: {e}")
    elif state == YDataLogger.RECORDING_OFF:
        print("\t\tData logger is OFF")
    elif state == YDataLogger.RECORDING_PENDING:
        print("\t\tData logger is PENDING start")
    else:
        print("\t\tData logger state unknown or error")

def poll_and_plot_temps():
    """
    Poll all temperature sensors every minute, plot on one graph.
    Save the plot every hour and once at exit.
    """
    print("\nPolling and plotting all sensors every second. Press Ctrl+C to stop.")

    # Start time
    start_time = time.time()
    last_save_time = start_time

    # Enable interactive plotting with larger figure
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 6))  # Wider and taller figure
    ax.set_title("Live Temperature Readings")
    ax.set_xlabel("Time")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

    # Sensor data: {name: {'times': [...], 'temps': [...], 'line': Line2D}}
    sensor_data = {}

    try:
        with open("data/temps.csv", mode='a', newline='') as csv_file:
            while True:
                current_time = datetime.now()
                temps_text = []

                temp_sensor = YTemperature.FirstTemperature()
                while temp_sensor:
                    serial = temp_sensor.get_module().get_serialNumber()
                    func_id = temp_sensor.get_functionId()
                    logical_name = temp_sensor.get_logicalName()
                    name = logical_name if logical_name else func_id
                    temp_value = temp_sensor.get_currentValue()
                    unit = temp_sensor.get_unit()

                    temps_text.append(f"{name}:{temp_value:.1f}{unit}")

                    # Append to csv file
                    csv_writer = csv.writer(csv_file)
                    csv_writer.writerow([current_time, name, temp_value])
                    csv_file.flush()
                    
                    if name not in sensor_data:
                        line, = ax.plot([], [], label=name)
                        sensor_data[name] = {
                            'times': [],
                            'temps': [],
                            'line': line
                        }

                    data = sensor_data[name]
                    data['times'].append(current_time)
                    data['temps'].append(temp_value)

                    if len(data['times']) > 60:  # up to an hour
                        data['times'].pop(0)
                        data['temps'].pop(0)

                    temp_sensor = temp_sensor.nextTemperature()

                for data in sensor_data.values():
                    data['line'].set_data(data['times'], data['temps'])

                ax.relim()
                ax.autoscale_view()
                ax.legend(loc='upper left')
                fig.autofmt_xdate()
                plt.tight_layout()  # Prevent clipping of labels/legend
                plt.draw()
                plt.pause(0.01)

                # Check if an hour has passed
                now = time.time()
                if now - last_save_time >= 3600:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"plots/all_sensors_{timestamp}.png"
                    print(f"\nAuto-saving plot: {filename}")
                    fig.tight_layout()
                    fig.savefig(filename)
                    last_save_time = now

                for _ in range(60):
                    plt.pause(1)  # pause for 1 second, allowing GUI events to process

    except KeyboardInterrupt:
        print("\nStopping and saving final plot...")
        plt.ioff()
        fig.autofmt_xdate()
        fig.tight_layout()
        final_filename = "plots/all_sensors_final_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        fig.savefig(final_filename)
        print(f"Saved final plot: {final_filename}")
        plt.show()

def main():
    if not connect_to_yocto():
        return

    try:
        module = YModule.FirstModule()
        while module:
            serial = module.get_serialNumber()
            product = module.get_productName()
            print(f"\nModule: {serial} - {product}")

            temp_sensor = YTemperature.FirstTemperature()
            while temp_sensor:
                if temp_sensor.get_module().get_serialNumber() == serial:
                    func_id = temp_sensor.get_functionId()
                    logical_name = temp_sensor.get_logicalName()
                    name = logical_name if logical_name else func_id
                    temp_value = temp_sensor.get_currentValue()
                    unit = temp_sensor.get_unit()

                    print(f"\tSensor: {name} ({func_id}): {temp_value:.1f} {unit}")

                    save_datalogger_data(temp_sensor)

                temp_sensor = temp_sensor.nextTemperature()
            module = module.nextModule()
        
        poll_and_plot_temps()

    finally:
        YAPI.FreeAPI()

if __name__ == "__main__":
    main()
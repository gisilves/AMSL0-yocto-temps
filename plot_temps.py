import pandas as pd

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import argparse
import os

def main(args):
    # Read data
    filename = args.filename
    df = pd.read_csv(filename, names=['time', 'name', 'temp'])

    # Convert time column to datetime
    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S.%f')

    if df.empty:
        print('No data found')
        return

    start_time = df['time'].min()
    end_time = df['time'].max()

    print(f"Start time: {start_time}")
    print(f"End time: {end_time}")

    # Get all unique sensor names
    names = df['name'].unique()

    if args.name:
        invalid_names = [n for n in args.name if n not in names]
        if invalid_names:
            print(f"Name(s) not found: {', '.join(invalid_names)}")
            return
        names = args.name

    # Plot data
    for name in names:
        df_name = df[df['name'] == name]
        plt.plot(df_name['time'], df_name['temp'], label=name)

    plt.xlabel('Time')
    plt.ylabel('Temperature (°C)')
    plt.xlim(start_time, end_time)

    # Format title
    start_str = start_time.strftime('%Y-%m-%d %H:%M')
    end_str = end_time.strftime('%Y-%m-%d %H:%M')
    plt.title(f"Temperature Readings: {start_str} to {end_str}")

    # Set x-axis ticks
    unique_times = df['time'].unique()
    step = max(1, len(unique_times) // 10)
    plt.xticks(unique_times[::step])

    # Format x-axis tick labels to full datetime
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.xticks(rotation=25)

    plt.grid(True)
    plt.legend()

    if args.output:
        # Save plot
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        plt.savefig(args.output)
        print(f"Plot saved to {args.output}")
    else:
        plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, default='data/temps.csv', help='Path to the CSV file')
    parser.add_argument('--output', type=str, default=None, help='Path to save the plot (optional)')
    parser.add_argument('--name', type=str, nargs='+', default=None, help='List of sensor names to plot (default: all)')
    args = parser.parse_args()
    main(args)

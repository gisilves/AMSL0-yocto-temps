import pandas as pd
import matplotlib
#matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import argparse
import os

def main(args):
    filename = args.filename

    # Read data
    try:
        df = pd.read_csv(filename, names=['time', 'name', 'temp'])
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return

    # Convert time column to datetime
    df['time'] = pd.to_datetime(df['time'], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce')
    df = df.dropna(subset=['time'])

    if df.empty:
        print('No valid data found in file')
        return
    
    if args.last_hours and (args.from_time or args.to_time):
        print('Cannot use --last-hours with --from or --to')
        return

    # Filter by last N hours if requested
    if args.last_hours:
        cutoff_time = df['time'].max() - pd.to_timedelta(args.last_hours, unit='h')
        df = df[df['time'] >= cutoff_time]
        print(f"Filtering data to last {args.last_hours} hours (from {cutoff_time} onwards)")

    if args.from_time:
        from_time = pd.to_datetime(args.from_time, format='%Y-%m-%d %H:%M:%S')
        df = df[df['time'] >= from_time]
        print(f"Filtering data from {from_time}")

    if args.to_time:
        to_time = pd.to_datetime(args.to_time, format='%Y-%m-%d %H:%M:%S')
        df = df[df['time'] <= to_time]
        print(f"Filtering data to {to_time}")

    if df.empty:
        print('No data in the specified time range')
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
    fig, ax = plt.subplots(figsize=(10, 6))
    for name in names:
        df_name = df[df['name'] == name]
        ax.plot(df_name['time'], df_name['temp'], label=name)

    ax.set_xlabel('Time')
    ax.set_ylabel('Temperature (°C)')
    ax.set_xlim(start_time, end_time)

    # Format title
    start_str = start_time.strftime('%Y-%m-%d %H:%M')
    end_str = end_time.strftime('%Y-%m-%d %H:%M')
    ax.set_title(f"Temperature Readings: {start_str} to {end_str}")

    # Set x-axis ticks
    unique_times = df['time'].unique()
    step = max(1, len(unique_times) // 10)
    ax.set_xticks(unique_times[::step])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    plt.xticks(rotation=25)

    ax.grid(True)
    ax.legend()

    plt.tight_layout()

    if args.output:
        directory = os.path.dirname(args.output)
        if directory:
            os.makedirs(directory, exist_ok=True)
        plt.savefig(args.output)
        print(f"Plot saved to {args.output}")
    else:
        plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--filename', type=str, default='data/temps.csv', help='Path to the CSV file')
    parser.add_argument('--output', type=str, default=None, help='Path to save the plot (optional)')
    parser.add_argument('--name', type=str, nargs='+', default=None, help='List of sensor names to plot (default: all)')
    parser.add_argument('--last-hours', type=float, default=None, help='Plot only data from the last N hours')
    parser.add_argument('--from_time', type=str, default=None, help='Start time (YYYY-MM-DD HH:MM)')
    parser.add_argument('--to_time', type=str, default=None, help='End time (YYYY-MM-DD HH:MM)')
    args = parser.parse_args()

    main(args)

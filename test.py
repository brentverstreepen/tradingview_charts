import asyncio
from binance.client import Client
from binance.streams import BinanceSocketManager
import pandas as pd
import mplfinance as mpf

# Insert your Binance API key and secret here
API_KEY = 'your_api_key_here'
API_SECRET = 'your_api_secret_here'


async def plot_live_candlestick():
    # Initialize Binance client with your API credentials
    client = Client(API_KEY, API_SECRET)

    # Set up Binance WebSocket Manager
    bsm = BinanceSocketManager(client)

    # Start the WebSocket connection
    bsm.start()

    # Create a WebSocket for receiving kline data
    socket = bsm.kline_futures_socket(symbol='BTCUSDT', interval='1m')

    # Initialize an empty DataFrame to store candlestick data
    df = pd.DataFrame(columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Fetch initial historical data to start with
    historical_klines = client.futures_klines(symbol='BTCUSDT', interval='1m', limit=50)
    for kline in historical_klines:
        df = df.append({
            'Date': pd.to_datetime(kline[0], unit='ms'),
            'Open': float(kline[1]),
            'High': float(kline[2]),
            'Low': float(kline[3]),
            'Close': float(kline[4]),
            'Volume': float(kline[5])
        }, ignore_index=True)

    # Plot initial chart
    mpf.plot(df.set_index('Date'), type='candle', style='charles', title='BTCUSDT.P', ylabel='Price')

    # Start listening to the WebSocket
    async with socket as stream:
        while True:
            res = await stream.recv()
            kline = res['k']

            # Check if the kline is closed
            if kline['x']:
                kline_data = {
                    'Date': pd.to_datetime(kline['t'], unit='ms'),
                    'Open': float(kline['o']),
                    'High': float(kline['h']),
                    'Low': float(kline['l']),
                    'Close': float(kline['c']),
                    'Volume': float(kline['v'])
                }

                # Append the new kline to the DataFrame
                df = df.append(kline_data, ignore_index=True)

                # Limit DataFrame size to keep it manageable (e.g., last 50 candles)
                if len(df) > 50:
                    df = df.iloc[-50:]

                # Clear the current plot and re-plot with updated data
                mpf.plot(df.set_index('Date'), type='candle', style='charles', title='BTCUSDT.P', ylabel='Price')

    # Close the Binance client
    await client.close_connection()


# Run the async function
asyncio.run(plot_live_candlestick())

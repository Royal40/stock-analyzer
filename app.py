from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker'].upper()

    try:
        # Download 6 months of daily stock data
        data = yf.download(ticker, period='6mo', interval='1d')

        if data.empty:
            return jsonify({'error': 'Invalid ticker or no data available'})

        # Use 1D Series — this is CRITICAL
        close_prices = data['Close']

        # Moving Averages
        data['MA50'] = close_prices.rolling(window=50).mean()
        data['MA200'] = close_prices.rolling(window=200).mean()

        # RSI
        rsi_indicator = RSIIndicator(close=close_prices)
        data['RSI'] = rsi_indicator.rsi()

        # Bollinger Bands
        bb_indicator = BollingerBands(close=close_prices)
        data['bb_upper'] = bb_indicator.bollinger_hband()
        data['bb_lower'] = bb_indicator.bollinger_lband()

        # MACD
        macd_indicator = MACD(close=close_prices)
        data['macd'] = macd_indicator.macd()
        data['macd_signal'] = macd_indicator.macd_signal()

        # Drop rows with any NaNs caused by indicators
        data.dropna(inplace=True)

        # Get latest row
        latest = data.iloc[-1]
        price = round(latest['Close'], 2)
        ma50 = round(latest['MA50'], 2)
        ma200 = round(latest['MA200'], 2)
        rsi_val = round(latest['RSI'], 2)

        # Basic recommendation logic
        if price > ma50 > ma200 and rsi_val < 70:
            recommendation = 'Buy'
        elif price < ma50 < ma200 and rsi_val > 30:
            recommendation = 'Sell'
        else:
            recommendation = 'Hold'

        # Prepare JSON response for frontend
        result = {
            'price': price,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi_val,
            'recommendation': recommendation,

            'ohlc': {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'open': data['Open'].round(2).tolist(),
                'high': data['High'].round(2).tolist(),
                'low': data['Low'].round(2).tolist(),
                'close': data['Close'].round(2).tolist(),
                'bb_upper': data['bb_upper'].round(2).tolist(),
                'bb_lower': data['bb_lower'].round(2).tolist()
            },

            'macd': {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'macd': data['macd'].round(2).tolist(),
                'signal': data['macd_signal'].round(2).tolist()
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

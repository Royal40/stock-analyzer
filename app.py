from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import ta

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
        # Download 6 months of daily data
        data = yf.download(ticker, period='6mo', interval='1d')

        if data.empty:
            return jsonify({'error': 'Invalid ticker or no data available'})

        # Add indicators
        data['MA50'] = data['Close'].rolling(window=50).mean()
        data['MA200'] = data['Close'].rolling(window=200).mean()

        # RSI
        rsi = RSIIndicator(data['Close']).rsi()
        data['RSI'] = rsi

        # Bollinger Bands
        bb = BollingerBands(close=data['Close'])
        data['bb_upper'] = bb.bollinger_hband()
        data['bb_lower'] = bb.bollinger_lband()

        # MACD
        macd = MACD(data['Close'])
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()

        # Latest values
        latest = data.dropna().iloc[-1]

        # Simple logic for recommendation
        price = latest['Close']
        ma50 = latest['MA50']
        ma200 = latest['MA200']
        rsi_val = latest['RSI']

        if price > ma50 > ma200 and rsi_val < 70:
            recommendation = 'Buy'
        elif price < ma50 < ma200 and rsi_val > 30:
            recommendation = 'Sell'
        else:
            recommendation = 'Hold'

        # Build JSON response
        result = {
            'price': round(price, 2),
            'ma50': round(ma50, 2),
            'ma200': round(ma200, 2),
            'rsi': round(rsi_val, 2),
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
                'dates': data['macd'].dropna().index.strftime('%Y-%m-%d').tolist(),
                'macd': data['macd'].dropna().round(2).tolist(),
                'signal': data['macd_signal'].dropna().round(2).tolist()
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

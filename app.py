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
        # Fetch historical data
        data = yf.download(ticker, period='6mo', interval='1d')
        if data.empty:
            return jsonify({'error': 'Invalid ticker or no data found.'})

        # Use only 1D Series
        close = data['Close']
        high = data['High']
        low = data['Low']
        open_ = data['Open']

        # Technical Indicators (1D safe)
        data['MA50'] = close.rolling(window=50).mean()
        data['MA200'] = close.rolling(window=200).mean()

        data['RSI'] = RSIIndicator(close=close).rsi()

        bb = BollingerBands(close=close)
        data['bb_upper'] = bb.bollinger_hband()
        data['bb_lower'] = bb.bollinger_lband()

        macd = MACD(close=close)
        data['macd'] = macd.macd()
        data['macd_signal'] = macd.macd_signal()

        # Drop rows with NaNs
        data.dropna(inplace=True)

        # Latest row
        latest = data.iloc[-1]
        price = round(latest['Close'], 2)
        ma50 = round(latest['MA50'], 2)
        ma200 = round(latest['MA200'], 2)
        rsi = round(latest['RSI'], 2)

        # Simple recommendation logic
        if price > ma50 > ma200 and rsi < 70:
            recommendation = 'Buy'
        elif price < ma50 < ma200 and rsi > 30:
            recommendation = 'Sell'
        else:
            recommendation = 'Hold'

        # Prepare JSON output
        result = {
            'price': price,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi,
            'recommendation': recommendation,
            'ohlc': {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'open': open_.loc[data.index].round(2).tolist(),
                'high': high.loc[data.index].round(2).tolist(),
                'low': low.loc[data.index].round(2).tolist(),
                'close': close.loc[data.index].round(2).tolist(),
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

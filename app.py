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
        # Download data
        df = yf.download(ticker, period='6mo', interval='1d')

        if df.empty:
            return jsonify({'error': 'Invalid ticker symbol or no data found.'})

        # Use only 1D Series
        open_ = df['Open']
        high = df['High']
        low = df['Low']
        close = df['Close']

        # Indicators (all passed 1D Series only)
        df['MA50'] = close.rolling(window=50).mean()
        df['MA200'] = close.rolling(window=200).mean()
        df['RSI'] = RSIIndicator(close=close).rsi()

        bb = BollingerBands(close=close)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()

        macd = MACD(close=close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        df.dropna(inplace=True)

        # Latest data point
        latest = df.iloc[-1]
        price = round(latest['Close'], 2)
        ma50 = round(latest['MA50'], 2)
        ma200 = round(latest['MA200'], 2)
        rsi = round(latest['RSI'], 2)

        # Recommendation
        if price > ma50 > ma200 and rsi < 70:
            recommendation = 'Buy'
        elif price < ma50 < ma200 and rsi > 30:
            recommendation = 'Sell'
        else:
            recommendation = 'Hold'

        # JSON response
        result = {
            'price': price,
            'ma50': ma50,
            'ma200': ma200,
            'rsi': rsi,
            'recommendation': recommendation,
            'ohlc': {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'open': open_.loc[df.index].round(2).tolist(),
                'high': high.loc[df.index].round(2).tolist(),
                'low': low.loc[df.index].round(2).tolist(),
                'close': close.loc[df.index].round(2).tolist(),
                'bb_upper': df['bb_upper'].round(2).tolist(),
                'bb_lower': df['bb_lower'].round(2).tolist()
            },
            'macd': {
                'dates': df.index.strftime('%Y-%m-%d').tolist(),
                'macd': df['macd'].round(2).tolist(),
                'signal': df['macd_signal'].round(2).tolist()
            }
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)


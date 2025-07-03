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
        df = yf.download(ticker, period='6mo', interval='1d')

        if df.empty:
            return jsonify({'error': 'Invalid ticker or no data'})

        # ✅ Gracefully handle both 1D and 2D inputs
        close = df['Close']
        if isinstance(close, pd.DataFrame):
            close = close.squeeze()

        # Indicators
        df['RSI'] = RSIIndicator(close=close).rsi()
        df['MA50'] = close.rolling(window=50).mean()
        df['MA200'] = close.rolling(window=200).mean()

        bb = BollingerBands(close=close)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()

        macd = MACD(close=close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()

        df.dropna(inplace=True)

        latest = df.iloc[-1]
        price = round(latest['Close'], 2)
        rsi = round(latest['RSI'], 2)
        ma50 = round(latest['MA50'], 2)
        ma200 = round(latest['MA200'], 2)

        if rsi < 30:
            recommendation = "Buy (Oversold)"
        elif rsi > 70:
            recommendation = "Sell (Overbought)"
        else:
            recommendation = "Hold"

        return jsonify({
            'ticker': ticker,
            'price': price,
            'rsi': rsi,
            'ma50': ma50,
            'ma200': ma200,
            'recommendation': recommendation,
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'close': close.loc[df.index].round(2).tolist(),
            'rsi_series': df['RSI'].round(2).tolist(),
            'bb_upper': df['bb_upper'].round(2).tolist(),
            'bb_lower': df['bb_lower'].round(2).tolist(),
            'macd': df['macd'].round(2).tolist(),
            'macd_signal': df['macd_signal'].round(2).tolist()
        })

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

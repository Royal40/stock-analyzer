from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    ticker = request.form['ticker'].upper()

    try:
        # Download historical data
        df = yf.download(ticker, period='6mo', interval='1d')

        if df.empty:
            return jsonify({'error': 'No data found for this ticker'})

        # ✅ Use ONLY Series — never DataFrame
        close = df['Close']  # This is a Series with shape (n,)

        # ✅ Confirm 1D
        print("DEBUG shape =", close.shape)
        print("DEBUG type =", type(close))

        # Calculate RSI
        df['RSI'] = RSIIndicator(close=close).rsi()

        # Drop NaN rows from early RSI calc
        df.dropna(inplace=True)

        # Get latest values
        latest = df.iloc[-1]
        rsi_val = round(latest['RSI'], 2)
        price = round(latest['Close'], 2)

        # Simple recommendation
        if rsi_val < 30:
            recommendation = 'Buy (RSI < 30 — Oversold)'
        elif rsi_val > 70:
            recommendation = 'Sell (RSI > 70 — Overbought)'
        else:
            recommendation = 'Hold (Neutral RSI)'

        return jsonify({
            'price': price,
            'rsi': rsi_val,
            'recommendation': recommendation,
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'rsi_series': df['RSI'].round(2).tolist()
        })

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

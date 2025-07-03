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
        # Download last 6 months of data
        df = yf.download(ticker, period='6mo', interval='1d')
        if df.empty:
            return jsonify({'error': 'No data found for this ticker'})

        # Use 1D Series only
        close = df['Close']
        print("DEBUG: close shape =", close.shape)  # confirm it's (n,)

        # Calculate RSI
        rsi = RSIIndicator(close=close).rsi()
        df['RSI'] = rsi

        # Drop NaNs from RSI
        df.dropna(inplace=True)

        # Get latest RSI and close price
        latest = df.iloc[-1]
        rsi_val = round(latest['RSI'], 2)
        price = round(latest['Close'], 2)

        # Recommendation based on RSI
        if rsi_val < 30:
            recommendation = "Buy (RSI < 30 — Oversold)"
        elif rsi_val > 70:
            recommendation = "Sell (RSI > 70 — Overbought)"
        else:
            recommendation = "Hold (Neutral RSI)"

        # Send data to frontend
        result = {
            'price': price,
            'rsi': rsi_val,
            'recommendation': recommendation,
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'rsi_series': df['RSI'].round(2).tolist()
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)

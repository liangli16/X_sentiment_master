# Stock Sentiment Analyzer 🐦📈

User-friendly Streamlit GUI for sentiment analysis of stock tickers based on today's X (Twitter) posts.

## Quick Start

1. Clone repo
2. `pip install -r requirements.txt`
3. Add `TWITTER_BEARER_TOKEN=your_token` to `.env` ([get token](https://developer.twitter.com/en/portal/dashboard))
4. `streamlit run stock_sentiment_gui.py`

Opens in browser!

## Features

- Enter ticker (e.g., NVDA)
- Fetches recent English tweets mentioning $TICKER
- VADER sentiment analysis
- **Metrics**: Avg score (-1 neg → +1 pos), % positive/negative/neutral
- **Chart**: Sentiment distribution
- **Tweets**: Top extreme examples with X links
- **Guide**: Score interpretation (bullish/bearish signals?)

## CLI Version

`python stock_sentiment.py NVDA`

## Disclaimer

Social sentiment ≠ financial advice. For fun & learning!

Built with Streamlit, Tweepy, VADER.
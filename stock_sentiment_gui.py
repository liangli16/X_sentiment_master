import streamlit as st
import os
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timezone
from dotenv import load_dotenv
from tweepy import Paginator

load_dotenv()

st.set_page_config(page_title="Stock Sentiment Analyzer", page_icon="📈", layout="wide")

def get_tweets(client, ticker, start_time):
    query = f"${ticker} OR \"{ticker}\" OR {ticker} lang:en -is:retweet"
    paginator = Paginator(
        client.search_recent_tweets,
        query=query,
        start_time=start_time,
        max_results=100,
        tweet_fields=['created_at', 'author_id', 'public_metrics']
    )
    return list(paginator.flatten(limit=500))

def get_sentiment_data(ticker):
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return None, "Error: TWITTER_BEARER_TOKEN not found in .env file. Get it from https://developer.twitter.com/en/portal/dashboard"
    
    try:
        client = tweepy.Client(bearer_token=bearer_token)
    except Exception as e:
        return None, f"Error initializing Twitter client: {str(e)}"
    
    # Today UTC start
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    tweets = get_tweets(client, ticker, today_start)
    
    if not tweets:
        return None, f"No tweets found for {ticker} today."
    
    analyzer = SentimentIntensityAnalyzer()
    
    data = []
    for tweet in tweets:
        text_lower = tweet.text.lower()
        if ticker.lower() in text_lower:
            score_dict = analyzer.polarity_scores(tweet.text)
            data.append({
                'tweet': tweet,
                'text': tweet.text,
                'score': score_dict['compound']
            })
    
    if not data:
        return None, f"No relevant tweets for {ticker} after filtering."
    
    sentiments = [d['score'] for d in data]
    avg_sent = sum(sentiments) / len(sentiments)
    
    pos = sum(1 for d in data if d['score'] > 0.05)
    neg = sum(1 for d in data if d['score'] < -0.05)
    neu = len(data) - pos - neg
    
    pos_pct = (pos / len(data)) * 100
    neg_pct = (neg / len(data)) * 100
    neu_pct = (neu / len(data)) * 100
    
    # Top 5 extreme tweets
    data_sorted = sorted(data, key=lambda d: abs(d['score']), reverse=True)[:5]
    
    most_pos = max(data, key=lambda d: d['score'])
    most_neg = min(data, key=lambda d: d['score'])
    
    return {
        'avg_sent': avg_sent,
        'total_tweets': len(data),
        'pos': pos,
        'pos_pct': pos_pct,
        'neg': neg,
        'neg_pct': neg_pct,
        'neu': neu,
        'neu_pct': neu_pct,
        'top_tweets': data_sorted,
        'most_pos': most_pos,
        'most_neg': most_neg
    }, None

st.title("📈 Stock Sentiment Analyzer")
st.markdown("Analyze public sentiment on X (Twitter) for a stock ticker based on today's posts.")
st.info("**Sentiment Guide:** Average score -1 (bearish) to +1 (bullish). Positive >0.05, Negative < -0.05. % is tweet breakdown. *VADER-tuned for X. Not financial advice—DYOR!*")

ticker = st.text_input("Enter stock ticker", placeholder="e.g., NVDA, AAPL, TSLA", label_visibility="collapsed")

col1, col2 = st.columns([4,1])
if col2.button("🔍 Analyze", type="primary"):
    if not ticker:
        st.warning("Please enter a stock ticker.")
    else:
        ticker_upper = ticker.upper().strip()
        with st.spinner(f"Analyzing sentiment for {ticker_upper}..."):
            result, error = get_sentiment_data(ticker_upper)
        
        if error:
            st.error(error)
        else:
            st.success(f"✅ Analyzed {result['total_tweets']} relevant tweets for {ticker_upper}")
            
            # Metrics
            col_a, col_b, col_c, col_d = st.columns(4)
            col_a.metric("Average Sentiment Score", f"{result['avg_sent']:.3f}")
            col_b.metric("Positive", f"{result['pos_pct']:.1f}%", delta=f"+{result['pos']}")
            col_c.metric("Negative", f"{result['neg_pct']:.1f}%", delta=f"+{result['neg']}")
            col_d.metric("Neutral", f"{result['neu_pct']:.1f}%")
            st.subheader("Sentiment Distribution")
            chart_data = {
                "Sentiment": ["Positive", "Negative", "Neutral"],
                "Percentage": [result['pos_pct'], result['neg_pct'], result['neu_pct']]
            }
            st.bar_chart(chart_data, use_container_width=True)
            
            # Top tweets
            st.subheader("📝 Sample Tweets (Most Extreme)")
            for d in result['top_tweets']:
                with st.expander(f"Score: {d['score']:.3f} | {d['text'][:100]}..."):
                    st.write(d['text'])
                    st.caption(f"Posted: {d['tweet'].created_at}")
                    st.markdown(f"[View on X](https://x.com/i/status/{d['tweet'].id})")
            
            # Most pos and neg expanders
            col_pos, col_neg = st.columns(2)
            with col_pos:
                st.subheader("Most Positive")
                pos_d = result['most_pos']
                st.info(f"Score: {pos_d['score']:.3f}")
                st.caption(pos_d['text'])
                st.markdown(f"[View](https://x.com/i/status/{pos_d['tweet'].id})")
            
            with col_neg:
                st.subheader("Most Negative")
                neg_d = result['most_neg']
                st.error(f"Score: {neg_d['score']:.3f}")
                st.caption(neg_d['text'])
                st.markdown(f"[View](https://x.com/i/status/{neg_d['tweet'].id})")

st.markdown("---")
st.caption("Powered by X API v2 & VADER Sentiment. Ensure TWITTER_BEARER_TOKEN is set in .env")
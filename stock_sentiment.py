import os
import tweepy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timezone
import argparse
from dotenv import load_dotenv
from tweepy import Paginator


load_dotenv()

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

def main():
    parser = argparse.ArgumentParser(description="Analyze sentiment of X posts for a stock ticker today.")
    parser.add_argument("ticker", help="Stock ticker (e.g., NVDA)")
    args = parser.parse_args()

    ticker = args.ticker.upper()
    bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        print("Error: Set TWITTER_BEARER_TOKEN environment variable.")
        print("Get it from https://developer.twitter.com/en/portal/dashboard -> Keys and tokens -> Bearer Token")
        return

    client = tweepy.Client(bearer_token=bearer_token)

    # Today UTC start
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    
    print(f"Fetching tweets for {ticker} since {today_start[:10]}...")

    tweets = get_tweets(client, ticker, today_start)

    if not tweets:
        print("No tweets found for today.")
        return

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

        print("No relevant tweets after filtering.")

        return

    sentiments = [d['score'] for d in data]

    avg_sent = sum(sentiments) / len(sentiments)

    pos = sum(1 for d in data if d['score'] > 0.05)

    neg = sum(1 for d in data if d['score'] < -0.05)

    neu = len(data) - pos - neg

    print(f"\n=== Summary for {ticker} ===")

    print(f"Tweets fetched: {len(tweets)}, analyzed: {len(data)}")

    print(f"Average compound sentiment: {avg_sent:.3f}")

    print(f"Positive: {pos} ({pos / len(data) * 100:.1f}%)")

    print(f"Negative: {neg} ({neg / len(data) * 100:.1f}%)")

    print(f"Neutral: {neu} ({neu / len(data) * 100:.1f}%)")

    # Sample top tweets

    data_sorted = sorted(data, key=lambda d: d['score'], reverse=True)

    print("\nTop 3 tweets:")

    for i in range(min(3, len(data_sorted))):

        d = data_sorted[i]

        print(f"{d['score']:.3f}: {d['text'][:150]}...")

        print(f"  https://twitter.com/i/status/{d['tweet'].id}")

    # Most positive and negative

    pos_idx = max(range(len(data)), key=lambda i: data[i]['score'])

    neg_idx = min(range(len(data)), key=lambda i: data[i]['score'])

    print("\nMost positive:")

    d_pos = data[pos_idx]

    print(f"  Score: {d_pos['score']:.3f}")

    print(f"  Text: {d_pos['text'][:200]}...")

    print(f"  Link: https://twitter.com/i/status/{d_pos['tweet'].id}")

    print("\nMost negative:")

    d_neg = data[neg_idx]

    print(f"  Score: {d_neg['score']:.3f}")

    print(f"  Text: {d_neg['text'][:200]}...")

    print(f"  Link: https://twitter.com/i/status/{d_neg['tweet'].id}")

if __name__ == "__main__":
    main()
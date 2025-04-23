import logging
import time
import json
from requests_oauthlib import OAuth1Session
from openai import OpenAI

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Twitter OAuth 1.0a Keys ---
consumer_key = "CONSUMER_KEY"
consumer_secret = "CONSUMER_SECRET"

# --- Perplexity API ---
PERPLEXITY_API_KEY = "PERPLEXITY/OPENAI KEY"

# --- Perplexity Setup ---
client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

def generate_tweet(prompt="Write a fun twitter post"):
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "Write a fun twitter post to test my bot"
                    "<You can add prompts by entereing here>"
                )
            },
            {"role": "user", "content": prompt}
        ]
        response = client.chat.completions.create(
            model="sonar-pro",
            messages=messages
        )
        tweet_text = response.choices[0].message.content.strip()
        logging.info("🧠 Generated tweet: %s", tweet_text)
        return tweet_text
    except Exception as e:
        logging.error("❌ Failed to generate tweet: %s", e)
        return None


def authenticate_twitter():
    try:
        request_token_url = "https://api.twitter.com/oauth/request_token?oauth_callback=oob&x_auth_access_type=write"
        oauth = OAuth1Session(consumer_key, client_secret=consumer_secret)

        fetch_response = oauth.fetch_request_token(request_token_url)
        resource_owner_key = fetch_response.get("oauth_token")
        resource_owner_secret = fetch_response.get("oauth_token_secret")
        logging.info("Got OAuth token: %s", resource_owner_key)

        base_authorization_url = "https://api.twitter.com/oauth/authorize"
        authorization_url = oauth.authorization_url(base_authorization_url)
        print("🔗 Please go here and authorize: %s" % authorization_url)
        verifier = input("🔑 Paste the PIN here: ")

        access_token_url = "https://api.twitter.com/oauth/access_token"
        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=resource_owner_key,
            resource_owner_secret=resource_owner_secret,
            verifier=verifier,
        )
        oauth_tokens = oauth.fetch_access_token(access_token_url)

        access_token = oauth_tokens["oauth_token"]
        access_token_secret = oauth_tokens["oauth_token_secret"]

        oauth = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=access_token,
            resource_owner_secret=access_token_secret,
        )

        logging.info("✅ Twitter authenticated via OAuth1Session.")
        return oauth

    except Exception as e:
        logging.error("❌ Error authenticating with Twitter: %s", e)
        return None

def post_tweet(oauth, text):
    try:
        payload = {"text": text}
        response = oauth.post(
            "https://api.twitter.com/2/tweets",
            json=payload,
        )

        if response.status_code != 201:
            raise Exception(
                f"Request returned an error: {response.status_code} {response.text}"
            )

        logging.info("✅ Tweet posted successfully!")
        json_response = response.json()
        logging.debug(json.dumps(json_response, indent=4, sort_keys=True))
    except Exception as e:
        logging.error("❌ Error posting tweet: %s", e)

def main(should_tweet=True, retries=3):
    twitter_oauth = authenticate_twitter()
    if not twitter_oauth:
        return

    tweet = None
    for attempt in range(retries):
        tweet = generate_tweet()
        if tweet:
            break
        logging.warning("Retrying tweet generation... (%d/%d)", attempt + 1, retries)
        time.sleep(2)

    if tweet and should_tweet:
        post_tweet(twitter_oauth, tweet)
    elif tweet:
        logging.info("🔒 Tweet generated but not posted (posting disabled).")
        logging.info("Tweet content:\n%s", tweet)
    else:
        logging.error("💥 Failed to generate tweet after %d attempts.", retries)

if __name__ == "__main__":
    main(should_tweet=True)

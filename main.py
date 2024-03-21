# Load lib
import os
from dotenv import load_dotenv
import discord
import aiohttp
import asyncio
import logging
from datetime import datetime, timedelta
from collections import deque

# Configure logging
logging.basicConfig(level=logging.ERROR)  # Set logging level to ERROR

intents = discord.Intents.default()
# Add specific intents your bot needs (e.g., messages, guilds)
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)

# Load environment variables from .env file
load_dotenv()

# Discord bot token and channel ID
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# Set to store URLs of posted articles
posted_articles = set()

# Queue to store fetched articles
article_queue = deque(maxlen=100)

# Variable to store the timestamp of the latest fetched article
latest_article_timestamp = None

# Throttling rate limit
THROTTLING_INTERVAL = 30  # seconds
MAX_REQUESTS_PER_INTERVAL = 5

# Function to fetch news from News API
async def fetch_news(session):
    global latest_article_timestamp
    try:
        url = f'https://newsapi.org/v2/everything?domains=techcrunch.com,thenextweb.com&apiKey={NEWS_API_KEY}'
        if latest_article_timestamp:
            url += f'&from={latest_article_timestamp}'
        async with session.get(url) as response:
            response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)
            data = await response.json()
            articles = data['articles']
            if articles:
                latest_article_timestamp = articles[0]['publishedAt']  # Update latest article timestamp
                article_queue.extend(articles)  # Add fetched articles to the queue
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching news: {e}")

# Function to post news to Discord channel
async def post_news():
    global posted_articles
    channel = client.get_channel(CHANNEL_ID)
    while article_queue:
        article = article_queue.pop()  # Get the latest fetched article from the queue
        url = article['url']
        # Check if the article URL has already been posted
        if url not in posted_articles:
            try:
                title = article['title']
                description = article['description']
                message = f"**{title}**\n{description}\n{url}"
                await channel.send(message)
                # Add the URL to the set of posted articles
                posted_articles.add(url)
            except Exception as e:
                logging.error(f"Error posting news: {e}")

# Function to fetch and post news periodically
async def fetch_and_post_news():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Fetch news articles
                await fetch_news(session)

                # Post news articles
                await post_news()

                # Throttle requests to avoid hitting rate limits
                await asyncio.sleep(THROTTLING_INTERVAL)
            except Exception as e:
                logging.error(f"Error in fetch_and_post_news: {e}")

# Event for bot being ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    print('------')
    # Start fetching and posting news
    asyncio.create_task(fetch_and_post_news())

# Run the bot
client.run(DISCORD_TOKEN)

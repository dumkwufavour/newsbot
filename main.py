#Load lib
import os
from dotenv import load_dotenv
import discord
import aiohttp
import asyncio
import logging
import concurrent.futures

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

# Function to fetch news from News API
async def fetch_news():
    try:
        url = f'https://newsapi.org/v2/everything?domains=techcrunch.com,thenextweb.com&apiKey={NEWS_API_KEY}'
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)
                data = await response.json()
                articles = data['articles']
                return articles[:10]  # Return only the first 10 articles
    except aiohttp.ClientError as e:
        logging.error(f"Error fetching news: {e}")
        return []

# Function to post news to Discord channel
async def post_news():
    global posted_articles
    channel = client.get_channel(CHANNEL_ID)
    articles = await fetch_news()
    for article in articles:
        url = article['url']
        # Check if the article URL has already been posted
        if url not in posted_articles:
            title = article['title']
            description = article['description']
            message = f"**{title}**\n{description}\n{url}"
            await channel.send(message)
            # Add the URL to the set of posted articles
            posted_articles.add(url)

# Execute the blocking operation in a separate thread
def fetch_news_blocking():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(fetch_news())
    finally:
        loop.close()

# Event for bot being ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user.name}')
    print('------')
    # Schedule task to fetch and post news every 8 seconds
    while True:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            articles = await asyncio.get_event_loop().run_in_executor(executor, fetch_news_blocking)
            for article in articles:
                url = article['url']
                # Check if the article URL has already been posted
                if url not in posted_articles:
                    title = article['title']
                    description = article['description']
                    message = f"**{title}**\n{description}\n{url}"
                    await client.get_channel(CHANNEL_ID).send(message)
                    # Add the URL to the set of posted articles
                    posted_articles.add(url)
        await asyncio.sleep(8)

# Run the bot
client.run(DISCORD_TOKEN)

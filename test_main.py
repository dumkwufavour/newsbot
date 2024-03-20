import unittest
from unittest.mock import patch, MagicMock
import asyncio
import main  # Assuming your main script is named main.py

class TestDiscordBot(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = main.client
        self.channel_id = main.CHANNEL_ID
        self.news_api_key = main.NEWS_API_KEY

    async def test_fetch_news(self):
        # Mocking the requests.get function
        with patch('requests.get') as mocked_get:
            mocked_response = MagicMock()
            mocked_response.json.return_value = {'articles': [{'title': 'Test Article', 'description': 'This is a test article', 'url': 'https://example.com'}]}
            mocked_get.return_value = mocked_response

            articles = main.fetch_news()
            self.assertEqual(len(articles), 1)
            self.assertEqual(articles[0]['title'], 'Test Article')

    async def test_post_news(self):
        # Mocking the channel send function
        mocked_channel = MagicMock()
        self.bot.get_channel = MagicMock(return_value=mocked_channel)

        # Mocking fetch_news
        with patch('main.fetch_news') as mocked_fetch_news:
            mocked_fetch_news.return_value = [{'title': 'Test Article', 'description': 'This is a test article', 'url': 'https://example.com'}]

            await main.post_news()

            self.bot.get_channel.assert_called_once_with(int(self.channel_id))
            mocked_channel.send.assert_called_once()

    async def test_fetch_and_post_news(self):
        # Mocking fetch_news
        with patch('main.fetch_news') as mocked_fetch_news:
            mocked_fetch_news.return_value = [{'title': 'Test Article', 'description': 'This is a test article', 'url': 'https://example.com'}]

            await main.fetch_and_post_news()

            self.assertTrue(mocked_fetch_news.called)

if __name__ == '__main__':
    unittest.main()

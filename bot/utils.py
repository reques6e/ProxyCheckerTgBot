import aiohttp
import asyncio
import urllib.request
import urllib.error
import aiohttp
from config import bot_token

def validate_proxy_format(proxy):
    proxy_parts = proxy.split(':')
    return len(proxy_parts) == 4


async def checker(proxy):
    proxy_parts = proxy.split(':')
    ip = proxy_parts[0]
    port = proxy_parts[1]
    username = proxy_parts[2]
    password = proxy_parts[3]

    proxy_url = f'http://{username}:{password}@{ip}:{port}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://www.example.com', proxy=proxy_url, timeout=5) as response:
                if response.status == 200:
                    return True
                else:
                    return False
    except Exception as e:
        return False

async def proxy_check(proxies):
    tasks = [checker(proxy) for proxy in proxies]
    results = await asyncio.gather(*tasks)
    for proxy, result in zip(proxies, results):
        return result

async def download_file(file_url):
    base_url = "https://api.telegram.org/file/bot" + bot_token + "/"
    full_url = base_url + file_url
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(full_url) as response:
                return await response.text()
        except Exception as e:
            print(f"Error downloading file: {e}")
            return ""

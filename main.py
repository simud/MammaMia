import asyncio
from curl_cffi.requests import AsyncSession
from streaming_community import streaming_community
import urllib.parse

CONTENT_LIST = [
    ("tt0111161", 1, None, None, "Le ali della libertà"),  # The Shawshank Redemption
    ("tt0468569", 1, None, None, "Il cavaliere oscuro"),   # The Dark Knight
    ("tmdb:1399:1:1", 0, 1, 1, "Il Trono di Spade S01E01"),  # Game of Thrones
    ("tt0944947:1:1", 0, 1, 1, "Il Trono di Spade S01E01"),  # Game of Thrones
]

async def generate_m3u8():
    m3u8_content = "#EXTM3U\n"
    async with AsyncSession() as client:
        for content_id, is_movie, season, episode, title in CONTENT_LIST:
            try:
                print(f"Recupero flusso per: {title}")
                url, url720, quality = await streaming_community(content_id, client, "1")
                if url:
                    encoded_title = urllib.parse.quote_plus(title.replace(" ", "+").replace("–", "+").replace("—", "+"))
                    m3u8_content += f'#EXTINF:-1 tvg-name="{title}" tvg-quality="{quality}",{title}\n'
                    m3u8_content += f"{url}\n"
                    if url720 and url720 != url:
                        m3u8_content += f'#EXTINF:-1 tvg-name="{title} (720p)" tvg-quality="720p",{title} (720p)\n'
                        m3u8_content += f"{url720}\n"
                else:
                    print(f"Flusso non trovato per: {title}")
            except Exception as e:
                print(f"Errore per {title}: {e}")
    
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    print("File streaming.m3u8 generato con successo!")

if __name__ == "__main__":
    asyncio.run(generate_m3u8())

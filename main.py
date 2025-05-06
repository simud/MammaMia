import asyncio
from curl_cffi.requests import AsyncSession
from streaming_community import streaming_community
import urllib.parse

# Lista di film e serie TV (ID IMDb/TMDb, is_movie, season, episode, title)
# Per serie TV, usa "tmdb:<id>:<season>:<episode>" o "tt<imdb_id>:<season>:<episode>"
CONTENT_LIST = [
    ("tt0111161", 1, None, None, "The Shawshank Redemption"),  # Film
    ("tt0468569", 1, None, None, "The Dark Knight"),           # Film
    ("tmdb:1399:1:1", 0, 1, 1, "Game of Thrones S01E01"),     # Serie TV
    ("tt0944947:1:1", 0, 1, 1, "Game of Thrones S01E01"),     # Serie TV (IMDb)
]

async def generate_m3u8():
    """Genera il file streaming.m3u8 con i flussi."""
    m3u8_content = "#EXTM3U\n"
    async with AsyncSession() as client:
        for content_id, is_movie, season, episode, title in CONTENT_LIST:
            try:
                print(f"Recupero flusso per: {title}")
                # Usa SC_FAST_SEARCH = "1" per evitare TMDb
                url, url720, quality = await streaming_community(content_id, client, "1")
                if url:
                    # Codifica il titolo per la ricerca
                    encoded_title = urllib.parse.quote_plus(title.replace(" ", "+").replace("–", "+").replace("—", "+"))
                    # Aggiungi metadati al file M3U8
                    m3u8_content += f'#EXTINF:-1 tvg-name="{title}" tvg-quality="{quality}",{title}\n'
                    m3u8_content += f"{url}\n"
                    if url720 and url720 != url:
                        m3u8_content += f'#EXTINF:-1 tvg-name="{title} (720p)" tvg-quality="720p",{title} (720p)\n'
                        m3u8_content += f"{url720}\n"
                else:
                    print(f"Flusso non trovato per: {title}")
            except Exception as e:
                print(f"Errore per {title}: {e}")
    
    # Scrivi il file M3U8
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    print("File streaming.m3u8 generato con successo!")

if __name__ == "__main__":
    asyncio.run(generate_m3u8())

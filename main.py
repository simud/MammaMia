import asyncio
from curl_cffi.requests import AsyncSession
from streaming_community import streaming_community
import urllib.parse
import os

# Titoli verificati su https://streamingcommunity.education
CONTENT_LIST = [
    ("tt0111161", 1, None, None, "Le ali della libertà"),  # Film: The Shawshank Redemption
    ("tt0468569", 1, None, None, "Il cavaliere oscuro"),   # Film: The Dark Knight
    ("tmdb:1399:1:1", 0, 1, 1, "Il Trono di Spade"),      # Serie: Game of Thrones S01E01
]

async def generate_m3u8():
    m3u8_content = "#EXTM3U\n"
    found_streams = 0
    async with AsyncSession() as client:
        for content_id, is_movie, season, episode, title in CONTENT_LIST:
            for attempt in range(3):  # Riprova fino a 3 volte
                try:
                    print(f"[INFO] Tentativo {attempt + 1} per '{title}' (ID: {content_id})")
                    url, url720, quality = await streaming_community(content_id, client, "1")
                    if url:
                        print(f"[SUCCESSO] Flusso trovato per '{title}': {url} (Qualità: {quality})")
                        encoded_title = urllib.parse.quote_plus(title.replace(" ", "+").replace("–", "+").replace("—", "+"))
                        m3u8_content += f'#EXTINF:-1 tvg-name="{title}" tvg-quality="{quality}",{title}\n'
                        m3u8_content += f"{url}\n"
                        if url720 and url720 != url:
                            print(f"[SUCCESSO] Flusso 720p trovato per '{title}': {url720}")
                            m3u8_content += f'#EXTINF:-1 tvg-name="{title} (720p)" tvg-quality="720p",{title} (720p)\n'
                            m3u8_content += f"{url720}\n"
                        found_streams += 1
                        break
                    else:
                        print(f"[ERRORE] Nessun flusso trovato per '{title}' al tentativo {attempt + 1}")
                        await asyncio.sleep(2)  # Aumentato a 2 secondi
                except Exception as e:
                    print(f"[ERRORE] Errore per '{title}' al tentativo {attempt + 1}: {str(e)}")
                    await asyncio.sleep(2)
    
    # Scrivi il file
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    
    # Log del contenuto
    print(f"[INFO] Contenuto di streaming.m3u8:\n{m3u8_content}")
    print(f"[INFO] Flussi trovati: {found_streams}/{len(CONTENT_LIST)}")
    
    # Controllo file vuoto
    if found_streams == 0:
        print("[ATTENZIONE] Nessun flusso valido trovato. Il file streaming.m3u8 contiene solo l'intestazione.")

if __name__ == "__main__":
    asyncio.run(generate_m3u8())

import asyncio
from curl_cffi.requests import AsyncSession
from streaming_community import streaming_community
import urllib.parse
import os
import Src.Utilities.config as config

# Configurazione dinamica
SC_DOMAIN = config.SC_DOMAIN
REFERRER = f"https://streamingcommunity.{SC_DOMAIN}"
ORIGIN = f"https://streamingcommunity.{SC_DOMAIN}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Configurazione proxy (opzionale)
PROXY = config.PROXY if hasattr(config, 'PROXY') else None

# Lista dei contenuti
CONTENT_LIST = [
    ("tt0111161", 1, None, None, "The Shawshank Redemption"),  # Usa titolo inglese per precisione
    ("tt0468569", 1, None, None, "Il cavaliere oscuro"),
    ("tmdb:1399:1:1", 0, 1, 1, "Il Trono di Spade"),
]

async def generate_m3u8():
    m3u8_content = "#EXTM3U\n"
    found_streams = 0
    session_params = {"impersonate": "chrome124"}
    if PROXY:
        session_params["proxies"] = {"http": PROXY, "https": PROXY}
    
    async with AsyncSession(**session_params) as client:
        for content_id, is_movie, season, episode, title in CONTENT_LIST:
            for attempt in range(3):
                try:
                    print(f"[INFO] Tentativo {attempt + 1} per '{title}' (ID: {content_id})")
                    url, url720, quality = await streaming_community(content_id, client, "1", title)
                    if url and "vixcloud.co/playlist" in url:
                        # Test flusso 1080p
                        test_response = await client.get(
                            url,
                            headers={"User-Agent": USER_AGENT, "Referer": REFERRER, "Origin": ORIGIN},
                            timeout=10
                        )
                        if test_response.status_code == 200:
                            print(f"[SUCCESSO] Flusso valido per '{title}': {url} (Qualità: {quality})")
                            tvg_id = content_id.replace("tmdb:", "").replace("tt", "sc")
                            group_title = "StreamingCommunity"
                            tvg_logo = "https://i.postimg.cc/j5d5bSGp/photo-2025-03-13-12-56-42.png"
                            m3u8_content += f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group_title}" tvg-logo="{tvg_logo}",{title}\n'
                            m3u8_content += f'#EXTVLCOPT:http-referrer={REFERRER}\n'
                            m3u8_content += f'#EXTVLCOPT:http-origin={ORIGIN}\n'
                            m3u8_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
                            m3u8_content += f"{url}\n"
                            # Test flusso 720p
                            if url720 and url720 != url and "vixcloud.co/playlist" in url720:
                                test_720_response = await client.get(
                                    url720,
                                    headers={"User-Agent": USER_AGENT, "Referer": REFERRER, "Origin": ORIGIN},
                                    timeout=10
                                )
                                if test_720_response.status_code == 200:
                                    print(f"[SUCCESSO] Flusso 720p valido per '{title}': {url720}")
                                    m3u8_content += f'#EXTINF:-1 tvg-id="{tvg_id}_720" group-title="{group_title}" tvg-logo="{tvg_logo}",{title} (720p)\n'
                                    m3u8_content += f'#EXTVLCOPT:http-referrer={REFERRER}\n'
                                    m3u8_content += f'#EXTVLCOPT:http-origin={ORIGIN}\n'
                                    m3u8_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
                                    m3u8_content += f"{url720}\n"
                            found_streams += 1
                            break
                        else:
                            print(f"[ERRORE] Flusso non valido per '{title}' (status: {test_response.status_code})")
                    else:
                        print(f"[ERRORE] Flusso non trovato per '{title}' al tentativo {attempt + 1}")
                    await asyncio.sleep(10)  # Ritardo aumentato
                except Exception as e:
                    print(f"[ERRORE] Errore per '{title}' al tentativo {attempt + 1}: {str(e)}")
                    await asyncio.sleep(10)
    
    # Scrivi il file
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    
    print(f"[INFO] Contenuto di streaming.m3u8:\n{m3u8_content}")
    print(f"[INFO] Flussi trovati: {found_streams}/{len(CONTENT_LIST)}")
    
    if found_streams == 0:
        print("[ATTENZIONE] Nessun flusso valido trovato.")

if __name__ == "__main__":
    asyncio.run(generate_m3u8())

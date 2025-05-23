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

# Configurazione proxy
PROXY = config.PROXY if hasattr(config, 'PROXY') else None

# Cookie di sessione manuali
SESSION_COOKIES = {
    "XSRF-TOKEN": "eyJpdiI6IkRMZy9hKzVpUUxkYlZlT2xOMWVQL1E9PSIsInZhbHVlIjoiTXVoclZKSm5lTHVmRWxmRjVMdEpIc2FKcnRMMTkyTzBoTHkyc0JNSEJsQ2dRYlhtOFk5N3IyYWZ2ZUUzbEJMTkpid0xURytrVDFLOTFhNDhEZndXeHhqTWo0VHVtZzNuOUJoTkpqdWpYQlZ3MVp6WU1RdllUWWNqbUpLNFlTQ2YiLCJtYWMiOiIxZmMzNDQ4Nzg3ZmQ4NmQwYTY1YzMzZDA0NDdkYWUxODdmNTA0NzQ2YTY3YzNlMmY5ODdlYmYyZTYzOGUyYzYyIiwidGFnIjoiIn0%3D",
    "streamingcommunity_session": "eyJpdiI6InhvL2FyRnk1ZjQ1NjZ4Y0FuQ0RwMlE9PSIsInZhbHVlIjoiVEtITWFRaGxmWC8zSUx3amtic2lEM0Y3QitNbFNWZVVMdlVqWExneEs5MjNpR3NYMFpsNUxLVUxIYlhmUWtMcnl1cmJLalZpUUUvU25laVZ5aENmZ2VBeUFoMkIySzEvRHZ6K2VMZEJMNmJILzd1ZnhwZWF6MThZeGtySXNVVWQiLCJtYWMiOiI4OWEwZjcxY2Q5YzY3MzY5ODJiMzFhZGM0NjEwYzUxNDM3M2E1ZmI2ZDMwZDBhZjczZTRjNmY0NmE3ZjZiNGQ4IiwidGFnIjoiIn0%3D%3D"
}

# Lista dei contenuti
CONTENT_LIST = [
    ("tt0111161", 1, None, None, "The Shawshank Redemption"),
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
        # Imposta cookie manuali
        client.cookies.update(SESSION_COOKIES)
        print(f"[INFO] Cookie impostati: {client.cookies}")
        
        # Inizializza la sessione
        try:
            init_response = await client.get(
                f"https://streamingcommunity.{SC_DOMAIN}/",
                headers={
                    "User-Agent": USER_AGENT,
                    "Referer": REFERRER,
                    "Origin": ORIGIN,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br"
                },
                timeout=15
            )
            print(f"[INFO] Sessione inizializzata, status: {init_response.status_code}, cookies: {client.cookies}")
        except Exception as e:
            print(f"[ERRORE] Errore inizializzazione sessione: {str(e)}")
        
        for content_id, is_movie, season, episode, title in CONTENT_LIST:
            stream_added = False
            for attempt in range(5):
                try:
                    print(f"[INFO] Tentativo {attempt + 1} per '{title}' (ID: {content_id})")
                    url, url720, quality = await streaming_community(content_id, client, "1", title)
                    if url and "vixcloud.co/playlist" in url:
                        # Verifica flusso
                        for test_attempt in range(3):
                            test_response = await client.get(
                                url,
                                headers={
                                    "User-Agent": USER_AGENT,
                                    "Referer": REFERRER,
                                    "Origin": ORIGIN,
                                    "Accept-Encoding": "gzip, deflate, br"
                                },
                                timeout=10
                            )
                            content_type = test_response.headers.get('content-type', '')
                            print(f"[DEBUG] Risposta flusso '{title}' (tentativo {test_attempt + 1}): status={test_response.status_code}, content-type={content_type}")
                            with open(f"response_{title}_{test_attempt + 1}.html", "w", encoding="utf-8") as f:
                                f.write(test_response.text)
                            if test_response.status_code == 200 and ("m3u8" in test_response.text.lower() or "application/vnd.apple.mpegurl" in content_type):
                                print(f"[SUCCESSO] Flusso valido per '{title}': {url} (Qualità: {quality})")
                                tvg_id = content_id.replace("tmdb:", "").replace("tt", "sc")
                                group_title = "StreamingCommunity"
                                tvg_logo = "https://i.postimg.cc/j5d5bSGp/photo-2025-03-13-12-56-42.png"
                                m3u8_content += f'#EXTINF:-1 tvg-id="{tvg_id}" group-title="{group_title}" tvg-logo="{tvg_logo}",{title}\n'
                                m3u8_content += f'#EXTVLCOPT:http-referrer={REFERRER}\n'
                                m3u8_content += f'#EXTVLCOPT:http-origin={ORIGIN}\n'
                                m3u8_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
                                m3u8_content += f"{url}\n"
                                if url720 and url720 != url and "vixcloud.co/playlist" in url720:
                                    test_720_response = await client.get(
                                        url720,
                                        headers={"User-Agent": USER_AGENT, "Referer": REFERRER, "Origin": ORIGIN},
                                        timeout=10
                                    )
                                    if test_720_response.status_code == 200 and ("m3u8" in test_720_response.text.lower() or "application/vnd.apple.mpegurl" in test_720_response.headers.get("content-type", "")):
                                        print(f"[SUCCESSO] Flusso 720p valido per '{title}': {url720}")
                                        m3u8_content += f'#EXTINF:-1 tvg-id="{tvg_id}_720" group-title="{group_title}" tvg-logo="{tvg_logo}",{title} (720p)\n'
                                        m3u8_content += f'#EXTVLCOPT:http-referrer={REFERRER}\n'
                                        m3u8_content += f'#EXTVLCOPT:http-origin={ORIGIN}\n'
                                        m3u8_content += f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n'
                                        m3u8_content += f"{url720}\n"
                                found_streams += 1
                                stream_added = True
                                break
                            else:
                                print(f"[ERRORE] Flusso non valido per '{title}' (status: {test_response.status_code}, tentativo {test_attempt + 1})")
                            await asyncio.sleep(5)
                        if stream_added:
                            break
                    else:
                        print(f"[ERRORE] Flusso non trovato per '{title}' al tentativo {attempt + 1}")
                    await asyncio.sleep(20)
                except Exception as e:
                    print(f"[ERRORE] Errore per '{title}' al tentativo {attempt + 1}: {str(e)}")
                    await asyncio.sleep(20)
    
    # Scrivi il file
    with open("streaming.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u8_content)
    
    print(f"[INFO] Contenuto di streaming.m3u8:\n{m3u8_content}")
    print(f"[INFO] Flussi trovati: {found_streams}/{len(CONTENT_LIST)}")
    
    if found_streams == 0:
        print("[ATTENZIONE] Nessun flusso valido trovato.")

if __name__ == "__main__":
    asyncio.run(generate_m3u8())

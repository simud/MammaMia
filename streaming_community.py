from bs4 import BeautifulSoup
from Src.Utilities.convert import get_TMDb_id_from_IMDb_id
from Src.Utilities.info import get_info_tmdb, is_movie, get_info_imdb
import Src.Utilities.config as config
import json
import random
import re
from urllib.parse import urlparse, parse_qs
from fake_headers import Headers  
from Src.Utilities.loadenv import load_env  
import urllib.parse

env_vars = load_env()
SC_DOMAIN = config.SC_DOMAIN
Public_Instance = config.Public_Instance
Alternative_Link = env_vars.get('ALTERNATIVE_LINK')

headers = Headers()
async def get_version(client):
    try:
        random_headers = headers.generate()
        random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
        random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
        base_url = f'https://streamingcommunity.{SC_DOMAIN}/richiedi-un-titolo' 
        response = await client.get(base_url, headers=random_headers, allow_redirects=True, impersonate="chrome120")
        soup = BeautifulSoup(response.text, "lxml")
        version = json.loads(soup.find("div", {"id": "app"}).get("data-page"))['version']
        return version
    except Exception as e:
        print("Couldn't find the version", e)
        version = "65e52dcf34d64173542cd2dc6b8bb75b"
        return version

async def search(query, date, ismovie, client, SC_FAST_SEARCH):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['Accept'] = 'application/json'
    random_headers['Content-Type'] = 'application/json'
    response = await client.get(query, headers=random_headers, allow_redirects=True)
    print(response)
    response = response.json()
    for item in response['data']:
        tid = item['id']
        slug = item['slug']
        type = item['type']
        if type == "tv":
            type = 0
        elif type == "movie":
            type = 1
        if type == ismovie: 
            if SC_FAST_SEARCH == "0":
                random_headers = headers.generate()
                random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
                random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
                response = await client.get(f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}', headers=random_headers, allow_redirects=True, impersonate="chrome120")
                pattern = r'<div[^>]*class="features"[^>]*>.*?<span[^>]*>(.*?)<\/span>'
                match = re.search(pattern, response.text)
                print(match.group(1).split("-")[0])
                first_air_year = match.group(1).split("-")[0]
                date = int(date)
                first_air_year = int(first_air_year)
                if first_air_year == date:
                    return tid, slug
            elif SC_FAST_SEARCH == "1":
                return tid, slug
        else:
            print("Couldn't find anything")

async def get_film(tid, version, client):  
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    url = f'https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}'
    response = await client.get(url, headers=random_headers, allow_redirects=True, impersonate="chrome120")
    iframe = BeautifulSoup(response.text, 'lxml')
    iframe = iframe.find('iframe').get("src")
    vixid = iframe.split("/embed/")[1].split("?")[0]
    parsed_url = urlparse(iframe)
    query_params = parse_qs(parsed_url.query)
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    resp = await client.get(iframe, headers=random_headers, allow_redirects=True, impersonate="chrome120")
    soup = BeautifulSoup(resp.text, "lxml")
    script = soup.find("body").find("script").text
    token = re.search(r"'token':\s*'(\w+)'", script).group(1)
    expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
    quality = re.search(r'"quality":(\d+)', script).group(1)
    url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
    if 'canPlayFHD' in query_params:
        canPlayFHD = 'h=1'
        url += "&h=1"
    if 'b' in query_params:
        b = 'b=1'
        url += "&b=1"
    url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
    return url, url720, quality

async def get_season_episode_id(tid, slug, season, episode, version, client):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    response = await client.get(f'https://streamingcommunity.{SC_DOMAIN}/titles/{tid}-{slug}/stagione-{season}', headers=random_headers, allow_redirects=True, impersonate="chrome120")
    json_response = response.json().get('props', {}).get('loadedSeason', {}).get('episodes', [])
    for dict_episode in json_response:
        if dict_episode['number'] == episode:
            return dict_episode['id']

async def get_episode_link(episode_id, tid, version, client):
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    params = {
        'episode_id': episode_id, 
        'next_episode': '1'
    }
    response = await client.get(f"https://streamingcommunity.{SC_DOMAIN}/iframe/{tid}", params=params, headers=random_headers, allow_redirects=True, impersonate="chrome120")
    soup = BeautifulSoup(response.text, "lxml")
    iframe = soup.find("iframe").get("src")
    vixid = iframe.split("/embed/")[1].split("?")[0]
    random_headers = headers.generate()
    random_headers['Referer'] = f"https://streamingcommunity.{SC_DOMAIN}/"
    random_headers['Origin'] = f"https://streamingcommunity.{SC_DOMAIN}"
    random_headers['x-inertia'] = "true"
    random_headers['x-inertia-version'] = version
    parsed_url = urlparse(iframe)
    query_params = parse_qs(parsed_url.query)
    resp = await client.get(iframe, headers=random_headers, allow_redirects=True, impersonate="chrome120")
    soup = BeautifulSoup(resp.text, "lxml")
    script = soup.find("body").find("script").text
    token = re.search(r"'token':\s*'(\w+)'", script).group(1)
    expires = re.search(r"'expires':\s*'(\d+)'", script).group(1)
    quality = re.search(r'"quality":(\d+)', script).group(1)
    url = f'https://vixcloud.co/playlist/{vixid}.m3u8?token={token}&expires={expires}'
    if 'canPlayFHD' in query_params:
        canPlayFHD = 'h=1'
        url += "&h=1"
    if 'b' in query_params:
        b = 'b=1'
        url += "&b=1"
    url720 = f'https://vixcloud.co/playlist/{vixid}.m3u8'
    return url, url720, quality

async def streaming_community(imdb, client, SC_FAST_SEARCH):
    try:
        if Public_Instance == "1":
            Weird_Link = json.loads(Alternative_Link)
            link_post = random.choice(Weird_Link)
            response = await client.get(f"{link_post}fetch-data/{SC_FAST_SEARCH}/{SC_DOMAIN}/{imdb}")
            url_streaming_community = response.headers.get('x-url-streaming-community')
            url_720_streaming_community = response.headers.get('x-url-720-streaming-community')
            quality_sc = response.headers.get('x-quality-sc')
            print(quality_sc, url_streaming_community)
            return url_streaming_community, url_720_streaming_community, quality_sc
        general = is_movie(imdb)
        ismovie = general[0]
        imdb_id =.calls[1]
        if ismovie == 0: 
            season = int(general[2])
            episode = int(general[3])
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                if "tt" in imdb:
                    showname = "Placeholder Title"  # Titolo fornito da CONTENT_LIST
                    date = None
                else:
                    date = None
                    tmdba = imdb_id.replace("tmdb:", "")
                    showname = "Placeholder Title"
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                tmdba = await get_TMDb_id_from_IMDb_id(imdb_id, client)
                showname, date = ("Placeholder Title", None) 
        else:
            if SC_FAST_SEARCH == "1":
                type = "StreamingCommunityFS"
                if "tt" in imdb:
                    date = None
                    showname = "Placeholder Title"
                else:
                    date = None
                    tmdba = imdb_id.replace("tmdb:", "")
                    showname = "Placeholder Title" 
            elif SC_FAST_SEARCH == "0":
                type = "StreamingCommunity"
                if "tt" in imdb:
                    showname, date = ("Placeholder Title", None)
                else:
                    tmdba = imdb_id.replace("tmdb:", "")
                    showname, date = ("Placeholder Title", None) 
        
        showname = showname.replace(" ", "+").replace("–", "+").replace("—", "+")
        showname = urllib.parse.quote_plus(showname)
        query = f'https://streamingcommunity.{SC_DOMAIN}/api/search?q={showname}'
        version = await get_version(client)
        tid, slug = await search(query, date, ismovie, client, SC_FAST_SEARCH)
        if ismovie == 1:
            url, url720, quality = await get_film(tid, version, client)
            print("MammaMia found results for StreamingCommunity")
            return url, url720, quality
        if ismovie == 0:
            episode_id = await get_season_episode_id(tid, slug, season, episode, version, client)
            url, url720, quality = await get_episode_link(episode_id, tid, version, client)
            print("MammaMia found results for StreamingCommunity")
            return url, url720, quality
    except Exception as e:
        print("MammaMia: StreamingCommunity failed", e)
        return None, None, None

import Src.Utilities.config as config
import json

def get_info_tmdb(tmbda, ismovie, type):
    # Senza TMDb, assumiamo che il titolo sia fornito altrove
    # Per StreamingCommunityFS, restituiamo un titolo placeholder
    if type == "StreamingCommunityFS":
        return "Placeholder Title"
    # Per StreamingCommunity, non usiamo la data
    return "Placeholder Title", None

async def get_info_imdb(imdb_id, ismovie, type, client):
    # Senza TMDb, assumiamo che il titolo sia fornito altrove
    if type == "StreamingCommunityFS":
        return "Placeholder Title"
    return "Placeholder Title", None

async def get_info_kitsu(kitsu_id, client):
    # Non usato in streaming_community, lasciato invariato
    api_url = f'https://kitsu.io/api/edge/anime/{kitsu_id}'
    response = await client.get(api_url)
    data = json.loads(response.text)
    showname = data['data']['attributes']['canonicalTitle']
    date = data['data']['attributes']['startDate']
    return showname, date

def is_movie(imdb_id):
    if "tmdb:" in imdb_id:
        imdb_id = imdb_id.replace("tmdb:", "")
    if ":" in imdb_id:
        season = imdb_id.split(":")[1]
        episode = imdb_id.split(":")[-1]
        ismovie = 0
        imdb_id = imdb_id.split(":")[0]
        return ismovie, imdb_id, season, episode
    else:
        ismovie = 1
        return ismovie, imdb_id

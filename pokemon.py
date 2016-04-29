'''
pokemon.py -- a hangoutsbot plugin for retrieving information about pokemon, given a name
This uses the pokeapi.co API to retrieve the information.

Because Pokéapi limits requests to 300 requests per method, we store cached data for each Pokémon for 5 days - this should be sufficient for up to 1500 Pokémon overall. Currently there are approximately 811 Pokémon accessible through the Pokéapi so this should be more than enough.
'''
import hangups, plugins, asyncio, logging, datetime
import urllib.request
import json
import aiohttp, os, io

logger = logging.getLogger(__name__)

def _initialise(bot):
  plugins.register_admin_command(["clearpokedex"])
  plugins.register_user_command(["pokedex"])

@asyncio.coroutine
def clearpokedex(bot, event):
  '''Clear the cached pokedex - useful when the data seems outdated.'''
  bot.memory.set_by_path(["pokedex"], {})
  yield from bot.coro_send_message(event.conv, "Pokedex cache cleared")

def getfromcache(bot, pokemonname):
  if not bot.memory.exists(["pokedex"]):
    bot.memory.set_by_path(["pokedex"], {})
  
  if not bot.memory.exists(["pokedex", pokemonname]):
    logger.info("{} not in cache.".format(pokemonname))
    return None
  else:
    try:
      if bot.memory.get_by_path(["pokedex", pokemonname, "expires"]) < str(datetime.datetime.now()):
        logger.info("Cached data for {} expired.".format(pokemonname))
        return None
    except:
      logger.info("No cache timestamp for {} available.".format(pokemonname))
      return None

    return bot.memory.get_by_path(["pokedex", pokemonname])

  return

def cachepkmn(bot, pkmndata, name):
  if not bot.memory.exists(["pokedex"]):
    bot.memory.set_by_path(["pokedex"], {})
  
  bot.memory.set_by_path(["pokedex", name], {"id":pkmndata["id"],"types":pkmndata["types"],"expires": str(datetime.datetime.now() + datetime.timedelta(days=5))})
  logger.info("Writing {} into cache".format(name))
  return

@asyncio.coroutine
def pokedex(bot, event, pokemon):
  '''Returns the number and types of a pokemon'''
  if pokemon.isdigit(): return
  url = "http://pokeapi.co/api/v2/pokemon/{}/".format(pokemon.lower())
  request = urllib.request.Request(url, headers = {"User-agent":"Mozilla/5.0"})
  cache = getfromcache(bot, pokemon.lower())

  if cache:
    logger.info("Found {} in cache".format(pokemon.lower()))
    data = cache
  else:
    logger.info("{} not found in cache OR cache expired, getting from pokeapi".format(pokemon.capitalize()))
    logger.info(cache)
    try:
      data = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
    except:
      yield from bot.coro_send_message(event.conv, "{}: Pokemon not found".format(event.user.full_name))
      return

    cachepkmn(bot, data, pokemon.lower())

  pkmn = "<b><a href='http://pokemondb.net/pokedex/{}'>{}</a></b> (#{})".format(pokemon.lower(),pokemon.capitalize(),data["id"])
  pkmn = pkmn + "<br>Type: <a href='http://pokemondb.net/type/{}'>{}</a>".format(data['types'][0]["type"]["name"],data['types'][0]["type"]["name"].capitalize())
  if len(data['types']) > 1 :
    pkmn = pkmn + " / <a href='http://pokemondb.net/type/{}'>{}</a>".format(data['types'][1]["type"]["name"],data['types'][1]["type"]["name"].capitalize())

  link_image = "http://img.pokemondb.net/artwork/{}.jpg".format(pokemon.lower())

  filename = os.path.basename(link_image)
  r = yield from aiohttp.request('get', link_image)
  raw = yield from r.read()
  image_data = io.BytesIO(raw)
  image_id = yield from bot._client.upload_image(image_data, filename=filename)
  yield from bot.coro_send_message(event.conv, pkmn, image_id=image_id)

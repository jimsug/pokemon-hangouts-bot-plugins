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

def comparetypes(data1, data2):
  weak1 = [x['name'] for x in data1['damage_relations']['double_damage_from']]
  weak2 = [x['name'] for x in data2['damage_relations']['double_damage_from']]
  resist1 = [x['name'] for x in data1['damage_relations']['half_damage_from']]
  resist2 = [x['name'] for x in data2['damage_relations']['half_damage_from']]
  immune1 = [x['name'] for x in data1['damage_relations']['no_damage_from']]
  immune2 = [x['name'] for x in data2['damage_relations']['no_damage_from']]
  immune = set(immune1).union(immune2)
  four = set(weak1).intersection(weak2).difference(immune)
  quarter = set(resist1).intersection(resist2).difference(immune)
  two = set(weak1).symmetric_difference(weak2).difference(set(resist1).symmetric_difference(resist2)).difference(immune)
  half = ((set(resist1).symmetric_difference(resist2)).difference(set(weak1).symmetric_difference(weak2))).difference(immune)
  matchup = {'4x':four,'2x':two,'1/2':half,'1/4':quarter,'immune':immune}
  return matchup
  
@asyncio.coroutine
def clearpokedex(bot, event):
  '''Clear the cached pokedex - useful when the data seems outdated.'''
  bot.memory.set_by_path(["pokedex"], {})
  yield from bot.coro_send_message(event.conv, "Pokedex cache cleared")

def gettypefromcache(bot, pkmntype):
  if not bot.memory.exists(["pokedex", "pokemontypes"]):
    bot.memory.set_by_path(["pokedex", "pokemontypes"], {})
    return None
  else:
    if not bot.memory.exists(["pokedex", "pokemontypes", pkmntype]):
      return None
    elif bot.get_by_path(["pokedex", "pokemontypes", pkmntype, "expires"]) < str(datetime.datetime.now()):
      logger.info("Cached data for {} type expired.".format(pkmntype))
      return None
    else:
      return bot.get_by_path(["pokedex","pokemontypes",pkmntype])

@asyncio.coroutine
def cachepkmntype(bot, pkmntypedata):
  if not bot.memory.exists(["pokedex", "pokemontypes"]):
    bot.memory.set_by_path(["pokedex", "pokemontypes"], {})
  
  bot.memory.set_by_path(["pokedex", "pokemontypes", pkmntypedata["name"]], {"name":pkmntypedata["name"],"damage_relations":pkmntypedata['damage_relations'],'expires':str(datetime.datetime.now() + datetime.timedelta(days=5))})
  logger.info("Writing {} type data into cache".format(pkmntypedata['name']))

def getpkmntype(bot, pkmntype):
  url = "http://pokeapi.co/api/v2/type/{}".format(pkmntype.lower())
  request = urllib.request.Request(url, headers = {"User-agent":"Mozilla/5.0"})
  try:
    data = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
  except:
    return None
  
  return data


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

def gettype(bot, pkmntype, logger):
  cache = gettypefromcache(bot, pkmntype)
  if cache:
    return cache
  else:
    typedata = getpkmntype(bot, pkmntype)
    if typedata:
      cachepkmntype(bot, typedata)

    return typedata
  return

@asyncio.coroutine
def pokedex(bot, event, pokemon):
  '''Returns the number, types, weaknesses and image of a pokemon'''
  if pokemon.isdigit(): return
  url = "http://pokeapi.co/api/v2/pokemon/{}/".format(pokemon.lower())
  request = urllib.request.Request(url, headers = {"User-agent":"Mozilla/5.0"})
  cache = getfromcache(bot, pokemon.lower())

  if cache:
    logger.info("Found {} in cache".format(pokemon.lower()))
    data = cache
    pkmn = "<b><a href='http://pokemondb.net/pokedex/{}'>{}</a></b> [#{}]".format(pokemon.lower(),pokemon.capitalize(),data["id"])
  else:
    logger.info("{} not found in cache OR cache expired, getting from pokeapi".format(pokemon.capitalize()))
    try:
      data = json.loads(urllib.request.urlopen(request).read().decode("utf-8"))
    except urllib.error.URLError as e:
      yield from bot.coro_send_message(event.conv, "{}: Error: {}".format(event.user.full_name, json.loads(e.read().decode("utf8","ignore"))['detail']))
      return

    cachepkmn(bot, data, pokemon.lower())
    pkmn = "<b><a href='http://pokemondb.net/pokedex/{}'>{}</a></b> (#{})".format(pokemon.lower(),pokemon.capitalize(),data["id"])

  type1 = gettype(bot, data['types'][0]['type']['name'], logger)
  pkmn = pkmn + "<br><b>Type</b>: <a href='http://pokemondb.net/type/{}'>{}</a>".format(data['types'][0]["type"]["name"],data['types'][0]["type"]["name"].capitalize())
  if len(data['types']) > 1 :
    type2 = gettype(bot, data['types'][1]['type']['name'], logger)
    pkmn = pkmn + " / <a href='http://pokemondb.net/type/{}'>{}</a>".format(data['types'][1]["type"]["name"],data['types'][1]["type"]["name"].capitalize())
    if type1 and type2:
      matchups = comparetypes(type1, type2)
  else:
    if type1:
      matchups = {'2x':type1['damage_relations']['double_damage_from'],'1/2':type1['damage_relations']['half_damage_from'],'immune':type1['damage_relations']['no_damage_from']}
  matches = ""
  
  if matchups:
    for x in matchups:
      if len(matchups[x]) > 0:
        matches = matches + "<br><b>{}</b>: ".format(x.capitalize())
        for y in matchups[x]:
          matches = matches + " <a href='http://pokemondb.net/type/{}'>{}</a>".format(y.lower(),y.capitalize())
  else:
    matches = "<i>Type matchups not currently available. Sorry :(</i>"

  pkmn = pkmn + matches
  link_image = "http://img.pokemondb.net/artwork/{}.jpg".format(pokemon.lower())
  filename = os.path.basename(link_image)
  r = yield from aiohttp.request('get', link_image)
  raw = yield from r.read()
  image_data = io.BytesIO(raw)
  image_id = yield from bot._client.upload_image(image_data, filename=filename)
  yield from bot.coro_send_message(event.conv, pkmn, image_id=image_id)

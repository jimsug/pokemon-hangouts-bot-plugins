# Pokemon Plugins for Hangoutsbot

A set of plugins for hangoutsbot/hangoutsbot.

Well, actually, just one, at the moment.

- pokemon.py:  
  - **/bot pokedex <pokemon-name>**: Uses the [pokeapi.co](pokeapi.co) API to get basic data on a specific Pokemon and gets images from [Pokebase](http://pokemondb.net/pokebase/)
  - **/bot clearpokedex**: Clears the Pokedex cache from memory. *(Admin only)* 

## To-do
### pokemon.py

- [ ] Indicate in some way whether the data used was fresh or cached
- [ ] Find some way to present type match-ups in a neat, concise manner
- [ ] Handle 5XX responses differently to 4XX responses
- [ ] Maybe some other options for data - blurb, sprite, etc. There's a lot of data available, may as well exploit it
- [ ] Change the type display to just type1/type2

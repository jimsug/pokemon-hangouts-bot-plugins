# Pokemon Plugins for Hangoutsbot

A set of plugins for hangoutsbot/hangoutsbot.

Well, actually, just one, at the moment.

## pokemon.py:  
  - **/bot pokedex <pokemon-name>**: Uses the [pokeapi.co](pokeapi.co) API to get basic data on a specific Pokemon and gets images from [Pokebase](http://pokemondb.net/pokebase/)
  - **/bot clearpokedex**: Clears the Pokedex cache from memory. *(Admin only)* 
  - **/bot pokemon nature <nature-name>**: Get basic data on a specified Pokemon nature as per [Bulbapedia](http://bulbapedia.bulbagarden.net/wiki/Nature#List_of_Natures)

### Configuration

```
`pokedex`:{
  'info':[
    'types',
    'ability
    ]
  }
```

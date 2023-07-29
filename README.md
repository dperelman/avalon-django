# avalon-django
`avalon-django` is a web-app implementation of the tabletop hidden-roles game
[The Resistance: Avalon](https://boardgamegeek.com/boardgame/128882/resistance-avalon)
powered by the Python web framework [Django](https://www.djangoproject.com/).

The impetus for implementing the game electronically was to speed up gameplay
by having the computer do the bookkeeping and (optionally) having the computer
display a history of public actions to reduce discussion about what had happened
so far in the game.


## How to play

Each player must have their own device (usually a smartphone, but any device
with a web browser will work) and go to the URL where the game is hosted.
(Feel free to
[play on my server](https://aweirdimagination.net/apps/avalon-django).)
When creating a game, a 6 letter game code will be generated to identify the
game for other players to join. Optionally, a shared device (e.g. a TV or
large tablet) may be setup as an "observer" to display the public data on
a common display (to make the game more social by avoiding everyone
constantly looking at their own phone). Once everyone has joined, follow
the on-screen instructions to play; the interface is made assuming everyone
already knows the basic game rules.


## Installation

TODO: Write more detail.

See the `deploy/awi` branch to see the configuration files used to
deploy this on https://avalon.aweirdimagination.net/

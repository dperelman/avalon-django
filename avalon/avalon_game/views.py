from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Game, Player

# helpers to interpret arguments
def lookup_access_code(func):
    def with_game(request, access_code, *args, **kwargs):
        game = get_object_or_404(Game, access_code=access_code)
        return func(request, game, *args, **kwargs)

    return with_game

def lookup_player_secret(func):
    def with_player(request, game, player_secret, *args, **kwargs):
        player = get_object_or_404(Player, game=game, secret_id=player_secret)
        return func(request, game, player, *args, **kwargs)

    return with_player


# views

def index(request):
    pass

def enter_code(request):
    pass

def new_game(request):
    pass

@lookup_access_code
def join_game(request, game):
    pass

@lookup_player_secret
@lookup_access_code
def game(request, game, player):
    pass

@lookup_player_secret
@lookup_access_code
def ready(request, game, player):
    pass

@lookup_player_secret
@lookup_access_code
def choose(request, game, player, round_num, vote_num, who):
    pass

@lookup_player_secret
@lookup_access_code
def remove(request, game, player, round_num, vote_num, who):
    pass

@lookup_player_secret
@lookup_access_code
def vote(request, game, player, round_num, vote_num, vote):
    pass

@lookup_player_secret
@lookup_access_code
def mission(request, game, player, round_num, mission_action):
    pass

@lookup_player_secret
@lookup_access_code
def assassinate(request, game, player, target):
    pass

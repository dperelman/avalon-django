from io import BytesIO
import json
import math
import random
import qrcode

from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_safe,\
                                         require_POST,\
                                         require_http_methods
from django.urls import reverse

from .forms import NewGameForm, JoinGameForm, StartGameForm
from .helpers import mission_size, mission_size_string
from .models import Game, GameRound, MissionAction,\
                    Player, PlayerVote, VoteRound

# helpers to interpret arguments
def lookup_access_code(func):
    def with_game(request, access_code, *args, **kwargs):
        game = get_object_or_404(Game, access_code=access_code.lower())
        return func(request, game, *args, **kwargs)

    return with_game

def lookup_player_secret(func):
    def with_player(request, game, player_secret, *args, **kwargs):
        player = get_object_or_404(Player, game=game, secret_id=player_secret)
        return func(request, game, player, *args, **kwargs)

    return with_player

def nums_to_int(func):
    def with_int(request, game, player, round_num, vote_num, *args, **kwargs):
        return func(request, game, player, int(round_num), int(vote_num),
                    *args, **kwargs)

    return with_int

# views

@require_safe
def index(request):
    return render(request, 'index.html')

@require_http_methods(["HEAD", "GET", "POST"])
def enter_code(request):
    if request.method == 'POST':
        form = JoinGameForm(request.POST)
        if form.is_valid():
            game = form.cleaned_data.get('game')
            player = form.cleaned_data.get('player')
            return redirect('game',
                            access_code=game.access_code,
                            player_secret=player.secret_id)
    else:
        form = JoinGameForm()

    return render(request, 'join_game.html', {'form': form})

@require_http_methods(["HEAD", "GET", "POST"])
def new_game(request):
    if request.method == 'POST':
        form = NewGameForm(request.POST)
        if form.is_valid():
            game = Game.objects.create()
            name = form.cleaned_data.get('name')
            player = Player.objects.create(game=game, name=name)
            return redirect('game',
                            access_code=game.access_code,
                            player_secret=player.secret_id)
    else:
        form = NewGameForm()

    return render(request, 'new_game.html', {'form': form})

@lookup_access_code
@require_safe
def join_game(request, game):
    form = JoinGameForm(initial={'game': game.access_code})
    return render(request, 'join_game.html', {'access_code': game.access_code,
                                              'form': form})

@lookup_access_code
@require_safe
def qr_code(request, game):
    join_url = reverse('join_game', kwargs={'access_code': game.access_code})
    join_url = request.build_absolute_uri(join_url)
    img = qrcode.make(join_url)
    output = BytesIO()
    img.save(output, "PNG")
    return HttpResponse(output.getvalue(), content_type='image/png')


def game_status_string(game, player):
    game_status_object = {}

    game_status_object['game_phase'] = game.game_phase_string()

    players = game.player_set.order_by('order', 'joined', 'name')
    num_players = players.count()

    if game.game_phase == Game.GAME_PHASE_LOBBY:
        game_status_object['players'] = [p.name for p in players]
    elif game.game_phase == Game.GAME_PHASE_ROLE:
        game_status_object['times_started'] = game.times_started
        ready_players = game.player_set.filter(ready=True).order_by('order')
        game_status_object['ready'] = [{'name': p.name, 'order': p.order}
                                       for p in ready_players]
    else:
        vote_round = VoteRound.objects.get_current_vote_round(game)
        game_status_object['round_num'] = vote_round.game_round.round_num
        game_status_object['vote_num'] = vote_round.vote_num
    if game.game_phase == Game.GAME_PHASE_PICK\
            or game.game_phase == Game.GAME_PHASE_VOTE:
        chosen = vote_round.chosen.order_by('order').all()
        game_status_object['chosen'] = [p.name for p in chosen]
        game_status_object['you_chosen'] = player in chosen
    if game.game_phase == Game.GAME_PHASE_VOTE:
        votes_cast = vote_round.playervote_set.count()
        game_status_object['missing_votes_count'] = num_players - votes_cast
        player_vote = vote_round.playervote_set.filter(player=player)
        if player_vote:
            if player_vote.get().accept:
                game_status_object['player_vote'] = 'accept'
            else:
                game_status_object['player_vote'] = 'reject'
        else:
            game_status_object['player_vote'] = 'none'

    return json.dumps(game_status_object)

@lookup_access_code
@lookup_player_secret
@require_safe
@transaction.non_atomic_requests
def status(request, game, player):
    player.save()

    return HttpResponse(game_status_string(game, player))

def game_base_context(game, player):
    players = game.player_set.order_by('order', 'joined', 'name')
    num_players = players.count()

    context = {}

    context['status'] = game_status_string(game, player)
    context['access_code'] = game.access_code
    context['player_secret'] = player.secret_id
    context['players'] = players
    context['player'] = player
    context['num_players'] = num_players
    context['game_rounds'] = game.gameround_set.all().order_by('round_num')

    if game.display_history is not None:
        context['display_history'] = game.display_history

    try:
        round_scores = {}
        for round_num in range(1, 6):
            round_scores[round_num] = {'mission_size': mission_size_string(mission_size(num_players=num_players, round_num=round_num)), 'result': ''}
        for game_round in game.gameround_set.all():
            round_scores[game_round.round_num]['result'] = game_round.result_string()
        context['round_scores'] = round_scores
    except ValueError:
        pass

    if game.game_phase != Game.GAME_PHASE_LOBBY:
        context['game_has_mordred'] = players.filter(role=Player.ROLE_MORDRED)\
                                             .exists()
        context['visible_spies'] = [p for p in players
                                    if player.sees_as_spy(p)]
        if player.is_percival():
            possible_merlins = " or ".join([p.name for p in players
                                            if p.appears_as_merlin()])
            context['possible_merlins'] = possible_merlins

    return context

def deterministic_random_boolean(seed):
    r = random.getstate()
    random.seed(seed)
    res = random.choice([True, False])
    random.setstate(r)
    return res

@lookup_access_code
@lookup_player_secret
@require_safe
def game(request, game, player):
    player.save() # update last_accessed

    context = game_base_context(game, player)

    if game.game_phase == Game.GAME_PHASE_LOBBY:
        context['form'] = StartGameForm()
        return render(request, 'lobby.html', context)
    elif game.game_phase == Game.GAME_PHASE_ROLE:
        context['times_started'] = game.times_started
        return render(request, 'role_phase.html', context)
    elif game.game_phase == Game.GAME_PHASE_PICK:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        assert vote_round.vote_status == VoteRound.VOTE_STATUS_WAITING
        context['chosen'] = vote_round.chosen.order_by('order').all()
        context['vote_rejected'] = not vote_round.is_first_vote()
        context['leader'] = vote_round.leader
        context['round_num'] = vote_round.game_round.round_num
        context['vote_num'] = vote_round.vote_num
        context['team_size'] = vote_round.game_round.num_players_on_mission()
        if vote_round.leader == player:
            return render(request, 'pick.html', context)
        else:
            return render(request, 'pick_wait.html', context)
    elif game.game_phase == Game.GAME_PHASE_VOTE:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        assert vote_round.vote_status == VoteRound.VOTE_STATUS_VOTING
        context['chosen'] = vote_round.chosen.order_by('order').all()
        context['leader'] = vote_round.leader
        round_num = vote_round.game_round.round_num
        context['round_num'] = round_num
        vote_num = vote_round.vote_num
        context['vote_num'] = vote_num
        player_vote = vote_round.playervote_set.filter(player=player)
        if player_vote:
            if player_vote.get().accept:
                context['player_vote'] = 'accept'
            else:
                context['player_vote'] = 'reject'
        player_votes = vote_round.playervote_set.count()
        num_players = context['num_players']
        context['missing_votes_count'] = num_players - player_votes
        seed = "%s-%s-%d-%d" % (game.access_code, player.secret_id,
                                round_num, vote_num)
        context['swap_buttons'] = deterministic_random_boolean(seed)
        return render(request, 'vote.html', context)
    elif game.game_phase == Game.GAME_PHASE_MISSION:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        assert vote_round.vote_status == VoteRound.VOTE_STATUS_VOTED
        chosen = vote_round.chosen.order_by('order').all()
        context['chosen'] = chosen
        context['leader'] = vote_round.leader
        round_num = vote_round.game_round.round_num
        context['round_num'] = round_num
        vote_num = vote_round.vote_num
        context['vote_num'] = vote_num
        if player in chosen:
            game_round = vote_round.game_round
            mission_action = game_round.missionaction_set.filter(player=player)
            if mission_action:
                if mission_action.get().played_success:
                    context['mission_action'] = 'Pass'
                else:
                    context['mission_action'] = 'Fail'
            seed = "%s-%s-%d-%d" % (game.access_code, player.secret_id,
                                    round_num, vote_num)
            context['swap_buttons'] = deterministic_random_boolean(seed)
            return render(request, 'mission.html', context)
        else:
            return render(request, 'mission_wait.html', context)
    elif game.game_phase == Game.GAME_PHASE_ASSASSIN:
        if player.is_assassin():
            context['targets'] = [p for p in context['players']
                                  if p != player and not player.sees_as_spy(p)]
            return render(request, 'assassinate.html', context)
        else:
            return render(request, 'assassinate_wait.html', context)
    elif game.game_phase == Game.GAME_PHASE_END:
        context['game_over'] = True
        res_wins = game.gameround_set.filter(mission_passed=True).count()
        res_won = res_wins == 3 and not game.player_assassinated.is_merlin()
        context['resistance_won'] = res_won

        if game.player_assassinated:
            context['player_assassinated'] = game.player_assassinated
        return render(request, 'end.html', context)

@lookup_access_code
@lookup_player_secret
@require_POST
def leave(request, game, player):
    player.delete()
    num_players = game.player_set.count()
    if num_players == 0:
        game.delete()
    return redirect('index')

@lookup_access_code
@lookup_player_secret
@require_POST
def start(request, game, player):
    player.save() # update last_accessed

    if game.game_phase != Game.GAME_PHASE_LOBBY:
        return redirect('game', access_code=game.access_code,
                        player_secret=player.secret_id)

    players = game.player_set.all()
    num_players = players.count()

    form = StartGameForm(request.POST)
    if num_players < 5:
        form.add_error(None, "You must have at least 5 players to play!")
    elif num_players > 10:
        form.add_error(None, "You can't have more than 10 players to play!")

    if form.is_valid():
        num_spies = int(math.ceil(num_players / 3.0))
        spy_roles = []
        if form.cleaned_data.get('assassin'):
            spy_roles.append(Player.ROLE_ASSASSIN)
        if form.cleaned_data.get('morgana'):
            spy_roles.append(Player.ROLE_MORGANA)
        if form.cleaned_data.get('mordred'):
            spy_roles.append(Player.ROLE_MORDRED)
        if form.cleaned_data.get('oberon'):
            spy_roles.append(Player.ROLE_OBERON)
        if len(spy_roles) > num_spies:
            form.add_error(None, "There will only be %d spies. Select no more than that many special roles for spies." % num_spies)
        else:
            game.display_history = form.cleaned_data.get('display_history')
            game.game_phase = Game.GAME_PHASE_ROLE
            game.times_started += 1

            resistance_roles = []
            if form.cleaned_data.get('merlin'):
                resistance_roles.append(Player.ROLE_MERLIN)
            if form.cleaned_data.get('percival'):
                resistance_roles.append(Player.ROLE_PERCIVAL)

            num_resistance = num_players - num_spies
            roles = spy_roles + resistance_roles +\
                    [Player.ROLE_SPY]*(num_spies - len(spy_roles)) +\
                    [Player.ROLE_GOOD]*(num_resistance - len(resistance_roles))
            assert len(roles) == num_players

            play_order = list(range(num_players))
            random.shuffle(play_order)
            random.shuffle(roles)

            for p, role, order in zip(players, roles, play_order):
                p.role = role
                p.order = order
                p.save()

            game.save()
            return redirect('game', access_code=game.access_code,
                            player_secret=player.secret_id)
    context = game_base_context(game, player)
    context['form'] = form

    return render(request, 'lobby.html', context)

@lookup_access_code
@lookup_player_secret
@require_POST
def cancel_game(request, game, player):
    if game.game_phase == Game.GAME_PHASE_ROLE:
        player.ready = False
        player.save()

        game.game_phase = Game.GAME_PHASE_LOBBY
        game.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@require_POST
def ready(request, game, player):
    if game.game_phase == Game.GAME_PHASE_ROLE:
        player.ready = True
        player.save()

        if not game.player_set.filter(ready=False):
            game.game_phase = Game.GAME_PHASE_PICK
            game.save()
            game_round = GameRound.objects.create(game=game, round_num=1)
            first_leader = Player.objects.get(game=game, order=0)
            vote_round = VoteRound.objects.create(game_round=game_round,
                                                  vote_num=1,
                                                  leader=first_leader)

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@nums_to_int
@require_POST
def choose(request, game, player, round_num, vote_num, who):
    player.save()

    if game.game_phase == Game.GAME_PHASE_PICK:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        if vote_round.vote_status == VoteRound.VOTE_STATUS_WAITING\
                and vote_round.game_round.round_num == round_num\
                and vote_round.vote_num == vote_num\
                and vote_round.leader == player:
            chosen_player = game.player_set.get(order=who)
            vote_round.chosen.add(chosen_player)
            vote_round.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@nums_to_int
@require_POST
def unchoose(request, game, player, round_num, vote_num, who):
    player.save()

    if game.game_phase == Game.GAME_PHASE_PICK:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        if vote_round.vote_status == VoteRound.VOTE_STATUS_WAITING\
                and vote_round.game_round.round_num == round_num\
                and vote_round.vote_num == vote_num\
                and vote_round.leader == player:
            chosen_player = game.player_set.get(order=who)
            vote_round.chosen.remove(chosen_player)
            vote_round.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@nums_to_int
@require_POST
def finalize_team(request, game, player, round_num, vote_num):
    player.save()

    if game.game_phase == Game.GAME_PHASE_PICK:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        if vote_round.vote_status == VoteRound.VOTE_STATUS_WAITING\
                and vote_round.game_round.round_num == round_num\
                and vote_round.vote_num == vote_num\
                and vote_round.leader == player\
                and vote_round.is_chosen_correct_size():
            vote_round.vote_status = VoteRound.VOTE_STATUS_VOTING
            vote_round.save()
            game.game_phase = Game.GAME_PHASE_VOTE
            game.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@nums_to_int
@require_POST
def retract_team(request, game, player, round_num, vote_num):
    player.save()

    if game.game_phase == Game.GAME_PHASE_VOTE:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        if vote_round.vote_status == VoteRound.VOTE_STATUS_VOTING\
                and vote_round.game_round.round_num == round_num\
                and vote_round.vote_num == vote_num\
                and vote_round.leader == player:
            vote_round.vote_status = VoteRound.VOTE_STATUS_WAITING
            vote_round.save()
            game.game_phase = Game.GAME_PHASE_PICK
            game.save()
            vote_round.playervote_set.all().delete()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@nums_to_int
@require_POST
def vote(request, game, player, round_num, vote_num, vote):
    player.save()

    if game.game_phase == Game.GAME_PHASE_VOTE:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        if vote_round.vote_status == VoteRound.VOTE_STATUS_VOTING\
                and vote_round.game_round.round_num == round_num\
                and vote_round.vote_num == vote_num:
            if vote == "cancel":
                try:
                    vote_round.playervote_set.get(player=player).delete()
                except PlayerVote.DoesNotExist:
                    pass
            else:
                accept = vote == "approve"
                vote_round.playervote_set\
                          .update_or_create(defaults={'accept': accept},
                                            player=player)
                team_approved = vote_round.team_approved()
                if team_approved is not None:
                    # All players voted, voting round is over.
                    vote_round.vote_status = VoteRound.VOTE_STATUS_VOTED
                    vote_round.save()
                    if team_approved:
                        # Team was approved
                        game.game_phase = Game.GAME_PHASE_MISSION
                    else:
                        # Team was rejected
                        if vote_round.is_final_vote():
                            game.game_phase = Game.GAME_PHASE_END
                        else:
                            game.game_phase = Game.GAME_PHASE_PICK
                            VoteRound.objects\
                                     .create(game_round=vote_round.game_round,
                                             vote_num=vote_round.vote_num+1,
                                             leader=vote_round.next_leader())
                game.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@require_POST
def mission(request, game, player, round_num, mission_action):
    round_num = int(round_num)

    player.save()

    if game.game_phase == Game.GAME_PHASE_MISSION:
        vote_round = VoteRound.objects.get_current_vote_round(game=game)
        game_round = vote_round.game_round
        if vote_round.vote_status == VoteRound.VOTE_STATUS_VOTED\
                and game_round.round_num == round_num\
                and player in vote_round.chosen.all():
            passed = mission_action == "success" or not player.is_spy()
            game_round.missionaction_set\
                      .update_or_create(defaults={'played_success': passed},
                                        player=player)
            num_on_mission = game_round.num_players_on_mission()
            if game_round.missionaction_set.count() == num_on_mission:
                num_fails_required = game_round.num_fails_required()
                fails = game_round.missionaction_set\
                                  .filter(played_success=False).count()
                game_round.mission_passed = fails < num_fails_required
                game_round.save()
                res_wins = game.gameround_set.filter(mission_passed=True)\
                                             .count()
                spy_wins = game.gameround_set.filter(mission_passed=False)\
                                             .count()
                if res_wins == 3:
                    # resistance wins... except for assassin
                    game.game_phase = Game.GAME_PHASE_ASSASSIN
                    game.save()
                elif spy_wins == 3:
                    # spies win
                    game.game_phase = Game.GAME_PHASE_END
                    game.save()
                else:
                    # another round
                    game.game_phase = Game.GAME_PHASE_PICK
                    game.save()
                    next_round_num = game_round.round_num+1
                    game_round = GameRound.objects\
                                          .create(game=game,
                                                  round_num=next_round_num)
                    next_leader = vote_round.next_leader()
                    vote_round = VoteRound.objects\
                                          .create(game_round=game_round,
                                                  vote_num=1,
                                                  leader=next_leader)

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

@lookup_access_code
@lookup_player_secret
@require_POST
def assassinate(request, game, player, target):
    player.save()

    if game.game_phase == Game.GAME_PHASE_ASSASSIN\
            and player.is_assassin():
        target_player = game.player_set.get(order=target)
        game.player_assassinated = target_player
        game.game_phase = Game.GAME_PHASE_END
        game.save()

    return redirect('game', access_code=game.access_code,
                    player_secret=player.secret_id)

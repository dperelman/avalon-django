from __future__ import unicode_literals

from datetime import datetime, timedelta
import random
import string

from django.db import models
from django.utils import timezone

from .helpers import mission_size, mission_size_string

def generate_code(length):
    return "".join([random.choice(string.ascii_lowercase)
                    for i in range(length)])

class Game(models.Model):
    ACCESS_CODE_LENGTH = 6
    access_code = models.CharField(db_index=True, unique=True,
                                   max_length=ACCESS_CODE_LENGTH)
    GAME_PHASE_LOBBY = 0
    GAME_PHASE_ROLE = 1
    GAME_PHASE_PICK = 2
    GAME_PHASE_VOTE = 3
    GAME_PHASE_MISSION = 4
    GAME_PHASE_ASSASSIN = 5
    GAME_PHASE_END = 6
    game_phase = models.IntegerField(default=GAME_PHASE_LOBBY)
    times_started = models.IntegerField(null=False, default=0)
    display_history = models.NullBooleanField()
    player_assassinated = models.ForeignKey('Player', null=True, default=None,
                                            related_name='+')
    created = models.DateTimeField()
    ended = models.DateTimeField(null=True, default=None)

    # from http://stackoverflow.com/a/11821832
    def save(self, *args, **kwargs):
        # object is being created, thus no primary key field yet
        if not self.pk:
            # Make sure access_code is unique before using it.
            access_code = generate_code(Game.ACCESS_CODE_LENGTH)
            while Game.objects.filter(access_code=access_code).exists():
                access_code = generate_code(Game.ACCESS_CODE_LENGTH)
            self.access_code = access_code
            self.created = timezone.now()
        if self.ended is None and self.game_phase == Game.GAME_PHASE_END:
            self.ended = timezone.now()
        super(Game, self).save(*args, **kwargs)

    _game_phase_strings = {
        GAME_PHASE_LOBBY: 'lobby',
        GAME_PHASE_ROLE: 'role',
        GAME_PHASE_PICK: 'pick',
        GAME_PHASE_VOTE: 'vote',
        GAME_PHASE_MISSION: 'mission',
        GAME_PHASE_ASSASSIN: 'assassin',
        GAME_PHASE_END: 'end',
    }
    def game_phase_string(self):
        return Game._game_phase_strings[self.game_phase]

    def num_players(self):
        return self.player_set.count()

class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    SECRET_ID_LENGTH = 8
    secret_id = models.CharField(db_index=True, max_length=SECRET_ID_LENGTH)
    name = models.CharField(max_length=80)
    ROLE_SPY = -1
    ROLE_ASSASSIN = -2
    ROLE_MORGANA = -3
    ROLE_MORDRED = -4
    ROLE_OBERON = -5
    ROLE_GOOD = 1
    ROLE_MERLIN = 2
    ROLE_PERCIVAL = 3
    role = models.IntegerField(null=True, default=None)
    order = models.IntegerField(null=True, default=None)
    ready = models.BooleanField(default=False)
    joined = models.DateTimeField()
    last_accessed = models.DateTimeField()
    # names are unique in a game
    unique_together = (("game", "name"), ("game", "secret_id"))

    def is_expired(self):
        return timezone.now() - self.last_accessed > timedelta(seconds=10)

    def change_secret_id(self):
        # Make sure secret_id is unique before using it.
        secret_id = generate_code(Player.SECRET_ID_LENGTH)
        while Player.objects.filter(game=self.game,
                                    secret_id=secret_id).exists():
            secret_id = generate_code(Player.SECRET_ID_LENGTH)
        self.secret_id = secret_id

    # from http://stackoverflow.com/a/11821832
    def save(self, *args, **kwargs):
        # object is being created, thus no primary key field yet
        if not self.pk:
            self.change_secret_id()
            self.joined = timezone.now()
        self.last_accessed = timezone.now()
        super(Player, self).save(*args, **kwargs)

    def is_spy(self):
        if self.role is None:
            return None
        elif self.role < 0:
            return True
        else:
            return False

    def team(self):
        if self.is_spy() is None:
            return None
        elif self.is_spy():
            return 'spy'
        else:
            return 'resistance'

    def role_string(self):
        if self.role is None:
            return None
        elif self.role == Player.ROLE_SPY:
            return "Minion of Mordred"
        elif self.role == Player.ROLE_ASSASSIN:
            return "Assassin"
        elif self.role == Player.ROLE_MORGANA:
            return "Morgana"
        elif self.role == Player.ROLE_MORDRED:
            return "Mordred"
        elif self.role == Player.ROLE_OBERON:
            return "Oberon"
        elif self.role == Player.ROLE_GOOD:
            return "Loyal servant of Arthur"
        elif self.role == Player.ROLE_MERLIN:
            return "Merlin"
        elif self.role == Player.ROLE_PERCIVAL:
            return "Percival"

    def is_oberon(self):
        return self.role == Player.ROLE_OBERON

    def is_merlin(self):
        return self.role == Player.ROLE_MERLIN

    def is_percival(self):
        return self.role == Player.ROLE_PERCIVAL

    def is_assassin(self):
        return self.role == Player.ROLE_ASSASSIN

    def is_morgana(self):
        return self.role == Player.ROLE_MORGANA

    def is_mordred(self):
        return self.role == Player.ROLE_MORDRED

    def sees_as_spy(self, other):
        if other.is_spy():
            if self.is_merlin() and not other.is_mordred():
                return True
            elif self.is_spy() and\
                    not self.is_oberon() and not other.is_oberon():
                return True
        return False

    def appears_as_merlin(self):
        return self.is_merlin() or self.is_morgana()

class GameRoundManager(models.Manager):
    def get_current_game_round(self, game):
        return self.filter(game=game).order_by('-round_num').first()

class GameRound(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    round_num = models.IntegerField()
    unique_together = (("game", "round_num"),)
    mission_passed = models.NullBooleanField()

    objects = GameRoundManager()

    def winner_string(self):
        if self.mission_passed is None:
            return ''
        elif self.mission_passed:
            return 'resistance'
        else:
            return 'spy'

    def result_string(self):
        if self.mission_passed is None:
            return ''
        elif self.mission_passed:
            return 'pass'
        else:
            return 'fail'

    def mission_size_tuple(self):
        num_players = Player.objects.filter(game=self.game).count()
        return mission_size(num_players=num_players,
                            round_num=self.round_num)

    def mission_size_string(self):
        return mission_size_string(self.mission_size_tuple())

    def num_players_on_mission(self):
        return self.mission_size_tuple()[0]

    def num_fails_required(self):
        return self.mission_size_tuple()[1]

    def num_fails(self):
        if self.mission_passed is None:
            return None
        else:
            return self.missionaction_set.filter(played_success=False).count()

    def played_fail(self):
        if self.mission_passed is None:
            return None
        else:
            fail_actions = self.missionaction_set.filter(played_success=False)
            return [action.player for action in fail_actions]

class MissionAction(models.Model):
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    unique_together = (("game", "player"),)
    played_success = models.BooleanField()

class VoteRoundManager(models.Manager):
    def get_current_vote_round(self, game=None, game_round=None):
        if game_round is None:
            game_round = GameRound.objects.get_current_game_round(game=game)
        return self.filter(game_round=game_round).order_by('-vote_num').first()

class VoteRound(models.Model):
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE, db_index=True)
    vote_num = models.IntegerField()
    unique_together = (("game_round", "vote_num"),)
    VOTE_STATUS_WAITING = 0
    VOTE_STATUS_VOTING = 1
    VOTE_STATUS_VOTED = 2
    vote_status = models.IntegerField(default=VOTE_STATUS_WAITING)
    leader = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='vote_round_leader')
    chosen = models.ManyToManyField(Player, related_name='vote_round_chosen')
    started = models.DateTimeField()
    chose_team = models.DateTimeField(null=True, default=None)
    voted = models.DateTimeField(null=True, default=None)

    objects = VoteRoundManager()

    def is_team_finalized(self):
        return self.vote_status != VoteRound.VOTE_STATUS_WAITING

    def is_waiting_on_leader(self):
        return self.vote_status == VoteRound.VOTE_STATUS_WAITING

    def is_currently_voting(self):
        return self.vote_status == VoteRound.VOTE_STATUS_VOTING

    def is_voting_complete(self):
        return self.vote_status == VoteRound.VOTE_STATUS_VOTED

    def is_first_vote(self):
        return self.vote_num == 1

    def is_chosen_correct_size(self):
        return self.chosen.count() == self.game_round.num_players_on_mission()

    def is_final_vote(self):
        return self.vote_num == 5

    def team_approved(self):
        num_players = self.game_round.game.num_players()
        if self.playervote_set.count() == num_players:
            accepts = self.playervote_set.filter(accept=True).count()
            rejects = num_players - accepts
            return accepts > rejects
        else:
            return None

    def next_leader(self):
        game = self.game_round.game
        num_players = Player.objects.filter(game=game).count()
        next_leader_order = (self.leader.order + 1) % num_players
        next_leader = Player.objects.get(game=game,
                                         order=next_leader_order)
        return next_leader

    def save(self, *args, **kwargs):
        # object is being created, thus no primary key field yet
        if not self.pk:
            # Make sure access_code is unique before using it.
            self.started = timezone.now()
        if self.vote_status == VoteRound.VOTE_STATUS_VOTING:
            self.chose_team = timezone.now()
        elif self.vote_status == VoteRound.VOTE_STATUS_VOTED:
            self.voted = timezone.now()
        super(VoteRound, self).save(*args, **kwargs)

class PlayerVote(models.Model):
    vote_round = models.ForeignKey(VoteRound, on_delete=models.CASCADE, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    unique_together = (("vote_round", "player"),)
    accept = models.BooleanField()

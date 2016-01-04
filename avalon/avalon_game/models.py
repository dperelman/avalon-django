from __future__ import unicode_literals

from datetime import datetime, timedelta
import random
import string

from django.db import models
from django.utils import timezone

def generate_code(length):
    return "".join([random.choice(string.ascii_lowercase)
                    for i in xrange(length)])

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
    display_history = models.NullBooleanField()
    player_assassinated = models.ForeignKey('Player', null=True, default=None,
                                            related_name='+')

    # from http://stackoverflow.com/a/11821832
    def save(self, *args, **kwargs):
        # object is being created, thus no primary key field yet
        if not self.pk:
            # Make sure access_code is unique before using it.
            access_code = generate_code(Game.ACCESS_CODE_LENGTH)
            while Game.objects.filter(access_code=access_code).exists():
                access_code = generate_code(Game.ACCESS_CODE_LENGTH)
            self.access_code = access_code
        super(Game, self).save(*args, **kwargs)

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

class GameRound(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    round_num = models.IntegerField()
    unique_together = (("game", "round_num"),)
    mission_passed = models.NullBooleanField()

    def winner_string(self):
        if self.mission_passed is None:
            return ''
        elif self.mission_passed:
            return 'resistance'
        else:
            return 'spy'

class MissionAction(models.Model):
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    unique_together = (("game", "player"),)
    played_success = models.NullBooleanField()

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

class PlayerVote(models.Model):
    vote_round = models.ForeignKey(VoteRound, on_delete=models.CASCADE, db_index=True)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    unique_together = (("vote_round", "player"),)
    accept = models.NullBooleanField()

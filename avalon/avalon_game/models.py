from __future__ import unicode_literals

from django.db import models

class Game(models.Model):
    access_key = models.CharField(db_index=True, unique=True, max_length=6)
    GAME_PHASE_LOBBY = 0
    GAME_PHASE_ROLE = 1
    GAME_PHASE_PICK = 2
    GAME_PHASE_VOTING = 3
    GAME_PHASE_MISSION = 4
    GAME_PHASE_ASSASSIN = 5
    GAME_PHASE_END = 6
    game_phase = models.IntegerField(default=GAME_PHASE_LOBBY)
    player_assassinated = models.ForeignKey('Player', related_name='+')

class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    secret_id = models.CharField(db_index=True, max_length=8)
    name = models.CharField(max_length=80)
    ROLE_SPY = -1
    ROLE_ASSASSIN = -2
    ROLE_MORGANA = -3
    ROLE_MORDRED = -4
    ROLE_OBERON = -5
    ROLE_GOOD = 1
    ROLE_MERLIN = 2
    ROLE_PERCIVAL = 3
    role = models.IntegerField()
    last_accessed = models.DateTimeField()
    # names are unique in a game
    unique_together = (("game", "name"), ("game", "secret_id"))

class GameRound(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    round_num = models.IntegerField()
    unique_together = (("game", "round_num"),)
    mission_passed = models.NullBooleanField()

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

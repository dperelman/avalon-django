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
    assassin_correct = models.NullBooleanField()
    resistance_won = models.NullBooleanField()

class Player(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    secret_id = models.CharField(db_index=True, max_length=8)
    name = models.CharField(max_length=80)
    last_accessed = models.DateTimeField()
    # names are unique in a game
    unique_together = (("game", "name"), ("game", "secret_id"))

class GameRound(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    round_num = models.IntegerField()
    unique_together = (("game", "round_num"),)
    mission_passed = models.NullBooleanField()
    # Record for end-game analysis
    failed = models.ManyToManyField(Player)
    passed = models.ManyToManyField(Player)
    #fails = models.IntegerField()

class MissionAction(models.Model):
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    unique_together = (("game", "player"),)
    played_success = models.NullBooleanField()

class VoteRound(models.Model):
    game_round = models.ForeignKey(GameRound, on_delete=models.CASCADE)
    vote_num = models.IntegerField()
    unique_together = (("game_round", "vote_num"),)
    VOTE_STATUS_WAITING = 0
    VOTE_STATUS_VOTING = 1
    VOTE_STATUS_VOTED = 2
    vote_status = models.IntegerField(default=VOTE_STATUS_WAITING)
    leader = models.ForeignKey(Player, on_delete=models.CASCADE)
    chosen = models.ManyToManyField(Player)
    approved = models.ManyToManyField(Player)

from django import forms

from .models import Game, Player

class NewGameForm(forms.Form):
    name = forms.CharField(label='Name', max_length=80, required=False)

    def clean(self):
        cleaned_data = super(NewGameForm, self).clean()

        name = cleaned_data.get("name")
        observer = 'observe' in self.data

        if observer and (name is None or len(name) > 0):
            self.add_error('name', "Only fill in 'Name' field if you will be playing (not observing) using this device.")
        elif not observer and len(name) == 0:
            self.add_error('name', "Player name must be non-empty (did you mean to click 'Create as observer'?).")

        if name is None or observer:
            cleaned_data["name"] = None

class JoinGameForm(forms.Form):
    game = forms.CharField(label='Access code',
                           max_length=Game.ACCESS_CODE_LENGTH)
    player = forms.CharField(label='Name', max_length=80, required=False)

    def clean_game(self):
        data = self.cleaned_data['game']

        try:
            return Game.objects.get(access_code=data.lower())
        except Game.DoesNotExist:
            raise forms.ValidationError("Invalid access code.")

    def clean(self):
        cleaned_data = super(JoinGameForm, self).clean()

        game = cleaned_data.get("game")
        name = cleaned_data.get("player")
        observer = 'observe' in self.data
        cleaned_data["observer"] = observer

        if game.game_phase == Game.GAME_PHASE_END:
            cleaned_data["player"] = None
            return

        if observer and (name is None or len(name) > 0):
            self.add_error('player', "Leave 'Name' field blank if observing or use 'Join' button to join as a player.")
        elif not observer and len(name) == 0:
            self.add_error('player', "Player name must be non-empty (did you mean to click 'Observe'?).")
            return

        if game is None or name is None or observer:
            cleaned_data["player"] = None
            return

        if game.previous_game is not None:
            try:
                player = Player.objects.get(game=game.previous_game, name=name)
                if not player.is_expired():
                    self.add_error('player', "Please choose a different name; there is already a player using that name.")
                    self.add_error('player', "Please try again in a few seconds if you are trying to rejoin.")
            except Player.DoesNotExist:
                pass

        try:
            player = Player.objects.get(game=game, name=name)
            if player.is_expired():
                player.change_secret_id();
                player.save()
                cleaned_data["player"] = player
            else:
                self.add_error('player', "Please choose a different name; there is already a player using that name.")
                self.add_error('player', "Please try again in a few seconds if you are trying to rejoin.")
        except Player.DoesNotExist:
            if game.game_phase == Game.GAME_PHASE_LOBBY:
                player = Player.objects.create(game=game, name=name)
                cleaned_data["player"] = player
            else:
                self.add_error('player', "That game has already started. If you want to rejoin, please enter your name exactly as you did before or select \"Observe\" if you just want to display the game status.")

class StartGameForm(forms.Form):
    display_history = forms.BooleanField(required=False, initial=True,
                                         label="show history table")
    merlin = forms.BooleanField(required=False, initial=True, label="Merlin")
    percival = forms.BooleanField(required=False, initial=True,
                                  label="Percival")
    assassin = forms.BooleanField(required=False, initial=True,
                                  label="Assassin")
    morgana = forms.BooleanField(required=False, initial=True, label="Morgana")
    mordred = forms.BooleanField(required=False, initial=False,
                                 label="Mordred")
    oberon = forms.BooleanField(required=False, initial=False, label="Oberon")

    def clean(self):
        cleaned_data = super(StartGameForm, self).clean()

        merlin = cleaned_data.get("merlin")
        percival = cleaned_data.get("percival")
        assassin = cleaned_data.get("assassin")
        morgana = cleaned_data.get("morgana")
        mordred = cleaned_data.get("mordred")

        if assassin and not merlin:
            self.add_error('assassin', "The assassin requires Merlin to be in the game.")
        if percival and not merlin:
            self.add_error('percival', "Percival requires Merlin to be in the game.")
        if morgana and (not merlin or not percival):
            self.add_error('morgana', "Morgana requies Merlin and Percival to be in the game.")
        if mordred and not merlin:
            self.add_error('mordred', "Mordred requires Merlin to be in the game.")

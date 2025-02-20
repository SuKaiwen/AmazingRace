import random
import string

from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.datetime_safe import datetime
from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    title = models.CharField(max_length=50)
    archived = models.BooleanField(default=False)
    code = models.TextField(max_length=100, unique=True)
    live = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    players = models.ManyToManyField(User)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):

        if self.start_time and self.end_time:
            self._refactor_input()
        if self.code == "":
            self._generate_code()
        return super(Game, self).save()

    """
        Code generator for the game
    """
    def _generate_code(self):
        game_codes = Game.objects.values_list('code')
        while True:
            unique = True
            code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            code = code[:4] + "-" + code[4:]
            for existing_code in game_codes:
                if code == existing_code:
                    unique = False
                    break
                else:
                    unique = True
            if unique:
                self.code = code
                return

    """
        Integrity checks for the times inside this class
    """
    def _refactor_input(self):

        if not self.start_time and not self.end_time:
            return

        elif self.end_time is None and self.start_time is not None:
            self.live = True if self.start_time <= datetime.now() else False
            self.archived = False

        if self.end_time.strftime('%Y-%m-%d %H:%M:%S') <= self.start_time.strftime('%Y-%m-%d %H:%M:%S'):
            self.end_time = None
            self.start_time = None
            self.live = False
            self.archived = False

        if self.start_time and self.start_time.strftime('%Y-%m-%d %H:%M:%S') > timezone.now().strftime(
                '%Y-%m-%d %H:%M:%S'):
            self.live = False
            self.archived = False
            self.end_time = None

        elif self.end_time is not None and self.end_time.strftime('%Y-%m-%d %H:%M:%S') <= timezone.now().strftime(
                '%Y-%m-%d %H:%M:%S'):
            self.live = False
            self.archived = True

        elif self.start_time is None or self.end_time is None:
            self.live = False
            self.live = False

        else:
            self.live = True
            self.archived = False


class GameCreator(models.Model):
    game = models.OneToOneField(Game, primary_key=True, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)


class Location(models.Model):
    name = models.TextField(max_length=20, validators=[MinLengthValidator(2)])
    clues = models.TextField(max_length=500, validators=[MinLengthValidator(2)])
    longitude = models.TextField()
    latitude = models.TextField()
    code = models.TextField(max_length=100)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    order = models.IntegerField()

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.code == "":
            self._generate_code()
        return super(Location, self).save()

    """
        Code generator for a new game
    """
    def _generate_code(self):
        location_codes = Location.objects.filter(game=self.game).values_list('code')
        while True:
            location_code = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            location_code = location_code[:4] + "-" + location_code[4:]
            if len(location_codes) == 0:
                self.code = location_code
                return
            for existing_code in location_codes:
                if location_code == existing_code:
                    break
                self.code = location_code
                return

    def __str__(self):
        return self.name


class LocationUser(models.Model):
    time_visited = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)


class GamePlayer(models.Model):
    rank = models.BigIntegerField()
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('game', 'player')

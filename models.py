"""This module contains classes and functions that are used in star battle game"""

# import
import math
import random
from superwires import games


# initialize game screen
games.init(screen_width=1024, screen_height=768, fps=50)


class Wrapper(games.Sprite):
    """ A model of a sprite that wraps around game screen"""

    def update(self):
        """Wraps sprite around game screen"""
        if self.top > games.screen.height:
            self.bottom = 0
        if self.bottom < 0:
            self.top = games.screen.height
        if self.left > games.screen.width:
            self.right = 0
        if self.right < 0:
            self.left = games.screen.width

    def die(self):
        """Destroys sprite"""
        self.destroy()


class Collider(Wrapper):
    """A model of a wrapper that can collide with other sprites"""

    def update(self):
        """Checks for overlapping sprites"""
        super().update()

        if self.overlapping_sprites:
            for sprite in self.overlapping_sprites:
                sprite.die()
                if sprite.name != 'gun_bonus':
                    self.die()
                elif sprite.name == 'gun_bonus' and self.name == 'ship':  # in case player's ship overlaps gun bonus
                    self.activate_gun_bonus()  # call 'activate_gun_bonus' method of player's ship object

    def die(self):
        """ Destroys sprite and leaves explosion behind"""
        new_explosion = Explosion(x=self.x, y=self.y)
        games.screen.add(new_explosion)
        super().die()


class Asteroid(Wrapper):
    """A model of an asteroid which floats across the game screen"""
    # possible asteroids sizes
    SMALL = 1
    MEDIUM = 2
    LARGE = 3
    images = {SMALL: games.load_image('./res/asteroid_small.bmp'),
              MEDIUM: games.load_image('./res/asteroid_med.bmp'),
              LARGE: games.load_image('./res/asteroid_big.bmp')}
    SPEED = 2  # basic asteroid speed
    SPAWN = 2  # how many smaller asteroids can a big one form when is destroyed
    POINTS = 30  # how many points do a player get when destroys an asteroid
    total = 0  # total number of created asteroids

    def __init__(self, game, x, y, size):
        """Initializes an asteroid sprite"""
        Asteroid.total += 1

        super().__init__(image=Asteroid.images[size], x=x, y=y,
                         dx=random.choice([1, -1]) * Asteroid.SPEED * random.random() / size,
                         dy=random.choice([1, -1]) * Asteroid.SPEED * random.random() / size)
        self.game = game
        self.size = size
        self.name = 'asteroid'

    def die(self):
        """Destroys an asteroid"""
        Asteroid.total -= 1
        self.game.score.value += int(Asteroid.POINTS / self.size)
        self.game.score.right = games.screen.width - 10
        self.game.score_legend.right = self.game.score.left - 5

        # if asteroid isn't small, replace it with two smaller asteroids
        if self.size != Asteroid.SMALL:
            for i in range(Asteroid.SPAWN):
                new_asteroid = Asteroid(game=self.game, x=self.x, y=self.y, size=self.size - 1)
                games.screen.add(new_asteroid)

        # if all asteroids are gone, advance to next level
        if Asteroid.total == 0:
            self.game.asteroid_aims = False
            self.game.advance()

        super().die()


class Ship(Collider):
    """A model of player's ship"""
    image = games.load_image('./res/ship1.png')
    sound = games.load_sound('./res/thrust.wav')
    ROTATION_STEP = 3
    VELOCITY_STEP = .05
    VELOCITY_MAX = 3
    MISSILE_DELAY = 25
    BONUS_DELAY = 15 * games.screen.fps  # how often do gun bonus appears in the game

    def __init__(self, game, x, y):
        """Initializes ship sprite"""
        super().__init__(image=Ship.image, x=x, y=y)
        self.game = game
        self.missile_wait = 0
        self.name = 'ship'
        self.gun_bonus_is_active = False
        self.gun_bonus_time = 0
        self.bonus_wait = Ship.BONUS_DELAY

    def update(self):
        """Rotates, thrusts and fires missiles based on keys pressed by player"""
        super().update()

        # rotate player's ship based on left and right arrow keys been pressed
        if games.keyboard.is_pressed(games.K_LEFT):
            self.angle -= Ship.ROTATION_STEP
        if games.keyboard.is_pressed(games.K_RIGHT):
            self.angle += Ship.ROTATION_STEP

        # apply thrust based on up arrow key
        if games.keyboard.is_pressed(games.K_UP):
            Ship.sound.play()

            # change velocity components based on ship's angle
            angle = self.angle * math.pi / 180  # convert into radians
            self.dx += Ship.VELOCITY_STEP * math.sin(angle)
            self.dy += Ship.VELOCITY_STEP * -math.cos(angle)

            # cap velocity in each direction
            self.dx = min(max(self.dx, -Ship.VELOCITY_MAX), Ship.VELOCITY_MAX)
            self.dy = min(max(self.dy, -Ship.VELOCITY_MAX), Ship.VELOCITY_MAX)

            # add jet stream animation
            new_jetstream = JetStream(self.x, self.y, self.angle)
            games.screen.add(new_jetstream)

        # if waiting until the ship can fire next, decrease wait
        if self.missile_wait > 0:
            self.missile_wait -= 1

        # fire missile if space bar is pressed and missile wait is over
        if games.keyboard.is_pressed(games.K_SPACE) and self.missile_wait == 0:
            if self.gun_bonus_is_active:
                missile_image = games.load_image('./res/missile_bonus1.bmp')
            else:
                missile_image = games.load_image('./res/missile.bmp')
            new_missile = Missile(missile_image, self.x, self.y, self.angle)
            games.screen.add(new_missile)
            self.missile_wait = Ship.MISSILE_DELAY

        if self.gun_bonus_time > 0:
            self.gun_bonus_time -= 1
        else:
            self.deactivate_gun_bonus()

        # if waiting until the next bonus, decrease wait
        if self.bonus_wait > 0:
            self.bonus_wait -= 1
        else:
            coords = random_coords(buffer=100, ship_current_x=self.x, ship_current_y=self.y,
                                   screen_width=games.screen.width, screen_height=games.screen.height)
            new_bonus = GunBonus(x=coords[0], y=coords[1])
            games.screen.add(new_bonus)
            self.bonus_wait = Ship.BONUS_DELAY

    def activate_gun_bonus(self):
        """Increases ship's firing rate"""
        self.gun_bonus_is_active = True
        self.gun_bonus_time = 10 * games.screen.fps
        Ship.MISSILE_DELAY = 8

    def deactivate_gun_bonus(self):
        """Decrease ship's firing rate"""
        self.gun_bonus_is_active = False
        Ship.MISSILE_DELAY = 25

    def die(self):
        """ Destroy ship and end the game. """
        self.game.end()
        super().die()


class Missile(Collider):
    """ A model of  a missile launched by the player's ship"""
    sound = games.load_sound('./res/missile.wav')
    BUFFER = 60  # guaranteed gap between player's ship and a missile it launches
    VELOCITY_FACTOR = 10
    LIFETIME = 25

    def __init__(self, image, ship_x, ship_y, ship_angle):
        """Initializes missile sprite"""
        Missile.sound.play()

        # convert angle to radians
        angle = ship_angle * math.pi / 180

        # calculate missile's starting position
        buffer_x = Missile.BUFFER * math.sin(angle)
        buffer_y = Missile.BUFFER * -math.cos(angle)
        x = ship_x + buffer_x
        y = ship_y + buffer_y

        # calculate missile's velocity components
        dx = Missile.VELOCITY_FACTOR * math.sin(angle)
        dy = Missile.VELOCITY_FACTOR * -math.cos(angle)

        # create the missile
        super().__init__(image=image, x=x, y=y, dx=dx, dy=dy)
        self.lifetime = Missile.LIFETIME
        self.name = 'missile'

    def update(self):
        """Moves the missile"""
        super().update()

        # if lifetime is up, destroy the missile
        self.lifetime -= 1
        if self.lifetime == 0:
            self.destroy()


class AlienShip(Wrapper):
    """A model of an alien ship which floats across the game screen"""
    images = ['./res/alienship1.png',
              './res/alienship2.png',
              './res/alienship3.png',
              './res/alienship4.png',
              './res/alienship5.png',
              './res/alienship6.png']
    SPEED = 1
    POINTS = 50  # how many points do player get when destroys alien ship
    ROTATION_STEP = 1
    total = 0  # how many alien ships have been created

    def __init__(self, game, x, y):
        """Initializes alien ship sprite"""
        AlienShip.total += 1
        super().__init__(image=games.load_image(random.choice(AlienShip.images)),
                         x=x, y=y,
                         dx=random.choice([1, -1]) * AlienShip.SPEED * random.random(),
                         dy=random.choice([1, -1]) * AlienShip.SPEED * random.random())
        self.game = game
        self.rotation_direction = random.choice([1, -1])
        self.armour = 2  # how many times player's ship have to hit the alien ship to destroy it
        self.name = 'alienship'

    def update(self):
        """Rotates alienship during it's flight"""
        super().update()
        self.angle += self.rotation_direction * AlienShip.ROTATION_STEP

    def die(self):
        """Destroys alienship"""
        self.armour -= 1

        if self.armour == 0:
            AlienShip.total -= 1
            self.game.score.value += int(AlienShip.POINTS)
            self.game.score.right = games.screen.width - 10
            self.game.score_legend.right = self.game.score.left - 5
            super().die()

        if AlienShip.total == 0:
            self.game.alienship_aims = False
            self.game.advance()


class Explosion(games.Animation):
    """A model of an explosion animation"""
    sound = games.load_sound('./res/explosion.wav')
    images = ['./res/explosion1.bmp',
              './res/explosion2.bmp',
              './res/explosion3.bmp',
              './res/explosion4.bmp',
              './res/explosion5.bmp',
              './res/explosion6.bmp',
              './res/explosion7.bmp',
              './res/explosion8.bmp',
              './res/explosion9.bmp']

    def __init__(self, x, y):
        super().__init__(images=Explosion.images, x=x, y=y, repeat_interval=4,
                         n_repeats=1, is_collideable=False)
        Explosion.sound.play()


class GunBonus(games.Animation):
    """A model of a gun bonus animation"""
    gun_bonus_sound = games.load_sound('./res/level.wav')
    images = ['./res/star coin rotate 1.png',
              './res/star coin rotate 2.png',
              './res/star coin rotate 3.png',
              './res/star coin rotate 4.png',
              './res/star coin rotate 5.png',
              './res/star coin rotate 6.png']

    def __init__(self, x, y):
        """Initializes gun bonus animation"""
        GunBonus.gun_bonus_sound.play()
        super().__init__(images=GunBonus.images, x=x, y=y, repeat_interval=3, n_repeats=0, is_collideable=True)
        self.name = 'gun_bonus'
        self.lifetime = 7 * games.screen.fps

    def update(self):
        if self.lifetime > 0:
            self.lifetime -= 1
        else:
            self.die()

    def die(self):
        """Destroys gun bonus"""
        GunBonus.gun_bonus_sound.play()
        self.destroy()


class JetStream(games.Animation):
    """A model of a jet stream animation"""
    images = ['./res/jetstream1.png', './res/jetstream2.png']
    BUFFER = 48

    def __init__(self, ship_x, ship_y, ship_angle):
        """Initializes jet stream animation"""
        # convert angle to radians
        angle = ship_angle * math.pi / 180

        # calculate jet stream position
        buffer_x = -JetStream.BUFFER * math.sin(angle)
        buffer_y = JetStream.BUFFER * math.cos(angle)
        x = ship_x + buffer_x
        y = ship_y + buffer_y
        super().__init__(images=JetStream.images, x=x, y=y, angle=ship_angle,
                         repeat_interval=1, n_repeats=0, is_collideable=False)
        self.name = 'jet_stream'
        self.lifetime = 2

    def update(self):
        if self.lifetime > 0:
            self.lifetime -= 1
        else:
            self.destroy()


def random_coords(buffer, ship_current_x, ship_current_y, screen_width, screen_height):
    """Generates random coordinates x and y outside buffer distance from the ship"""
    # choose minimum distance along x-axis and y-axis
    x_min = random.randrange(buffer)
    y_min = buffer - x_min

    # choose distance along x-axis and y-axis based on minimum distance
    x_distance = random.randrange(x_min, screen_width - x_min)
    y_distance = random.randrange(y_min, screen_height - y_min)

    # calculate location based on distance
    x = ship_current_x + x_distance
    y = ship_current_y + y_distance

    # wrap around screen, if necessary
    x %= screen_width
    y %= screen_height

    return x, y

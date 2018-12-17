"""This module contains class describing the game and function starting it"""
# 'Star battle' game

# import
from superwires import games, color
from models import Asteroid, Ship, AlienShip, random_coords


class Game:
    """A model of star battle game"""

    def __init__(self):
        """Initializes the game"""
        # set level
        self.level = 0

        # load sound for level advance
        self.sound = games.load_sound('./res/level.wav')

        # create score
        self.score = games.Text(value=0, size=30, color=color.white, top=5, right=games.screen.width - 10,
                                is_collideable=False)
        games.screen.add(self.score)
        self.score_legend = games.Text(value="score: ", size=30, color=color.white, top=5,
                                       right=self.score.left - 5, is_collideable=False)
        games.screen.add(self.score_legend)

        # create player's ship
        self.ship = Ship(game=self, x=games.screen.width / 2, y=games.screen.height / 2)
        games.screen.add(self.ship)

        self.asteroid_aims = False
        self.alienship_aims = False

    def play(self):
        """Controls game mechanics"""
        # begin theme music
        games.music.load('./res/theme.mid')
        games.music.play(-1)

        # load and set background
        background_image = games.load_image('./res/space.jpg')
        games.screen.background = background_image

        # advance to level 1
        self.advance()

        # start mainloop
        games.screen.mainloop()

    def advance(self):
        """Advances the game to the next level"""
        if not self.asteroid_aims and not self.alienship_aims:

            self.level += 1

            # min distance to a closest possible asteroid position
            ship_safety_buffer = 100

            # create new asteroids
            for i in range(self.level):
                asteroid_coords = random_coords(buffer=ship_safety_buffer,
                                                ship_current_x=self.ship.x, ship_current_y=self.ship.y,
                                                screen_width=games.screen.width, screen_height=games.screen.height)
                # create the asteroid
                new_asteroid = Asteroid(game=self, x=asteroid_coords[0], y=asteroid_coords[1], size=Asteroid.LARGE)
                games.screen.add(new_asteroid)

            # create new alien ships
            for i in range(self.level):
                alien_coords = random_coords(buffer=ship_safety_buffer,
                                             ship_current_x=self.ship.x, ship_current_y=self.ship.y,
                                             screen_width=games.screen.width, screen_height=games.screen.height)
                # create new alien ship
                new_alienship = AlienShip(game=self, x=alien_coords[0], y=alien_coords[1])
                games.screen.add(new_alienship)

            # display level info
            level_message = games.Message(value="Level {}".format(str(self.level)), size=50, color=color.white,
                                          x=games.screen.width / 2, y=games.screen.width / 10,
                                          lifetime=3 * games.screen.fps, is_collideable=False)
            games.screen.add(level_message)

            self.asteroid_aims = True
            self.alienship_aims = True

            # play new level sound
            if self.level > 1:
                self.sound.play()

    @staticmethod
    def end():
        """Ends the game"""
        # show 'Game Over' message
        end_message = games.Message(value="Game Over", size=90, color=color.red,
                                    x=games.screen.width / 2, y=games.screen.height / 2,
                                    lifetime=5 * games.screen.fps, after_death=games.screen.quit,
                                    is_collideable=False)
        games.screen.add(end_message)


def main():
    starbattle = Game()
    starbattle.play()


# start the game
main()

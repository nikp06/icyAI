import pygame
# import time
from pygame.locals import *
import numpy as np
import random
import pickle
import neat
import sys
import os
import glob
import visualize

# screen resolution and scaling
SCREEN_MAX = 700  # 600, 700, 800, 900, 1000
SCALE1 = SCREEN_MAX * 1 / 500  # 2 vel_x
SCALE2 = SCREEN_MAX * 1 / 250  # 4 bonus y 1
SCALE3 = SCREEN_MAX * 3 / 500  # 6 vel_x threshold for bonus y 1
SCALE4 = SCREEN_MAX * 1 / 125  # 8 bonus y 2
SCALE5 = SCREEN_MAX * 3 / 250  # 12 vel_x threshold for bonus y 2
SCALE6 = SCREEN_MAX * 2 / 125  # 16 bonus y 3
SCALE7 = SCREEN_MAX * 1 / 50  # 20 vel_x threshold for bonus y 3; max speed; vel_y gain when jumping
SCALE8 = SCREEN_MAX * 3 / 100  # 30
SCALE9 = SCREEN_MAX * 1 / 20  # 50 wall width; player height
SCALE10 = SCREEN_MAX * 3 / 20  # 150 distance between tiles
SCALE11 = SCREEN_MAX * 1 / 5  # 200 left boundary for switch to end; min tile width
SCALE12 = SCREEN_MAX * 1 / 2.5  # 400 max tile width
SCALE13 = SCREEN_MAX * 1 / 2  # 500 when dropping first starts
SCALE14 = SCREEN_MAX * 4 / 5  # 800 right boundary for switch to end
SCALE15 = SCREEN_MAX * 9 / 10  # 9000

pygame.init()

# colors
TEXT_COLOR = (255, 255, 255)
GREEN = (100, 230, 100)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PALETTE = (GREEN, RED, BLUE, YELLOW)
WALL_WIDTH = SCALE9
FONT = pygame.font.SysFont("Sans", 20)
SCREEN = pygame.display.set_mode((SCREEN_MAX, SCREEN_MAX), 0, 32)
# loading sprites and conversion
IMAGE = pygame.image.load('icyMan.png').convert_alpha()
IMAGE = pygame.transform.scale(IMAGE, (int(SCALE8), int(SCALE9)))
ICE = pygame.image.load('icy2.png').convert_alpha()
BG = pygame.image.load('background.jpg')
BG = pygame.transform.scale(BG, (SCREEN_MAX, SCREEN_MAX))
WALL_RIGHT = pygame.image.load('wall2.png')
WALL_RIGHT = pygame.transform.scale(WALL_RIGHT, (int(WALL_WIDTH), SCREEN_MAX))
WALL_RIGHT_FLIP = pygame.transform.flip(WALL_RIGHT, False, True)
WALL_LEFT = pygame.transform.flip(WALL_RIGHT, True, True)
WALL_LEFT_FLIP = pygame.transform.flip(WALL_LEFT, False, True)
wall_height1 = 0
wall_height2 = -SCREEN_MAX
GENERATION = 0


def main(genomes, config):
    global GENERATION
    game = IcyTowerGameAI(genomes, config)
    GENERATION += 1
    # print(genomes)

    while True:
        game.play_step()
        if len(game.players) == 0:
            print(game.false_count)
            break


class IcyTowerGameAI:

    def __init__(self, genomes, config):
        pygame.display.set_caption('IcyTower by NikP')
        self.mainClock = pygame.time.Clock()
        self.genomes = genomes
        self.config = config
        self.generation = GENERATION
        self.reset()

    def reset(self):
        pygame.display.set_caption('IcyTower by NikP')
        self.mainClock = pygame.time.Clock()
        # initialized objects
        self.nets = []
        self.ge = []
        self.players = []

        for _, g in self.genomes:
            net = neat.nn.FeedForwardNetwork.create(g, self.config)
            self.nets.append(net)
            self.players.append(Player(random.randint(int(WALL_WIDTH), int(SCREEN_MAX-Player.PLAYER_WIDTH-WALL_WIDTH)), SCREEN_MAX - SCALE9 - SCALE9))
            g.fitness = 0  # TODO: maybe wrong
            self.ge.append(g)
        # initialize game state for first movement
        for player in self.players:
            player.right = True

        self.tiles = [Tile(WALL_WIDTH, SCREEN_MAX - SCALE9, SCREEN_MAX-WALL_WIDTH)]
        # self.floors_passed = 0
        self.update_tiles()
        self.walls = [Wall('left'), Wall('right')]
        # initialized variables
        self.drop = False
        self.level = 0
        self.drop_speed = self.level
        self.timesince = 0
        self.stars = 0
        self.start_time = 0
        self.highest_floor = 0
        self.highest_fitness = 0
        self.false_count = 0

        self.particles_drop_vel = []
        self.star_list = []
        self.colors = []

        self.start_time = pygame.time.get_ticks()
        self.end_pos = 0
        self.start_pos = None

    def play_step(self):
        self.timesince = int((pygame.time.get_ticks() - self.start_time - 10) / 1000)

        # self.frame_iteration += 1
        # DROPPING EVERYTHING ON SCREEN & TIMER [drop_all]
        # if self.drop is False:
        #     if self.frame_iteration >= 500 or self.highest_floor > 2:  #int(pygame.time.get_ticks() / 1000) == 10 or self.highest_floor > 2:  # or self.max_height < SCREEN_MAX/2:
        #         self.drop = True
        #         self.start_time = pygame.time.get_ticks()
        # else:
        #     self.drop_all()
        #     self.timesince = int((pygame.time.get_ticks() - self.start_time - 10) / 1000)
        #     if self.timesince >= self.level * 30:  # TODO: zuückändern
        #         self.level += 1

        self.listen()

        # tile_details = []
        # for tile in self.tiles:
        #     tile_details.append(tile.rect.x)
        #     tile_details.append(tile.rect.y)
        #     tile_details.append(tile.tile_width)

        for x, player in enumerate(self.players):
            tile_details = []
            for i in range(11):
                tile_details.append(self.tiles[player.current_floor + i].rect.x-player.rect.x)
                tile_details.append(self.tiles[player.current_floor + i].rect.y-player.rect.y)
                tile_details.append(self.tiles[player.current_floor + i].tile_width)
            # for tile in self.tiles:
            #     tile_details.append(tile.rect.x)
            #     tile_details.append(tile.rect.y)
            #     tile_details.append(tile.tile_width)
            if player.on_floor is True:
                a = 1
            else:
                a = 0
            action = self.nets[x].activate((player.rect.x, player.rect.y, player.vel_x, player.vel_y, a, *tile_details))

            action_idx = action.index(max(action))
            for i in range(len(action)):
                if i == action_idx:
                    action[i] = 1
                else:
                    action[i] = 0
            if action[2] == 1 and a == 0:
                self.false_count += 1

            player.move(action)
            if player.jump is True:
                player.jump = False
                # increase fitness for staying alive?
            self.ge[x].fitness += 0.1

            # CHECKING FOR COLLISIONS [collision_check]
            self.collision_check(player)

            if player.switch is True:
                self.ge[x].fitness -= 10

            if player.frame_iteration > 300:
                self.players.pop(x)
                self.ge[x].fitness -= 50
                self.nets.pop(x)
                self.ge.pop(x)



            # if player.rect.y >= SCREEN_MAX - player.PLAYER_HEIGHT: # or self.frame_iteration > 500:
                # self.players.pop(x)
                # self.ge[x].fitness -= 50
                # self.nets.pop(x)
                # self.ge.pop(x)
                # TODO: adapt so no players die immediately!

        # GET KEYBOARD INPUT [listen]
        # for player in self.players:



        self.highest_fitness = 0
        for x, player in enumerate(self.players):
            player.frame_iteration += 1

            # if player.current_floor != player.old_floor:
                # print("success")
                # self.ge[x].fitness += 10*(player.current_floor-player.old_floor)
                # print(player.current_floor)
            if player.current_floor > player.old_floor:
                player.frame_iteration = 0
                self.ge[x].fitness += 10 * (player.current_floor - player.old_floor)
                    # print("jip")
                player.old_floor = player.current_floor


            if player.current_floor > self.highest_floor:
                self.highest_floor = player.current_floor

            if self.ge[x].fitness > self.highest_fitness:
                self.highest_fitness = int(self.ge[x].fitness)
                # frame_iteration = 0

        self.drop_all()
        # REMOVE OLD TILES AND GENERATE NEW ONES IF NECESSARY
        self.update_tiles()

        # DRAW EVERYTHING TO THE SCREEN
        self.draw_window()

        # UPDATE THE SCREEN
        pygame.display.update()

        # UPDATE THE CLOCK
        self.mainClock.tick(60)

    def drop_all(self):  # TODO: adapt to moving camera
        # print(self.max_height)
        # drop_speed = 0
        # max_height = SCREEN_MAX
        # max_vel = 0

        #     if player.rect.y < max_height:
        #         max_height = player.rect.y
        #         max_vel = -player.dy
        #         drop_speed = max_vel
        # drop_speed += self.level
        if self.start_pos:
            cur_pos = pygame.mouse.get_pos()
            self.drop_speed = int((cur_pos[1] - self.start_pos[1])/10)
        else:
            self.drop_speed = 0
            for player in self.players:
                if 0 < player.rect.y <= SCREEN_MAX / 10:
                    self.drop_speed = 8
                elif player.rect.y <= 0:
                    self.drop_speed = 15
                    continue

        # self.end_pos = 0
        # self.start_pos = 0
        for player in self.players:
            player.rect.y += self.drop_speed
        for tile in self.tiles:
            tile.rect.y += self.drop_speed

        for wall in self.walls:
            if self.drop_speed > 0:
                if wall.wall_height1 >= SCREEN_MAX:
                    wall.wall_height1 = -SCREEN_MAX
                    wall.wall_height2 = 0

                if wall.wall_height2 >= SCREEN_MAX:
                    wall.wall_height2 = -SCREEN_MAX
                    wall.wall_height1 = 0

            elif self.drop_speed < 0:
                # print("jo")
                if wall.wall_height1 <= -SCREEN_MAX:
                    wall.wall_height1 = SCREEN_MAX
                    wall.wall_height2 = 0
                if wall.wall_height2 <= -SCREEN_MAX:
                    wall.wall_height2 = SCREEN_MAX
                    wall.wall_height1 = 0

            wall.wall_height1 += self.drop_speed
            wall.wall_height2 += self.drop_speed
        self.drop_speed = 0

    def listen(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                self.start_pos = pygame.mouse.get_pos()

            if event.type == MOUSEBUTTONUP:
                self.start_pos = None

    def collision_check(self, player):
        # for player in self.players:
        # tile_collisions = []
        # wall_collisions = []
        player.on_floor = False
        for idx, tile in enumerate(self.tiles):
            if player.rect.colliderect(tile):
                # tile_collisions.append(tile)
                if player.falling is True and player.rect.bottom - tile.rect.top < 21:
                    player.current_floor = idx
                    player.on_floor = True
                    player.tilting = False
                    player.tilt = 0
                    player.rect.bottom = tile.rect.top + 1
                    player.current_height = tile.rect.top + 1
            # else:
            #     player.on_floor = False


        if (player.rect.x <= WALL_WIDTH) or (player.rect.x+player.PLAYER_WIDTH >= SCREEN_MAX-WALL_WIDTH):
            player.switch = True

        # if tile_collisions:
        #     for tile in tile_collisions:
        #         if player.falling is True and player.rect.bottom - tile.rect.top < 21:
        #             player.current_floor = self.floors_passed + self.tiles.index(tile)
        #             player.on_floor = True
        #             player.tilting = False
        #             player.tilt = 0
        #             player.rect.bottom = tile.rect.top + 1
        #             player.current_height = tile.rect.top + 1
        # else:
        #     player.on_floor = False
        #     player.old_floor = player.current_floor

    def update_tiles(self):
        # removing tiles that are out of bounds
        # if self.tiles[0].rect.top >= SCREEN_MAX:
        #     # del self.tiles[0]
        #     self.floors_passed += 1

        # adding tiles procedurally if necessary
        # while len(self.tiles) <= 10:
        #     tile_diff = self.tiles[-1].rect.top - 100  # scale10
        #     # self.tiles.append(
        #     #         Tile(0, tile_diff,
        #     #              SCREEN_MAX))
        #     # checkpoint floors_passed (each 50th)
        #     if (self.floors_passed + len(self.tiles) + 1) % 50 == 1:
        #         self.tiles.append(Tile(SCALE9, tile_diff, SCALE15))
        #     # normal floors_passed
        #     else:
        #         tile_width = random.randint(int(SCALE11), int(SCALE12))
        #         self.tiles.append(
        #             Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff,
        #                  tile_width))

        # tile_diff = self.tiles[-1].rect.top - 100
        for player in self.players:
            nr_tiles = len(self.tiles)  # 11
            if player.current_floor > nr_tiles - 11:
                for i in range(player.current_floor - nr_tiles + 11):
                    tile_diff = self.tiles[-1].rect.top - 100
                    tile_width = random.randint(int(SCALE11), int(SCALE12))
                    if len(self.tiles) % 49 == 0:
                        self.tiles.append(Tile(WALL_WIDTH, tile_diff, SCREEN_MAX-WALL_WIDTH))
                    else:
                        self.tiles.append(
                            Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff,
                                 tile_width))
        # print(len(self.tiles))

    def draw_window(self):
        SCREEN.fill((0, 0, 0))

        SCREEN.blit(BG, (0, 0))

        for tile in self.tiles:
            if 0 <= tile.rect.y <= SCREEN_MAX:
                tile.draw()

        for player in self.players:
            if 0 <= player.rect.y <= SCREEN_MAX:
                player.draw()

        for wall in self.walls:
            wall.draw()

        msg_generation = FONT.render('Generation: ' + str(self.generation), True, GREEN)
        msg_time = FONT.render('Time: ' + str(self.timesince), True, GREEN)
        msg_floors = FONT.render('Floors climbed: ' + str(self.highest_floor), True, GREEN)
        msg_fitness = FONT.render('Highest Fitness: ' + str(self.highest_fitness), True, GREEN)
        msg_alive = FONT.render('Alive: ' + str(len(self.players)), True, GREEN)

        SCREEN.blit(msg_time, (60, 20))
        SCREEN.blit(msg_floors, (60, 50))
        SCREEN.blit(msg_generation, (SCREEN_MAX - 50 - msg_generation.get_width(), 20))
        SCREEN.blit(msg_fitness, (SCREEN_MAX - 50 - msg_fitness.get_width(), 50))
        SCREEN.blit(msg_alive, (SCREEN_MAX - 50 - msg_alive.get_width(), 80))

# player class
class Player(pygame.sprite.Sprite):
    PLAYER_WIDTH = SCALE8
    PLAYER_HEIGHT = SCALE9
    ROTATION = 25

    def __init__(self, x, y):
        super().__init__()
        self.image = IMAGE
        self.rect = pygame.Rect(x, y, self.PLAYER_WIDTH, self.PLAYER_HEIGHT)
        self.tick_count = 0
        self.tilt = 0
        self.current_floor = 0
        self.old_floor = 0
        self.highest_floor = 0
        # self.floors_passed = 0
        self.vel_x = 0
        self.vel_y = 0
        self.current_height = self.rect.y
        self.bonus_y = 0  # [0 - 12]

        self.falling = False
        self.collision = True
        self.on_floor = True

        self.left = False
        self.right = False
        self.jump = False
        self.switch = False
        self.switching = False
        self.switch_count = 0
        self.tilting = False
        self.combo = False
        self.combo_added = True
        self.combo_floors = 0
        self.dy = 0

        self.frame_iteration = 0

    def jumping(self):

        self.vel_y = -15 - self.bonus_y
        self.current_height = self.rect.y
        if self.bonus_y == 17:
            self.tilting = True

    def move(self, action):
        # movements = [self.left, self.right, self.jump]
        if action[0] == 1:
            self.left = True
            self.right = False
            # print("do nothing")
            # print()
        # print(self.on_floor)
        if action[1] == 1:  # change direction
            self.left = False
            self.right = True
            # print("change direction!")
            # self.left = not self.left
            # self.right = not self.right
        elif action[2] == 1:  # jump
            # print("jump")
            self.jump = True


        # IN X DIRECTION:
        # VELOCITY ADJUSTMENT IN X
        if self.switch is False:
            # don't change anything for a little while after bouncing off wall
            if self.switching:
                if self.switch_count == 8:
                    self.switching = False
                self.switch_count += 1
            # then respond to keyboard input again
            elif self.left or self.right:
                if self.left:
                    if self.vel_x > 0:  # fast direction change
                        self.vel_x = 0
                    self.vel_x -= .5
                if self.right:
                    if self.vel_x < 0:  # fast direction change
                        self.vel_x = 0
                    self.vel_x += .5
            # if nothing is pressed -> decelerate
            else:
                if self.vel_x > 2:
                    self.vel_x -= .5
                elif self.vel_x < -2:
                    self.vel_x += .5
                else:
                    self.vel_x = 0
        else:  # change movement direction if switch is True
            self.vel_x = -self.vel_x
            self.switch_count = 0
            # put player next to wall so there are no bugs
            if self.rect.x > SCREEN_MAX/2:  # for right switch
                self.rect.x = SCREEN_MAX-WALL_WIDTH-self.PLAYER_WIDTH
            else:  # for left switch
                self.rect.x = WALL_WIDTH
            self.switching = True
            self.switch = False

        dx = self.vel_x

        # VELOCITY ADJUSTMENT IN Y
        # JUMPING MOTION IF REQUESTED
        if self.on_floor is True:
            self.tick_count = 0
            if self.jump is True:
                self.jumping()
                self.on_floor = False
                dy = self.vel_y + self.tick_count
            else:
                # self.rect.bottom = self.current_height
                self.vel_y = 0
                dy = 0
        else:
            self.tick_count += 1
            dy = self.vel_y + self.tick_count
            self.dy = dy
            # ensuring max speed
            if dy >= 15:
                dy = 15
        self.falling = dy > 0

        # DISTANCE OF MOVEMENT; MAX SPEEDS AND BONUS Y
        # if not standing -> grant bonus_y and ensure max
        if dx != 0:
            speed = [6 < dx*np.sign(dx) <= 8, 8 < dx*np.sign(dx) <= 11, 11 < dx*np.sign(dx) < 15, dx*np.sign(dx) >= 15]
            if speed[0]:
                self.bonus_y = 2
            elif speed[1]:
                self.bonus_y = 5
            elif speed[2]:
                self.bonus_y = 11
            elif speed[3]:
                self.vel_x = 15 * np.sign(dx)
                dx = 15 * np.sign(dx)
                self.bonus_y = 17
            else:
                self.bonus_y = 0
        else:
            self.bonus_y = 0

        # PERFORMING MOVEMENT
        self.rect.x = self.rect.x + dx
        self.rect.y = self.rect.y + dy
        if self.tilting is True:
            self.tilt += self.ROTATION

    # drawing function for the player
    def draw(self):
        if self.tilting is True:
            rotated_image = pygame.transform.rotate(self.image, self.tilt)
            new_rect = rotated_image.get_rect(center=self.image.get_rect(topleft=(self.rect.x, self.rect.y)).center)
            SCREEN.blit(rotated_image, new_rect.topleft)  # , (self.rect.x, self.rect.y))
        else:
            SCREEN.blit(self.image, (self.rect.x, self.rect.y))


class Wall(pygame.sprite.Sprite):
    WALL_WIDTH = SCALE9

    def __init__(self, side):
        super().__init__()
        self.side = side.lower()
        if self.side == 'left':
            self.rect = pygame.Rect(0, 0, WALL_WIDTH, SCREEN_MAX)
            self.image = WALL_LEFT
            self.image_flip = WALL_LEFT_FLIP
        if side.lower() == 'right':
            # pygame.Rect()
            self.rect = pygame.Rect(SCREEN_MAX-SCALE9, 0, WALL_WIDTH, SCREEN_MAX)
            self.image = WALL_RIGHT
            self.image_flip = WALL_RIGHT_FLIP
        self.width = self.WALL_WIDTH
        self.wall_height1 = 0
        self.wall_height2 = -SCREEN_MAX

    def draw(self):
        # wall left
        SCREEN.blit(self.image, (self.rect.x, self.wall_height1))
        SCREEN.blit(self.image_flip, (self.rect.x, self.wall_height2))


# class for tiles
class Tile(pygame.sprite.Sprite):
    TILE_HEIGHT = SCALE7

    def __init__(self, x, y, tile_width):
        super().__init__()
        # self.image = pygame.transform.scale(ICE, (int(tile_width), int(Player.PLAYER_HEIGHT)))
        self.image = ICE
        self.rect = pygame.Rect(x, y, tile_width, self.TILE_HEIGHT)
        self.width = pygame.Surface.get_width(self.image)
        self.tile_width = tile_width

    # drawing function for tiles
    def draw(self):
        repetitions = int(self.tile_width/self.width)
        image = self.image
        for i in range(repetitions):
            SCREEN.blit(image, (self.rect.x+i*self.width, self.rect.y))
            image = pygame.transform.flip(image, True, False)


def run(config_path):
    global GENERATION
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    # config = neat.config.Config(config_path)
    # setting population

    # giving statistics
    # p.add_reporter(neat.StdOutReporter(True))
    # checkpointer = neat.Checkpointer(25)
    # stats = neat.StatisticsReporter()
    # p.add_reporter(stats)

    if len(sys.argv) > 2:
        checkpointer = neat.Checkpointer(1)
        checkpointer.filename_prefix = os.path.join(sys.argv[1], sys.argv[1])

        # Load specified model
        if os.path.isdir(sys.argv[1]):
            if os.path.isfile(os.path.join(sys.argv[1], sys.argv[1]+'.pkl')):
                filenamesList = []
                for item in glob.glob(os.path.join(sys.argv[1], sys.argv[1] + '*')):
                    if '.' not in item:
                        filenamesList.append(item)
                print(filenamesList)
                p = neat.Checkpointer.restore_checkpoint(filenamesList[-1])
                print(f"\nLoading existing model '{sys.argv[1]}'...")
                with open(os.path.join(sys.argv[1], sys.argv[1]+'.pkl'), "rb") as f:
                    genome = pickle.load(f)
        else:
            os.mkdir(sys.argv[1])
            print(f"\nCreating new model '{sys.argv[1]}'...")
            p = neat.Population(config)
        p.add_reporter(checkpointer)
        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)
        GENERATION = p.generation
        if sys.argv[2] == 'train':
            if len(sys.argv) == 4:
                n = int(sys.argv[3])
            else:
                n = 50
            print(f"\nTraining in process for given model '{sys.argv[1]}' for {n} runs...")
            winner = p.run(main, n)

            with open(os.path.join(sys.argv[1], sys.argv[1]+'.pkl'), "wb") as f:
                pickle.dump(winner, f)
                f.close()

            node_names = {-1:'A', -2: 'B', 0:'A XOR B'}
            visualize.draw_net(config, winner, True, filename=os.path.join(sys.argv[1], sys.argv[1]), node_names=node_names)
            visualize.plot_stats(stats, ylog=False, view=True, filename=os.path.join(sys.argv[1], sys.argv[1]+'_avg_fitness'))
            visualize.plot_species(stats, view=True, filename=os.path.join(sys.argv[1], sys.argv[1]+'_speciation'))

        elif sys.argv[2] == 'play':
            # Convert loaded genome into required data structure
            genomes = [(1, genome)]

            if len(sys.argv) == 4:
                # Call game with only the loaded genome
                n = int(sys.argv[3])
            else:
                n = 50

            print(f"\nPlaying in process for given model '{sys.argv[1]}' for {n} runs...")
            for i in range(n):
                main(genomes, config)
                GENERATION -= 1

    else:
        print("\nNo/Invalid Arguments given... Please specify {name of model}, {train/play}, {n_runs}")



if __name__ == '__main__':
    local_dir = os.path.dirname(__name__)
    config_path = os.path.join(local_dir, "config_file.txt")
    run(config_path)

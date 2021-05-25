import pygame
# import time
from pygame.locals import *
import numpy as np
import random
import neat
import sys
import os

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

# pygame initialization
pygame.init()
# mainClock = pygame.time.Clock()
# pygame.display.set_caption('IcyTower by NikP')

# colors
TEXT_COLOR = (255, 255, 255)
GREEN = (0, 255, 0)
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

def main(genomes, config):
    # nets = []
    # ge = []
    # players = []
    #
    # for _, g in genomes:
    #     net = neat.nn.FeedForwardNetwork(g, config)
    #     nets.append(net)
    #     players.append(Player(100, SCREEN_MAX - SCALE9 - SCALE9))
    #     g.fitness = 0
    #     ge.append(g)
    game = IcyTowerGameAI(genomes, config)
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
        # initialized objects
        self.reset()
        # self.player = Player(100, SCREEN_MAX - SCALE9 - SCALE9)
        # # initialize game state for first movement
        # self.player.right = True
        # self.tiles = [Tile(0, SCREEN_MAX - SCALE9, SCREEN_MAX)]
        # self.walls = [Wall('left'), Wall('right')]
        # # initialized variables
        # self.drop = False
        # self.level = 0
        # self.timesince = 0
        # self.score = 0
        # self.stars = 0
        # self.start_time = 0
        # self.particles_drop_vel = []
        # self.star_list = []
        # self.colors = []

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
            self.players.append(Player(100, SCREEN_MAX - SCALE9 - SCALE9))
            g.fitness = 0  # TODO: maybe wrong
            self.ge.append(g)
        # initialize game state for first movement
        for player in self.players:
            player.right = True
        # self.tiles = [Tile(0, SCREEN_MAX - SCALE9, SCREEN_MAX)]
        # for start_tile
        # self.tiles = [Tile(100, SCREEN_MAX - SCALE9, 200)]  # TODO: zurückändern
        self.tiles = [Tile(0, SCREEN_MAX - SCALE9, SCREEN_MAX)]
        self.floors_passed = 0
        self.update_tiles()
        self.walls = [Wall('left'), Wall('right')]
        # initialized variables
        self.drop = False
        self.level = 0
        self.drop_speed = self.level
        self.timesince = 0
        self.score = 0
        self.stars = 0
        self.start_time = 0
        self.highest_floor = 0
        self.false_count = 0
        # self.max_height = SCREEN_MAX

        self.particles_drop_vel = []
        self.star_list = []
        self.colors = []
        self.frame_iteration = 0
        # self.frame_iteration2

    def play_step(self):
        self.frame_iteration += 1
        # print(self.drop_speed)
        # self.drop_speed = self.level
        # DROPPING EVERYTHING ON SCREEN & TIMER [drop_all]
        # print(self.max_height< SCREEN_MAX/2)
        if self.drop is False:
            # print(self.frame_iteration)
            if self.frame_iteration >= 500 or self.highest_floor > 2:  #int(pygame.time.get_ticks() / 1000) == 10 or self.highest_floor > 2:  # or self.max_height < SCREEN_MAX/2:
                self.drop = True
                self.start_time = pygame.time.get_ticks()
        else:
            self.drop_all()
            self.timesince = int((pygame.time.get_ticks() - self.start_time - 10) / 1000)
            if self.timesince >= self.level * 5:  # TODO: zuückändern
                self.level += 1
                for g in self.ge:
                    g.fitness += 100


        self.listen()
        # CHECK IF GAME OVER
        # reward = 0
        # game_over_state = False
        # self.frame_iteration += 1
        # self.frame_iteration2 += 1
        tile_details = []
        for tile in self.tiles:  # TODO: wieder reinnehmen
            tile_details.append(tile.rect.x)
            tile_details.append(tile.rect.y)
            tile_details.append(tile.tile_width)

        for x, player in enumerate(self.players):
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
                # print("FALSE!!!")
            # print(self.false_count)
            # print(action)

            player.move(action)
            if player.jump is True:
                player.jump = False
            self.ge[x].fitness += 0.1


            if player.rect.y >= SCREEN_MAX - player.PLAYER_HEIGHT: # or self.frame_iteration > 500:
                self.score += player.combo_floors ** 2 * 10  # take out maybe because of ai
                self.players.pop(x)
                self.ge[x].fitness -= 50
                self.nets.pop(x)
                self.ge.pop(x)
            elif player.rect.y <= 0:
                player.rect.top = 1
            # elif player.rect.y < self.max_height:
            #     self.max_height = player.rect.y
                # game_over_state = True
                # reward = -50
                # return reward, game_over_state, self.score

            # break

        # GET KEYBOARD INPUT [listen]
        # for player in self.players:

        # CHECKING FOR COLLISIONS [collision_check]
            self.collision_check(player)

        for x, player in enumerate(self.players):
            if player.current_floor != player.old_floor:
                self.ge[x].fitness += 10*(player.current_floor-player.old_floor)
                # self.frame_iteration = 0
                # reward = 10*(player.current_floor-player.old_floor)
            # elif player.current_floor < player.old_floor:
            #     self.g.fitness[x] -= 10
                # self.frame_iteration = 0
                # reward = 10 * (player.current_floor - player.old_floor)

            if player.current_floor > self.highest_floor:
                self.highest_floor = player.current_floor
                # frame_iteration = 0

            # PERFORMING MOVEMENT ACCORDING TO INPUT AND TO COLLISIONS
            # print(action)
            # player.move(action)
            # if player.jump is True:
            #     player.jump = False
        # self.player.jump = False
        # self.player.right = False
        # self.player.left = False

        # REMOVE OLD TILES AND GENERATE NEW ONES IF NECESSARY
        self.update_tiles()

        # UPDATING THE SCORE
        # self.update_score()
        # print(self.score)
        # for player in self.players:
        #     self.score = player.current_floor*10

        # DRAW EVERYTHING TO THE SCREEN
        self.draw_window()

        # # ADDING PARTICLES IF NECESSARY
        # if self.player.combo:
        #     if self.stars % 2 == 0:
        #         self.add_particles()
        #     self.stars += 1
        # if self.star_list:
        #     self.drop_particles()
        #     for idx, star in enumerate(self.star_list):
        #         pygame.draw.polygon(SCREEN, self.colors[idx], star)

        # UPDATE THE SCREEN
        pygame.display.update()

        # UPDATE THE CLOCK
        self.mainClock.tick(60)

        # RETURN GAME_OVER AND SCORE
        # return reward, game_over_state, self.score

    def drop_all(self):
        # print(self.max_height)
        drop_speed = self.level
        # for player in self.players:
        #     if 0 < player.rect.y <= SCREEN_MAX / 10:
        #         drop_speed = 8
        #     elif player.rect.y <= 0:
        #         drop_speed = 15
        #         continue
            # else:
            #     drop_speed = self.level
        for player in self.players:
            player.rect.y += drop_speed
        for tile in self.tiles:
            tile.rect.y += drop_speed

        for wall in self.walls:
            if wall.wall_height1 >= SCREEN_MAX:
                wall.wall_height1 = -SCREEN_MAX
                wall.wall_height2 = 0
            if wall.wall_height2 >= SCREEN_MAX:
                wall.wall_height2 = -SCREEN_MAX
                wall.wall_height1 = 0

            wall.wall_height1 += drop_speed
            wall.wall_height2 += drop_speed

    def listen(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()


    def collision_check(self, player):

        # for player in self.players:
        tile_collisions = []
        # wall_collisions = []
        for tile in self.tiles:
            if player.rect.colliderect(tile):
                tile_collisions.append(tile)
        # for wall in self.walls:
        #     if player.rect.colliderect(wall):
        #         wall_collisions.append(wall)
        if (player.rect.x <= WALL_WIDTH) or (player.rect.x+player.PLAYER_WIDTH >= SCREEN_MAX-WALL_WIDTH):
            player.switch = True

        if tile_collisions:
            for tile in tile_collisions:
                if player.falling is True and player.rect.bottom - tile.rect.top < 21:
                    player.current_floor = self.floors_passed + self.tiles.index(tile)
                    player.on_floor = True
                    player.tilting = False
                    player.tilt = 0
                    player.rect.bottom = tile.rect.top + 1
                    player.current_height = tile.rect.top + 1
        else:
            player.on_floor = False
            player.old_floor = player.current_floor

        # if wall_collisions:
        #     player.switch = True
        # return tile_collisions, wall_collisions

    def update_tiles(self):
        # removing tiles that are out of bounds
        if self.tiles[0].rect.top >= SCREEN_MAX:
            del self.tiles[0]
            self.floors_passed += 1
            for player in self.players:
                player.score = player.current_floor * 10
        # adding tiles procedurally if necessary
        while len(self.tiles) <= 10:
            tile_diff = self.tiles[-1].rect.top - 100  # scale10
            # self.tiles.append(
            #         Tile(0, tile_diff,
            #              SCREEN_MAX))
            # checkpoint floors_passed (each 50th)
            if (self.floors_passed + len(self.tiles) + 1) % 50 == 1:
                self.tiles.append(Tile(SCALE9, tile_diff, SCALE15))
            # normal floors_passed
            else:
                tile_width = random.randint(int(SCALE11), int(SCALE12))
                self.tiles.append(
                    Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff,
                         tile_width))

    # def update_score(self):
    #     add_score = 0
    #     if self.player.jump is True:
    #         self.player.combo_added = False
    #     if self.player.on_floor is True:
    #         if self.player.current_floor > self.player.old_floor:
    #             if self.player.current_floor > self.player.highest_floor:
    #                 self.player.highest_floor = self.player.current_floor
    #                 add_score = (self.player.current_floor - self.player.old_floor) * 10
    #             else:
    #                 add_score = 0
    #             if (self.player.current_floor - self.player.old_floor) > 1:
    #                 self.player.combo = True
    #                 if self.player.combo_added is False:
    #                     self.player.combo_floors += self.player.current_floor - self.player.old_floor
    #             else:
    #                 if self.player.combo is True:
    #                     self.score += self.player.combo_floors ** 2 * 10
    #                 self.player.combo = False
    #                 self.player.combo_floors = 0
    #         elif self.player.current_floor < self.player.old_floor:
    #             if self.player.combo is True:
    #                 self.player.combo = False
    #                 self.score += self.player.combo_floors ** 2 * 10
    #                 self.player.combo_floors = 0
    #         self.player.combo_added = True
    #         self.score += add_score

    def draw_window(self):
        SCREEN.fill((0, 0, 0))

        SCREEN.blit(BG, (0, 0))

        for tile in self.tiles:
            tile.draw()

        for player in self.players:
            player.draw()

        for wall in self.walls:
            wall.draw()

        msg_time = 'Time: ' + str(self.timesince)
        # msg_combo = 'Combo ON - combo_floors: ' + str(self.player.combo_floors)
        msg_score = 'Score: ' + str(self.score)
        msg_floors = 'Floors climbed: ' + str(self.highest_floor)

        SCREEN.blit(FONT.render(msg_time, True, TEXT_COLOR), (60, 20))
        SCREEN.blit(FONT.render(msg_score, True, TEXT_COLOR), (60, 50))
        SCREEN.blit(FONT.render(msg_floors, True, TEXT_COLOR), (60, 80))
        # if self.player.combo:
        #     SCREEN.blit(FONT.render(msg_combo, True, GREEN), (60, 110))

    # def add_particles(self):
    #     add_x = self.player.rect.x + random.randint(0, int(self.player.PLAYER_WIDTH))
    #     add_y = self.player.rect.y + self.player.PLAYER_HEIGHT
    #     pointlist = [(8.25, 7.55), (10.0, 1.0), (11.75, 7.55), (18.55, 7.2), (12.85, 10.95), (15.3, 17.3),
    #                  (10.0, 13.0), (4.7, 17.3), (7.15, 10.95), (1.45, 7.2)]
    #
    #     for idx, item in enumerate(pointlist):
    #         pointlist[idx] = (item[0] + add_x, item[1] + add_y)
    #
    #     self.star_list[0:0] = [pointlist]
    #     self.particles_drop_vel.insert(0, -2)
    #     self.colors.insert(0, random.choice(PALETTE))
    #     if self.star_list[-1][0][1] > SCREEN_MAX + 50:
    #         self.star_list = self.star_list[:-1]
    #         self.particles_drop_vel = self.particles_drop_vel[:-1]
    #         self.colors = self.colors[:-1]

    # def drop_particles(self):
    #     for idx, vel in enumerate(self.particles_drop_vel):
    #         self.particles_drop_vel[idx] = vel + 0.5
    #     for idx, star in enumerate(self.star_list):
    #         pair_list = []
    #         for pair in star:
    #             pair_list.append((pair[0], pair[1] + self.particles_drop_vel[idx]))
    #         self.star_list[idx] = pair_list


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
        self.floors_passed = 0
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

    def jumping(self):
        self.vel_y = -15 - self.bonus_y
        self.current_height = self.rect.y
        if self.bonus_y == 17:
            self.tilting = True

    def move(self, action):
        movements = [self.left, self.right, self.jump]
        # if action[0] == 1:
        #     # print("do nothing")
        if action[1] == 1:  # change direction
            self.left = not self.left
            self.right = not self.right
        elif action[2] == 1:  # jump
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

#
# if __name__ == '__main__':
#     game = IcyTowerGameAI()
#     # game loop
#     i = 1
#     a = 0
#     b = 0
#     while True:
#         # print(i)
#         if i % 100 == 0:
#             a = random.randint(0,2)
#             b = 1
#         elif i % 40:
#             if b == 1:
#                 b = 0
#             else:
#                 b = 1
#         if b == 1:
#             print("change dir")
#         if a == 0:
#             print("jumping")
#             reward, game_over, score = game.play_step([b, 1])
#         else:
#
#             reward, game_over, score = game.play_step([b, 0])
#
#
#         #
#         #
#         #     reward, game_over, score = game.play_step([1, 0, 0])
#         # elif a == 2:
#         #     reward, game_over, score = game.play_step([0, 1, 0])
#         # print(reward)
#
#
#
#         i += 1
#
#         # print("loop")
#         if game_over is True:
#             break
#
#     print('Final Score ', score)


def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    # setting population
    p = neat.Population(config)
    # giving statistics
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(main, 100)
    print(winner)


if __name__ == '__main__':
    local_dir = os.path.dirname(__name__)
    config_path = os.path.join(local_dir, "config_file.txt")
    run(config_path)

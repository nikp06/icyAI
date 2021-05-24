import pygame
from pygame.locals import *
import numpy as np
import random
import sys

# screen resolution and scaling
SCREEN_MAX = 900  # 600, 700, 800, 900, 1000
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


class IcyTowerGame:

    def __init__(self):
        # self.SCREEN_MAX = SCREEN_MAX
        # init display
        # self.SCREEN = pygame.display.set_mode((self.SCREEN_MAX, self.SCREEN_MAX), 0, 32)
        pygame.display.set_caption('IcyTower by NikP')
        self.mainClock = pygame.time.Clock()
        # initialized objects
        self.player = Player(100, SCREEN_MAX - SCALE9 - SCALE9)
        self.tiles = [Tile(0, SCREEN_MAX - SCALE9, SCREEN_MAX)]
        self.walls = [Wall('left'), Wall('right')]
        # initialized variables
        self.drop = False
        self.level = 0
        self.timesince = 0
        self.score = 0
        self.stars = 0
        self.start_time = 0
        self.particles_drop_vel = []
        self.star_list = []
        self.colors = []

    def play_step(self):
        # DROPPING EVERYTHING ON SCREEN & TIMER [drop_all]
        if self.drop is False:
            if int(pygame.time.get_ticks() / 1000) == 10 or self.player.rect.y <= SCALE13:
                self.drop = True
                self.start_time = pygame.time.get_ticks()
        else:
            self.drop_all()
            self.timesince = int((pygame.time.get_ticks() - self.start_time - 5) / 1000)
            if self.timesince >= self.level * 30:
                self.level += 1

        # CHECK IF GAME OVER
        game_over_state = False
        if self.player.rect.y >= SCREEN_MAX - self.player.PLAYER_HEIGHT:
            self.score += self.player.combo_floors ** 2 * 10  # take out maybe because of ai
            game_over_state = True
            return game_over_state, self.score
            # break

        # GET KEYBOARD INPUT [listen]
        self.listen()

        # CHECKING FOR COLLISIONS [collision_check]
        tile_collisions, wall_collisions = self.collision_check()
        if tile_collisions:
            for tile in tile_collisions:
                if self.player.falling is True and self.player.rect.bottom - tile.rect.top < 21:  # player.vel_y >= 0 and
                    self.player.current_floor = self.player.floors_passed + self.tiles.index(tile)
                    self.player.on_floor = True
                    self.player.tilting = False
                    self.player.tilt = 0
                    self.player.rect.bottom = tile.rect.top + 1
                    self.player.current_height = tile.rect.top + 1
        else:
            self.player.on_floor = False
            self.player.old_floor = self.player.current_floor
        if wall_collisions:
            self.player.switch = True

        # PERFORMING MOVEMENT ACCORDING TO INPUT AND TO COLLISIONS
        self.player.move()

        # REMOVE OLD TILES AND GENERATE NEW ONES IF NECESSARY
        self.update_tiles()

        # UPDATING THE SCORE
        self.update_score()

        # DRAW EVERYTHING TO THE SCREEN
        self.draw_window()

        # ADDING PARTICLES IF NECESSARY
        if self.player.combo:
            if self.stars % 2 == 0:
                self.add_particles()
            self.stars += 1
        if self.star_list:
            self.drop_particles()
            for idx, star in enumerate(self.star_list):
                pygame.draw.polygon(SCREEN, self.colors[idx], star)

        # UPDATE THE SCREEN
        pygame.display.update()

        # UPDATE THE CLOCK
        self.mainClock.tick(60)

        # RETURN GAME_OVER AND SCORE
        return game_over_state, self.score

    def drop_all(self):
        if 0 < self.player.rect.y <= SCREEN_MAX / 10:
            drop_speed = 8
        elif self.player.rect.y <= 0:
            drop_speed = 15
        else:
            drop_speed = self.level
        self.player.rect.y += drop_speed
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
            if event.type == KEYDOWN:
                if event.key == K_RIGHT:
                    self.player.right = True
                if event.key == K_LEFT:
                    self.player.left = True
                if event.key == K_SPACE:  # and player.falling is False:
                    self.player.jump = True

            if event.type == KEYUP:
                if event.key == K_RIGHT:
                    self.player.right = False
                if event.key == K_LEFT:
                    self.player.left = False
                if event.key == K_SPACE:
                    self.player.jump = False

    def collision_check(self):
        tile_collisions = []
        wall_collisions = []
        for tile in self.tiles:
            if self.player.rect.colliderect(tile):
                tile_collisions.append(tile)
        for wall in self.walls:
            if self.player.rect.colliderect(wall):
                wall_collisions.append(wall)
        return tile_collisions, wall_collisions

    def update_tiles(self):
        # removing tiles that are out of bounds
        if self.tiles[0].rect.top >= SCREEN_MAX:
            del self.tiles[0]
            self.player.floors_passed += 1
        # adding tiles procedurally if necessary
        if len(self.tiles) <= 10:
            tile_diff = self.tiles[-1].rect.top - 100  # scale10
            # checkpoint floors_passed (each 50th)
            if (self.player.floors_passed + len(self.tiles) + 1) % 50 == 1:
                self.tiles.append(Tile(SCALE9, tile_diff, SCALE15))
            # normal floors_passed
            else:
                tile_width = random.randint(int(SCALE11), int(SCALE12))
                self.tiles.append(
                    Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff,
                         tile_width))

    def update_score(self):
        add_score = 0
        if self.player.jump is True:
            self.player.combo_added = False
        if self.player.on_floor is True:
            if self.player.current_floor > self.player.old_floor:
                if self.player.current_floor > self.player.highest_floor:
                    self.player.highest_floor = self.player.current_floor
                    add_score = (self.player.current_floor - self.player.old_floor) * 10
                else:
                    add_score = 0
                if (self.player.current_floor - self.player.old_floor) > 1:
                    self.player.combo = True
                    if self.player.combo_added is False:
                        self.player.combo_floors += self.player.current_floor - self.player.old_floor
                else:
                    if self.player.combo is True:
                        self.score += self.player.combo_floors ** 2 * 10
                    self.player.combo = False
                    self.player.combo_floors = 0
            elif self.player.current_floor < self.player.old_floor:
                if self.player.combo is True:
                    self.player.combo = False
                    self.score += self.player.combo_floors ** 2 * 10
                    self.player.combo_floors = 0
            self.player.combo_added = True
            self.score += add_score
        # return score

    def draw_window(self):
        SCREEN.fill((0, 0, 0))

        SCREEN.blit(BG, (0, 0))

        for tile in self.tiles:
            tile.draw()

        self.player.draw()

        for wall in self.walls:
            wall.draw()

        msg_time = 'Time: ' + str(self.timesince)
        msg_combo = 'Combo ON - combo_floors: ' + str(self.player.combo_floors)
        msg_score = 'Score: ' + str(self.score)
        msg_floors = 'Floors climbed: ' + str(self.player.current_floor)

        SCREEN.blit(FONT.render(msg_time, True, TEXT_COLOR), (60, 20))
        SCREEN.blit(FONT.render(msg_score, True, TEXT_COLOR), (60, 50))
        SCREEN.blit(FONT.render(msg_floors, True, TEXT_COLOR), (60, 80))
        if self.player.combo:
            SCREEN.blit(FONT.render(msg_combo, True, GREEN), (60, 110))

    def add_particles(self):
        add_x = self.player.rect.x + random.randint(0, int(self.player.PLAYER_WIDTH))
        add_y = self.player.rect.y + self.player.PLAYER_HEIGHT
        pointlist = [(8.25, 7.55), (10.0, 1.0), (11.75, 7.55), (18.55, 7.2), (12.85, 10.95), (15.3, 17.3),
                     (10.0, 13.0), (4.7, 17.3), (7.15, 10.95), (1.45, 7.2)]

        for idx, item in enumerate(pointlist):
            pointlist[idx] = (item[0] + add_x, item[1] + add_y)

        self.star_list[0:0] = [pointlist]
        self.particles_drop_vel.insert(0, -2)
        self.colors.insert(0, random.choice(PALETTE))
        if self.star_list[-1][0][1] > SCREEN_MAX + 50:
            self.star_list = self.star_list[:-1]
            self.particles_drop_vel = self.particles_drop_vel[:-1]
            self.colors = self.colors[:-1]
        # return star_list, particles_drop_vel, colors

    def drop_particles(self):
        for idx, vel in enumerate(self.particles_drop_vel):
            self.particles_drop_vel[idx] = vel + 0.5
        for idx, star in enumerate(self.star_list):
            pair_list = []
            for pair in star:
                pair_list.append((pair[0], pair[1] + self.particles_drop_vel[idx]))
            self.star_list[idx] = pair_list
        # return star_list, drop_vel


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

    def move(self):
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

    # def update_score(self, score):
    #     add_score = 0
    #     if self.jump is True:
    #         self.combo_added = False
    #     if self.on_floor is True:
    #         if self.current_floor > self.old_floor:
    #             if self.current_floor > self.highest_floor:
    #                 self.highest_floor = self.current_floor
    #                 add_score = (self.current_floor - self.old_floor) * 10
    #             else:
    #                 add_score = 0
    #             if (self.current_floor - self.old_floor) > 1:
    #                 self.combo = True
    #                 if self.combo_added is False:
    #                     self.combo_floors += self.current_floor - self.old_floor
    #             else:
    #                 if self.combo is True:
    #                     score += self.combo_floors ** 2 * 10
    #                 self.combo = False
    #                 self.combo_floors = 0
    #         elif self.current_floor < self.old_floor:
    #             if self.combo is True:
    #                 self.combo = False
    #                 score += self.combo_floors ** 2 * 10
    #                 self.combo_floors = 0
    #         self.combo_added = True
    #         score += add_score
    #     return score

    # particle creation at current player position (rather make an own class for particles and pass player to it)
    # def add_particles(self, star_list, particles_drop_vel, colors):
    #     add_x = self.rect.x + random.randint(0, int(self.PLAYER_WIDTH))
    #     add_y = self.rect.y + self.PLAYER_HEIGHT
    #     pointlist = [(8.25, 7.55), (10.0, 1.0), (11.75, 7.55), (18.55, 7.2), (12.85, 10.95), (15.3, 17.3),
    #                  (10.0, 13.0), (4.7, 17.3), (7.15, 10.95), (1.45, 7.2)]
    #
    #     for idx, item in enumerate(pointlist):
    #         pointlist[idx] = (item[0] + add_x, item[1] + add_y)
    #
    #     star_list[0:0] = [pointlist]
    #     particles_drop_vel.insert(0, -2)
    #     colors.insert(0, random.choice(PALETTE))
    #     if star_list[-1][0][1] > SCREEN_MAX + 50:
    #         star_list = star_list[:-1]
    #         particles_drop_vel = particles_drop_vel[:-1]
    #         colors = colors[:-1]
    #     return star_list, particles_drop_vel, colors

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


# def listen(player):
#     for event in pygame.event.get():
#         if event.type == QUIT:
#             pygame.quit()
#             sys.exit()
#         if event.type == KEYDOWN:
#             if event.key == K_RIGHT:
#                 player.right = True
#             if event.key == K_LEFT:
#                 player.left = True
#             if event.key == K_SPACE:  # and player.falling is False:
#                 player.jump = True
#
#         if event.type == KEYUP:
#             if event.key == K_RIGHT:
#                 player.right = False
#             if event.key == K_LEFT:
#                 player.left = False
#             if event.key == K_SPACE:
#                 player.jump = False


# def draw_window(player, tiles, timesince, score, walls):
#     SCREEN.fill((0, 0, 0))
#
#     SCREEN.blit(BG, (0, 0))
#
#     for tile in tiles:
#         tile.draw()
#
#     player.draw()
#
#     for wall in walls:
#         wall.draw()
#
#     msg_time = 'Time: ' + str(timesince)
#     msg_combo = 'Combo ON - combo_floors: ' + str(player.combo_floors)
#     msg_score = 'Score: ' + str(score)
#     msg_floors = 'Floors climbed: ' + str(player.current_floor)
#
#     SCREEN.blit(FONT.render(msg_time, True, TEXT_COLOR), (60, 20))
#     SCREEN.blit(FONT.render(msg_score, True, TEXT_COLOR), (60, 50))
#     SCREEN.blit(FONT.render(msg_floors, True, TEXT_COLOR), (60, 80))
#     if player.combo:
#         SCREEN.blit(FONT.render(msg_combo, True, GREEN), (60, 110))

#
# def update_tiles(player, tiles):
#     # removing tiles that are out of bounds
#     if tiles[0].rect.top >= SCREEN_MAX:
#         del tiles[0]
#         player.floors_passed += 1
#     # adding tiles procedurally if necessary
#     if len(tiles) <= 10:
#         tile_diff = tiles[-1].rect.top - 100  # scale10
#         # checkpoint floors_passed (each 50th)
#         if (player.floors_passed + len(tiles) + 1) % 50 == 1:
#             tiles.append(Tile(SCALE9, tile_diff, SCALE15))
#         # normal floors_passed
#         else:
#             tile_width = random.randint(int(SCALE11), int(SCALE12))
#             tiles.append(
#                 Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff, tile_width))
#

# def collision_check(player, tiles, walls):
#     tile_collisions = []
#     wall_collisions = []
#     for tile in tiles:
#         if player.rect.colliderect(tile):
#             tile_collisions.append(tile)
#     for wall in walls:
#         if player.rect.colliderect(wall):
#             wall_collisions.append(wall)
#     return tile_collisions, wall_collisions
#




# def drop_particles(star_list, drop_vel):
#     for idx, vel in enumerate(drop_vel):
#         drop_vel[idx] = vel + 0.5
#     for idx, star in enumerate(star_list):
#         pair_list = []
#         for pair in star:
#             pair_list.append((pair[0], pair[1] + drop_vel[idx]))
#         star_list[idx] = pair_list
#     return star_list, drop_vel

#
# def game_loop():
#     # creating player and first tile object
#     player = Player(100, SCREEN_MAX - SCALE9 - SCALE9)
#     tiles = [Tile(0, SCREEN_MAX - SCALE9, SCREEN_MAX)]
#     walls = [Wall('left'), Wall('right')]
#     # walls = Walls()
#     drop = False
#     level = 0
#     timesince = 0
#     score = 0
#     stars = 0
#     start_time = 0
#     particles_drop_vel = []
#     star_list = []
#     colors = []
#
#     while True:
#         # DROPPING EVERYTHING ON SCREEN & TIMER
#         if drop is False:
#             if int(pygame.time.get_ticks()/1000) == 10 or player.rect.y <= SCALE13:
#                 drop = True
#                 start_time = pygame.time.get_ticks()
#         else:
#             drop_all(player, tiles, level, walls)
#             timesince = int((pygame.time.get_ticks() - start_time - 5) / 1000)
#             if timesince >= level * 30:
#                 level += 1
#
#         # CHECK IF GAME OVER
#         if player.rect.y >= SCREEN_MAX - player.PLAYER_HEIGHT:
#             score += player.combo_floors ** 2 * 10  # take out maybe because of ai
#             # print end_score
#             break
#
#         # GET KEYBOARD INPUT
#         listen(player)
#
#         # CHECKING FOR COLLISIONS
#         tile_collisions, wall_collisions = collision_check(player, tiles, walls)
#         if tile_collisions:
#             for tile in tile_collisions:
#                 if player.falling is True and player.rect.bottom - tile.rect.top < 21:  # player.vel_y >= 0 and
#                     player.current_floor = player.floors_passed + tiles.index(tile)
#                     player.on_floor = True
#                     player.tilting = False
#                     player.tilt = 0
#                     player.rect.bottom = tile.rect.top + 1
#                     player.current_height = tile.rect.top + 1
#         else:
#             player.on_floor = False
#             player.old_floor = player.current_floor
#         if wall_collisions:
#             player.switch = True
#
#         # PERFORMING MOVEMENT ACCORDING TO INPUT AND TO COLLISIONS
#         player.move()
#
#         # REMOVE OLD TILES AND GENERATE NEW ONES IF NECESSARY
#         update_tiles(player, tiles)
#
#         # UPDATING THE SCORE
#         score = player.update_score(score)
#
#         # DRAW EVERYTHING TO THE SCREEN
#         draw_window(player, tiles, timesince, score, walls)
#
#         # ADDING PARTICLES IF NECESSARY
#         if player.combo:
#             if stars % 2 == 0:
#                 star_list, particles_drop_vel, colors = player.add_particles(star_list, particles_drop_vel, colors)
#             stars += 1
#         if star_list:
#             drop_particles(star_list, particles_drop_vel)
#             for idx, star in enumerate(star_list):
#                 pygame.draw.polygon(SCREEN, colors[idx], star)
#
#         # UPDATE THE SCREEN
#         pygame.display.update()
#
#         # UPDATE THE CLOCK
#         mainClock.tick(60)
#
#
# def main():
#     game_loop()


if __name__ == '__main__':
    game = IcyTowerGame()
    # game loop
    while True:
        game_over, score = game.play_step()

        if game_over is True:
            break

    print('Final Score ', score)


# main()

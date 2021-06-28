import pygame
from pygame.locals import *
import sys
import os
import neat
import random
import numpy as np

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
FONT2 = pygame.font.SysFont("Sans", 50)
SCREEN = pygame.display.set_mode((SCREEN_MAX, SCREEN_MAX), 0, 32)
# loading sprites and conversion
IMAGE = pygame.image.load(os.path.join('sprites', 'icyMan.png')).convert_alpha()
IMAGE_ANTAGONIST = pygame.image.load(os.path.join('sprites', 'icyMan_antagonist.png')).convert_alpha()
IMAGE = pygame.transform.scale(IMAGE, (int(SCALE8), int(SCALE9)))
IMAGE_ANTAGONIST = pygame.transform.scale(IMAGE_ANTAGONIST, (int(SCALE8), int(SCALE9)))
IMAGE2 = pygame.image.load(os.path.join('sprites', 'icyMan2.png')).convert_alpha()
IMAGE2 = pygame.transform.scale(IMAGE2, (int(SCALE8), int(SCALE9)))
IMAGE3 = pygame.image.load(os.path.join('sprites', 'icyMan3.png')).convert_alpha()
IMAGE3 = pygame.transform.scale(IMAGE3, (int(SCALE8), int(SCALE9)))
IMAGE4 = pygame.image.load(os.path.join('sprites', 'icyMan4.png')).convert_alpha()
IMAGE4 = pygame.transform.scale(IMAGE4, (int(SCALE8), int(SCALE9)))
IMAGE5 = pygame.image.load(os.path.join('sprites', 'icyMan5.png')).convert_alpha()
IMAGE5 = pygame.transform.scale(IMAGE5, (int(SCALE8), int(SCALE9)))
COLOR_IMAGE = pygame.Surface(IMAGE.get_size()).convert_alpha()
COLOR_IMAGE.fill(RED)
ICY_IMAGES = [IMAGE, IMAGE2, IMAGE3, IMAGE4, IMAGE5]
ICE = pygame.image.load(os.path.join('sprites', 'icy2.png')).convert_alpha()
BG = pygame.image.load(os.path.join('sprites', 'background.jpg'))
BG = pygame.transform.scale(BG, (SCREEN_MAX, SCREEN_MAX))
WALL_RIGHT = pygame.image.load(os.path.join('sprites', 'wall2.png'))
WALL_RIGHT = pygame.transform.scale(WALL_RIGHT, (int(WALL_WIDTH), SCREEN_MAX))
WALL_RIGHT_FLIP = pygame.transform.flip(WALL_RIGHT, False, True)
WALL_LEFT = pygame.transform.flip(WALL_RIGHT, True, True)
WALL_LEFT_FLIP = pygame.transform.flip(WALL_LEFT, False, True)
wall_height1 = 0
wall_height2 = -SCREEN_MAX


class IcyTowerGame:
    def __init__(self, genomes, config, train, ai, versus):
        pygame.display.set_caption('IcyTower by NikP')
        self.explosion_group = pygame.sprite.Group()
        self.mainClock = pygame.time.Clock()
        self.genomes = genomes
        self.config = config
        self.train = train
        self.ai = ai
        self.versus = versus
        self.draw = True
        self.clock_speed = 60
        self.height = 0

        if self.ai:
            # initialized objects
            self.generation = 0
            self.nets = []
            self.ge = []
            self.ai_players = []
            self.reset()
        else:
            self.human_players = [
                Player(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - Player.PLAYER_WIDTH - WALL_WIDTH)),
                       SCREEN_MAX - SCALE9 - SCALE9)]

        if self.versus:
            self.human_players = [
                Player(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - Player.PLAYER_WIDTH - WALL_WIDTH)),
                       SCREEN_MAX - SCALE9 - SCALE9)]
            self.players = self.ai_players + self.human_players
        else:
            if self.ai:
                self.players = self.ai_players
            else:
                self.players = self.human_players

        self.tiles = [Tile(WALL_WIDTH, SCREEN_MAX - SCALE9 + 100, SCREEN_MAX - WALL_WIDTH),
                      Tile(WALL_WIDTH, SCREEN_MAX - SCALE9, SCREEN_MAX - WALL_WIDTH)]
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

        self.particles_drop_vel = []
        self.star_list = []
        self.colors = []

        self.start_time = pygame.time.get_ticks()
        self.end_pos = 0
        self.start_pos = None

        self.score = 0
        self.frame_iteration = 0

    def reset(self):
        pygame.display.set_caption('IcyTower by NikP')
        self.mainClock = pygame.time.Clock()

        for _, g in self.genomes:
            net = neat.nn.FeedForwardNetwork.create(g, self.config)
            self.nets.append(net)
            self.ai_players.append(
                Player(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - Player.PLAYER_WIDTH - WALL_WIDTH)),
                       SCREEN_MAX - SCALE9 - SCALE9))
            # print(g.species_id)
            # if not g.fitness:
            g.fitness = 0
            # print(g.key)
            self.ge.append(g)
        # initialize game state for first movement
        for player in self.ai_players:
            player.right = True

    def color_species(self):
        for i, (_, g) in enumerate(self.genomes):
            self.players[i].image = ICY_IMAGES[(g.species_id-1) % len(ICY_IMAGES)]
            self.players[i].og_image = self.players[i].image

    def play_step(self):
        self.timesince = int((pygame.time.get_ticks() - self.start_time - 10) / 1000)

        # LISTENING FOR NEW INPUT
        self.listen()

        # EXECUTING THE REQUESTED MOVEMENT
        if self.versus:
            self.execute_movement_ai(self.ai_players)
            self.execute_movement(self.human_players)
        else:
            if self.ai:
                self.execute_movement_ai(self.ai_players)
            else:
                self.execute_movement(self.human_players)

        # CHECKING COLLISION
        self.collision_check()

        # UPDATING THE SCORE
        if self.train:
            self.update_fitness()
        else:
            self.update_score()


        # DETERMINING THE DROP_SPEED OF EVERYTHING ON SCREEN
        self.drop_all()

        # REMOVE OLD TILES AND GENERATE NEW ONES IF NECESSARY
        self.update_tiles()

        # DRAW EVERYTHING TO THE SCREEN
        if self.draw:
            if self.versus:
                self.draw_window_versus()
            else:
                if self.train:
                    self.draw_window_train()
                else:
                    self.draw_window_play()
        # self.draw_window_train()
        # self.draw_window_versus()

        # ADDING PARTICLES IF NECESSARY
        self.generate_particles()

        # UPDATE THE SCREEN
        if self.draw:
            self.explosion_group.draw(SCREEN)
            self.explosion_group.update()
            pygame.display.update()

        # UPDATE THE CLOCK
        self.mainClock.tick(self.clock_speed)

    def execute_movement_ai(self, players):
        for x, player in enumerate(players):
            tile_details = []
            for i in range(11):
                tile_details.append(self.tiles[player.current_floor + i].rect.x - player.rect.x)
                tile_details.append(self.tiles[player.current_floor + i].rect.y - player.rect.y)
                tile_details.append(self.tiles[player.current_floor + i].tile_width)

            action = self.nets[x].activate(
                (player.rect.x, player.rect.y, player.vel_x, player.vel_y, int(player.on_floor),
                 *tile_details))

            indices = [i for i, x in enumerate(action) if x == max(action)]
            action_idx = random.choice(indices)
            # action_idx = action.index(max(action))
            for i in range(len(action)):
                if i == action_idx:
                    action[i] = 1
                else:
                    action[i] = 0

            player.move(action)
            if player.jump is True:
                player.jump = False
                # increase fitness for staying alive?
            # self.ge[x].fitness += 0.1

            # if player.switch is True:
                # self.ge[x].fitness -= 10
            player.frame_iteration += 1
            if self.draw:
                if player.rect.y < SCREEN_MAX:
                    if player.frame_iteration == 250:
                        player.change_color((230, 150, 150))
                    elif player.frame_iteration == 270:
                        player.change_color((230, 120, 120))
                    elif player.frame_iteration == 280:
                        player.change_color((230, 90, 90))
                    elif player.frame_iteration == 290:
                        player.change_color((230, 0, 0))
            #     player.image = pygame.transform.scale(player.image, (int(SCALE8)*2, int(SCALE9)*2))
            # elif player.frame_iteration == 250:
            #     player.image = pygame.transform.scale(player.image, (int(SCALE8)*3, int(SCALE9)*3))
            if player.frame_iteration > 300:
                if self.draw:
                    if player.rect.y < SCREEN_MAX:
                        explosion = Explosion(player.rect.x, player.rect.y)
                        self.explosion_group.add(explosion)
                # player.image = pygame.transform.scale(player.image, (int(SCALE8)*4, int(SCALE9)*4))
                players.pop(x)
                self.ge[x].fitness -= 500
                self.nets.pop(x)
                self.ge.pop(x)

    @staticmethod
    def execute_movement(players):
        action = None
        for player in players:
            player.move(action)
            if player.jump is True:
                player.jump = False

    def drop_all(self):
        self.frame_iteration += 1
        if self.drop is False:
            # int(pygame.time.get_ticks() / 1000) == 10 or self.highest_floor > 2:  # or self.max_height < SCREEN_MAX/2:
            if self.frame_iteration >= 500 or self.highest_floor > 2:
                self.drop = True
        else:
            if self.timesince >= self.level * 30:
                self.level += 1

            if self.start_pos:
                cur_pos = pygame.mouse.get_pos()
                self.drop_speed = int((cur_pos[1] - self.start_pos[1])/10)
            else:
                self.drop_speed = 0
                # self.drop_speed = self.level
                for player in self.players:
                    if 0 < player.rect.y <= SCREEN_MAX / 10:
                        self.drop_speed = 8
                    elif player.rect.y <= 0:
                        self.drop_speed = 15
                        continue

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
                    if wall.wall_height1 <= -SCREEN_MAX:
                        wall.wall_height1 = SCREEN_MAX
                        wall.wall_height2 = 0
                    if wall.wall_height2 <= -SCREEN_MAX:
                        wall.wall_height2 = SCREEN_MAX
                        wall.wall_height1 = 0

                wall.wall_height1 += self.drop_speed
                wall.wall_height2 += self.drop_speed
            self.height += self.drop_speed
            self.drop_speed = 0

    def back_to_start(self, height):
        # self.frame_iteration += 1
        self.drop_speed = height
                # self.drop_speed = self.level

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
                if wall.wall_height1 <= -SCREEN_MAX:
                    wall.wall_height1 = SCREEN_MAX
                    wall.wall_height2 = 0
                if wall.wall_height2 <= -SCREEN_MAX:
                    wall.wall_height2 = SCREEN_MAX
                    wall.wall_height1 = 0

            wall.wall_height1 += self.drop_speed
            wall.wall_height2 += self.drop_speed
        # self.height += self.drop_speed
        self.drop_speed = 0

    def listen(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                self.start_pos = pygame.mouse.get_pos()

            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    self.clock_speed += 60
                    self.draw = not self.draw
                    if not self.draw:
                        self.draw_window_pause()

                        self.clock_speed = 120
                    else:
                        self.clock_speed = 60

                if event.key == K_PLUS:
                    self.clock_speed += 20
                    self.draw_window_pause()

                if event.key == K_MINUS:
                    self.clock_speed -= 20
                    self.draw_window_pause()

            if event.type == MOUSEBUTTONUP:
                self.start_pos = None

            if not self.ai or self.versus:
                if event.type == KEYDOWN:
                    if event.key == K_RIGHT:
                        self.human_players[0].right = True
                    if event.key == K_LEFT:
                        self.human_players[0].left = True
                    if event.key == K_SPACE:
                        self.human_players[0].jump = True

                if event.type == KEYUP:
                    if event.key == K_RIGHT:
                        self.human_players[0].right = False
                    if event.key == K_LEFT:
                        self.human_players[0].left = False
                    # if event.key == K_SPACE:
                    #     self.players[0].jump = False

    def collision_check(self):
        for player in self.players:
            player.on_floor = False
            for idx, tile in enumerate(self.tiles):
                if player.rect.colliderect(tile):
                    if player.rect.bottom - tile.rect.top < 21 and player.dy > 0:
                        player.current_floor = idx
                        player.on_floor = True
                        player.tilting = False
                        player.tilt = 0
                        player.rect.bottom = tile.rect.top + 1
                        player.current_height = tile.rect.top + 1

            if (player.rect.x <= WALL_WIDTH) or (player.rect.x+player.PLAYER_WIDTH >= SCREEN_MAX-WALL_WIDTH):
                player.switch = True

    def update_tiles(self):
        for player in self.players:
            nr_tiles = len(self.tiles)  # 11
            if player.current_floor > nr_tiles - 11:
                for i in range(player.current_floor - nr_tiles + 11):
                    tile_diff = self.tiles[-1].rect.top - 100
                    tile_width = random.randint(int(SCALE11), int(SCALE12))
                    if len(self.tiles) % 50 == 0:
                        self.tiles.append(Tile(WALL_WIDTH, tile_diff, SCREEN_MAX-WALL_WIDTH))
                    else:
                        self.tiles.append(
                            Tile(random.randint(int(WALL_WIDTH), int(SCREEN_MAX - WALL_WIDTH - tile_width)), tile_diff,
                                 tile_width))

    def draw_window_train(self):
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

    def draw_window_play(self):
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

        for player in self.players:
            msg_time = 'Time: ' + str(self.timesince)
            msg_combo = 'Combo ON - combo_floors: ' + str(player.combo_floors)
            msg_score = 'Score: ' + str(self.score)
            msg_floors = 'Floors climbed: ' + str(player.current_floor)

            SCREEN.blit(FONT.render(msg_time, True, TEXT_COLOR), (60, 20))
            SCREEN.blit(FONT.render(msg_score, True, TEXT_COLOR), (60, 50))
            SCREEN.blit(FONT.render(msg_floors, True, TEXT_COLOR), (60, 80))
            if player.combo:
                SCREEN.blit(FONT.render(msg_combo, True, GREEN), (60, 110))

    def draw_window_versus(self):
        SCREEN.fill((0, 0, 0))
        SCREEN.blit(BG, (0, 0))

        for tile in self.tiles:
            if 0 <= tile.rect.y <= SCREEN_MAX:
                tile.draw()
        for player in self.ai_players:
            if 0 <= player.rect.y <= SCREEN_MAX:
                player.image = IMAGE_ANTAGONIST
                player.draw()
        for player in self.human_players:
            if 0 <= player.rect.y <= SCREEN_MAX:
                player.draw()

        for wall in self.walls:
            wall.draw()

    def draw_window_pause(self):
        SCREEN.fill((0, 0, 0))
        SCREEN.blit(BG, (0, 0))
        guy = pygame.image.load(os.path.join('sprites', 'icyMan.png')).convert_alpha()
        SCREEN.blit(guy, ((SCREEN_MAX/2-guy.get_width()+80), 30))
        msg_draw = FONT2.render('Running simulation in ' + str(self.clock_speed) + ' FPS', True, GREEN)
        msg_draw2 = FONT2.render('Press Return to continue normal simulation', True, GREEN)
        msg_draw3 = FONT2.render('Press +/- to increase/decrease simulation speed', True, GREEN)

        SCREEN.blit(msg_draw, (SCREEN_MAX / 2 - msg_draw.get_width() / 2, SCREEN_MAX / 2))
        SCREEN.blit(msg_draw2, (SCREEN_MAX / 2 - msg_draw2.get_width() / 2, SCREEN_MAX / 2 + 50))
        SCREEN.blit(msg_draw3, (SCREEN_MAX / 2 - msg_draw3.get_width() / 2, SCREEN_MAX / 2 + 100))
        pygame.display.update()

    def update_fitness(self):
        if self.train:
            # for player in self.players:
            self.highest_fitness = 0
            for x, player in enumerate(self.ai_players):
                if player.current_floor > player.old_floor:
                    # player.image = pygame.transform.scale(player.image, (int(SCALE8), int(SCALE9)))
                    player.image = player.og_image
                    player.frame_iteration = 0
                    self.ge[x].fitness += 10 * (player.current_floor - player.old_floor)
                    player.old_floor = player.current_floor
                if player.current_floor > self.highest_floor:
                    self.highest_floor = player.current_floor
                if self.ge[x].fitness > self.highest_fitness:
                    self.highest_fitness = int(self.ge[x].fitness)

    def update_score(self):
        for player in self.players:
            add_score = 0

            if player.on_floor is True:
                if player.current_floor > self.highest_floor:
                    self.highest_floor = player.current_floor

                if player.current_floor > player.old_floor:

                    if player.current_floor > player.highest_floor:
                        player.frame_iteration = 0
                        player.highest_floor = player.current_floor
                        add_score = (player.current_floor - player.old_floor) * 10
                    else:
                        add_score = 0
                    if (player.current_floor - player.old_floor) > 1:
                        player.combo = True
                        if player.combo_added is False:
                            player.combo_floors += player.current_floor - player.old_floor
                    else:
                        if player.combo is True:
                            self.score += player.combo_floors ** 2 * 10
                        player.combo = False
                        player.combo_floors = 0
                elif player.current_floor < player.old_floor:
                    if player.combo is True:
                        player.combo = False
                        self.score += player.combo_floors ** 2 * 10
                        player.combo_floors = 0
                player.combo_added = True
                self.score += add_score
            else:
                player.old_floor = player.current_floor

    def generate_particles(self):
        if not self.versus:
            if not self.train:
                for player in self.players:
                    if player.combo:
                        if self.stars % 2 == 0:
                            self.add_particles(player)
                        self.stars += 1
                    if self.star_list:
                        self.drop_particles()
                        for idx, star in enumerate(self.star_list):
                            pygame.draw.polygon(SCREEN, self.colors[idx], star)

    def add_particles(self, player):
        add_x = player.rect.x + random.randint(0, int(player.PLAYER_WIDTH))
        add_y = player.rect.y + player.PLAYER_HEIGHT
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


# player class
class Player(pygame.sprite.Sprite):
    PLAYER_WIDTH = SCALE8
    PLAYER_HEIGHT = SCALE9
    ROTATION = 25

    def __init__(self, x, y):
        super().__init__()
        self.start_pos = [x, y]
        self.image = IMAGE
        self.og_image = self.image
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

    def change_color(self, color):
        colouredImage = pygame.Surface(self.image.get_size())
        colouredImage.fill(color)

        finalImage = self.image.copy()
        finalImage.blit(colouredImage, (0, 0), special_flags=pygame.BLEND_MULT)
        self.image = finalImage
        # return finalImage

    def jumping(self):
        self.vel_y = -15 - self.bonus_y
        self.current_height = self.rect.y
        if self.bonus_y == 17:
            self.tilting = True

    def move(self, action):
        # movements = [self.left, self.right, self.jump]
        if action:
            # print(action)
            if action[0] == 1:
                self.left = True
                self.right = False
            elif action[1] == 1:  # change direction
                self.left = False
                self.right = True
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
                self.combo_added = False
                dy = self.vel_y + self.tick_count
            else:
                self.vel_y = 0
                dy = 0
        else:
            self.tick_count += 1
            dy = self.vel_y + self.tick_count
            self.dy = dy
            # ensuring max speed
            if dy >= 15:
                dy = 15

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


#create Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f"sprites/exp{num}.png")
            img = pygame.transform.scale(img, (100, 100))
            self.images.append(img)
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.rect.center = [x, y]
        self.counter = 0

    def update(self):
        explosion_speed = 4
        #update explosion animation
        self.counter += 1

        if self.counter >= explosion_speed and self.index < len(self.images) - 1:
            self.counter = 0
            self.index += 1
            self.image = self.images[self.index]

        #if the animation is complete, reset animation index
        if self.index >= len(self.images) - 1 and self.counter >= explosion_speed:
            self.kill()
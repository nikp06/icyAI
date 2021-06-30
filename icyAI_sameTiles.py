import pickle
import neat
import sys
import os
import glob
import visualize
import re
import shutil
import time
from pynput.keyboard import Key, Controller
import copy
# import numpy as np
from classes_sameTiles import IcyTowerGame, Tile

GENERATION = 0
CLOCK_SPEED = 60
DRAW = True
RECORDING = False
TILES = None


def main(genomes, config):
    global GENERATION
    global P
    global CLOCK_SPEED
    global DRAW
    global TILES

    game = None
    if len(sys.argv) > 1:
        if sys.argv[2] == 'train':
            game = IcyTowerGame(genomes, config, TILES, train=True, ai=True, versus=False)
        elif sys.argv[2] == 'play':
            if len(sys.argv) > 4:
                if sys.argv[4] == 'versus':
                    game = IcyTowerGame(genomes, config, TILES, train=False, ai=True, versus=True)
                else:
                    game = IcyTowerGame(genomes, config, TILES, train=False, ai=True, versus=False)
            else:
                game = IcyTowerGame(genomes, config, TILES, train=False, ai=True, versus=False)
    else:
        game = IcyTowerGame(genomes, config, TILES, train=False, ai=False, versus=False)

    game.generation = GENERATION
    if not DRAW:
        game.draw = False

    if not TILES:
        TILES = [(tile.rect.x, tile.rect.y, tile.tile_width) for tile in game.tiles]
    else:
        for x, y, width in TILES:
            game.tiles.append(Tile(x, y, width))

    if len(sys.argv) > 1:
        if sys.argv[2] == 'train':
            i = None
            for _, g in game.genomes:
                if i != P.species.get_species_id(g.key):
                    i = P.species.get_species_id(g.key)
                g.species_id = i
            game.color_species()
    game.clock_speed = CLOCK_SPEED

    while True:
        game.play_step()
        # if not RECORDING:
            # if game.highest_fitness > 9800:
            #     if not game.draw:
            #         game.clock_speed = 60
            #         game.draw = True
                # start_stop_capture()

        # if len(game.players) == 1:
        #     last_player = game.players[0]
        #     last_genome = game.genomes[0]
        if len(game.players) == 0:
            GENERATION += 1
            if RECORDING:
                # start_stop_capture()
                game.clock_speed = CLOCK_SPEED
                game.draw_window_pause()
            else:
                DRAW = game.draw
                CLOCK_SPEED = game.clock_speed
            break


def extract_number(f):
    s = re.findall("\d+$", f)
    return int(s[0]) if s else -1, f


def start_stop_capture():
    global RECORDING
    keyboard = Controller()
    keyboard.press(Key.cmd)
    keyboard.press(Key.alt)
    keyboard.press('r')
    time.sleep(2)
    keyboard.release('r')
    keyboard.release(Key.alt)
    keyboard.release(Key.cmd)
    time.sleep(2)
    RECORDING = not RECORDING


def run(config_path):
    global GENERATION
    global P
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    if len(sys.argv) > 2:
        # checkpointer = neat.Checkpointer(int(sys.argv[3]))
        checkpointer = neat.Checkpointer()
        checkpointer.filename_prefix = os.path.join('trained_models', sys.argv[1], sys.argv[1])

        # Load specified model
        path = os.path.join('trained_models', sys.argv[1])
        if os.path.isdir(path):
            if len(glob.glob(os.path.join(path, sys.argv[1] + '*.pkl'))) != 0:
                # if os.path.isfile(os.path.join(sys.argv[1], sys.argv[1]+'*'+'.pkl')):
                filenames_list = []
                for item in glob.glob(os.path.join(path, sys.argv[1] + '*')):
                    if '.' not in item:
                        filenames_list.append(item)

                P = neat.Checkpointer.restore_checkpoint(max(filenames_list, key=extract_number))

                print(f"\nLoading existing model '{sys.argv[1]}'...")
                filenames_list = [_[:-4] for _ in os.listdir(path) if _.endswith('.pkl')]
                print(max(filenames_list, key=extract_number))
                with open(os.path.join(path, max(filenames_list, key=extract_number) + '.pkl'), "rb") as f:
                    genome = pickle.load(f)
            else:
                print(f"\nCreating new model '{sys.argv[1]}'...")
                P = neat.Population(config)
        else:
            os.mkdir(path)
            print(f"\nCreating new model '{sys.argv[1]}'...")
            P = neat.Population(config)

        P.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        # print(P.best_genome)
        # print(stats.best_genome().fitness)
        # print(P.)
        P.add_reporter(stats)
        P.add_reporter(checkpointer)
        # print(P.species)
        # print(P.population)
        GENERATION = P.generation
        # print(genome.key)
        # print(P.species.get_species(genome.key).members)

        # print(P.species)
        if sys.argv[2] == 'train':
            if len(sys.argv) == 4:
                n = int(sys.argv[3])
            else:
                n = 10

            node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}
            shutil.copyfile('config_file.txt', os.path.join(path, sys.argv[1] + '_config.txt'))

            for i in range(50):
                print(f"\nTraining in process for given model '{sys.argv[1]}' for {n} runs...")
                winner = P.run(main, n)

                visualize.draw_net(config, winner, False, filename=os.path.join(path, sys.argv[1] + str(GENERATION)),
                                   node_names=node_names)
                visualize.plot_stats(stats, ylog=False, view=False,
                                     filename=os.path.join(path, sys.argv[1] + '_avg_fitness' + str(GENERATION)))
                visualize.plot_species(stats, view=False,
                                       filename=os.path.join(path, sys.argv[1] + '_speciation' + str(GENERATION)))
                checkpointer.save_checkpoint(config, P.population, P.species, P.generation)
                with open(os.path.join(path, sys.argv[1] + str(GENERATION) + '.pkl'), "wb") as f:
                    pickle.dump(winner, f)
                    f.close()
            shutil.copyfile('config_file.txt', os.path.join(path, sys.argv[1] + '_config.txt'))

        elif sys.argv[2] == 'play':
            # Convert loaded genome into required data structure

            genomes = [(1, genome)]  # genome.key instead of 1?

            if len(sys.argv) == 4:
                # Call game with only the loaded genome
                n = int(sys.argv[3])
            else:
                n = 10

            print(f"\nPlaying in process for given model '{sys.argv[1]}' for {n} runs...")
            for i in range(n):
                main(genomes, config)
                GENERATION -= 1

    else:
        main(genomes=None, config=None)
        print("\nNo/Invalid Arguments given... Please specify {name of model}, {train/play}, {n_runs}")


if __name__ == '__main__':
    start_time = time.time()
    local_dir = os.path.dirname(__name__)
    config_path = os.path.join(local_dir, "config_file.txt")
    run(config_path)
    print("--- %s minutes ---" % (round(time.time() - start_time)/60), 2)

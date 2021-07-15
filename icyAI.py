import pickle
import neat
import os
import glob
import visualize
import re
import shutil
import time
from classes import IcyTowerGame, menu, screen_options, update_variables, specify_amount

GENERATION = 0
CLOCK_SPEED = 60
DRAW = True
RECORDING = False
RECORDING_COUNTER = 0
PLAY = False
PLAY_AI = False
TRAIN_AI = False
VERSUS = False


def main(genomes, config):
    global GENERATION
    global P
    global CLOCK_SPEED
    global DRAW
    global RECORDING_COUNTER
    global PLAY
    global PLAY_AI
    global TRAIN_AI
    global VERSUS

    game = IcyTowerGame(genomes, config, train=TRAIN_AI, ai=True if TRAIN_AI or PLAY_AI or VERSUS else False, versus=VERSUS)

    game.generation = GENERATION
    if not DRAW:
        game.draw = False

    # if len(sys.argv) > 1:
    if TRAIN_AI:
        i = None
        for _, g in game.genomes:
            if i != P.species.get_species_id(g.key):
                i = P.species.get_species_id(g.key)
            g.species_id = i
        game.color_species()
    game.clock_speed = CLOCK_SPEED

    while True:
        game.play_step()
        # if not RECORDING and GENERATION <= 20:
        #     if not game.draw:
        #         game.clock_speed = 60
        #         game.draw = True
        #     # start_stop_capture()
        #     # RECORDING_COUNTER += 1
        # elif not RECORDING and GENERATION % 10 == 0:
        #     if not game.draw:
        #         game.clock_speed = 60
        #         game.draw = True
        #     # start_stop_capture()
        #     # RECORDING_COUNTER += 1
        # if not RECORDING:
        #     if game.highest_fitness > 6800:
        #         if not game.draw:
        #             game.clock_speed = 60
        #             game.draw = True
        #         # start_stop_capture()
        #         # RECORDING_COUNTER += 1

        # if len(game.players) == 1:
        #     last_player = game.players[0]
        #     last_genome = game.genomes[0]
        if len(game.players) == 0:  # or game.ai_players[0].rect.y > 900 or game.human_players[0].rect.y > 900:
            GENERATION += 1
            if RECORDING:
                # start_stop_capture()
                game.clock_speed = CLOCK_SPEED
                game.draw_window_pause()
            else:
                DRAW = game.draw
                CLOCK_SPEED = game.clock_speed
            break

        if game.versus:
            if game.human_players[0].rect.y > screen_size - game.human_players[0].rect.height or game.ai_players[0].rect.y > screen_size - game.ai_players[0].rect.height:
                break

        if genomes is None:
            if game.human_players[0].rect.y > screen_size - game.human_players[0].rect.height:
                break

        if PLAY_AI:
            if game.ai_players[0].rect.y > screen_size - game.ai_players[0].rect.height:
                break


def extract_number(f):
    s = re.findall("\d+$", f)
    return int(s[0]) if s else -1, f


# def start_stop_capture():
#     # for automated screen capturing on windows
#     global RECORDING
#     keyboard = Controller()
#     keyboard.press(Key.cmd)
#     keyboard.press(Key.alt)
#     keyboard.press('r')
#     time.sleep(2)
#     keyboard.release('r')
#     keyboard.release(Key.alt)
#     keyboard.release(Key.cmd)
#     time.sleep(2)
#     RECORDING = not RECORDING


def run(config_path, open_file, play_ai, train_ai, versus, runs):
    global GENERATION
    global P
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)
    if train_ai or play_ai or versus:
        if train_ai:
            # checkpointer = neat.Checkpointer(int(sys.argv[3]))
            checkpointer = neat.Checkpointer(5)
            model_list = [x[0] for x in os.walk('trained_models')]
            if len(model_list) == 1:
                os.mkdir(os.path.join('trained_models', 'model1'))
                model_name = os.path.join('trained_models', 'model1')
                # model_path = os.path.join('trained_models', 'model1')
            else:
                model_nr = int(max(model_list, key=extract_number)[20:]) + 1
                model_name = max(model_list, key=extract_number)[:20]+str(model_nr)
                os.mkdir(model_name)
                print(f"\nCreating new model '{model_name}'...")
            P = neat.Population(config)
            checkpointer.filename_prefix = os.path.join(model_name, model_name[15:] + '_')

        if play_ai or versus:
            # Load specified model
            # path = os.path.join('trained_models', sys.argv[1])
            # if os.path.isdir(path):

            if len(glob.glob(os.path.join(open_file, open_file.split('/')[-1] + '_*.pkl'))) != 0:
                print("jo")
                # if os.path.isfile(os.path.join(sys.argv[1], sys.argv[1]+'*'+'.pkl')):
                filenames_list = []
                for item in glob.glob(os.path.join(open_file, open_file.split('/')[-1] + '_*')):
                    print(item)
                    if '.' not in item:
                        filenames_list.append(item)
                try:
                    P = neat.Checkpointer.restore_checkpoint(max(filenames_list, key=extract_number))
                except:
                    filenames_list.remove(max(filenames_list, key=extract_number))
                    P = neat.Checkpointer.restore_checkpoint(max(filenames_list, key=extract_number))

                print(f"\nLoading existing model '{max(filenames_list, key=extract_number)}'...")
                filenames_list = [_[:-4] for _ in os.listdir(open_file) if _.endswith('.pkl')]
                # print(max(filenames_list, key=extract_number))
                with open(os.path.join(open_file, max(filenames_list, key=extract_number) + '.pkl'), "rb") as f:
                    genome = pickle.load(f)

        P.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        # print(P.best_genome)
        # print(stats.best_genome().fitness)
        # print(P.)
        P.add_reporter(stats)
        if train_ai:
            P.add_reporter(checkpointer)
        # print(P.species)
        # print(P.population)
        GENERATION = P.generation
        # print(genome.key)
        # print(P.species.get_species(genome.key).members)
        n = runs
        # print(P.species)
        if train_ai:

            node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}
            shutil.copyfile('config_file.txt', os.path.join(model_name, model_name[15:] + '_config.txt'))

            # run the algorithm the specified amount of times x 25 -> after each iteration the best genome is saved
            for i in range(round(n/5)):
                print(f"\nTraining in process for given model '{model_name}' for {n} runs...")
                winner = P.run(main, 5)

                visualize.draw_net(config, winner, False, filename=os.path.join(model_name, model_name[15:] + '_' + str(GENERATION)),
                                   node_names=node_names)
                visualize.plot_stats(stats, ylog=False, view=False,
                                     filename=os.path.join(model_name, model_name[15:] + '_avg_fitness' + str(GENERATION)))
                visualize.plot_species(stats, view=False,
                                       filename=os.path.join(model_name, model_name[15:] + '_speciation' + str(GENERATION)))
                # checkpointer.save_checkpoint(config, P.population, P.species, P.generation)
                with open(os.path.join(model_name, model_name[15:] + '_' + str(GENERATION) + '.pkl'), "wb") as f:
                    pickle.dump(winner, f)
                    f.close()

        elif play_ai or versus:
            # Convert loaded genome into required data structure
            genomes = [(1, genome)]  # genome.key instead of 1?

            print(f"\nPlaying in process for given model '{open_file}' for {n} runs...")
            for i in range(n):
                main(genomes, config)
                GENERATION -= 1

    else:
        # for i in range(runs):
        main(genomes=None, config=None)
            # print("\nNo/Invalid Arguments given... Please specify {name of model}, {train/play}, {n_runs}")
    start_new()


def start_new():
    open_file, PLAY, PLAY_AI, TRAIN_AI, VERSUS = menu()
    runs = 0
    if not PLAY:
        runs = specify_amount()
    run(config_path, open_file, PLAY_AI, TRAIN_AI, VERSUS, runs)


if __name__ == '__main__':
    screen_size = screen_options()
    update_variables(screen_size)
    start_time = time.time()
    local_dir = os.path.dirname(__name__)
    config_path = os.path.join(local_dir, "config_file.txt")
    open_file, PLAY, PLAY_AI, TRAIN_AI, VERSUS = menu()
    runs = 0
    if not PLAY:
        runs = specify_amount()
    run(config_path, open_file, PLAY_AI, TRAIN_AI, VERSUS, runs)
    print("--- %s minutes ---" % (round(time.time() - start_time)/60), 2)

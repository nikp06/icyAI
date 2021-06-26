import pickle
import neat
import sys
import os
import glob
import visualize
from classes import IcyTowerGameAI, IcyTowerGame
GENERATION = 0


def main(genomes, config):
    global GENERATION
    if len(sys.argv) > 1:
        if sys.argv[2] == 'train':
            game = IcyTowerGame(genomes, config, train=True, ai=True, versus=False)
        elif sys.argv[2] == 'play':
            if len(sys.argv) > 4:
                if sys.argv[4] == 'versus':
                    game = IcyTowerGame(genomes, config, train=False, ai=True, versus=True)
                else:
                    game = IcyTowerGame(genomes, config, train=False, ai=True, versus=False)
            else:
                game = IcyTowerGame(genomes, config, train=False, ai=True, versus=False)
    else:
        game = IcyTowerGame(genomes, config, train=False, ai=False, versus=False)
    # game = Test(genomes, config, train)
    game.generation = GENERATION

    # if game.ai:
    #     while True:
    #         game.play_step()
    #         if len(game.players) == 0:
    #             GENERATION += 1
    #             break
    # else:
    while True:
        game.play_step()
        if len(game.players) == 0:
            GENERATION += 1
            break



def run(config_path):
    global GENERATION
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_path)

    if len(sys.argv) > 2:
        # checkpointer = neat.Checkpointer(int(sys.argv[3]))
        checkpointer = neat.Checkpointer()
        checkpointer.filename_prefix = os.path.join('trained_models', sys.argv[1], sys.argv[1])

        # Load specified model
        path = os.path.join('trained_models', sys.argv[1])
        if os.path.isdir(path):
            if len(glob.glob(os.path.join(path, sys.argv[1]+'*.pkl'))) != 0:
            # if os.path.isfile(os.path.join(sys.argv[1], sys.argv[1]+'*'+'.pkl')):
                filenamesList = []
                for item in glob.glob(os.path.join(path, sys.argv[1] + '*')):
                    if '.' not in item:
                        filenamesList.append(item)
                print(filenamesList[-1])
                p = neat.Checkpointer.restore_checkpoint(filenamesList[-1])

                print(f"\nLoading existing model '{sys.argv[1]}'...")
                filenamesList = [_ for _ in os.listdir(path) if _.endswith('.pkl')]

                with open(os.path.join(path, filenamesList[-1]), "rb") as f:
                    genome = pickle.load(f)
            else:
                print(f"\nCreating new model '{sys.argv[1]}'...")
                p = neat.Population(config)
        else:
            os.mkdir(path)
            print(f"\nCreating new model '{sys.argv[1]}'...")
            p = neat.Population(config)

        p.add_reporter(neat.StdOutReporter(True))
        stats = neat.StatisticsReporter()
        p.add_reporter(stats)
        p.add_reporter(checkpointer)
        GENERATION = p.generation
        if sys.argv[2] == 'train':
            if len(sys.argv) == 4:
                n = int(sys.argv[3])
            else:
                n = 10

            node_names = {-1: 'A', -2: 'B', 0: 'A XOR B'}

            for i in range(5):
                print(f"\nTraining in process for given model '{sys.argv[1]}' for {n} runs...")
                winner = p.run(main, n)

                visualize.draw_net(config, winner, False, filename=os.path.join(path, sys.argv[1]+str(GENERATION)),
                                   node_names=node_names)
                visualize.plot_stats(stats, ylog=False, view=False,
                                     filename=os.path.join(path, sys.argv[1]+'_avg_fitness'+str(GENERATION)))
                visualize.plot_species(stats, view=False,
                                       filename=os.path.join(path, sys.argv[1]+'_speciation'+str(GENERATION)))
                checkpointer.save_checkpoint(config, p.population, p.species, p.generation)
                with open(os.path.join(path, sys.argv[1]+str(GENERATION)+'.pkl'), "wb") as f:
                    pickle.dump(winner, f)
                    f.close()

        elif sys.argv[2] == 'play':
            train = False
            # Convert loaded genome into required data structure
            genomes = [(1, genome)]

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
    local_dir = os.path.dirname(__name__)
    config_path = os.path.join(local_dir, "config_file.txt")
    run(config_path)

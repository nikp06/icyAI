import torch
import random
import numpy as np
from collections import deque
from gameAI import IcyTowerGameAI, Player, Tile, Wall
from model import Linear_QNet, QTrainer
from helper import plot

MAX_MEMORY = 100_000 # TODO: ändern
BATCH_SIZE = 1000 # TODO: ändern
LR = 0.001 # TODO: ändern

class Agent:

    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.8  # discount rate (play around with it; smaller than one; try .8)
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft automatically if exceeds memory
        self.model = Linear_QNet(4, 256, 3)  # TODO: ändern in 37 input
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        # TODO: model, trainer

    def get_state(self, game):
        # TODO: noch onfloor oder nicht, damit er checkt, dass er nicht springen soll, wenn in der Luft
        # TODO: noch bonusy damit er checkt bei welchem momentum gesprungen werden soll
        # player details
        x = game.player.rect.x
        y = game.player.rect.y
        # velocity details
        vel_x = game.player.vel_x
        vel_y = game.player.vel_y
        state = [x, y, vel_x, vel_y]
        # tile details
        # print(len(game.tiles))
        # for tile in game.tiles:  # TODO: wieder reinnehmen
        #     state.append(tile.rect.x)
        #     state.append(tile.rect.y)
        #     state.append(tile.tile_width)
        # print(state)

        return np.array(state, dtype=int) # TODO: ändern (vielleicht besser nicht als int?)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))  # popleft if max memory is reached

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)  # returns list of tuples
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        # random moves for tradeoff between exploration and exploitation
        self.epsilon = 80 - self.n_games # TODO: ändern (randomness)
        final_move = [0, 0, 0]
        # if epsilon negative no random moves anymore
        if random.randint(0, 200) < self.epsilon: # TODO: ändern
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1

        return final_move


def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = IcyTowerGameAI()
    while True:
        # get old state
        state_old = agent.get_state(game)

        # get move
        final_move = agent.get_action(state_old)

        # perform move and get new state
        reward, done, score = game.play_step(final_move)
        state_new = agent.get_state(game)

        # train short memory
        agent.train_short_memory(state_old, final_move, reward, state_new, done)

        # remember and store in memory
        agent.remember(state_old, final_move, reward, state_new, done)

        if done:
            # train long memory (replay memory / experienced replay)
            # plot result
            game.reset()
            agent.n_games += 1
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.n_games, 'Score', score, 'Record', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)


if __name__ == '__main__':
    train()

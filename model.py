import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import os

class Linear_QNet(nn.Module):
    def __init__(self, input_size, hidden_size, output_size):
        super().__init__()
        self.linear1 = nn.Linear(input_size, hidden_size) # TODO: ändern
        self.linear2 = nn.Linear(hidden_size, output_size) # TODO: ändern

    def forward(self, x):
        x = F.relu(self.linear1(x)) # TODO: ändern
        x = self.linear2(x)
        return x

    def save(self, file_name='model.pth'):
        model_folder_path = './model'
        if not os.path.exists(model_folder_path):
            os.makedirs(model_folder_path)

        file_name = os.path.join(model_folder_path, file_name)
        torch.save(self.state_dict(), file_name)


class QTrainer:
    def __init__(self, model, lr, gamma):
        self.lr = lr
        self.gamma = gamma
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=self.lr) # TODO: ändern
        self.criterion = nn.MSELoss() # TODO: ändern

    def train_step(self, state, action, reward, next_state, done):  # either tuple or list of tuples
        state = torch.tensor(state, dtype=torch.float)
        next_state = torch.tensor(next_state, dtype=torch.float)
        action = torch.tensor(action, dtype=torch.long)
        reward = torch.tensor(reward, dtype=torch.float)
        # (n, x)

        if len(state.shape) == 1:
            # only one dimension -> we have to append one dimension (1, x)
            state = torch.unsqueeze(state, 0)
            next_state = torch.unsqueeze(next_state, 0)
            action = torch.unsqueeze(action, 0)
            reward = torch.unsqueeze(reward, 0)
            done = (done, )

        # video 4 -> min 17~
        # 1: predicted Q values with current state
        pred = self.model(state)

        target = pred.clone()
        for idx in range(len(done)):
            q_new = reward[idx]
            if not done[idx]:
                q_new = reward[idx] + self.gamma * torch.max(self.model(next_state[idx]))

            target[idx][torch.argmax(action).item()] = q_new

        # 2: Q_new = r + y * max(next_predicted Q value) -> only do this if not done!
        # pred.clone()
        # preds[argmax(action)] = Q_new

        self.optimizer.zero_grad() # TODO: ändern
        loss = self.criterion(target, pred) # TODO: ändern
        loss.backward() # TODO: ändern

        self.optimizer.step()



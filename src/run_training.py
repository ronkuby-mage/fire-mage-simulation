import argparse

import ray
import gym
import numpy as np
from gym.spaces import Discrete, Box
from fire_env import FireMageEnv
from ray.rllib.models.preprocessors import get_preprocessor
from ray.rllib.models.torch.recurrent_torch_model import RecurrentTorchModel
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.utils.annotations import override
from ray.rllib.utils import try_import_torch
from ray.rllib.models import ModelCatalog
import ray.tune as tune

torch, nn = try_import_torch()

parser = argparse.ArgumentParser()
parser.add_argument("--run", type=str, default="PPO")
parser.add_argument("--env", type=str, default="repeat_initial")
parser.add_argument("--stop", type=int, default=90)
parser.add_argument("--num-cpus", type=int, default=0)
parser.add_argument("--fc-size", type=int, default=64)
parser.add_argument("--lstm-cell-size", type=int, default=256)


class RNNModel(RecurrentTorchModel):
    def __init__(self,
                 obs_space,
                 action_space,
                 num_outputs,
                 model_config,
                 name,
                 fc_size=64,
                 lstm_state_size=256):
        super().__init__(obs_space, action_space, num_outputs, model_config,
                         name)

        self.obs_size = get_preprocessor(obs_space)(obs_space).size
        self.fc_size = fc_size
        self.lstm_state_size = lstm_state_size

        # Build the Module from fc + LSTM + 2xfc (action + value outs).
        self.fc1 = nn.Linear(self.obs_size, self.fc_size)
        self.lstm = nn.LSTM(
            self.fc_size, self.lstm_state_size, batch_first=True)
        self.action_branch = nn.Linear(self.lstm_state_size, num_outputs)
        self.value_branch = nn.Linear(self.lstm_state_size, 1)
        # Store the value output to save an extra forward pass.
        self._cur_value = None

    @override(ModelV2)
    def get_initial_state(self):
        # make hidden states on same device as model
        h = [
            self.fc1.weight.new(1, self.lstm_state_size).zero_().squeeze(0),
            self.fc1.weight.new(1, self.lstm_state_size).zero_().squeeze(0)
        ]
        return h

    @override(ModelV2)
    def value_function(self):
        assert self._cur_value is not None, "must call forward() first"
        return self._cur_value

    @override(RecurrentTorchModel)
    def forward_rnn(self, inputs, state, seq_lens):
        """Feeds `inputs` (B x T x ..) through the Gru Unit.

        Returns the resulting outputs as a sequence (B x T x ...).
        Values are stored in self._cur_value in simple (B) shape (where B
        contains both the B and T dims!).

        Returns:
            NN Outputs (B x T x ...) as sequence.
            The state batches as a List of two items (c- and h-states).
        """
        x = nn.functional.relu(self.fc1(inputs))
        lstm_out = self.lstm(
            x, [torch.unsqueeze(state[0], 0),
                torch.unsqueeze(state[1], 0)])
        action_out = self.action_branch(lstm_out[0])
        self._cur_value = torch.reshape(self.value_branch(lstm_out[0]), [-1])
        return action_out, [
            torch.squeeze(lstm_out[1][0], 0),
            torch.squeeze(lstm_out[1][1], 0)
        ]

class SimpleCorridor(gym.Env):
    """Example of a custom env in which you have to walk down a corridor.

    You can configure the length of the corridor via the env config."""

    def __init__(self, config):
        self.end_pos = config["corridor_length"]
        self.cur_pos = 0
        self.action_space = Discrete(2)
        self.observation_space = Box(
            0.0, self.end_pos, shape=(1, ), dtype=np.float32)

    def reset(self):
        self.cur_pos = 0
        return [self.cur_pos]

    def step(self, action):
        assert action in [0, 1], action
        if action == 0 and self.cur_pos > 0:
            self.cur_pos -= 1
        elif action == 1:
            self.cur_pos += 1
        done = self.cur_pos >= self.end_pos
        return [self.cur_pos], 1 if done else 0, done, {}
    
if __name__ == "__main__":
    args = parser.parse_args()

    ray.init(num_cpus=args.num_cpus or None)
    ModelCatalog.register_custom_model("rnn", RNNModel)
    config = {
        'num_mages': 5,
        'duration_average': 60.0,
        'duration_sigma': 12.0,
        'sp_average': 650.0,
        'sp_sigma': 100.0,
        'hit_average': 0.96,
        'hit_sigma': 0.015,
        'crit_average': 0.30,
        'crit_sigma': 0.08,
        'response_time': 1.0,
        'react_time': 0.05,
        'power_infusion': 0,
        'mqg': 0}

    scon = {'corridor_length': 9}
    
    tune.register_env(
        "fire_mage", lambda _: FireMageEnv(config))
    tune.register_env(
        "blea", lambda _: SimpleCorridor(scon))

    rnn_config = {
        "env": "fire_mage",
        "use_pytorch": True,
        "num_workers": 6,
        "num_envs_per_worker": 20,
        "gamma": 0.9,
        "entropy_coeff": 0.0001,
        "model": {
            "custom_model": "rnn",
            "max_seq_len": 500,
            "lstm_use_prev_action_reward": "store_true",
            "custom_options": {
                "fc_size": args.fc_size,
                "lstm_state_size": args.lstm_cell_size,
            }
        },
        "lr": 3e-4,
        "num_sgd_iter": 5,
        "vf_loss_coeff": 0.0003,
        "log_level": "WARN",
        "clip_param": 10.0,
        "vf_clip_param": 10.0
    }

    tune.run(
        args.run,
        stop={
            "episode_reward_mean": args.stop,
            "timesteps_total": 100000
        },
        checkpoint_at_end=True,
        config=rnn_config,
    )

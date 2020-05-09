import argparse

import sys
import ray
from fire_env import FireMageEnv
from ray.rllib.models.preprocessors import get_preprocessor
from ray.rllib.models.torch.recurrent_torch_model import RecurrentTorchModel
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.utils.annotations import override
from ray.rllib.utils import try_import_torch
from ray.rllib.models import ModelCatalog
from ray.rllib.agents.ppo import PPOTrainer
import ray.tune as tune

torch, nn = try_import_torch()

parser = argparse.ArgumentParser()
parser.add_argument("--run", type=str, default="PPO")
parser.add_argument("--stop", type=int, default=9000)
parser.add_argument("--num-cpus", type=int, default=0)
parser.add_argument("--fc-size", type=int, default=64)
parser.add_argument("--lstm-cell-size", type=int, default=64)

class RNNModel(RecurrentTorchModel):
    def __init__(self,
                 obs_space,
                 action_space,
                 num_outputs,
                 model_config,
                 name,
                 fc_size=64,
                 lstm_state_size=64):
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
    
if __name__ == "__main__":
    args = parser.parse_args()

    ray.init(num_cpus=args.num_cpus or None)
    ModelCatalog.register_custom_model("rnn", RNNModel)
    config = {
        'num_mages': 5,
        'duration_average': 60.0,
        'duration_sigma': 6.0,
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

    tune.register_env(
        "fire_mage", lambda _: FireMageEnv(config))

    rnn_config = {
        "env": "fire_mage",
        "use_pytorch": True,
        "num_workers": 6,
        "num_envs_per_worker": 20,
        "use_gae": True,
        "lambda": 0.97,
        "gamma": 0.995,
        "entropy_coeff": 0.0,
        "model": {
            "custom_model": "rnn",
            "max_seq_len": 500,
            "lstm_use_prev_action_reward": "store_true",
            "custom_options": {
                "fc_size": args.fc_size,
                "lstm_state_size": args.lstm_cell_size,
            }
        },
        "lr": 0.001,
        #"lr_schedule": [[  0*264000, 0.0005],
        #                [ 75*264000, 0.00005],
        #                [150*264000, 0.000005],
        #                [225*264000, 0.0000005]],
        "num_sgd_iter": 5,
        "vf_loss_coeff": 0.0003,
        "log_level": "WARN",
        #"train_batch_size": 65536,
        #"sgd_minibatch_size": 32768,
        "train_batch_size": 262144,
        "sgd_minibatch_size": 65536,
        "clip_param": 10.0,
        "vf_clip_param": 10.0
    }

    trainer = PPOTrainer(env="fire_mage", config=rnn_config)
    #trainer.restore('/home/ronkuby/ray_results/PPO/PPO_fire_mage_0_2020-05-08_19-41-57c2yes9uk/checkpoint_100/checkpoint-100')
    for ii in range(300):
        result = trainer.train()
        print(ii, result['episode_reward_mean'])
        sys.stdout.flush()
        if ((ii + 1)%25) == 0:
            trainer.save('./checkpoints2')

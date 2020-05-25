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
from copy import deepcopy

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
        'num_mages': 6,
        'duration_average': 40.0,
        'duration_sigma': 3.0,
        'sp_average': 750.0,
        'sp_sigma': 100.0,
        'hit_average': 0.99,
        'hit_sigma': 0.0,
        'crit_average': 0.30,
        'crit_sigma': 0.08,
        'response_time': 1.0,
        'react_time': 0.05,
        'power_infusion': 2,
        'mqg': 5}

    tune.register_env(
        "fire_mage", lambda _: FireMageEnv(config))

    ff = FireMageEnv(config)
    env_list = []
    for ii in range(config['num_mages']):
        name = 'mage_' + str(ii + 1)
        if config['num_mages'] - ii <= config['power_infusion']:
            key = "all"
        elif config['num_mages'] - ii <= config['mqg']:
            key = "mqg"
        else:
            key = "none"
        entry = (None, ff.obs_space(key), ff.act_space(key), {})
        env_list.append((name, entry))
    env_list = dict(env_list)
    print(env_list)
    
    rnn_config = {
        "env": "fire_mage",
        "use_pytorch": True,
        "num_workers": 6,
        "num_envs_per_worker": 20,
        "use_gae": True,
        "lambda": 0.97,
        "gamma": 0.995,
        "entropy_coeff": 0.01,
        "model": {
            "custom_model": "rnn",
            "max_seq_len": 500,
            "lstm_use_prev_action_reward": "store_true",
            "custom_options": {
                "fc_size": args.fc_size,
                "lstm_state_size": args.lstm_cell_size,
            }
        },
        "multiagent": {
            "policies": env_list,
            "policy_mapping_fn": lambda agent_id: agent_id
        },
        "lr": 0.0001, # started at 0.0001
        "num_sgd_iter": 5,
        "vf_loss_coeff": 0.001,
        "log_level": "WARN",
        "train_batch_size": 512,
        "sgd_minibatch_size": 32,
        "clip_param": 0.3,
        "vf_clip_param": 10.0
    }

    last_improve = 150

    iteration = 22
    improved = 0
    while True:
        trainer = PPOTrainer(env="fire_mage", config=rnn_config)
        print(dir(trainer))
        #trainer.restore('./checkpoints_flush/checkpoint_379/checkpoint-379')

        step = 0
        best_val = 0.0
        if False:
            save_0 = trainer.save_to_object()
        while True:
            if False:
                save_0 = trainer.save_to_object()
                result = trainer.train()
                while result['episode_reward_mean'] > best_val:
                    print('UPENING')
                    best_save = deepcopy(save_0)
                    best_val = result['episode_reward_mean']
                    save_0 = trainer.save_to_object()
                    trainer.save('./checkpoints_flush')
                    result = trainer.train()
                print('REVERTING')
                trainer.restore_from_object(best_save)
            else:
                result = trainer.train()
                if result['episode_reward_mean'] > best_val:
                    improved = step
                    best_val = result['episode_reward_mean']
                    trainer.save('./checkpoints_iter_' + str(iteration))
                elif step > improved + last_improve:
                    trainer.save('./checkpoints_iter_' + str(iteration))
                    break
                step += 1
            print(step, best_val, result['episode_reward_mean'])
            sys.stdout.flush()

        trainer.stop()
        print('MARK', iteration, best_val)
        iteration += 1

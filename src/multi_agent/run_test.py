import argparse

import ray
import numpy as np
from fire_env import FireMageEnv
from ray.rllib.models.preprocessors import get_preprocessor
from ray.rllib.models.torch.recurrent_torch_model import RecurrentTorchModel
from ray.rllib.models.modelv2 import ModelV2
from ray.rllib.utils.annotations import override
from ray.rllib.utils import try_import_torch
from ray.rllib.models import ModelCatalog
from ray.rllib.agents.ppo import PPOTrainer
from ray import tune
from copy import deepcopy

torch, nn = try_import_torch()

parser = argparse.ArgumentParser()
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
    
    rnn_config = {
        "env": "fire_mage",
        "use_pytorch": True,
        "num_workers": 0,
        "num_envs_per_worker": 1,
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
        "multiagent": {
            "policies": env_list,
            "policy_mapping_fn": lambda agent_id: agent_id
        },
        "lr": 3e-4,
        "num_sgd_iter": 5,
        "vf_loss_coeff": 0.0003,
        "log_level": "WARN",
        "clip_param": 10.0,
        "vf_clip_param": 10.0
    }

    trainer = PPOTrainer(env="fire_mage", config=rnn_config)
    trainer.restore('./checkpoints_iter_24/checkpoint_138/checkpoint-138')
    #trainer.restore('./checkpoints_iter_20/checkpoint_325/checkpoint-325')
    #trainer.restore('./checkpoints_iter_13/checkpoint_193/checkpoint-193')
    #trainer.restore('./checkpoints_iter_12/checkpoint_206/checkpoint-206')

    state_list = []
    for key, val in env_list.items():
        dummy_model = RNNModel(val[1],
                               val[2],
                               0,
                               rnn_config['model'],
                               'happy')
        state = dummy_model.get_initial_state()
        state_list.append((key, [s.detach().numpy() for s in state]))
    state_list = dict(state_list)
    iters = 100
    tdiff = 0.0
    tot = [0.0, 0.0]
    for i in range(iters):
        obs = ff.reset()
        r1 = 0.0
        state2 = deepcopy(state_list)
        while True:
            policy_id = list(obs.keys())[0]
            logits = trainer.compute_action(obs[policy_id],
                                            state2[policy_id],
                                            policy_id=policy_id,
                                            full_fetch=False)
            state2[policy_id] = logits[1]
            turn = int(list(obs.values())[0][6]/0.025 + 0.0125)
            if turn < 2:
                action = 0
            elif turn == 2:
                action = 6
            elif len(obs) == 13:
                if turn == 3:
                    action = 4
                elif turn == 4:
                    action = 7
                elif turn == 5:
                    action = 8
                else:
                    action = logits[0]
            elif len(obs) == 11:
                if turn == 3:
                    action = 4
                elif turn == 4:
                    action = 7
                else:
                    action = logits[0]
            else:
                if turn == 3:
                    action = 4
                else:
                    action = logits[0]
            action = logits[0]
            obs, reward, done, info = ff.step(action)
            if done['__all__']:
                break
            r1 += list(reward.values())[0]
        #ff.render()
        #foof()
        t1 = ff.total()
        tot[0] += ff.total()
        obs = ff.reset(retain_stats=True)
        r2 = 0.0
        
        while True:
            mn = int(list(obs.keys())[0][5]) - 1
            obs = list(obs.values())[0]
            turn = int(obs[6]/0.025 + 0.0125)
            if turn < 2:
                action = 0
            elif turn == 2:
                action = 6
            elif len(obs) == 13:
                if turn == 3:
                    action = 1
                elif turn == 4:
                    action = 7
                elif turn == 5:
                    action = 8
                else:
                    action = 2
            elif len(obs) == 11:
                if turn == 3:
                    action = 1
                elif turn == 4:
                    action = 7
                else:
                    action = 2
            else:
                if turn == 3:
                    action = 1
                elif turn == 11 and mn == 0:
                    action = 0
                else:
                    action = 2

            obs, reward, done, info = ff.step(action)
            if done['__all__']:
                #ff.render()
                #dfoof()
                break
            r2 += list(reward.values())[0]
        print('{:3d}: {:5.3f} {:5.3f}'.format(i + 1, t1/ff.total(), r1/r2))
        tot[1] += ff.total()
        tdiff += t1 - ff.total()
        #ff.render()
    print('dd', tot[1])
    print('total value: {:.0f}  {:.3f}'.format(tdiff/iters, tot[0]/tot[1]))


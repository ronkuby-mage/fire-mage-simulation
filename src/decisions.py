import numpy as np

class Decider():

    def __init__(self, C, rotation, array_shape, configuration):
        self._C = C
        self._rotation = rotation
        self._stage = np.zeros(array_shape, dtype=np.int32)
        num_mages = array_shape[1]
        self._config = [config for config in configuration \
                        if config['num_mages'] == num_mages][0]

    def _common(self, arrays, still_going, next_hit):
        C = self._C

        decisions = -np.ones(still_going.size).astype(np.int32)

        stage = self._stage[still_going, next_hit]
        action = np.array(self._rotation['initial']['common'])[stage]
        
        # SCORCH_STACK
        #    assume here that any actions occurring before scorch stack are one
        #    cast since the exception would be cooldowns and who would cast their
        #    cooldowns before scorch stack?
        ss_actions = arrays['player']['cast_number'][still_going, next_hit] - stage
        ss_needed = C._SCORCHES[self._config['num_mages']]
        scorch_stage = action == "stack_scorch"
        do_stack = scorch_stage & (ss_actions < ss_needed)
        stack = np.where(do_stack)[0]
        if stack.size:
            decisions[do_stack] = C._CAST_SCORCH

        # no more scorches
        no_stack = np.where(scorch_stage & np.logical_not(do_stack))[0]
        if no_stack.size:
            self._stage[still_going[no_stack], next_hit[no_stack]] += 1

        # other actions
        regular = np.where(np.logical_not(scorch_stage))[0]
        if regular.size:
            decisions[regular] = [C._DECIDE[ar] for ar in action[regular]]
            self._stage[still_going[regular], next_hit[regular]] += 1

        return decisions

    def _special(self, arrays, still_going, next_hit):
        C = self._C

        decisions = -np.ones(still_going.size).astype(np.int32)
        stage = self._stage[still_going, next_hit] - len(self._rotation['initial']['common'])

        if "have_pi" in self._rotation['initial']:
            has_pi = next_hit >= self._config['num_mages'] - self._config['num_pi']
            other = np.where(np.logical_not(has_pi))[0]

            pi = np.where(has_pi)[0]
            if pi.size:
                action = np.array(self._rotation['initial']['have_pi'])[stage[pi]]
                cooldown_stage = action == "cooldowns"
                cooldown = np.where(cooldown_stage)[0]

                if cooldown.size:
                    mod_sg = still_going[pi][cooldown]
                    mod_nh = next_hit[pi][cooldown]
                    buff_avail = np.stack(arrays['player']['buff_avail'], axis=2)[mod_sg, mod_nh, :]
                    is_buff = np.max(buff_avail, axis=1) > 0
                    buff = np.where(is_buff)[0]
                    if buff.size:
                        cast = C._BUFF_CAST_TYPE[np.argmax(buff_avail[buff, :], axis=1)]
                        decisions[pi[cooldown[buff]]] = cast

                    # no cooldowns left
                    not_buff = np.where(np.logical_not(is_buff))[0]
                    if not_buff.size:
                        mod_sg = still_going[pi][cooldown][not_buff]
                        mod_nh = next_hit[pi][cooldown][not_buff]
                        self._stage[mod_sg, mod_nh] += 1
                
                not_cooldown = np.where(np.logical_not(cooldown_stage))[0]
                if not_cooldown.size:
                    decisions[pi[not_cooldown]] = [C._DECIDE[an] for an in action[not_cooldown]]
                    self._stage[still_going[pi][not_cooldown], next_hit[pi][not_cooldown]] += 1
        else:
            other = np.arange(decisions.size)

        if not other.size:
            return decisions
            
        action = np.array(self._rotation['initial']['other'])[stage[other]]
        frostbolt_stack = action == "frostbolt_to_stack"
        frostbolt = np.where(frostbolt_stack)[0]

        if frostbolt.size:
            mod_sg = still_going[other][frostbolt]
            mod_nh = next_hit[other][frostbolt]
            not_stack = arrays['boss']['ignite_count'][still_going[other][frostbolt]] < C._IGNITE_STACK
            nstack = np.where(not_stack)[0]
            if nstack.size:
                decisions[other[frostbolt[nstack]]] = C._CAST_FROSTBOLT

            stack = np.where(np.logical_not(not_stack))[0]
            if stack.size:
                self._stage[mod_sg[stack], mod_nh[stack]] += 1

        regular = np.where(np.logical_not(frostbolt_stack))[0]
        if regular.size:
            action = np.array(self._rotation['initial']['have_pi'])[stage[other][regular]]
            cooldown_stage = action == "cooldowns"
            cooldown = np.where(cooldown_stage)[0]

            if cooldown.size:
                mod_sg = still_going[other][regular][cooldown]
                mod_nh = next_hit[other][regular][cooldown]
                buff_avail = np.stack(arrays['player']['buff_avail'], axis=2)[mod_sg, mod_nh, :]
                is_buff = np.max(buff_avail, axis=1) > 0
                buff = np.where(is_buff)[0]
                if buff.size:
                    cast = C._BUFF_CAST_TYPE[np.argmax(buff_avail[buff, :], axis=1)]
                    decisions[other[regular[cooldown[buff]]]] = cast

                # no cooldowns left
                not_buff = np.where(np.logical_not(is_buff))[0]
                if not_buff.size:
                    mod_sg = still_going[other][regular][cooldown][not_buff]
                    mod_nh = next_hit[other][regular][cooldown][not_buff]
                    self._stage[mod_sg, mod_nh] += 1
                
            not_cooldown = np.where(np.logical_not(cooldown_stage))[0]
            if not_cooldown.size:
                # not currently using this -- "other" is all special actions
                decisions[other[regular[not_cooldown]]] = [C._DECIDE[an] for an in action[not_cooldown]]
                self._stage[still_going[other][regular][not_cooldown],
                            next_hit[other][regular][not_cooldown]] += 1

        return decisions

    def _continue(self, arrays, still_going, next_hit):
        C = self._C
        decisions = -np.ones(still_going.size).astype(np.int32)

        if "special" in self._rotation['continuing']:
            is_special = next_hit == self._rotation['continuing']['special']['slot']
            not_special = np.where(np.logical_not(is_special))[0]

            special = np.where(is_special)[0]
            if special.size:
                if self._rotation['continuing']['special']['value'] == 'maintain_scorch':
                    need_scorch = (arrays['boss']['scorch_timer'][still_going[special]] < C._MAX_SCORCH_REMAIN) |\
                                  (arrays['boss']['scorch_count'][still_going[special]] < C._SCORCH_STACK)
                    need_scorch &= arrays['player']['spell_type'][still_going[special], next_hit[special]] != C._CAST_SCORCH
                    no_scorch = np.where(np.logical_not(need_scorch))[0]
                    scorch = np.where(need_scorch)[0]
                    if scorch.size:
                        decisions[special[scorch]] = C._CAST_SCORCH
                    if no_scorch.size:
                        decisions[special[no_scorch]] = C._DECIDE[self._rotation['continuing']['default']]
                else:
                    decisions[special] = C._DECIDE[self._rotation['continuing']['special']['value']]
        else:
            not_special = np.arange(decisions.size)

        if not_special.size:
            decisions[not_special] = C._DECIDE[self._rotation['continuing']['default']]

        return decisions
        
    def get_decisions(self, arrays, still_going):
        C = self._C
        rotation = self._rotation
        decisions = -np.ones(still_going.size).astype(np.int32)

        next_hit = np.argmin(arrays['player']['cast_timer'][still_going, :], axis=1)

        while True:
            no_decision = np.where(decisions < 0)[0]
            mod_sg = still_going[no_decision]
            mod_nh = next_hit[no_decision]

            # initial['other'] and any other non-common sequence must
            # be the same number of stages
            pre_cont = len(self._rotation['initial']['common'] + self._rotation['initial']['other'])
            out_initial = self._stage[mod_sg, mod_nh] >= pre_cont
            cont = np.where(out_initial)[0]
            if cont.size:
                decisions[no_decision[cont]] = self._continue(arrays, mod_sg[cont], mod_nh[cont])

            init = np.where(np.logical_not(out_initial))[0]
            mod_sg = mod_sg[init]
            mod_nh = mod_nh[init]
            
            common = self._stage[mod_sg, mod_nh] < len(rotation['initial']['common'])
            is_com = np.where(common)[0]
            if is_com.size:
                decisions[no_decision[init[is_com]]] = self._common(arrays,
                                                                    mod_sg[is_com],
                                                                    mod_nh[is_com])

            spec = np.where(np.logical_not(common))[0]
            if spec.size:
                decisions[no_decision[init[spec]]] = self._special(arrays,
                                                                   mod_sg[spec],
                                                                   mod_nh[spec])
            if not (decisions < 0).any():
                break
            
        return decisions, next_hit

import os
import numpy as np
import json
import pickle
from sklearn.linear_model import LinearRegression
from itertools import product, combinations_with_replacement

def find_combinations_util(arr, index, num, reducedNum):
    if (reducedNum < 0):
        return []
    if (reducedNum == 0):
        return [tuple([arr[i] for i in range(index)])]
    prev = 1 if index == 0 else arr[index - 1]
    combs = []
    for k in range(prev, num + 1):
        arr[index] = k;
        combs += find_combinations_util(arr, index + 1, num, reducedNum - k)

    return combs

def find_combs(n):
    arr = [0]*n
    combs = find_combinations_util(arr, 0, n, n)
    combs = [sorted(aa, reverse=True) for aa in combs]
    return sorted(combs, reverse=True)

def range_norm(vals, rang):
    return 4.0*(vals - rang[0])/(rang[1] - rang[0]) - 2.0

def poly(order, values):
    value_list = []
    for jdx, val in enumerate(values):
        value_list.append([chr(ord('A') + jdx) + str(idx) for idx in range(val)])
    value_index = list(range(len(value_list)))
    tind = 0
    outs = [[0]]
    prefs = set([-1])
    for torder in range(order):
        for comb in find_combs(torder + 1):
            for ptype in combinations_with_replacement(value_index, len(comb)):
                if len(set(ptype)) < len(ptype):
                    continue
                perms = []
                for set_ind, count in zip(ptype, comb):
                    ll = []
                    for comb2 in find_combs(count):
                        for perm in combinations_with_replacement(value_list[set_ind], len(comb2)):
                            if len(set(perm)) < len(perm):
                                continue
                            sf = ''
                            for val, p in zip(perm, comb2):
                                sf += ' ' + str(p) + str(val)
                            ll.append(str(tind) + ':' + sf)
                        tind += 1
                    perms.append(ll)
                for tt in product(*perms):
                    llist = [tt[0]] + [dd.split(': ')[-1] for dd in tt[1:]]
                    llist = ' '.join(llist)
                    cc = llist.split(': ')
                    if cc[0] not in prefs:
                        prefs.add(cc[0])
                    output = [len(prefs) - 1]
                    cca = cc[1].split(' ')
                    for entry in cca:
                        output.append((ord(entry[1]) - ord('A'),
                                       ord(entry[2]) - ord('0'),
                                       float(ord(entry[0]) - ord('0'))))
                    outs.append(output)
    return outs

class Fitter():

    def __init__(self, params):
        self._params = params
        self._load()
        
    def _load(self):
        run_name = self._params['run_name']
        dfn = self._params['mc_dir'] + run_name
        cfn = self._params['config_dir'] + run_name + '.json'
        with open(cfn, "rt") as fid:
            config = json.load(fid)
        sp_range = config['stats']['spell_power']['clip']
        hit_range = config['stats']['hit_chance']['clip']
        crit_range = config['stats']['crit_chance']['clip']
        dur_range = config['timing']['duration']['clip']

        values = []
        ignites = []
        sps = []
        hits = []
        crits = []
        durs = []
        for fn in os.listdir(dfn):
            filename = os.path.join(dfn, fn)

            with open(filename, "rb") as fid:
                while fid.tell() < os.fstat(fid.fileno()).st_size and\
                    len(durs) < self._params['num_load']:
                    value = pickle.load(fid)
                    values.append(value[0])
                    ignites.append(value[1])
                    args = pickle.load(fid)
                    sp = range_norm(np.array(args['spell_power']['fixed']), sp_range)
                    hit = range_norm(np.array(args['hit_chance']['fixed']), hit_range)
                    crit = range_norm(np.array(args['crit_chance']['fixed']), crit_range)
                    dur = range_norm(np.array(args['timing']['duration']['mean']), dur_range)
                    sps.append(sp)
                    hits.append(hit)
                    crits.append(crit)
                    durs.append(dur)
            if len(durs) >= self._params['num_load']:
                break

        sps = np.stack(sps)
        hits = np.stack(hits)
        crits = np.stack(crits)
        durs = np.stack(durs)
        g2_size = args["num_mages"]["num_pi"]
        g1_size = args["num_mages"]["num_mages"] - g2_size
        num_mages = args["num_mages"]["num_mages"]

        self._arrays = [sps[:, :g1_size],
                  sps[:, g1_size:],
                  hits[:, :g1_size],
                  hits[:, g1_size:],
                  crits[:, :g1_size],
                  crits[:, g1_size:],
                  durs[:, None]]
        self._values = values
        self._ignites = ignites
        self._num_mages = num_mages
        self._g_size = [g1_size, g2_size]
        
        self._clip = [
                config['timing']['duration']['clip'],
                config['stats']['spell_power']['clip'],
                config['stats']['hit_chance']['clip'],
                config['stats']['crit_chance']['clip']]
        
    def _fit(self, order, ignites=False):
        arrays = self._arrays
        if ignites:
            values = self._ignites
        else:
            values = self._values
        
        num_terms = [arr.shape[1] for arr in arrays]
        outs = poly(order, num_terms)
        num_coeff = outs[-1][0] + 1
        t_size = int((1.0 - self._params['test_fraction'])*arrays[0].shape[0])
        X = np.zeros((t_size, num_coeff))
        y = np.stack(values)[:t_size] 
        for out in outs:
            coeff_idx = out[0]
            term = 1.0
            for group, member, exponent in out[1:]:
                term *= np.power(arrays[group][:t_size, member], exponent)
            X[:, coeff_idx] += term
        model = LinearRegression(fit_intercept=False)

        reg = model.fit(X, y)

        if self._params['test_fraction'] > 0.0:
            v_size = arrays[0].shape[0] - t_size
            X_v = np.zeros((v_size, num_coeff))
            y_v = np.stack(values)[t_size:]
            for out in outs:
                coeff_idx = out[0]
                term = 1.0
                for group, member, exponent in out[1:]:
                    term *= np.power(arrays[group][t_size:, member], exponent)
                X_v[:, coeff_idx] += term
                print(t_size, X_v.shape, y_v.shape)
                print(reg.score(X_v, y_v))
                print(self._params['num_load'], np.sqrt(np.power(reg.predict(X_v) - y_v, 2).mean()))

        if True:
            if ignites:
                big_terms = np.where(np.abs(reg.coef_) >= 0.01)[0]
            else:
                big_terms = np.where(np.abs(reg.coef_) >= 0.05)[0]
            X = X[:, big_terms]
            model = LinearRegression(fit_intercept=False)
            reg = model.fit(X, y)
            print(reg.coef_.size)
            print(reg.score(X, y))
            print(np.sqrt(np.power(reg.predict(X) - y, 2).mean()))
        else:
            big_terms = np.arange(reg.coef_.size, dtype=np.int32)
        
        self._big_terms.append(big_terms)
        self._outs.append(outs)
        self._coef.append(reg.coef_)
        
    def fit(self, order):
        self._big_terms = []
        self._outs = []
        self._coef = []
        self._fit(order)
        self._fit(order, ignites=True)

    @property
    def clip(self):
        return self._clip

def main():
    if False:
        # goodness of fit as a function of data quantity
        for nl in np.arange(250, 9600, 250):
            config = {
                    'run_name': 'frostbolt_7n_7m_0p',
                    'mc_dir': '../mc/',
                    'config_dir': '../config/',
                    'num_load': nl,
                    'test_fraction': 0.2}
            fitter = Fitter(config)
            fitter.fit(5)

    config = {
            'run_name': 'frostbolt_4n_4m_0p',
            'mc_dir': '../mc/',
            'config_dir': '../config/mc/',
            'num_load': 999999999,
            'test_fraction': 0.0}
    fitter = Fitter(config)
    fitter.fit(5)

    
if __name__ == '__main__':
    main()





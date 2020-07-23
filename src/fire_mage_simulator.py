import os
import sys
import numpy as np
import json
import itertools
from collections import OrderedDict
from sortedcontainers import SortedDict
from pathos.multiprocessing import Pool
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from copy import deepcopy
import pickle
import time
from mechanics import get_damage

VERSION = 2

def str_encode(n):
    enc_table_64 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
    
    if n == 0:
        return enc_table_64[0]
    base = len(enc_table_64)
    digits = ""    
    while n:
        digits += enc_table_64[int(n % base)]
        n //= base

    return digits[::-1]

def get_str():
    digits = ""
    for rr in range(3):
        digits += str_encode(np.random.randint(64**5))
        
    return digits

def get_values(objs, idxs):
    ret = {}
    for idx, (name, obj) in zip(idxs, objs.items()):
        if isinstance(obj, dict):
            if 'mean' in obj:
                ret[name] = get_values({name: obj['mean']}, [idx])[name]
            elif 'value' in obj:
                ret[name] = get_values({name: obj['value']}, [idx])[name]
        elif isinstance(obj, list):
            ret[name] = obj[idx]
        else:
            ret[name] = obj

    return ret

def all_values(obj):
    if isinstance(obj, dict):
        if 'mean' in obj:
            return all_values(obj['mean'])
        elif 'value' in obj:
            return all_values(obj['value'])
    elif isinstance(obj, list):
        return obj
    else:
        return [obj]

def num_elements(obj):
    return len(all_values(obj))

def get_element(config, var):
    if var == 'spell_power':
        return config['stats']['spell_power']
    elif var == 'hit_chance':
        return config['stats']['hit_chance']
    elif var == 'crit_chance':
        return config['stats']['crit_chance']
    elif var == 'num_mages':
        return config['configuration']
    elif var == 'rotation':
        if 'compare' in config['rotation']:
            return config['rotation']['compare']
        else:
            return [config['rotation']['baseline']]
    elif var == 'duration':
        return config['timing']['duration']
    elif var == 'delay':
        return config['timing']['delay']
    elif var == 'single':
        cs = config['stats']
        stats = [cs['spell_power'], cs['hit_chance'], cs['crit_chance']]
        for stat in stats:
            if 'single' in stat:
                return stat['single']
    else:
        raise ValueError("Unknown variable.")

def do_plot(values, intra, inter, y_desc, plot_type, plot_name, sim_size, t0):
    sinter = SortedDict(inter)
    colors = ['purple', 'indigo', 'darkblue', 'royalblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
    keys = []
    vals = []
    for k, vv in intra.items():
        v = all_values(vv)
        if k in ['crit_chance', 'hit_chance']:
            keys.append(k.split('_')[0])
            vals.append((100.0*np.array(v)).astype(np.int32))
        elif k == 'spell_power':
            keys.append('SP')
            vals.append(np.array(v))
        elif k == 'num_mages':
            keys.append('mages')
            vals.append(np.array([nv['num_mages'] for nv in v]))
        else:
            keys.append(k)
            vals.append(np.array(v))

    plt.close('all')
    plt.figure(figsize=(10.0, 7.0), dpi=200)
    title = ''
    fn = ''
    for k, v in sinter.items():
        if k == 'rotation':
            pass
        elif k in ['duration', 'delay']:
            title += ' {:s} = {:.1f}s'.format(k, v)
            fn += '_{:s}{:d}'.format(k[1], int(v))
        elif k in ['crit_chance', 'hit_chance']:
            title += ' {:s} = {:d}%'.format(k.split('_')[0], int(v*100))
            fn += '_{:s}{:d}'.format(k[0], int(v*100))
        elif k == 'spell_power':
            title += ' SP = {:d}'.format(int(v))
            fn += '_s{:d}'.format(int(v))
        elif k == 'single':
            title += ' single mage crit = {:d}%'.format(int(v*100))
            fn += '_m{:d}'.format(int(v*100))
        elif k == 'num_mages':
            title += ' # mages = {:d}, {:d} w/MQG, {:d} w/PI'.format(v['num_mages'], v['num_mqg'], v['num_pi'])
            fn += '_n{:d}'.format(v['num_mages'])
        
    fn += '_ss{:d}'.format(sim_size)
    plt.title(title)
    print('{:8.1f}: {:s}'.format(time.time() - t0, title))
    sys.stdout.flush()
    relabel = {
        'SP': 'Spell Power',
        'hit': 'Hit Chance (percent)',
        'crit': 'Crit Chance (percent)',
        'single': 'Single Mage Crit Chance (percent)',
        'duration': 'Duration (seconds)',
        'delay': 'Delay (seconds)',
        'mages': 'Number of Mages'}
    plt.xlabel(relabel[keys[1]])
    plt.ylabel(y_desc)
            
    for index, (lval, yval) in enumerate(zip(vals[0], values)):
        color = colors[index*len(colors)//values.shape[0]]
        plt.plot(vals[1], yval, label='{:} {:s}'.format(lval, keys[0]), color=color, marker='.')
                
    plt.legend()
    plt.grid()
    savefile = '../plots/{:s}/{:s}{:s}.png'.format(plot_type, plot_name, fn)
    os.makedirs('../plots/{:s}'.format(plot_type), exist_ok=True)
    plt.savefig(savefile)
    savefile = '../savestates/{:s}/{:s}{:s}.pck'.format(plot_type, plot_name, fn)
    os.makedirs('../savestates/{:s}'.format(plot_type), exist_ok=True)
    with open(savefile, 'wb') as fid:
        pickle.dump(values, fid)
        pickle.dump(intra, fid)
        pickle.dump(inter, fid)
        pickle.dump(sim_size, fid)
    
def main_plot(config, name):
    ss_nm = 5 # standard number of mages for sim_size purposes
    sim_size = {
        'rotation': 50000,
        'crit_equiv': 50000,
        'hit_equiv': 100000,
        'dps': 10000,
        'test': 100000}
    variables = {'spell_power',
                 'hit_chance',
                 'crit_chance',
                 'num_mages',
                 'duration',
                 'delay',
                 'rotation'}
    cs = config['stats']
    stats = [cs['spell_power'], cs['hit_chance'], cs['crit_chance']]
    if any(['single' in stat for stat in stats]):
        variables.add('single')
    intra_names = [config['plot']['lines'], config['plot']['x_axis']]
    inter_names = variables - set(intra_names)
    inter = OrderedDict([(iname, get_element(config, iname)) for iname in inter_names])
    intra = OrderedDict([(iname, get_element(config, iname)) for iname in intra_names])
    inter_idx = [np.arange(num_elements(element)) for element in inter.values()]
    t0 = time.time()
    for idxs in [*itertools.product(*inter_idx)]:
        inter_param = get_values(inter, idxs)
        intra_idx = [np.arange(num_elements(element)) for element in intra.values()]
        plot_type = config['plot']['y_axis']
        nom_ss = sim_size[plot_type]
        args = [{**config,
                 **inter_param,
                 **get_values(intra, jdxs)}
                for jdxs in [*itertools.product(*intra_idx)]]
        print(args[0]['duration'])
        args = [{**arg, **{'mc': False}, **{'sim_size': int(nom_ss*ss_nm/arg['num_mages']['num_mages'])}}
                for arg in args]

        if plot_type == "test":
            args[0]['sim_size'] = nom_ss
            value = get_damage(args[0])
            print("total dps =", value)
            return
        elif plot_type == "rotation":
            y_desc = 'Damage({:s})/Damage({:s})'.format(args[0]['rotation']['description'],
                                                        config['rotation']['baseline']['description'])
            with Pool() as p:
                out1 = np.array(p.map(get_damage, args))
            for index in range(len(args)):
                args[index]['rotation'] = config['rotation']['baseline']
            with Pool() as p:
                out2 = np.array(p.map(get_damage, args))
            value = out1/out2
        elif plot_type == "crit_equiv":
            y_desc = 'SP ratio'
            dcrit = 0.025
            dsp = 25.0
            factor = dsp/dcrit/100.0
            
            orig_args = deepcopy(args)
            outs = []
            for dc, ds in zip([0.0, 0.0, -dcrit, +dcrit], [-dsp, +dsp, 0.0, 0.0]):
                for index in range(len(args)):
                    args[index]['crit_chance'] = orig_args[index]['crit_chance'] + dc
                    args[index]['spell_power'] = orig_args[index]['spell_power'] + ds
                with Pool() as p:
                    out = np.array(p.map(get_damage, args))
                outs.append(out)
            value = factor*(outs[3] - outs[2])/(outs[1] - outs[0])
        elif plot_type == "dps":
            y_desc = "DPS"
            with Pool() as p:
                value = np.array(p.map(get_damage, args))

        value = value.reshape([len(idx) for idx in intra_idx])
        do_plot(value, intra, inter_param, y_desc, plot_type, name, nom_ss, t0)

def main_mc(config, name):
    ss_nm = 5 # standard number of mages for sim_size purposes
    sim_size = 50000
    t0 = time.time()
    var_range = {
        'spell_power': config["stats"]["spell_power"]["clip"],
        'hit_chance': config["stats"]["hit_chance"]["clip"],
        'crit_chance': config["stats"]["crit_chance"]["clip"],
        'duration': config["timing"]["duration"]["clip"]}
    dfn = '../mc/{:s}'.format(name)
    os.makedirs(dfn, exist_ok=True)
    have = len(os.listdir(dfn))
    for bindex in range(have, config["mc_params"]["batches"]):
        args = []
        for iindex in range(config["mc_params"]["batch_size"]):
            arg = {
                "rotation": config["rotation"]["baseline"],
                "configuration": config["configuration"],
                "num_mages": config["configuration"][0],
                "delay": config["timing"]["delay"],
                "timing": config["timing"]}
            arg["sim_size"] = sim_size*ss_nm/arg["num_mages"]["num_mages"]
            if np.random.rand() < config["mc_params"]["correlated_fraction"]:
                for var, rng in var_range.items():
                    if var != "duration":
                        if np.random.rand() < config["mc_params"]["correlated_edge"]:
                            value = rng[1] if np.random.rand() < 0.5 else rng[0]
                            arg[var] = {"fixed": value*np.ones(arg["num_mages"]["num_mages"])}
                        else:
                            arg[var] = {"fixed": rng[0] + np.random.rand()*(rng[1] - rng[0])*np.ones(arg["num_mages"]["num_mages"])}
                        arg[var]["fixed"] += (rng[1] - rng[0])*config["mc_params"]["correlated_std"]*np.random.randn(arg["num_mages"]["num_mages"])
                        arg[var]["fixed"] = np.maximum(arg[var]["fixed"], rng[0])
                        arg[var]["fixed"] = np.minimum(arg[var]["fixed"], rng[1])
            else:
                for var, rng in var_range.items():
                    if var != "duration":
                        arg[var] = {"fixed": rng[0]*np.ones(arg["num_mages"]["num_mages"])}
                        arg[var]["fixed"] += (rng[1] - rng[0])*np.random.rand(arg["num_mages"]["num_mages"])
            rng = var_range['duration']
            arg["timing"]["duration"] = {
                    "mean": rng[0] + config["mc_params"]["duration_var"] + (rng[1] - rng[0] - 2.0*config["mc_params"]["duration_var"])*np.random.rand(),
                    "var": config["mc_params"]["duration_var"],
                    "clip": [rng[0], rng[1]]}
            arg['sim_size'] = int((0.5*arg['sim_size']*(rng[1] + rng[0]))/arg["timing"]["duration"]["mean"])
            arg['mc'] = True
            arg['version'] = VERSION
            args.append(deepcopy(arg))

        #for arg in args:
        #    print(arg)
        #    value = get_damage(arg)
        #    print(arg['spell_power'])
        #    print(arg['hit_chance'])
        #    print(arg['crit_chance'])
        #    print(value)
        #fdsojsd()

        with Pool() as p:
            out1 = np.array(p.map(get_damage, args))
        savefile = '{:s}/{:s}_{:s}.pck'.format(dfn, name, get_str())
        with open(savefile, 'wb') as fid:
            for arg, out in zip(args, out1):
                pickle.dump(out, fid)
                pickle.dump(arg, fid)
        print(bindex, time.time() - t0, out1.mean())
        sys.stdout.flush()

def test():
    config_file = os.path.join(*['..', 'config', 'test.json'])
    name = os.path.split(config_file)[-1].split('.')[0]
    main_plot(config, name)
        
if __name__ == '__main__':
    if len(sys.argv) > 1:
        config_file = sys.argv[1]
    else:
        config_file = os.path.join(*['..', 'config', 'test.json'])
    with open(config_file, 'rt') as fid:
        config = json.load(fid)
    if len(sys.argv) > 2:
        need = int(sys.argv[2])
        if 'mc_params' in config:
            config['mc_params']['batches'] = need
    name = os.path.split(config_file)[-1].split('.')[0]
    print('starting', name)
    if "plot" in config:
        main_plot(config, name)
    elif "mc_params" in config:
        main_mc(config, name)

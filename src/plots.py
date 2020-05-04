import os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

def plot_response(responses, damages, spd, hit, crit, fn_desc, desc, nmages, sim_size, duration):
    colors = ['indigo', 'purple', 'skyblue', 'green', 'lime', 'gold', 'darkorange', 'red', 'firebrick']
    plt.close('all')
    plt.figure(figsize=(10.0, 7.0), dpi=200)
    plt.title('{:3.0f} spell damage, {:2.0f}% hit, {:2.0f}% crit, n={:d}, encounter duration {:3.0f}s'.format(spd, hit*100.0, crit*100.0, sim_size, duration))
    plt.xlabel('Casting start variance (seconds)')
    plt.ylabel('{:s}'.format(desc))
    plt.xlim(0, 3.0)
    for color, num_mages, damage in zip(colors, nmages, damages):
        plt.plot(np.array(responses), np.array(damage), label='{:d} mage{:s}'.format(num_mages, 's' if num_mages > 1 else ''), color=color, marker='.')
    plt.legend()
    plt.grid()
    savefile = '../plots/reaction/{:s}_{:3.0f}_{:2.0f}_{:2.0f}.png'.format(fn_desc, spd, hit*100.0, crit*100.0)
    os.makedirs('../plots/reaction', exist_ok=True)
    plt.savefig(savefile)
    
def plot_rotation(crit_chance, nmages, rotation_map, spd, hit, sim_size, duration, response):
    plt.close('all')
    fig, ax1 = plt.subplots(1, 1, figsize=(6, 6), dpi=200)

    cmap = plt.cm.jet

    ax1.grid(False)
    ax1.set_xticks(np.arange(len(nmages)))
    ax1.set_yticks(np.arange(len(crit_chance)))
    ax1.set_xticklabels(nmages)
    ax1.set_yticklabels((crit_chance*100.0).astype(np.int32))

    ax1.set_xlabel('Number of mages')
    ax1.set_ylabel('Crit chance (percent)')

    title = 'max damage spell in {scorch -> *spell* -> fireball} rotation\n'
    title += '{:3.0f}  spell damage, {:2.0f}% hit, n={:d}\n'.format(spd, hit*100.0, sim_size)
    title += 'encounter duration {:3.0f}s, {:3.1f}s cast start variance'.format(duration, response)

    ax1.set_title(title)
    cmap = mpl.colors.ListedColormap(['blue','black','red'])
    bounds=[-0.5, 0.5, 1.5, 2.5]
    norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    im = ax1.imshow(rotation_map, cmap=cmap, norm=norm)

    divider = make_axes_locatable(ax1)
    cax = divider.append_axes("right", size="7%", pad=0.10)
    cbar = plt.colorbar(im, cax=cax, cmap=cmap,
                            norm=norm,boundaries=bounds,ticks=[0, 1, 2])
    cbar.set_ticklabels(['pyroblast', 'frostbolt', 'fire blast'])
    cbar.set_label('spell', labelpad=-30, y=0.0, rotation=0)
        
    savefile = '../plots/rotation/rotation_{:3.0f}_{:2.0f}.png'.format(spd, hit*100.0)
    os.makedirs('../plots/rotation', exist_ok=True)
    plt.savefig(savefile)
    mpl.rcParams.update(mpl.rcParamsDefault)

def plot_equiv(sps, crit_chance, conversions, hit, num_mages, sim_size, duration, ptype):
    colors = ['indigo', 'purple', 'darkblue', 'royalblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
    plt.close('all')
    plt.figure(figsize=(10.0, 7.0), dpi=200)
    plt.title('{:d} mage{:s}, {:2.0f}% hit, n={:d}, encounter duration {:3.0f}s'.format(num_mages, 's' if num_mages > 1 else '', 100.0*hit, sim_size, duration))
    plt.xlabel('Crit Chance (percent)')
    plt.ylabel('SP ratio')
    plt.xlim(0, 75.0)
    plt.ylim(0, 5 + int(np.array(conversions).max()/5)*5)

    for color, spell_power, conv in zip(colors, sps, conversions):
        plt.plot(100.0*np.array(crit_chance), np.array(conv), label='{:3.0f} SP'.format(spell_power), color=color, marker='.')
    plt.legend()
    plt.grid()
    savefile = '../plots/{:s}_equiv/{:s}_equiv_{:2.0f}_{:d}.png'.format(ptype, ptype, hit*100.0, num_mages)
    os.makedirs('../plots/{:s}_equiv'.format(ptype), exist_ok=True)
    plt.savefig(savefile)
    
def plot_dps(crit_chance, nmages, damages, spd, hit, sim_size, duration, response):
    colors = ['indigo', 'purple', 'darkblue', 'skyblue', 'green', 'lime', 'gold', 'orange', 'darkorange', 'red', 'firebrick', 'black']
    plt.close('all')
    plt.figure(figsize=(10.0, 7.0), dpi=200)

    title = 'max damage spell in {scorch -> *spell* -> fireball} rotation\n'
    title += '{:3.0f}  spell damage, {:2.0f}% hit, n={:d}\n'.format(spd, hit*100.0, sim_size)
    title += 'encounter duration {:3.0f}s, {:3.1f}s cast start variance'.format(duration, response)

    plt.xlabel('Number of mages')
    plt.ylabel('Average DPS')
    plt.xlim(0, 10)
    for color, crit, damage in zip(colors, crit_chance, damages):
        plt.plot(np.array(nmages), np.array(damage), label='{:2.0f}% crit'.format(100.0*crit), color=color, marker='.')
    plt.legend()
    plt.grid()
    savefile = '../plots/dps/dps__{:3.0f}_{:2.0f}.png'.format(spd, hit*100.0)
    os.makedirs('../plots/dps', exist_ok=True)
    plt.savefig(savefile)


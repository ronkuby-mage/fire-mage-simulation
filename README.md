**Steps to determine stat weighting:**
1) Use Table 1 to determine which configuration best fits your raid in terms of boss kill time and average mage gear level.
2) Follow the "stats" link.
3) Select whether your raid has world buffs or not -- this will also determine the optimal rotation.
4) Pick the applicable (# mages)/(hit %) cell.

## Fire Mage Simulations

These simulations play out scenarios in which multiple fire mages are casting against a single raid boss.  The mechanics considered include ignite, scorch, combustion, talents, Curse of the Elements, spell travel time, power infusion (PI), Mind Quickening Gem (MQG), and Dark Moon Faire double dip (turned off by default).  The effects of nightfall, other active trinkets (including Arcanite Dragonling), spell batching, and unmitigable boss resistance are not included.

The primary purpose of these simulations is to determine the balance between spell power, +hit chance, and +crit chance for the purpose of gear selection.  In order to determine these equivalencies, the rotation must also be optimized at every possible stat point and raid configuration.  Doing so would require simulations at too many permutations.  Instead, for the purpose of rotation optimization, the problem is divided into three tiers of gear and raid configurations: phase four building, phase four near-max, and phase five maxed out.

|               |  Min SP |  Max SP | Min Crit| Max Crit| #PI | Duration | Gear |
|---------------|:-------:|:-------:|:-------:|:-------:|:---:|:--------:|:----:|
| P4 Building   |   472   |   632   |   15%   |   35%   |  0  |  2 mins  | [link](https://sixtyupgrades.com/set/r5UDRwhdCR8kkm7DtGv7BG) |
| P4 Near-Max   |   525   |   785   |   20%   |   40%   |  2  |  60 sec  | [link](https://sixtyupgrades.com/set/r5UDRwhdCR8kkm7DtGv7BG) |
| P5 Max        |   683   |   943   |   19%   |   39%   |  4  |  30 sec  | [link](https://sixtyupgrades.com/set/r5UDRwhdCR8kkm7DtGv7BG) |

**Table 1: Stats for gear and buff scenarios.**

Here, min and max reflect the range of stats from raid buffed to raid + world + consumable buffed (within reason).  The world buffs are: Dire Maul Tribute Crit, Ony, Zandalar (effectively +1% crit), and Songflower.  The consumables are Brilliant Wizard Oil, Elixir of Greater Firepower, Greater Arcane Elixir, and Flask of Supreme Power.  These are the stat ranges used to determine the rotations for the respective gear levels.  At each gear level the equivalencies will be calculated over a much larger range of stats, still with the fixed rotations.  

The simulation starts immediately before the first scorch finishes casting.  Each of the mages is given a normally distributed initial delay with standard deviation 1.0 seconds.  Between casts an additional normally distributed delay of 0.05 seconds is imposed.  The duration of a session is again normally distributed with an average of 120 seconds and a 12 second deviation.  If a fixed encounter duration is imposed rather than a distribution, the selected encounter duration highly influences relative rotation values due to cyclical advantages of spell timing.

### Rotations

In the previous iteration of this simulation, fire blast was found to be the best buffer spell between scorch stacking and ignite stacking from a pure dps perpective.  Here, fire blast is excluded from the rotations considered for a few reasons: 1) the fire blast buffer is too thin to be effective given real world coordination, 2) its range is a problem -- 26 yards would waste time moving to the boss (although untalented frostbolt's 30 yards isn't much better), and 3) fire blast should generally be kept out of rotations due to mana inefficiency.

The baseline rotation is now:
**```scorch to stack -> combustion -> *buffer* -> *cooldowns* -> fireball (repeated)```**
with a designated scorch mage (see below). *Cooldowns* are MQG (when available, five are allocated for all gear levels), and PI (when available, see Table 1 for allocation).  Many experiments were performed to explore possibilities such as expanding the buffer for non PI mages to guarentee a PI double-dip ignite stack and having a high crit chance mage spam scorch to keep the buffed ignite stack up.  None of these experments produced higher average damage than the baseline regardless of number of mages, crit chance, etc..

There will always be a designated scorch mage who, after the initial rotation, casts scorch instead of fireball if:
1. The scorch debuff has less than five seconds to expiration
2. The scorch debuff stack is not at its full value of 5
If the number of mages is less than 6, at least 2 scorches should be initially cast (see below).  Two mages should cast 3 scorches and one mage should cast 6 scorches.

The only variation in optimal rotation was including frostbolt as the *buffer* spell, which was better in world buffed cases -- see "Max Crit" column in Table 1.  For lower crit chance situations it was better to not include a buffer.  The cross-over point is around 30% crit chance as shown in Figures 1, 2, and 3.

![low end gear](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/decision-tree/plots/rotation/fireball_low_e1_u120_h97_s550_ss50000.png)
**Figure 1: Rotation ratio for low-end performance.**

![mid end gear](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/decision-tree/plots/rotation/fireball_mid_e1_u60_h96_s650_ss50000.png)
**Figure 2: Rotation ratio for mid-end performance.**

![high end gear](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/decision-tree/plots/rotation/fireball_high_e1_u30_h99_s950_ss50000.png)
**Figure 3: Rotation ratio for high-end performance.**

### Spell power equivalency of critical strike rating

With finite-differences the simulations are used to determine the equivalency between a single spell power increase and 1% critical strike chance increase.  The equivalency value is dependent on current spell power, hit chance, crit chance, and number of mages.  Each plot below shows the values for a range of crit chance and spell power values.  To find the appropriate plot, select from the table based on your current hit chance and number of mages:

|             | 89% Hit | 91% Hit | 93% Hit | 95% Hit | 97% Hit | 99% Hit |
|-------------|:-------:|:-------:|:-------:|:-------:|:-------:|:-------:|
| One Mage    |  [89_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_1.png) |  [91_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_1.png) |  [93_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_1.png) |  [95_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_1.png) |  [97_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_1.png) |  [99_1](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_1.png) |
| Two Mages   |  [89_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_2.png) |  [91_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_2.png) |  [93_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_2.png) |  [95_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_2.png) |  [97_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_2.png) |  [99_2](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_2.png) |
| Three Mages |  [89_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_3.png) |  [91_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_3.png) |  [93_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_3.png) |  [95_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_3.png) |  [97_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_3.png) |  [99_3](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_3.png) |
| Four Mages |  [89_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_4.png) |  [91_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_4.png) |  [93_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_4.png) |  [95_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_4.png) |  [97_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_4.png) |  [99_4](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_4.png) |
| Five Mages |  [89_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_5.png) |  [91_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_5.png) |  [93_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_5.png) |  [95_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_5.png) |  [97_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_5.png) |  [99_5](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_5.png) |
| Six Mages |  [89_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_6.png) |  [91_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_6.png) |  [93_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_6.png) |  [95_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_6.png) |  [97_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_6.png) |  [99_6](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_6.png) |
| Seven Mages |  [89_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_7.png) |  [91_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_7.png) |  [93_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_7.png) |  [95_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_7.png) |  [97_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_7.png) |  [99_7](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_7.png) |
| Eight Mages |  [89_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_8.png) |  [91_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_8.png) |  [93_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_8.png) |  [95_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_8.png) |  [97_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_8.png) |  [99_8](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_8.png) |
| Nine Mages |  [89_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_89_9.png) |  [91_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_91_9.png) |  [93_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_93_9.png) |  [95_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_9.png) |  [97_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_97_9.png) |  [99_9](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_99_9.png) |

Here is an example equivalency for 5 mages:
![seven mage equivalence](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/crit_equiv/crit_equiv_95_5.png)
Compare with other simulations:
* [Quasexort](https://docs.google.com/spreadsheets/d/1dqFuQeNVa403ulrmuW_8Ww-5UszOde0RPMBe2g7t1g4)
* [elio](https://github.com/ignitelio/ignite/blob/master/magus2.ipynb)

### Alternative rotations

The comparative average damage from several alternative rotations is plotted [here](https://github.com/ronkuby-mage/fire-mage-simulation/tree/master/plots/rotation).  In cases of 3 or 4 mages, starting with two scorches yields higher DPS than the baseline of a single scorch to start:
![two scorches vs one](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/legacy/two_scorches_700.png)
The superiority of an extra scorch in these conditions is not surprising because otherwise some of the initial crits will not benefit from a full scorch stack.

Replacing pyroblast with an (approximate) frostbolt + fireball results in up to 1% dps improvement:
![frostbolt+fireball vs pyroblast](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/legacy/frostbolt_700.png)
The frostbolt is rank 11 and untalented aside from elemental precision.

Replacing pyroblast with fire blast + fireball results in up to 2% dps improvement:
![combustion first vs later](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/legacy/fire_blast_open_700.png)
**```scorch -> fire blast -> combustion -> -> fireball (repeated)```** is the highest tested opening rotation.

### DPS by number of mages

DPS per mage as a function of number of mages is plotted for a few values of spell power [here](https://github.com/ronkuby-mage/fire-mage-simulation/tree/master/dps_per_mage_plots).
![dps per mage, 700 sp](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/dps/dps_700_97.png)
Assuming the number of mages is fixed, these curves are only useful towards determining ones expected dps.

*Thanks to elio for tracking down the error in ignite timing and providing parallel code sample!*

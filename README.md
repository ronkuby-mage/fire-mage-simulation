[Skip to SP to critical conversion table](#spell-power-equivalency-of-critical-strike-rating)

## Fire Mage Simulations

These simulations play out scenarios in which multiple fire mages are casting against a single raid boss.  The mechanics considered include ignite, scorch, combustion, and travel time.  The effects of nightfall, power infusion, DMF double dip, trinkets, spell batching, and unmitigable boss resistance are not included.  The baseline rotation is:
**```N x scorch -> *spells* -> fireball (repeated)```**
Several options for *spells* were explored: **combustion -> pyroblast**, **combustion -> frostbolt**, and **fire blast -> combustion**.  [Here](https://github.com/ronkuby-mage/fire-mage-simulation/tree/master/plots/rotation) are the highest average dps values for *spell*.  

Most evaluations depend on current spell power, hit chance, crit chance, and number of mages.  For example the highest dps rotation for fixed 700 spell power and a 95% hit chance is:
![rotation](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/plots/rotation/rotation_700_95.png)
and this plot will change depending on the hit and spell power values.

There will always be a designated scorch mage who, after the initial rotation, casts scorch instead of fireball if:
1. The scorch debuff has less than five seconds to expiration
2. The scorch debuff stack is not at its full value of 5
If the number of mages is less than 5, at least 2 scorches should be initially cast (see below).  Two mages should cast 3 scorches and one mage should cast 5 scorches.

The simulation starts immediately before the first scorch finishes casting.  Each of the mages is given a normally distributed initial delay with standard deviation 1.0 seconds.  Between casts an additional normally distributed delay of 0.05 seconds is imposed.  The duration of a session is again normally distributed with an average of 120 seconds and a 12 second deviation.  If a fixed encounter duration is imposed rather than a distribution, the selected encounter duration highly influences relative rotation values due to cyclical advantages of spell timing.

A [posted log](https://github.com/ronkuby-mage/fire-spec-simulation/blob/master/log_example.txt) can be reviewed to verify mechanics.  Most of the status information in the logs is shown when a cast damages the boss.  This status information reports the condition after the spell has affected both boss and player.  Logs can be activated by setting the ```_LOG_SIM``` variable to an integer n, where n >= 0 and n < ```_SIM_SIZE```.

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

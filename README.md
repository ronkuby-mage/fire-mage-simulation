## Fire Mage Simulations

These simulations play out scenarios in which multiple fire mages are casting against a single raid boss.  The mechanics considered include ignite, scorch, combustion, and travel time.  The baseline rotation is:
**```scorch -> combustion -> pyroblast -> fireball (repeated)```**
There will always be a designated scorch mage who, after pyroblast, casts scorch instead of fireball if:
1. The scorch debuff has less than five seconds to expiration
2. The scorch debuff stack is not at its full value of 5

The simulation starts immediately before the first scorch finishes casting.  Each of the mages is given a normally distributed initial delay with standard deviation 0.4 seconds.  Between casts an additional normally distributed delay of 0.05 seconds is imposed.  The duration of a session is again normally distributed with an average of 120 seconds and a 12 second deviation.  If a fixed encounter duration is imposed rather than a distribution, the selected encounter duration highly influences relative rotation values due to cyclical advantages of spell timing.

A [posted log](https://github.com/ronkuby-mage/fire-spec-simulation/blob/master/log_example.txt) can be reviewed to verify mechanics.  Most of the status information in the logs is shown when a cast damages the boss.  This status information reports the condition after the spell has affected both boss and player.  Logs can be activated by setting the ```_LOG_SIM``` variable to an integer n, where n >= 0 and n < ```_SIM_SIZE```.

### Spell power equivalency of critical strike rating

With finite-differences the simulations are used to determine the equivalency between a single spell power increase and 1% critical strike chance increase.  Here is the equivalency for 7 mages:
![seven mage equivalence](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/sp_equiv_plots/sp_equiv_7_mages_96_25000.png)
Compare with other simulations:
* [Quasexort](https://docs.google.com/spreadsheets/d/1dqFuQeNVa403ulrmuW_8Ww-5UszOde0RPMBe2g7t1g4)
* [elio](https://github.com/ignitelio/ignite/blob/master/magus2.ipynb)

### Alternative rotations

The comparative average damage from several alternative rotations is plotted [here](https://github.com/ronkuby-mage/fire-mage-simulation/tree/master/rotation_plots).  In cases of 3 or 4 mages, starting with two scorches yields higher DPS than the baseline of a single scorch to start:
![two scorches vs one](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/rotation_plots/two_scorches_700.png)
The superiority of an extra scorch in these conditions is not surprising because otherwise some of the initial crits will not benefit from a full scorch stack.

Replacing pyroblast with an (approximate) frostbolt + fireball results in up to 1% dps improvement:
![frostbolt+fireball vs pyroblast](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/rotation_plots/frostbolt_700.png)
The frostbolt is rank 11 and untalented aside from elemental precision.

Replacing pyroblast with fire blast + fireball results in up to 2% dps improvement:
![combustion first vs later](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/rotation_plots/fire_blast_open_700.png)
A opening rotation of **```scorch -> fire blast -> combustion -> -> fireball (repeated)```** is the highest tested.

### DPS by number of mages

DPS per mage as a function of number of mages is plotted for a few values of spell power [here](https://github.com/ronkuby-mage/fire-mage-simulation/tree/master/dps_per_mage_plots).
![dps per mage, 700 sp](https://github.com/ronkuby-mage/fire-mage-simulation/raw/master/dps_per_mage_plots/spellpower_700.png)
Assuming the number of mages is fixed, these curves are only useful towards determining ones expected dps.

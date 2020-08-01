*29JUL20* Adding charts for PI=0 with the new ignite mechanics as they come in.  The sheet will be updated for PI=0 later this week and for PI>0 once new rotations have been worked out.

*26JUL20: Sheet updated for PI=1 with new ignite stacking mechanics and rotation.  Also added 90% level output and weights.*

*23JUL20: Ignite mechanics have changed such that the below information is not accurate for PI > 0.  The plan is to update the sheet, correcting the PI=1 tab by phase 5 release.  Higher PI value tabs will then be populated.  There are no plans to update the charts.*

# [Sheet Calculator](https://docs.google.com/spreadsheets/d/1fOXRbWAfbT0FiIu8gytV0Fj4Dnu2ZiLxSBc4tptczu4/edit?usp=sharing)

If one or more mage receives a Power Infusion (PI) buff, use the sheet calculator.  In these cases, stat equivalencies differ between the mages getting PI and those who don't so the sheet shows the stats listed separately for two representative mages.

# Fire Mage Simulations

These simulations play out scenarios in which multiple fire mages are casting against a single raid boss.  The mechanics considered include ignite, scorch, combustion, talents, Curse of the Elements, spell travel time, PI, Mind Quickening Gem (MQG), and Dark Moon Faire double dip (turned off by default).  The effects of nightfall, other active trinkets (including Arcanite Dragonling), spell batching, and unmitigable boss resistance are not included.

The simulation starts when the first scorch starts casting.  Each of the mages is given a normally distributed initial delay with standard deviation 1.0 seconds.  Between casts an additional normally distributed delay of 0.05 seconds is imposed.  The duration of a session is again normally distributed with the average shown in Table 1.  If a fixed encounter duration is imposed rather than a distribution, the selected encounter duration highly influences relative rotation values due to cyclical advantages of spell timing.

## Rotations

The primary purpose of these simulations is to determine the balance between spell power, +hit chance, and +crit chance for the purpose of gear selection.  In order to determine these equivalencies, the rotation must also be optimized at every possible stat point and raid configuration.  Doing so would require simulations at too many permutations.  Instead, the equivalencies are shown for two rotations here: a buffered rotation and unbuffered.  For the PI=0 case, there will be very little overall dps difference between the buffered and unbuffered rotations.

In the previous iteration of this simulation, fire blast was found to be the best buffer spell between scorch stacking and ignite stacking from a pure dps perceptive.  Here, fire blast is excluded from the rotations considered for a few reasons: 1) the fire blast buffer is too thin to be effective given real world coordination, 2) its range is a problem -- moving to 26 yards would waste time moving to the boss (although untalented frostbolt's 30 yards isn't much better), and 3) fire blast should generally be kept out of rotations due to mana inefficiency.

The unbuffered rotation is:
**```scorch to stack -> fireball -> combustion -> MQG -> fireball (repeated)```**
with a designated scorch mage (see below).

There will always be a designated scorch mage who, after the initial rotation, casts scorch instead of fireball if:
1. The scorch debuff has less than five seconds to expiration *or*
2. The scorch stack count is less than 5

The buffered rotation is:
**```scorch to stack -> MQG --> frostbolt -> combustion -> fireball (repeated)```**
again with a designated scorch mage (see below).

Note that after MQG has expired, the scorch mage can sometimes spam scorch on full ignite stakcs with no DPS loss and perhaps a DPS gain.

## Spell power equivalency of critical strike rating

With finite-differences the simulations are used to determine the equivalency between a single spell power increase and 1% critical strike chance increase.  The equivalency value is dependent on current spell power, hit chance, crit chance, number of mages, encounter duration, and selected rotation.  Each plot below shows the values for a range of crit chance and spell power values.  To find the appropriate plot, select from the table based on your current hit chance and number of mages:

### No Buffer

![One mage no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n1_ss50000.png)

![Two mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n2_ss50000.png)

![Three mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n3_ss50000.png)

![Four mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n4_ss50000.png)

![Five mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n5_ss50000.png)

![Six mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n6_ss50000.png)

![Seven mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n7_ss50000.png)

![Eight mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n8_ss50000.png)

![Nine mages no buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_fireball_crit_e1_u100_h99_n9_ss50000.png)

### Buffer

![One mage buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n1_ss50000.png)

![Two mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n2_ss50000.png)

![Three mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n3_ss50000.png)

![Four mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n4_ss50000.png)

![Five mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n5_ss50000.png)

![Six mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n6_ss50000.png)

![Seven mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n7_ss50000.png)

![Eight mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n8_ss50000.png)

![Nine mages buffer](https://raw.githubusercontent.com/ronkuby-mage/fire-mage-simulation/master/plots/crit_equiv/PS_PI0_frostbolt_crit_e1_u100_h99_n9_ss50000.png)

## Crit equivalency comparisons

Here are some results from other simulations:
* [Quasexort](https://docs.google.com/spreadsheets/d/1dqFuQeNVa403ulrmuW_8Ww-5UszOde0RPMBe2g7t1g4)
* [elio](https://github.com/ignitelio/ignite/blob/master/magus2.ipynb)

## Acknowledgement
*Thanks to elio for tracking down the error in ignite timing and providing parallel code sample!*

*Thanks to alzy for the sim result comparison, which helped pin down a bug in the scorch refresh logic!*

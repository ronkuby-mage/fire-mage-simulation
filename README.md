# API Interface

This branch is a rework to simplify and push outer loop configuration to the user/client side.  Individual simulation parameters are specified by JSON file.  Complete documentation of the JSON specifications are ongoing (below).  For now, see examples in src/fire_mage_simulator.py.

### Basic Example

Here are the minimum commands to run a simulation from the src folder:
```python
import json
from mechanics import get_damage

with open("my_sim.json", "rt") as fid:
    config = json.load(fid)
config["sim_size"] = 50000
values = get_damage(config)
```

## JSON Specification

### Stats

#### Spell Power

#### Hit Chance

#### Crit Chance

#### Intellect

### Buffs

### Configuration

### Rotation

### Timing

## Crit equivalency comparisons

Here are some results from other simulations:
* [Quasexort](https://docs.google.com/spreadsheets/d/1dqFuQeNVa403ulrmuW_8Ww-5UszOde0RPMBe2g7t1g4)
* [elio](https://github.com/ignitelio/ignite/blob/master/magus2.ipynb)

## Acknowledgement
*Thanks to elio for tracking down the error in ignite timing and providing parallel code sample!*
*Thanks to alzy for the sim result comparison, which helped pin down a bug in the scorch refresh logic!*

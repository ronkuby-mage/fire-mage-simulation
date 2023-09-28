# Vanilla Fire Mage Simulation

This application simulates a team of fire mages casting against a single boss level target within the framework of Classic Era mechanics.

### Installation

Here are the steps to install and run the application on Windows.
1. Under the "Code" link above, download a ZIP file and extract it into a directory such as "C:\sims\"
2. Download the Anaconda package: [tested version](https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Windows-x86_64.exe)
3. From the Start menu, open an Anaconda Prompt (see below)
4. Go to the directory you extracted the code to in Step 1 using the "cd" command.  For the above example, ```cd \sims\fire-mage-simulation```
5. Run the application with ```python -m src.gui.main```
  
![](./data/pictures/anaconda_prompt.png)

## Walkthrough
Start by selecting the Scenario editor tab on the top left.  Here is the example scenario we will work through:
![](./data/pictures/scenario_editor.png)
Within the **Mages** section you can changes the stats and other information for each mage.  From left to right -- The stats should be entered as from gear/enchant only for spell power, hit, and crit.  Int should be entered as base value + gear, with no buffs.  The trinket section informs the sim which active trinkets are available.  Next are indicators for the UDC set bonus and whether the mage can receive PI.  For now, only one PI can be available.  *Target* indicates whether that mage's personal DPS and their share of the ignite are included in the output.  If you want to see the expected output for only one mage on the team, check the *target* box for them only.  On the far right (for the bottom mage) are buttons that increase or decrease the number of mages.

The **Rotation** section has an initial fixed set of rotation command that each mage attempts to cast when the fight start.  Abilities that are not available to a mage are not cast and do not expend any time.  For example if "mqg" is on the list but a mage doesn't have Mind Quickening Gem, when they get to that cast in the sequence it is ignored.  The *Special* section 


### Scenario Editor

### Stat Weights/Distribution Run

### Setting up Multiple Scenarios

### Scenario Comparison Run


### Crit equivalency comparisons

Here are some results from other simulations:
* [Quasexort](https://docs.google.com/spreadsheets/d/1dqFuQeNVa403ulrmuW_8Ww-5UszOde0RPMBe2g7t1g4)
* [elio](https://github.com/ignitelio/ignite/blob/master/magus2.ipynb)

### Acknowledgement
*Thanks to elio for tracking down the error in ignite timing and providing parallel code sample!*
*Thanks to alzy for the sim result comparison, which helped pin down a bug in the scorch refresh logic!*

// in src/main.rs
use std::collections::HashMap;
use simulation::constants::{Action, ConstantsConfig, Buff};
use simulation::decisions::{Decider, ScriptedDecider};
use simulation::orchestration::{run_many_with, Configuration, SimParams, Stats, Buffs, Timing};

fn main() {
    let num_mages = 3usize;

    // Base stats for each mage
    let stats = Stats {
        spell_power: vec![600.0; num_mages],
        crit_chance: vec![0.18; num_mages], // additional to base 0.062 added later
        hit_chance: vec![0.08; num_mages],  // additional to base 0.89 capped at 0.99
        intellect: vec![300.0; num_mages],
    };

    // Buffs/consumes (trimmed set — mirrors a subset of ArrayGenerator adjustments)
    let buffs = Buffs {
        consumes: vec![
            "greater_arcane_elixir",
            "elixir_of_greater_firepower",
            // "flask_of_supreme_power",
            // "brilliant_wizard_oil",
        ],
        raid: vec!["arcane_intellect", "improved_mark"],
        world: vec!["rallying_cry_of_the_dragonslayer"],
        boss: "",
        auras_mage_atiesh: vec![0.0; num_mages],
        auras_lock_atiesh: vec![0.0; num_mages],
        auras_boomkin: vec![0.0; num_mages],
        racial: vec!["human"; num_mages],
    };

    let timing = Timing {
        duration_mean: 45.0,
        duration_sigma: 0.0,
        initial_delay: 0.2,
        recast_delay: 0.05,
    };

    let mut buff_assignments = HashMap::new();
    buff_assignments.insert(Buff::Sapp, vec![]);
    buff_assignments.insert(Buff::Toep, vec![0, 1]);
    buff_assignments.insert(Buff::Zhc, vec![]);
    buff_assignments.insert(Buff::Mqg, vec![]);
    buff_assignments.insert(Buff::PowerInfusion, vec![0, 2]);

    let config = Configuration {
        num_mages,
        target: (0..num_mages).collect(), // treat all as target for player_damage
        buff_assignments,
        udc: vec![1, 2],
        nightfall: vec![1.77, 3.55],
        dragonling: 20.0,
    };

    let consts_cfg = ConstantsConfig { ..Default::default() };

    let params = SimParams { stats, buffs, timing, config, consts_cfg };

    // Example: open with 3x Scorch then a Pyroblast, then default to Fireball
    let initial_sequence = vec![
        Action::Scorch,
        Action::Scorch,
        Action::Combustion,
        Action::Toep,
        Action::PowerInfusion,
    ];
    let default_action = Action::Fireball;

    // Reaction-time sigmas (tweak to taste)
    let initial_react = 0.05;     // e.g. slightly slower on openers
    let continuing_react = 0.05;  // tighter after ramp

    // If your AdvancedDecider::new takes (num_mages, …), capture it here as needed
    let make_decider = || ScriptedDecider::new(
        /* num_mages: */
        params.config.num_mages,
        initial_sequence.clone(),
        default_action,
        initial_react,
        continuing_react,
    );

    let sims = 50000;
    let seed = 42;
    let results = run_many_with::<ScriptedDecider, _>(&params, make_decider, sims, seed);


    // Per-mage / per-target summary (as we discussed earlier)
    let m = params.config.num_mages as f64;
    let target_count = params.config.target.len() as f64;

    let (mut total, mut ignite, mut player) = (0.0, 0.0, 0.0);
    for r in &results { total += r.total_dps; ignite += r.ignite_dps; player += r.player_dps; }
    let n = results.len() as f64;

    println!("Ran {} sims:", results.len());
    println!("  mean total dps per mage:    {:.1}", total / (n * m));
    println!("  mean ignite dps per mage:   {:.1}", ignite / (n * m));
    println!("  mean player dps per target: {:.1}", player / (n * target_count));
}

use simulation::{
    decisions::{Decider, FireballSpam},
    orchestration::{run_many, Configuration, SimParams, Stats, Buffs, Timing},
    constants::ConstantsConfig,
};

fn main() {
    // --- Minimal demo parameters (feel free to tweak) ---
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

    let config = Configuration {
        num_mages,
        udc: vec![],            // lane indices that can "clean" ignite
        pi: vec![],             // lane indices that can receive PI windows
        target: (0..num_mages).collect(), // treat all as target for player_damage
    };

    let consts_cfg = ConstantsConfig { ..Default::default() };

    // Grab counts now, before `config` is moved
    let m = num_mages as f64;
    let targets = config.target.len() as f64;

    let params = SimParams { stats, buffs, timing, config, consts_cfg };

    let mut decider = FireballSpam;
    let results = run_many(&params, &mut decider, 50000, 9);

    // --- summary ---
    let (mut total, mut ignite, mut player) = (0.0, 0.0, 0.0);
    for r in &results { total += r.total_dps; ignite += r.ignite_dps; player += r.player_dps; }
    let n = results.len() as f64;
    println!("Ran {} sims:", results.len());
    println!("  mean total dps per mage:    {:.1}", total / (n * m));
    println!("  mean ignite dps per mage:   {:.1}", ignite / (n * m));
    println!("  mean player dps per target: {:.1}", player / (n * targets));
}

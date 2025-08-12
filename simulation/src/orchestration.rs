//! orchestration.rs — high-level driver and initialization

use rand::SeedableRng;
use rand::Rng; // bring trait into scope
use rand_pcg::Pcg64Mcg;
use rand_distr::{Normal, Distribution};
use std::collections::HashMap;

use crate::constants::{Buff, Constants, ConstantsConfig};
use crate::state::{State};
use crate::decisions::Decider;

// ---- Parameters mirrored from Python inputs (trimmed first pass) ----
#[derive(Debug, Clone)]
pub struct Stats { pub spell_power: Vec<f64>, pub crit_chance: Vec<f64>, pub hit_chance: Vec<f64>, pub intellect: Vec<f64> }
#[derive(Debug, Clone)]
pub struct Buffs {
    pub consumes: Vec<&'static str>,
    pub raid: Vec<&'static str>,
    pub world: Vec<&'static str>,
    pub boss: &'static str,
    pub auras_mage_atiesh: Vec<f64>,
    pub auras_lock_atiesh: Vec<f64>,
    pub auras_boomkin: Vec<f64>,
    pub racial: Vec<&'static str>,
}
#[derive(Debug, Clone)]
pub struct Timing { pub duration_mean: f64, pub duration_sigma: f64, pub initial_delay: f64, pub recast_delay: f64 }

#[derive(Debug, Clone)]
pub struct Configuration {
    pub num_mages: usize,
    pub target: Vec<usize>,
    pub buff_assignments: HashMap<Buff, Vec<usize>>,
    pub udc: Vec<usize>,
    pub nightfall: Vec<f64>,
    pub dragonling: f64,
}
impl Configuration {
    pub fn new() -> Self {
        let mut buff_assignments = HashMap::new();
        buff_assignments.insert(Buff::Sapp, vec![]);
        buff_assignments.insert(Buff::Toep, vec![]);
        buff_assignments.insert(Buff::Zhc, vec![]);
        buff_assignments.insert(Buff::Mqg, vec![]);
        buff_assignments.insert(Buff::PowerInfusion, vec![]);

        Self {
            num_mages: 0,
            target: vec![],
            buff_assignments,
            udc: vec![],
            nightfall: vec![],
            dragonling: f64::INFINITY,
        }
    }
}

#[derive(Debug, Clone)]
pub struct SimParams {
    pub stats: Stats,
    pub buffs: Buffs,
    pub timing: Timing,
    pub config: Configuration,
    pub consts_cfg: ConstantsConfig,
}

#[derive(Debug, Clone, Default)]
pub struct SimResult { pub total_dps: f64, pub ignite_dps: f64, pub player_dps: f64 }

// ---- Helpers ----
fn sample_duration<R: Rng + ?Sized>(tim: &Timing, rng: &mut R) -> f64 {
    let normal = Normal::new(tim.duration_mean, tim.duration_sigma).unwrap();
    normal.sample(rng)
    //(tim.duration_mean + tim.duration_sigma * Rng::r#gen::<f64>(rng)).max(1.0)
}

fn first_action_offsets<R: Rng + ?Sized>(num_mages: usize, initial_delay: f64, rng: &mut R) -> Vec<f64> {
    //let mut rng = Pcg64Mcg::seed_from_u64(9);
    let normal = Normal::new(0.0, initial_delay).unwrap();
    (0..num_mages).map(|_| normal.sample(rng)).collect()
    //(0..num_mages).map(|_| (initial_delay * Rng::r#gen::<f64>(rng)).abs()).collect()
}

fn apply_buffs(stats: &mut Stats, buffs: &Buffs) {
    // 1) Intellect pipeline (mirror Python ordering)
    for i in 0..stats.intellect.len() {
        let mut intel = stats.intellect[i];
        // flat adds
        if buffs.raid.contains(&"arcane_intellect") { intel += 31.0; }
        if buffs.raid.contains(&"improved_mark") { intel += 1.35 * 12.0; }
        if buffs.consumes.contains(&"stormwind_gift_of_friendship") { intel += 30.0; }
        if buffs.consumes.contains(&"infallible_mind") { intel += 25.0; }
        if buffs.consumes.contains(&"runn_tum_tuber_surprise") { intel += 10.0; }
        // multiplicative
        let kings = if buffs.raid.contains(&"blessing_of_kings") { 1.10 } else { 1.0 };
        let soz   = if buffs.world.contains(&"spirit_of_zandalar") { 1.15 } else { 1.0 };
        let racial = if buffs.racial.get(i).map(|&r| r == "gnome").unwrap_or(false) { 1.05 } else { 1.0 };
        intel = intel * kings * soz * racial;
        stats.intellect[i] = intel;
    }

    // 2) Spell power buffs
    for (i, sp) in stats.spell_power.iter_mut().enumerate() {
        if buffs.consumes.contains(&"greater_arcane_elixir") { *sp += 35.0; }
        if buffs.consumes.contains(&"elixir_of_greater_firepower") { *sp += 40.0; }
        if buffs.consumes.contains(&"flask_of_supreme_power") { *sp += 150.0; }
        if buffs.consumes.contains(&"blessed_wizard_oil") { *sp += 60.0; }
        if buffs.consumes.contains(&"brilliant_wizard_oil") { *sp += 36.0; }
        if buffs.consumes.contains(&"very_berry_cream") { *sp += 23.0; }
        *sp += 33.0 * buffs.auras_lock_atiesh.get(i).copied().unwrap_or(0.0);
    }

    // 3) Crit chance buffs (uses UPDATED intellect)
    for (i, cc) in stats.crit_chance.iter_mut().enumerate() {
        *cc += 0.062; // base + talents per Python comment
        if buffs.consumes.contains(&"brilliant_wizard_oil") { *cc += 0.01; }
        if buffs.world.contains(&"rallying_cry_of_the_dragonslayer") { *cc += 0.10; }
        if buffs.world.contains(&"songflower_serenade") { *cc += 0.05; }
        if buffs.world.contains(&"dire_maul_tribute") { *cc += 0.03; }
        *cc += stats.intellect[i] / 5950.0; // intellect → crit
        *cc += 0.60 * (buffs.boss == "loatheb") as i32 as f64;
        *cc += 0.02 * buffs.auras_mage_atiesh.get(i).copied().unwrap_or(0.0);
        *cc += 0.03 * buffs.auras_boomkin.get(i).copied().unwrap_or(0.0);
        if *cc > 1.0 { *cc = 1.0; }
    }

    // 4) Hit chance floor/cap
    for hc in &mut stats.hit_chance { *hc = (*hc + 0.89).min(0.99); }
}

fn init_state<R: Rng + ?Sized>(p: &SimParams, rng: &mut R, idx: u64) -> State {
    use crate::constants as C;

    let num = p.config.num_mages;
    let mut st = State::new(sample_duration(&p.timing, rng), num);

    st.log = idx == 0 && C::LOG;

    st.meta.cleaner_slots = p.config.udc.clone();
    st.meta.target_slots = p.config.target.clone();
    let dmf_dip: f64 = if p.buffs.world.contains(&"sayges_dark_fortune_of_damage") { 1.0 + C::DMF_BUFF } else { 1.0 };
    let thaddius_dip: f64 = if p.buffs.boss.contains(&"thaddius") { 1.0 + C::THADDIUS_BUFF } else { 1.0 };
    st.meta.double_dip = dmf_dip * thaddius_dip;
    st.meta.nightfall_period = p.config.nightfall.clone();
    st.boss.nightfall = p.config.nightfall.clone(); // start the swing timers
    st.boss.dragonling_start = p.config.dragonling;

    // Per-lane stats
    let offsets = first_action_offsets(num, p.timing.initial_delay, rng);
    for i in 0..num {
        let l = &mut st.lanes[i];
        l.cast_timer = offsets[i];
        l.hit_chance = p.stats.hit_chance[i];
        l.crit_chance = p.stats.crit_chance[i];
        l.spell_power = p.stats.spell_power[i];
        // Buff availability: PI, trinkets that are assigned get 0 cooldown to open
        for cooldown in l.buff_cooldown.iter_mut() { *cooldown = f64::INFINITY; }
        if st.meta.pi_slots.iter().any(|&idx| idx == i) { l.buff_cooldown[Buff::PowerInfusion as usize] = 0.0; }
        // Others could come from config similarly
    }

    for lane_idx in 0..st.lanes.len() {
        for (buff, indices) in &p.config.buff_assignments {
            if indices.contains(&lane_idx) {
                if let Some(lane) = st.lanes.get_mut(lane_idx) {
                    lane.buff_cooldown[*buff as usize] = 0.0;
                }
            }
        }
    }

    st
}

/// Print SP / Hit / Crit / Int for each mage, plus which buffs are currently ready (cooldown <= 0).
/// Call this right after `init_state(...)` inside `run_single`.
pub fn display_party_stats(st: &State, intellect: Option<&[f64]>) {
    // If you add/remove buffs, update this list to match Buff order/variants.
    let known_buffs: &[(Buff, &str)] = &[
        (Buff::Sapp, "sapp"),
        (Buff::Toep, "toep"),
        (Buff::Zhc,  "zhc"),
        (Buff::Mqg,  "mqg"),
        (Buff::PowerInfusion, "pi"),
    ];

    println!("\n=== Player Stats ===");
    for (i, lane) in st.lanes.iter().enumerate() {
        // gather ready buffs
        let mut ready: Vec<&str> = Vec::new();
        for (b, label) in known_buffs {
            let idx = *b as usize;
            if lane.buff_cooldown.get(idx).map(|&cd| cd <= 0.0).unwrap_or(false) {
                ready.push(*label);
            }
        }
        let ready_str = if ready.is_empty() { "-".to_string() } else { ready.join(",") };

        // intellect if provided; otherwise show "-"
        let int_str = intellect
            .and_then(|ints| ints.get(i).copied())
            .map(|v| format!("{:.0}", v))
            .unwrap_or_else(|| "-".to_string());

        println!(
            "Mage {:>2}: SP={:>4.0}  Hit={:>5.2}%  Crit={:>5.2}%  Int={}  Ready=[{}]",
            i,
            lane.spell_power,
            100.0 * lane.hit_chance,
            100.0 * lane.crit_chance,
            int_str,
            ready_str
        );
    }
}


pub fn run_single<D: Decider>(params: &SimParams, decider: &mut D, seed: u64, idx: u64) -> SimResult {
    let mut rng = Pcg64Mcg::seed_from_u64(seed + idx);

    // Build constants and bake stats
    let k = Constants::new(&params.consts_cfg);
    let mut baked_params = params.clone();

    apply_buffs(&mut baked_params.stats, &params.buffs);

    // Init state
    let mut st = init_state(&baked_params, &mut rng, idx);

    if st.log {
        // show effective stats & ready buffs
        display_party_stats(&st, Some(&baked_params.stats.intellect));
    }

    while st.in_progress() {
        
        if let Some((lane, action, react_sigma)) = decider.next_action(&st) {
            // sample reaction time
            let normal = Normal::new(0.0, react_sigma).unwrap();
            let react: f64 = normal.sample(&mut rng).abs();
            st.start_action(lane, action, react, &k);
        }

        // step one event
        while !st.decision_gate() && st.in_progress() {
            st.step_one(&k, &mut rng);
        }
    }

    // Aggregate DPS
    let dur = st.global.duration.max(1e-9);
    if st.log {
        println!("Logged sim:");
        println!("  total damage: {:.1} duration {:.1}", st.totals.total_damage + st.totals.ignite_damage, dur);
    }
    SimResult {
        total_dps: (st.totals.total_damage + st.totals.ignite_damage) / dur,
        ignite_dps: st.totals.ignite_damage / dur,
        player_dps: st.totals.player_damage / dur,
    }
}

pub fn run_many_with<D, F>(
    params: &SimParams,
    make_decider: F,
    n: usize,
    seed: u64,
) -> Vec<SimResult>
where
    D: Decider,
    F: Fn() -> D,
{
    (0..n)
        .map(|i| {
            let mut dec = make_decider();            // <-- fresh instance each iteration
            run_single(params, &mut dec, seed, i as u64)
        })
        .collect()
}

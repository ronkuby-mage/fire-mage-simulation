//! constants.rs — first pass port from Python `constants.py`
//!
//! Notes:
//! - Keeps spell ordering: [Scorch, Pyroblast, Fireball, FireBlast, Frostbolt]
//! - Replaces string/idx maps with enums where possible.
//! - Values that depended on runtime toggles in Python (ranks, talents, incinerate, etc.)
//!   are computed in `Constants::new(cfg)`.
//! - This file intentionally avoids any sim state. That lives in `state.rs`.

use std::fmt;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Spell { Scorch = 0, Pyroblast = 1, Fireball = 2, FireBlast = 3, Frostbolt = 4 }

impl fmt::Display for Spell {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Spell::Fireball => write!(f, "fireball  "),
            Spell::Scorch => write!(f, "scorch    "),
            Spell::Pyroblast => write!(f, "pyroblast "),
            Spell::FireBlast => write!(f, "fire blast"),
            Spell::Frostbolt => write!(f, "Frostbolt "),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Action {
    // Castable spells
    Scorch = 0,
    Pyroblast = 1,
    Fireball = 2,
    FireBlast = 3,
    Frostbolt = 4,
    // Pseudo-cast for pushing GCD-only waits
    Gcd = 5,
    // Instants / external sources (non-GCD spells in the Python model)
    Combustion = 6,
    Sapp = 7,
    Toep = 8,
    Zhc = 9,
    Mqg = 10,
    PowerInfusion = 11,
}

impl fmt::Display for Action {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Action::Fireball => write!(f, "Fireball"),
            Action::Scorch => write!(f, "Scorch"),
            Action::Pyroblast => write!(f, "Pyroblast"),
            Action::FireBlast => write!(f, "FireBlast"),
            Action::Frostbolt => write!(f, "Frostbolt"),
            Action::Gcd => write!(f, "GCD"),
            Action::Combustion => write!(f, "Combustion"),
            Action::Sapp => write!(f, "Sapp"),
            Action::Toep => write!(f, "Toep"),
            Action::Zhc => write!(f, "Zhc"),
            Action::Mqg => write!(f, "Mqg"),
            Action::PowerInfusion => write!(f, "Power Infusion")
        }
    }
}

impl Action {
    #[inline]
    pub fn is_instant(self) -> bool { matches!(self, Action::Combustion | Action::Sapp | Action::Toep | Action::Zhc | Action::Mqg | Action::PowerInfusion | Action::Gcd) }
}

impl Action {
    pub fn triggers_gcd(&self) -> bool {
        use Action::*;
        matches!(self, Scorch | Pyroblast | Fireball | FireBlast | Frostbolt)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Buff { Sapp = 0, Toep = 1, Zhc = 2, Mqg = 3, PowerInfusion = 4 }

pub const LOG: bool = true;

pub const NUM_SPELLS: usize = 5;          // Scorch, Pyro, Fireball, FireBlast, Frostbolt
pub const NUM_ACTIONS: usize = 12;         // includes GCD + instants

// --- Global mechanical constants (mostly invariant during a run) ---
pub const GLOBAL_COOLDOWN: f64 = 1.5;

pub const IGNITE_TIME: f64 = 4.0;
pub const IGNITE_TICK: f64 = 2.0;
pub const IGNITE_STACK: u8 = 5;

pub const SCORCH_TIME: f64 = 30.0;
pub const SCORCH_STACK: u8 = 5;

pub const COE_MULTIPLIER: f64 = 1.10;      // Curse of Elements multiplier
pub const SCORCH_MULTIPLIER: f64 = 0.03;   // +3% fire vuln per stack

pub const FIRE_BLAST_COOLDOWN: f64 = 7.0;  // assumes 2 talent points

pub const POWER_INFUSION: f64 = 0.20;
pub const MQG_HASTE: f64 = 0.33;           // Mind Quickening Gem cast speed bonus

pub const NUM_BUFFS: usize = 5;            // Sapp, TOEP, ZHC, MQG, PI
pub const NUM_DAMAGE_BUFFS: usize = 3;     // Sapp, TOEP, ZHC
pub const BUFF_DURATION: [f64; NUM_BUFFS] = [20.0, 15.0, 20.0, 20.0, 15.0];
pub const BUFF_COOLDOWN: [f64; NUM_BUFFS] = [120.0, 90.0, 120.0, 300.0, 180.0];
/// Flat damage added per spell hit while active (Sapp, TOEP, ZHC)
pub const BUFF_DAMAGE: [f64; NUM_DAMAGE_BUFFS] = [130.0, 175.0, 204.0];
/// Damage per-tick added per single cast while the buff is active (ZHC drains -17 per cast)
pub const BUFF_PER_TICK: [f64; NUM_DAMAGE_BUFFS] = [0.0, 0.0, -17.0];

pub const COMBUSTIONS: u8 = 3;             // charges
pub const PER_COMBUSTION: f64 = 0.10;      // +10% crit per stack
pub const COMBUSTION_COOLDOWN: f64 = 180.0;

pub const RES_AMOUNT: [f64; 4] = [1.0, 0.75, 0.5, 0.25];
pub const RES_THRESH: [f64; 4] = [0.0, 0.8303, 0.9415, 0.9905];
pub const RES_THRESH_UL: [f64; 4] = [0.8303, 0.9415, 0.9905, 1.0];
/// Folded resistance modifier (kept from Python; used in damage tuning)
pub const RESISTANCE_MODIFIER: f64 = 0.940_997;

pub const DMF_BUFF: f64 = 0.1;
pub const THADDIUS_BUFF: f64 = 1.9;

pub const DECISION_POINT: f64 = 2.0;       // seconds remaining threshold used in rotation logic

pub const DRAGONLING_DURATION: f64 = 60.0;
pub const DRAGONLING_BUFF: f64 = 300.0;    // flat SP during window

pub const NIGHTFALL_PROC_PROB: f64 = 0.15;
pub const NIGHTFALL_VULN: f64 = 0.15;      // +15% spell vulnerability
pub const NIGHTFALL_DURATION: f64 = 5.0;

pub const UDC_MOD: f64 = 0.02;

/// How many opening Scorches are required by number of mages (index by num_mages)
pub const SCORCHES_BY_MAGES: [i32; 13] = [9000, 6, 3, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1];

/// Maps a Buff to the Action that casts it.
#[inline]
pub const fn buff_cast_action(buff: Buff) -> Action {
    match buff {
        Buff::Sapp => Action::Sapp,
        Buff::Toep => Action::Toep,
        Buff::Zhc => Action::Zhc,
        Buff::Mqg => Action::Mqg,
        Buff::PowerInfusion => Action::PowerInfusion,
    }
}

/// Configuration inputs that influence constant tables.
#[derive(Debug, Clone)]
pub struct ConstantsConfig {
    pub fireball_rank: u8,        // default 12
    pub frostbolt_rank: u8,       // default 11
    pub frostbolt_talented: bool, // +6% dmg; 2.5s talented cast
    pub incinerate: bool,         // +4% crit chance bonus to Scorch/Fire Blast
    pub simple_spell: bool,       // use simplified bases/ranges
}

impl Default for ConstantsConfig {
    fn default() -> Self {
        Self {
            fireball_rank: 12,
            frostbolt_rank: 11,
            frostbolt_talented: false,
            incinerate: true,
            simple_spell: false,
        }
    }
}

/// Constants computed from config at sim start (immutable afterward)
#[derive(Debug, Clone)]
pub struct Constants {
    // Multipliers and base/range tables are aligned to NUM_SPELLS order
    pub sp_multiplier: [f64; NUM_SPELLS],
    pub damage_multiplier: [f64; NUM_SPELLS],
    pub spell_base: [f64; NUM_SPELLS],
    pub spell_range: [f64; NUM_SPELLS],
    pub is_scorch: [bool; NUM_SPELLS],
    pub is_fire: [bool; NUM_SPELLS],
    pub incin_bonus: [f64; NUM_SPELLS],

    /// Cast time contribution (without reaction delay); use GLOBAL_COOLDOWN for Action::Gcd
    pub cast_time: [f64; NUM_SPELLS],
    /// Projectile/travel time until impact for non-instant spells
    pub spell_travel: [f64; NUM_SPELLS],

    // Crit math (variant for talented Frostbolt is handled here)
    pub ignite_damage: f64,   // 0.2 of crit
    pub icrit_damage: f64,    // +0.5 for fire crits to emulate 150%
    pub crit_damage: f64,     // +0.5 normal or +1.0 for talented frostbolt

}

impl Constants {
    pub fn new(cfg: &ConstantsConfig) -> Self {
        // Base SP and damage multipliers
        let mut sp_multiplier = [0.428_571_429, 1.0, 1.0, 0.428_571_429, 0.814_285_714];
        let mut damage_multiplier = [1.1, 1.1, 1.1, 1.1, 1.0]; // fire power; frostbolt starts 1.0

        // Base and ranges: simplified or detailed
        let (mut spell_base, mut spell_range) = if cfg.simple_spell {
            ([250.0, 900.0, 750.0, 500.0, 500.0], [0.0, 0.0, 0.0, 0.0, 0.0])
        } else {
            ([237.0, 716.0, 596.0, 446.0, 515.0], [43.0, 174.0, 164.0, 78.0, 40.0])
        };

        // Rank overrides
        if cfg.fireball_rank == 11 { // Fireball (rank 11)
            spell_base[Spell::Fireball as usize] = 561.0;
            spell_range[Spell::Fireball as usize] = 154.0;
        }
        match cfg.frostbolt_rank {
            10 => {
                spell_base[Spell::Frostbolt as usize] = 440.0;
                spell_range[Spell::Frostbolt as usize] = 75.0;
            }
            1 => {
                spell_base[Spell::Frostbolt as usize] = 20.0;
                spell_range[Spell::Frostbolt as usize] = 2.0;
                // Faster rank with different coeff
                let fb = Spell::Frostbolt as usize;
                sp_multiplier[fb] = 0.407_142_857;
            }
            _ => {}
        }

        // Talented Frostbolt adjustments
        if cfg.frostbolt_talented {
            damage_multiplier[Spell::Frostbolt as usize] = 1.06; // Piercing Ice 3/3
        }

        // Cast times (base, before MQG/gcd math)
        let mut cast_time = [1.5, 6.0, 3.0, 0.0, 3.0];
        if cfg.frostbolt_talented {
            cast_time[Spell::Frostbolt as usize] = 2.5;
        }
        if cfg.frostbolt_rank == 1 {
            cast_time[Spell::Frostbolt as usize] = 1.5;
        }

        // Projectile/travel times (to impact)
        let spell_travel = [0.0, 0.875, 0.875, 0.0, 0.75];

        // Flags for spell schools
        let is_scorch = [true, false, false, false, false];
        let is_fire = [true, true, true, true, false];

        // Incinerate talent bonus to Scorch/Fire Blast crit chance
        let incin_bonus = if cfg.incinerate { [0.04, 0.0, 0.0, 0.04, 0.0] } else { [0.0; NUM_SPELLS] };

        // Crit/ignite math
        let ignite_damage = 0.2;
        let icrit_damage = 0.5; // +50% for fire crits
        let crit_damage = if cfg.frostbolt_talented { 1.0 } else { 0.5 };

        Self {
            sp_multiplier,
            damage_multiplier,
            spell_base,
            spell_range,
            is_scorch,
            is_fire,
            incin_bonus,
            cast_time,
            spell_travel,
            ignite_damage,
            icrit_damage,
            crit_damage,
        }
    }
}

/// Convenience for printing the same header Python used (optional)
pub fn log_message() {
    println!("\n===== Simulation Log =====");
}

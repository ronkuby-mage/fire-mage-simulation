//! state.rs — dynamic per-simulation state + mechanics (faithful to Python)

use rand::prelude::*; // bring gen() into scope safely

use crate::constants as C;
use crate::constants::{Action, Buff, Spell, Constants};

#[derive(Debug, Clone, Copy, Default)]
pub struct Totals {
    pub total_damage: f64,
    pub player_damage: f64,
    pub ignite_damage: f64,
    pub crit_damage: f64,
}

#[derive(Debug, Clone)]
pub struct Global {
    pub running_time: f64,
    pub duration: f64,
    pub decision_gate: bool,
}
impl Global { pub fn new(duration: f64) -> Self { Self { running_time: 0.0, duration, decision_gate: false } } }

#[derive(Debug, Clone)]
pub struct Boss {
    pub ignite_timer: f64,
    pub ignite_count: u8,
    pub ignite_value: f64,
    pub ignite_multiplier: f64,
    pub tick_timer: f64,
    pub scorch_timer: f64,
    pub scorch_count: u8,
    pub spell_vulnerability: f64,
    pub dragonling_start: f64,
    pub nightfall: Vec<f64>,
}
impl Default for Boss {
    fn default() -> Self {
        Self {
            ignite_timer: 0.0,
            ignite_count: 0,
            ignite_value: 0.0,
            ignite_multiplier: 1.0,
            tick_timer: f64::INFINITY,
            scorch_timer: 0.0,
            scorch_count: 0,
            spell_vulnerability: 0.0,
            dragonling_start: -C::DRAGONLING_DURATION,
            nightfall: vec![],
        }
    }
}

// dynamic values
#[derive(Debug, Clone)]
pub struct MageLane {
    pub cast_type: Action,
    pub spell_type: Spell,
    pub cast_timer: f64,
    pub spell_timer: f64,
    pub gcd_timer: f64,
    pub fb_cooldown: f64,
    pub comb_stack: u8,
    pub comb_left: u8,
    pub comb_avail: u8,
    pub comb_cooldown: f64,
    pub buff_timer: [f64; C::NUM_BUFFS],
    pub buff_cooldown: [f64; C::NUM_BUFFS],
    pub buff_ticks: [u32; C::NUM_DAMAGE_BUFFS],
    pub crit_too_late: bool,
    pub hit_chance: f64,
    pub crit_chance: f64,
    pub spell_power: f64,
    pub cast_number: i32,
    
}

impl Default for MageLane {
    fn default() -> Self {
        Self {
            cast_type: Action::Gcd,
            spell_type: Spell::Scorch,
            cast_timer: f64::INFINITY,
            spell_timer: f64::INFINITY,
            gcd_timer: 0.0,
            fb_cooldown: 0.0,
            comb_stack: 0,
            comb_left: 0,
            comb_avail: 1,
            comb_cooldown: f64::INFINITY,
            buff_timer: [0.0; C::NUM_BUFFS],
            buff_cooldown: [f64::INFINITY; C::NUM_BUFFS],
            buff_ticks: [0; C::NUM_DAMAGE_BUFFS],
            crit_too_late: false,
            hit_chance: 0.99,
            crit_chance: 0.062,
            spell_power: 0.0,
            cast_number: -1,
        }
    }
}

// stat values
#[derive(Debug, Clone, Default)]
pub struct PlayerMeta {
    pub dmf_slots: Vec<usize>,
    pub cleaner_slots: Vec<usize>,
    pub pi_slots: Vec<usize>,
    pub target_slots: Vec<usize>,
    pub nightfall_period: Vec<f64>,
    pub vulnerability: f64,
}

#[derive(Debug, Clone)]
pub struct State {
    pub global: Global,
    pub boss: Boss,
    pub lanes: Vec<MageLane>,
    pub meta: PlayerMeta,
    pub totals: Totals,
    pub log: bool,
}

impl State {
    pub fn new(duration: f64, num_mages: usize) -> Self {
        Self {
            global: Global::new(duration),
            boss: Boss::default(),
            lanes: vec![MageLane::default(); num_mages],
            meta: PlayerMeta::default(),
            totals: Totals::default(),
            log: false,
        }
    }

    // ---------- time & scheduling ----------
    pub fn subtime(&mut self, dt: f64) {
        self.global.running_time += dt;
        self.boss.ignite_timer -= dt;
        self.boss.tick_timer -= dt;
        self.boss.scorch_timer -= dt;
        self.boss.spell_vulnerability -= dt;
        for l in &mut self.lanes {
            l.cast_timer -= dt;
            l.spell_timer -= dt;
            l.gcd_timer -= dt;
            l.comb_cooldown -= dt;
            l.fb_cooldown -= dt;
            for t in &mut l.buff_timer { *t -= dt; }
            for c in &mut l.buff_cooldown { *c -= dt; }
        }
        for t in &mut self.boss.nightfall {
            *t -= dt;
        }
    }

    pub fn next_cast_lane(&self) -> Option<usize> {
        self.lanes
            .iter()
            .enumerate()
            .min_by(|a, b| a.1.cast_timer.total_cmp(&b.1.cast_timer))
            .map(|(i, _)| i)
    }

    pub fn next_spell_lane(&self) -> Option<usize> {
        self.lanes
            .iter()
            .enumerate()
            .min_by(|a, b| a.1.spell_timer.total_cmp(&b.1.spell_timer))
            .map(|(i, _)| i)
    }

    pub fn set_decision_gate(&mut self, on: bool) { self.global.decision_gate = on; }
    pub fn decision_gate(&self) -> bool { self.global.decision_gate }
    pub fn in_progress(&self) -> bool { self.global.running_time < self.global.duration }

    /// Called by the decider mapping of _apply_decisions → start_action
    pub fn start_action(&mut self, lane: usize, action: Action, react_time: f64, k: &Constants) {
        use crate::constants::{Action as A, Buff as B, Spell as S};

        let l = &mut self.lanes[lane];

        // schedule start
        l.cast_timer = react_time;
        l.cast_type = action;

        // GCD spells add cast time and compute leftover gcd
        if action == A::Gcd {
            l.cast_timer = C::GLOBAL_COOLDOWN;
        }
        else if action.triggers_gcd() {
            let base_cast = match action {
                A::Scorch      => k.cast_time[S::Scorch as usize],
                A::Pyroblast   => k.cast_time[S::Pyroblast as usize],
                A::Fireball    => k.cast_time[S::Fireball as usize],
                A::FireBlast   => k.cast_time[S::FireBlast as usize], // 0.0 in constants; still on GCD
                A::Frostbolt   => k.cast_time[S::Frostbolt as usize],
                _ => 0.0,
            };

            // MQG haste (Python divides cast portion by 1+MQG)
            let mqg = if l.buff_timer[B::Mqg as usize] > 0.0 { 1.0 + C::MQG_HASTE } else { 1.0 };
            let cast_time = base_cast / mqg;

            let total = react_time + cast_time;
            l.cast_timer = total;

            // leftover GCD stored to be pushed after cast ends
            let gcd_len = C::GLOBAL_COOLDOWN;
            l.gcd_timer = (gcd_len + react_time - total).max(0.0);
        } else {
            l.gcd_timer = 0.0;
        }
        if self.log {
            println!("  {:6.2} mage {} START {}", self.global.running_time, lane, action);
        }

        // Block decisions until the event is handled (Python clears global decision flag)
        self.set_decision_gate(false);
    }

    pub fn finish_cast(&mut self, k: &Constants) {
        use crate::constants::{Action as A, Buff as B, Spell as S};

        // Which lane just finished its cast?
        let Some(lane) = self.next_cast_lane() else { return };
        let dt = self.lanes[lane].cast_timer;
        self.subtime(dt); // advance global & subtract dt from all timers

        // Snapshot and reset lane cast timer
        let l = &mut self.lanes[lane];
        let action = l.cast_type;
        //l.cast_timer = f64::INFINITY;

        // 1) transfer to spell stage if it's a non-instant (Python: cast_type < CAST_GCD)
        let is_instant = matches!(action, A::Combustion | A::Sapp | A::Toep | A::Zhc | A::Mqg | A::PowerInfusion | A::Gcd);
        if !is_instant {
            // map Action → Spell index
            let spell = match action {
                A::Scorch    => S::Scorch,
                A::Pyroblast => S::Pyroblast,
                A::Fireball  => S::Fireball,
                A::FireBlast => S::FireBlast, // its SPELL_TIME will be 0, handled as instant projectile
                A::Frostbolt => S::Frostbolt,
                _ => S::Scorch, // safe default; you can refine
            };
            l.spell_type  = spell;
            l.spell_timer = k.spell_travel[spell as usize];

            // Special: fire blast starts its own cooldown on *cast end* in Python
            if matches!(action, A::FireBlast) {
                l.fb_cooldown = C::FIRE_BLAST_COOLDOWN;
            }
        } else {

            // 2) apply instant casts’ effects immediately (Python “apply instant spells” block)
            match action {
                A::Combustion => {
                    l.comb_left = C::COMBUSTIONS as u8;
                    l.comb_stack = 1;
                    l.comb_cooldown = f64::INFINITY; // temp hold until last charge is used
                }
                A::Sapp | A::Toep | A::Zhc | A::Mqg | A::PowerInfusion => {
                    let b = match action {
                        A::Sapp => B::Sapp,
                        A::Toep => B::Toep,
                        A::Zhc => B::Zhc,
                        A::Mqg => B::Mqg,
                        A::PowerInfusion => B::PowerInfusion,
                        _ => unreachable!(),
                    } as usize;

                    // start active duration and cooldown
                    l.buff_timer[b] = C::BUFF_DURATION[b];
                    l.buff_cooldown[b] = C::BUFF_COOLDOWN[b];

                    // reset damage-buff tick counters
                    if b < C::NUM_DAMAGE_BUFFS {
                        l.buff_ticks[b] = 0;
                    }

                    // Internal cooldown on all *other* dmg trinkets + MQG:
                    // set their cooldown to at least this buff’s duration
                    let lock_icd = C::NUM_DAMAGE_BUFFS + 1; // include MQG
                    for bb in 0..lock_icd {
                        if bb == b { continue; }
                        l.buff_cooldown[bb] = l.buff_cooldown[bb].max(C::BUFF_DURATION[b]);
                    }
                }
                _ => {}
            }
        }

        let push_gcd: bool;
        {
            let l = &mut self.lanes[lane];

            if l.gcd_timer > 0.0 {
                // schedule a GCD placeholder cast immediately
                l.cast_type  = Action::Gcd;
                l.cast_timer = l.gcd_timer;
                l.gcd_timer  = 0.0;
                push_gcd = true;
            } else {
                // we’ll open the decision gate after we drop `l`
                push_gcd = false;
            }
            // `l` goes out of scope here — mutable borrow ends.
        }

        // ---- now we can borrow &mut self again safely ----
        if !push_gcd {
            self.set_decision_gate(true);
            let cn = self.lanes[lane].cast_number;
            self.lanes[lane].cast_number = cn.saturating_add(1);
        }
        if self.log {
            println!("  {:6.2} mage {} END   {}", self.global.running_time, lane, action);
        }

    }

    // ---------- mechanics: landing & effects (faithful to Python) ----------
    pub fn land_spell<R: rand::Rng + ?Sized>(&mut self, k: &Constants, rng: &mut R) {
        let Some(lane) = self.next_spell_lane() else { return };
        let dt = self.lanes[lane].spell_timer;
        self.subtime(dt);

        if !self.in_progress() { return }
        let lanes_len = self.lanes.len();

        // grab lane fields you need for early checks
        let lane_hit = self.lanes[lane].hit_chance;
        let spell_string = self.lanes[lane].spell_type;
        let spell_type = self.lanes[lane].spell_type as usize;
        let l = &mut self.lanes[lane];
        l.spell_timer = f64::INFINITY;

        // use the stashed values instead of reading through `l` where possible
        if rng.r#gen::<f64>() >= lane_hit {
            if self.log {
                println!("  {:6.2} mage {} misses", self.global.running_time, lane);
            }
            // ---- now take the mutable borrow of this lane ----

            return;
        }

        // ---- read-only stuff from &self (no &mut borrow yet) ----
        let targeted_all = self.meta.target_slots.len() == lanes_len;
        let is_cleaner = self.meta.cleaner_slots.iter().any(|&i| i == lane);
        let is_target = targeted_all || self.meta.target_slots.iter().any(|&i| i == lane);
        let is_dmf = self.meta.dmf_slots.iter().any(|&i| i == lane);

        let dragonling_active = (self.global.running_time >= self.boss.dragonling_start) && (self.global.running_time < self.boss.dragonling_start + C::DRAGONLING_DURATION);
        let mut buff_damage = if dragonling_active { C::DRAGONLING_BUFF } else { 0.0 };
        for b in 0..C::NUM_DAMAGE_BUFFS { if l.buff_timer[b] > 0.0 { buff_damage += C::BUFF_DAMAGE[b] + (l.buff_ticks[b] as f64)*C::BUFF_PER_TICK[b]; l.buff_ticks[b]=l.buff_ticks[b].saturating_add(1); } }

        let base_roll: f64 = rng.r#gen();
        let mut spell_damage = k.spell_base[spell_type] + base_roll*k.spell_range[spell_type] + k.sp_multiplier[spell_type]*(l.spell_power + buff_damage);
        if k.is_fire[spell_type] {
            let r: f64 = rng.r#gen();
            let partial = if r < C::RES_THRESH[1] { C::RES_AMOUNT[0] } else if r < C::RES_THRESH[2] { C::RES_AMOUNT[1] } else if r < C::RES_THRESH[3] { C::RES_AMOUNT[2] } else { C::RES_AMOUNT[3] };
            spell_damage *= partial;
        }

        // all damage multipliers
        spell_damage *= C::COE_MULTIPLIER * k.damage_multiplier[spell_type]; // COE + fire power
        if k.is_fire[spell_type] && self.boss.scorch_timer > 0.0 { spell_damage *= 1.0 + C::SCORCH_MULTIPLIER*(self.boss.scorch_count as f64); }
        if l.buff_timer[Buff::PowerInfusion as usize] > 0.0 { spell_damage *= 1.0 + C::POWER_INFUSION; }
        if self.boss.spell_vulnerability > 0.0 { spell_damage *= 1.0 + C::NIGHTFALL_VULN; }
        if is_dmf { spell_damage *= 1.0 + C::DMF_BUFF; }
        spell_damage *= self.meta.vulnerability; // Thaddius
        if is_cleaner { spell_damage *= 1.0 + C::UDC_MOD }

        // add to total
        self.totals.total_damage += spell_damage;
        if is_target { self.totals.player_damage += spell_damage; }

        let is_fire = k.is_fire[spell_type];
        let is_scorch = k.is_scorch[spell_type];
        let comb_bonus = if is_fire && !is_scorch && l.comb_left > 0 { C::PER_COMBUSTION * (l.comb_stack as f64) } else { 0.0 };
        let crit_chance = (l.crit_chance + comb_bonus + k.incin_bonus[spell_type]).clamp(0.0, 1.0);
        let is_crit = rng.r#gen::<f64>() < crit_chance;

        if is_crit {
            if is_fire {
                // ignite timer checks
                if self.boss.ignite_timer <= 0.0 {
                    self.boss.ignite_count = 0;
                    self.boss.ignite_value = 0.0;
                }
                if self.boss.ignite_timer < C::DECISION_POINT { l.crit_too_late = true; }
                if self.boss.tick_timer > C::IGNITE_TICK && self.boss.ignite_count > 0 { self.boss.tick_timer = C::IGNITE_TICK; }
                self.boss.ignite_timer = C::IGNITE_TIME + 1e-6;

                if self.boss.ignite_count == 0 {
                    self.boss.tick_timer = C::IGNITE_TICK;
                    let pi_mult = if l.buff_timer[Buff::PowerInfusion as usize] > 0.0 { 1.0 + C::POWER_INFUSION } else { 1.0 };
                    let dmf_mult = if is_dmf {1.0 + C::DMF_BUFF} else { 1.0 };
                    // snap shot value
                    self.boss.ignite_multiplier = if is_cleaner { 1.0 + C::UDC_MOD } else { 1.0 } * pi_mult * dmf_mult * self.meta.vulnerability;
                }
                if self.boss.ignite_count < C::IGNITE_STACK {
                    let crit_mult = 1.0 + k.icrit_damage; // 1.5
                    let ignite_add = crit_mult * k.ignite_damage * spell_damage;
                    if is_cleaner { self.boss.ignite_value += (1.0 + C::UDC_MOD) * ignite_add; } else { self.boss.ignite_value += ignite_add; }
                    self.boss.ignite_count = self.boss.ignite_count.saturating_add(1).min(C::IGNITE_STACK);
                }

                // subtract previous damage from totals
                self.totals.total_damage -= spell_damage;
                if is_target { self.totals.player_damage -= spell_damage; }

                // calculate crit damage
                let crit_line = (1.0 + k.icrit_damage) * spell_damage; // 1.5x for fire crit ledger
                let crit_mult_line = if is_cleaner { 1.0 + C::UDC_MOD } else { 1.0 };

                // add crit damage
                self.totals.total_damage += crit_line * crit_mult_line;
                if is_target { self.totals.player_damage += crit_line * crit_mult_line; }

                // reset spell damage
                spell_damage = crit_line * crit_mult_line;

                if l.comb_left == 1 { l.comb_cooldown = C::COMBUSTION_COOLDOWN; }
                if l.comb_left > 0 { l.comb_left -= 1; }
            } else {
                let extra = k.crit_damage * spell_damage; // +0.5 or +1.0
                self.totals.total_damage += extra;
                if is_target { self.totals.player_damage += extra; }
            }
        }
        if self.boss.scorch_timer <= 0.0 {
            self.boss.scorch_count = 0     
        }
        if k.is_scorch[spell_type] {
            if rng.r#gen::<f64>() < lane_hit {
                self.boss.scorch_timer = C::SCORCH_TIME;
                self.boss.scorch_count = (self.boss.scorch_count + 1).min(C::SCORCH_STACK);
            }
        }
        if is_fire { l.comb_stack = l.comb_stack.saturating_add(1); }

        if self.log {
            if is_crit {
                println!("  {:6.2} mage {} spell {} CRIT for {}", self.global.running_time, lane, spell_string, spell_damage)
            } else {
                println!("  {:6.2} mage {} spell {} hit  for {}", self.global.running_time, lane, spell_string, spell_damage)
            }
        }

    }

    pub fn tick_ignite<R: Rng + ?Sized>(&mut self, rng: &mut R) {
        // subtime
        let dt = self.boss.tick_timer;
        self.subtime(dt);

        if !self.in_progress() { return }

        if self.boss.ignite_timer >= C::IGNITE_TICK {
            self.boss.tick_timer = C::IGNITE_TICK;
        } else {
            self.boss.tick_timer = f64::INFINITY;
        }
        if self.boss.ignite_timer <= 0.0 {
            return
        }

        let mut mult = C::COE_MULTIPLIER * self.boss.ignite_multiplier;
        if self.boss.scorch_timer > 0.0 { mult *= 1.0 + C::SCORCH_MULTIPLIER*(self.boss.scorch_count as f64); }
        if self.boss.spell_vulnerability > 0.0 { mult *= 1.0 + C::NIGHTFALL_VULN; }
        let r: f64 = rng.r#gen();
        mult *= if r < C::RES_THRESH[1] { C::RES_AMOUNT[0] } else if r < C::RES_THRESH[2] { C::RES_AMOUNT[1] } else if r < C::RES_THRESH[3] { C::RES_AMOUNT[2] } else { C::RES_AMOUNT[3] };
        self.totals.ignite_damage += mult * self.boss.ignite_value;
        if self.log {
            println!("  {:6.2} in ignite {} mult {}", self.global.running_time, mult * self.boss.ignite_value, mult);
        }

    }

    pub fn proc_nightfall<R: rand::Rng + ?Sized>(&mut self, _k: &Constants, rng: &mut R) {
        // 1) find soonest Nightfall check
        let (idx, dt) = match self.boss.nightfall
            .iter()
            .enumerate()
            .min_by(|a, b| a.1.total_cmp(b.1))
        {
            Some((i, &t)) if t.is_finite() => (i, t),
            _ => return, // nothing scheduled
        };

        // 2) advance time by dt (this also subtracts dt from all boss.nightfall_timers)
        self.subtime(dt);

        // 3) reset this source's swing timer to its period
        if let Some(period) = self.meta.nightfall_period.get(idx).copied() {
            self.boss.nightfall[idx] = period;
        }

        // 4) roll Nightfall proc; if it hits, apply vulnerability window
        if rng.r#gen::<f64>() < C::NIGHTFALL_PROC_PROB {
            self.boss.spell_vulnerability = C::NIGHTFALL_DURATION;
        }
    }

    /// One discrete simulation step (faithful to mechanics._advance):
    /// choose the nearest event among: cast finish, spell land, ignite tick, nightfall proc
    /// Priority on ties: cast < spell < tick < proc
    pub fn step_one<R: rand::Rng + ?Sized>(&mut self, k: &Constants, rng: &mut R) {
        // Gather next event times
        let cast_t  = self.lanes.iter().map(|l| l.cast_timer).fold(f64::INFINITY, f64::min);
        let spell_t = self.lanes.iter().map(|l| l.spell_timer).fold(f64::INFINITY, f64::min);
        let tick_t  = self.boss.tick_timer;
        let proc_t  = self.boss.nightfall.iter().copied().fold(f64::INFINITY, f64::min);

        // Short-circuit if nothing scheduled
        if !cast_t.is_finite() && !spell_t.is_finite() && !tick_t.is_finite() && !proc_t.is_finite() {
            return;
        }

        // Exact Python priority: cast < spell < tick < proc
        if cast_t <= spell_t && cast_t <= tick_t && cast_t <= proc_t {
            self.finish_cast(k);
            return;
        }
        if spell_t <= tick_t && spell_t <= proc_t {
            self.land_spell(k, rng);
            return;
        }
        if tick_t <= proc_t {
            self.tick_ignite(rng);
            return;
        }
        self.proc_nightfall(k, rng);
    }

}

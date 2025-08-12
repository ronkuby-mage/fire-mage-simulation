//! decisions.rs — rotation logic

use crate::constants::{Action, Buff};
use crate::state::State;

fn action_to_buff(action: Action) -> Option<Buff> {
    match action {
        Action::Sapp => Some(Buff::Sapp),
        Action::Toep => Some(Buff::Toep),
        Action::Zhc => Some(Buff::Zhc),
        Action::Mqg => Some(Buff::Mqg),
        Action::PowerInfusion => Some(Buff::PowerInfusion),
        _ => None,
    }
}

fn buff_ready_for_action(st: &State, lane: usize, action: Action) -> bool {
    if let Some(buff) = action_to_buff(action) {
        st.lanes[lane].buff_cooldown[buff as usize] <= 0.0
    } else {
        false
    }
}

pub trait Decider {
    fn next_action(&mut self, st: &State) -> Option<(usize, Action, f64)>;
}

pub struct ScriptedDecider {
    stages: Vec<usize>,            // per-lane progress
    initial_sequence: Vec<Action>, // opener shared by all lanes
    default_action: Action,
    initial_react: f64,
    continuing_react: f64,
}

impl ScriptedDecider {
    pub fn new(
        num_mages: usize,
        initial_sequence: Vec<Action>,
        default_action: Action,
        initial_react: f64,
        continuing_react: f64,
    ) -> Self {
        Self {
            stages: vec![0; num_mages],
            initial_sequence,
            default_action,
            initial_react,
            continuing_react,
        }
    }
}

impl Decider for ScriptedDecider {
    fn next_action(&mut self, st: &State) -> Option<(usize, Action, f64)> {
        let lane = st.next_cast_lane()?;

        while self.stages[lane] < self.initial_sequence.len() {
            let action = self.initial_sequence[self.stages[lane]];
            self.stages[lane] += 1;
            if action_to_buff(action).is_some() {
                if buff_ready_for_action(st, lane, action) {
                    return Some((lane, action, self.initial_react));
                }
            } else {
                return Some((lane, action, self.initial_react));
            }
        }

        // Otherwise, always cast the default spell
        Some((lane, self.default_action, self.continuing_react))
    }
}

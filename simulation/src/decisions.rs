//! decisions.rs — rotation logic

use crate::constants::Action;
use crate::state::State;

/// Decider returns: (lane_idx, action, reaction_sigma)
pub trait Decider {
    fn next_action(&mut self, state: &State) -> Option<(usize, Action, f64)>;
}

/// Minimal stub: always casts Fireball on the next-ready lane, small reaction.
pub struct FireballSpam;
impl Decider for FireballSpam {
    fn next_action(&mut self, state: &State) -> Option<(usize, Action, f64)> {
        let lane = state.next_cast_lane()?;
        Some((lane, Action::Fireball, 0.05))
    }
}

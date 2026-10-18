//! CHOICE: one lock protects the entire count/total/seen invariant.
use std::sync::Mutex;

use crate::{Job, MAX_ITEMS, RunError};

#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Snapshot {
    pub count: usize,
    pub total: u32,
    pub values: [Option<u16>; MAX_ITEMS],
}

#[derive(Debug, Default)]
pub struct Ledger(Mutex<Snapshot>);

impl Ledger {
    pub fn commit(&self, job: Job) -> Result<(), RunError> {
        if job.id >= MAX_ITEMS {
            return Err(RunError::InvalidId);
        }
        let mut state = self.0.lock().map_err(|_| RunError::WorkerPanicked)?;
        if state.values[job.id].is_some() {
            return Err(RunError::DuplicateId);
        }
        state.values[job.id] = Some(job.value);
        state.count += 1;
        state.total += u32::from(job.value);
        Ok(())
    }

    pub fn snapshot(&self) -> Result<Snapshot, RunError> {
        self.0.lock().map(|state| state.clone()).map_err(|_| RunError::WorkerPanicked)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::sync::atomic::{AtomicUsize, Ordering};

    #[test]
    fn a_split_update_can_break_a_compound_invariant() {
        let count = AtomicUsize::new(0);
        let total = AtomicUsize::new(0);
        count.fetch_add(1, Ordering::SeqCst);
        // Deterministic observer seam between two individually atomic writes.
        assert_eq!(count.load(Ordering::SeqCst), 1);
        assert_eq!(total.load(Ordering::SeqCst), 0);
        total.fetch_add(7, Ordering::SeqCst);
        assert_eq!(total.load(Ordering::SeqCst), 7);
    }

    #[test]
    fn locked_commits_keep_every_value_and_total_together() {
        let ledger = Arc::new(Ledger::default());
        std::thread::scope(|scope| {
            let left = Arc::clone(&ledger);
            let a = scope.spawn(move || left.commit(Job { id: 0, value: 7 }));
            let right = Arc::clone(&ledger);
            let b = scope.spawn(move || right.commit(Job { id: 1, value: 17 }));
            assert_eq!(a.join().unwrap(), Ok(()));
            assert_eq!(b.join().unwrap(), Ok(()));
        });
        let state = ledger.snapshot().unwrap();
        assert_eq!(state.count, state.values.iter().flatten().count());
        assert_eq!(state.total, state.values.iter().flatten().map(|value| u32::from(*value)).sum::<u32>());
        assert_eq!((state.count, state.total), (2, 24));
    }

    #[test]
    fn duplicate_is_a_no_op() {
        let ledger = Ledger::default();
        assert_eq!(ledger.commit(Job { id: 0, value: 7 }), Ok(()));
        let before = ledger.snapshot().unwrap();
        assert_eq!(ledger.commit(Job { id: 0, value: 17 }), Err(RunError::DuplicateId));
        assert_eq!(ledger.snapshot().unwrap(), before);
    }

    #[test]
    fn invalid_id_is_a_no_op() {
        let ledger = Ledger::default();
        assert_eq!(ledger.commit(Job { id: 8, value: 7 }), Err(RunError::InvalidId));
        assert_eq!(ledger.snapshot().unwrap(), Snapshot::default());
    }
}

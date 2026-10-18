#![forbid(unsafe_code)]

pub mod ledger;

pub const MAX_ITEMS: usize = 8;
pub const WORKERS: usize = 2;
pub const CHANNEL_CAPACITY: usize = 2;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Job {
    pub id: usize,
    pub value: u16,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Mode {
    Normal,
    FailItem(usize),
    CancelBeforeStart,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RunError {
    TooManyItems,
    InvalidId,
    DuplicateId,
    WorkerFailed(usize),
    WorkerPanicked,
    SpawnFailed,
    Deadline,
    Cancelled,
    Incomplete,
}

impl RunError {
    pub fn code(self) -> String {
        match self {
            Self::TooManyItems => "too-many-items".into(),
            Self::InvalidId => "invalid-id".into(),
            Self::DuplicateId => "duplicate-id".into(),
            Self::WorkerFailed(id) => format!("worker-failed id={id}"),
            Self::WorkerPanicked => "worker-panicked".into(),
            Self::SpawnFailed => "spawn-failed".into(),
            Self::Deadline => "deadline".into(),
            Self::Cancelled => "cancelled".into(),
            Self::Incomplete => "incomplete".into(),
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
pub struct Report {
    pub ids: Vec<usize>,
    pub total: u32,
}

impl Report {
    pub fn render(&self) -> String {
        let ids = if self.ids.is_empty() {
            "-".into()
        } else {
            self.ids
                .iter()
                .map(usize::to_string)
                .collect::<Vec<_>>()
                .join("|")
        };
        format!("count={} total={} ids={ids}\n", self.ids.len(), self.total)
    }
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Lifecycle {
    pub spawned: usize,
    pub joined: usize,
    pub received: usize,
    pub channel_closed: bool,
    pub cancelled: bool,
}

#[derive(Debug)]
pub struct Run {
    pub report: Result<Report, RunError>,
    pub lifecycle: Lifecycle,
}

fn validate(jobs: &[Job]) -> Result<(), RunError> {
    if jobs.len() > MAX_ITEMS {
        return Err(RunError::TooManyItems);
    }
    let mut seen = [false; MAX_ITEMS];
    for job in jobs {
        if job.id >= MAX_ITEMS {
            return Err(RunError::InvalidId);
        }
        if seen[job.id] {
            return Err(RunError::DuplicateId);
        }
        seen[job.id] = true;
    }
    Ok(())
}

fn summarize(mut completed: Vec<Job>, expected: usize) -> Result<Report, RunError> {
    validate(&completed)?;
    if completed.len() != expected {
        return Err(RunError::Incomplete);
    }
    completed.sort_by_key(|job| job.id);
    Ok(Report {
        ids: completed.iter().map(|job| job.id).collect(),
        total: completed.iter().map(|job| u32::from(job.value)).sum(),
    })
}

// CORE: preserve this working sequential contract while introducing threads.
pub fn run(jobs: Vec<Job>, mode: Mode) -> Run {
    let mut lifecycle = Lifecycle::default();
    let report = validate(&jobs).and_then(|()| {
        if mode == Mode::CancelBeforeStart {
            lifecycle.cancelled = true;
            return Err(RunError::Cancelled);
        }
        let mut completed = Vec::new();
        for job in &jobs {
            if mode == Mode::FailItem(job.id) {
                lifecycle.cancelled = true;
                return Err(RunError::WorkerFailed(job.id));
            }
            completed.push(*job);
            lifecycle.received += 1;
        }
        summarize(completed, jobs.len())
    });
    Run { report, lifecycle }
}

#[cfg(test)]
mod tests {
    use super::*;

    const THREADED: bool = false;

    fn jobs() -> Vec<Job> {
        vec![Job { id: 3, value: 17 }, Job { id: 0, value: 7 }]
    }

    fn stopped(result: &Run) {
        assert_eq!(result.lifecycle.spawned, result.lifecycle.joined);
        if THREADED {
            assert_eq!(result.lifecycle.spawned, WORKERS);
            assert!(result.lifecycle.channel_closed);
        } else {
            assert_eq!(result.lifecycle.spawned, 0);
        }
    }

    #[test]
    fn sorted_report_accounts_for_every_item() {
        let result = run(jobs(), Mode::Normal);
        assert_eq!(
            result.report.as_ref().unwrap().render(),
            "count=2 total=24 ids=0|3\n"
        );
        assert_eq!(result.lifecycle.received, 2);
        stopped(&result);
    }

    #[test]
    fn empty_also_closes_and_joins() {
        let result = run(Vec::new(), Mode::Normal);
        assert_eq!(
            result.report.as_ref().unwrap().render(),
            "count=0 total=0 ids=-\n"
        );
        stopped(&result);
    }

    #[test]
    fn sparse_zero_values_preserve_ids_count_and_total() {
        let result = run(
            vec![
                Job { id: 7, value: 0 },
                Job { id: 2, value: 65535 },
                Job { id: 4, value: 0 },
            ],
            Mode::Normal,
        );
        assert_eq!(
            result.report.as_ref().unwrap().render(),
            "count=3 total=65535 ids=2|4|7\n"
        );
        assert_eq!(result.lifecycle.received, 3);
        stopped(&result);
    }

    #[test]
    fn exact_cap_and_largest_values() {
        let input = (0..MAX_ITEMS)
            .map(|id| Job {
                id,
                value: u16::MAX,
            })
            .collect();
        let result = run(input, Mode::Normal);
        assert_eq!(result.report.as_ref().unwrap().total, 524280);
        assert_eq!(result.lifecycle.received, MAX_ITEMS);
        stopped(&result);
    }

    #[test]
    fn rejects_one_over_before_starting() {
        let result = run(vec![Job { id: 0, value: 0 }; 9], Mode::Normal);
        assert_eq!(result.report, Err(RunError::TooManyItems));
        assert_eq!(result.lifecycle, Lifecycle::default());
    }

    #[test]
    fn rejects_duplicate_before_starting() {
        let result = run(vec![Job { id: 1, value: 0 }; 2], Mode::Normal);
        assert_eq!(result.report, Err(RunError::DuplicateId));
        assert_eq!(result.lifecycle, Lifecycle::default());
    }

    #[test]
    fn rejects_outside_id_before_starting() {
        let result = run(vec![Job { id: 8, value: 0 }], Mode::Normal);
        assert_eq!(result.report, Err(RunError::InvalidId));
        assert_eq!(result.lifecycle, Lifecycle::default());
    }

    #[test]
    fn propagates_a_known_worker_failure_without_report() {
        let result = run(jobs(), Mode::FailItem(3));
        assert_eq!(result.report, Err(RunError::WorkerFailed(3)));
        assert!(result.lifecycle.cancelled);
        stopped(&result);
    }

    #[test]
    fn cancelling_before_start_closes_and_joins() {
        let result = run(jobs(), Mode::CancelBeforeStart);
        assert_eq!(result.report, Err(RunError::Cancelled));
        assert!(result.lifecycle.cancelled);
        assert_eq!(result.lifecycle.received, 0);
        stopped(&result);
    }

    #[test]
    fn absent_failure_id_is_not_a_failure() {
        let result = run(jobs(), Mode::FailItem(7));
        assert_eq!(result.report.as_ref().unwrap().total, 24);
        stopped(&result);
    }

    #[test]
    fn missing_completion_is_rejected() {
        assert_eq!(summarize(vec![jobs()[0]], 2), Err(RunError::Incomplete));
    }

    #[test]
    fn duplicate_completion_is_rejected() {
        assert_eq!(summarize(vec![jobs()[0]; 2], 2), Err(RunError::DuplicateId));
    }

    #[test]
    fn arrival_order_does_not_change_report() {
        let forward = summarize(jobs(), 2).unwrap();
        let mut reversed = jobs();
        reversed.reverse();
        assert_eq!(summarize(reversed, 2), Ok(forward));
    }
}

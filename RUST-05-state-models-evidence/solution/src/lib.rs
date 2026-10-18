#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Draft,
    Reviewed,
    Published,
}

impl Phase {
    pub fn code(self) -> &'static str {
        match self {
            Self::Draft => "draft",
            Self::Reviewed => "reviewed",
            Self::Published => "published",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TransitionError {
    InvalidLegacyState,
    InvalidReviewer,
    NeedsReview,
    AlreadyReviewed,
    AlreadyPublished,
    PublishedCannotReset,
}

impl TransitionError {
    pub fn code(self) -> &'static str {
        match self {
            Self::InvalidLegacyState => "invalid-legacy-state",
            Self::InvalidReviewer => "invalid-reviewer",
            Self::NeedsReview => "needs-review",
            Self::AlreadyReviewed => "already-reviewed",
            Self::AlreadyPublished => "already-published",
            Self::PublishedCannotReset => "published-cannot-reset",
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Reviewer(String);

impl Reviewer {
    pub fn new(name: &str) -> Result<Self, TransitionError> {
        // Count Unicode scalars; displayed graphemes may contain several scalars.
        if name.is_empty()
            || name.trim() != name
            || name == "-"
            || name.chars().count() > 32
            || name.chars().any(char::is_control)
        {
            return Err(TransitionError::InvalidReviewer);
        }
        Ok(Self(name.to_owned()))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Legacy {
    pub reviewed: bool,
    pub published: bool,
    pub reviewer: Option<String>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Event {
    Review(String),
    Publish,
    Reset,
}

fn validate_legacy(input: &Legacy) -> Result<Option<Reviewer>, TransitionError> {
    match (input.reviewed, input.published, input.reviewer.is_some()) {
        (false, false, false) | (true, false, true) | (true, true, true) => {}
        _ => return Err(TransitionError::InvalidLegacyState),
    }
    input.reviewer.as_deref().map(Reviewer::new).transpose()
}

#[derive(Clone, Debug, PartialEq, Eq)]
enum State {
    Draft,
    Reviewed(Reviewer),
    Published(Reviewer),
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Session {
    state: State,
}

impl Session {
    pub fn new() -> Self {
        Self {
            state: State::Draft,
        }
    }

    pub fn from_legacy(input: Legacy) -> Result<Self, TransitionError> {
        let reviewer = validate_legacy(&input)?;
        let state = match (input.published, reviewer) {
            (true, Some(name)) => State::Published(name),
            (false, Some(name)) => State::Reviewed(name),
            (false, None) => State::Draft,
            (true, None) => return Err(TransitionError::InvalidLegacyState),
        };
        Ok(Self { state })
    }

    pub fn snapshot(&self) -> Legacy {
        match &self.state {
            State::Draft => Legacy {
                reviewed: false,
                published: false,
                reviewer: None,
            },
            State::Reviewed(name) => Legacy {
                reviewed: true,
                published: false,
                reviewer: Some(name.as_str().to_owned()),
            },
            State::Published(name) => Legacy {
                reviewed: true,
                published: true,
                reviewer: Some(name.as_str().to_owned()),
            },
        }
    }

    pub fn phase(&self) -> Result<Phase, TransitionError> {
        Ok(match self.state {
            State::Draft => Phase::Draft,
            State::Reviewed(_) => Phase::Reviewed,
            State::Published(_) => Phase::Published,
        })
    }

    pub fn reviewer(&self) -> Option<&str> {
        match &self.state {
            State::Draft => None,
            State::Reviewed(name) | State::Published(name) => Some(name.as_str()),
        }
    }

    pub fn apply(&mut self, event: Event) -> Result<(), TransitionError> {
        let next = match (&self.state, event) {
            (State::Draft, Event::Review(name)) => State::Reviewed(Reviewer::new(&name)?),
            (State::Reviewed(_), Event::Review(_)) => return Err(TransitionError::AlreadyReviewed),
            (State::Published(_), Event::Review(_)) => {
                return Err(TransitionError::AlreadyPublished);
            }
            (State::Draft, Event::Publish) => return Err(TransitionError::NeedsReview),
            (State::Reviewed(name), Event::Publish) => State::Published(name.clone()),
            (State::Published(_), Event::Publish) => return Err(TransitionError::AlreadyPublished),
            (State::Draft | State::Reviewed(_), Event::Reset) => State::Draft,
            (State::Published(_), Event::Reset) => {
                return Err(TransitionError::PublishedCannotReset);
            }
        };
        self.state = next;
        Ok(())
    }
}

impl Default for Session {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fresh_review_and_publish_preserve_the_reviewer() {
        let mut session = Session::new();
        assert_eq!(session.phase(), Ok(Phase::Draft));
        session.apply(Event::Review("Alex".to_owned())).unwrap();
        assert_eq!(session.phase(), Ok(Phase::Reviewed));
        session.apply(Event::Publish).unwrap();
        assert_eq!(session.phase(), Ok(Phase::Published));
        assert_eq!(session.reviewer(), Some("Alex"));
    }

    #[test]
    fn every_phase_event_pair_has_an_explicit_outcome() {
        let phases = [Session::new(), reviewed(), published()];
        let expected = [
            [Ok(()), Err(TransitionError::NeedsReview), Ok(())],
            [Err(TransitionError::AlreadyReviewed), Ok(()), Ok(())],
            [
                Err(TransitionError::AlreadyPublished),
                Err(TransitionError::AlreadyPublished),
                Err(TransitionError::PublishedCannotReset),
            ],
        ];
        for (row, initial) in phases.into_iter().enumerate() {
            for (column, event) in [
                Event::Review("Bea".to_owned()),
                Event::Publish,
                Event::Reset,
            ]
            .into_iter()
            .enumerate()
            {
                let mut session = initial.clone();
                assert_eq!(session.apply(event), expected[row][column]);
                if expected[row][column].is_err() {
                    assert_eq!(session, initial);
                }
            }
        }
    }

    #[test]
    fn reset_removes_review_data_before_a_new_review() {
        let mut session = reviewed();
        session.apply(Event::Reset).unwrap();
        assert_eq!(session, Session::new());
        session.apply(Event::Review("Bea".to_owned())).unwrap();
        assert_eq!(session.reviewer(), Some("Bea"));
    }

    #[test]
    fn invalid_review_is_atomic_and_state_errors_take_precedence() {
        let mut draft = Session::new();
        assert_eq!(
            draft.apply(Event::Review(String::new())),
            Err(TransitionError::InvalidReviewer)
        );
        assert_eq!(draft, Session::new());
        assert_eq!(
            reviewed().apply(Event::Review(String::new())),
            Err(TransitionError::AlreadyReviewed)
        );
        assert_eq!(
            published().apply(Event::Review(String::new())),
            Err(TransitionError::AlreadyPublished)
        );
    }

    #[test]
    fn only_three_of_eight_legacy_shapes_are_valid() {
        let mut valid = 0;
        for reviewed in [false, true] {
            for published in [false, true] {
                for reviewer in [None, Some("Alex".to_owned())] {
                    let input = Legacy {
                        reviewed,
                        published,
                        reviewer,
                    };
                    let expected = if reviewed {
                        input.reviewer.is_some()
                    } else {
                        !published && input.reviewer.is_none()
                    };
                    let parsed = Session::from_legacy(input.clone());
                    assert_eq!(parsed.is_ok(), expected);
                    if let Ok(session) = parsed {
                        valid += 1;
                        assert_eq!(session.snapshot(), input);
                    }
                }
            }
        }
        assert_eq!(valid, 3);
    }

    #[test]
    fn reviewer_policy_and_the_documented_starter_limit_are_visible() {
        for name in ["Alex", "A B", "é", "🦀", &"a".repeat(32)] {
            assert!(Reviewer::new(name).is_ok());
        }
        for name in ["", "-", " Alex", "Alex ", "A\nB", "A\0B", &"a".repeat(33)] {
            assert_eq!(Reviewer::new(name), Err(TransitionError::InvalidReviewer));
        }
        assert!(Reviewer::new(&"é".repeat(17)).is_ok());
        assert_eq!(
            Reviewer::new(&"🦀".repeat(33)),
            Err(TransitionError::InvalidReviewer)
        );
    }

    #[test]
    fn legacy_shape_errors_precede_invalid_reviewer_errors() {
        assert_eq!(
            Session::from_legacy(Legacy {
                reviewed: false,
                published: true,
                reviewer: Some(String::new())
            }),
            Err(TransitionError::InvalidLegacyState)
        );
        assert_eq!(
            Session::from_legacy(Legacy {
                reviewed: true,
                published: false,
                reviewer: Some(String::new())
            }),
            Err(TransitionError::InvalidReviewer)
        );
    }

    #[test]
    fn event_sequences_preserve_invariants_and_rejections_preserve_state() {
        let events = [
            Event::Review("Bea".to_owned()),
            Event::Review(String::new()),
            Event::Publish,
            Event::Reset,
        ];
        for initial in [Session::new(), reviewed(), published()] {
            for first in &events {
                for second in &events {
                    for third in &events {
                        let mut session = initial.clone();
                        for event in [first, second, third] {
                            let before = session.clone();
                            if session.apply(event.clone()).is_err() {
                                assert_eq!(session, before);
                            }
                            let snapshot = session.snapshot();
                            assert!(!snapshot.published || snapshot.reviewed);
                            assert_eq!(snapshot.reviewed, snapshot.reviewer.is_some());
                            assert_eq!(Session::from_legacy(snapshot).unwrap(), session);
                        }
                    }
                }
            }
        }
    }

    fn reviewed() -> Session {
        let mut session = Session::new();
        session.apply(Event::Review("Alex".to_owned())).unwrap();
        session
    }

    fn published() -> Session {
        let mut session = reviewed();
        session.apply(Event::Publish).unwrap();
        session
    }
}

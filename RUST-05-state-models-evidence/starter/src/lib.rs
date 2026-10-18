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
        // TODO CHOICE: use the 32-scalar policy instead of this byte budget.
        if name.is_empty()
            || name.trim() != name
            || name == "-"
            || name.len() > 32
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

// TODO CORE: replace these independently writable fields with a payload enum.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Session {
    pub reviewed: bool,
    pub published: bool,
    pub reviewer: Option<String>,
}

impl Session {
    pub fn new() -> Self {
        Self {
            reviewed: false,
            published: false,
            reviewer: None,
        }
    }

    pub fn from_legacy(input: Legacy) -> Result<Self, TransitionError> {
        validate_legacy(&input)?;
        Ok(Self {
            reviewed: input.reviewed,
            published: input.published,
            reviewer: input.reviewer,
        })
    }

    pub fn snapshot(&self) -> Legacy {
        Legacy {
            reviewed: self.reviewed,
            published: self.published,
            reviewer: self.reviewer.clone(),
        }
    }

    pub fn phase(&self) -> Result<Phase, TransitionError> {
        validate_legacy(&self.snapshot())?;
        Ok(if self.published {
            Phase::Published
        } else if self.reviewed {
            Phase::Reviewed
        } else {
            Phase::Draft
        })
    }

    pub fn reviewer(&self) -> Option<&str> {
        self.reviewer.as_deref()
    }

    pub fn apply(&mut self, event: Event) -> Result<(), TransitionError> {
        let phase = self.phase()?;
        match event {
            Event::Review(name) => {
                if phase == Phase::Published {
                    return Err(TransitionError::AlreadyPublished);
                }
                if phase == Phase::Reviewed {
                    return Err(TransitionError::AlreadyReviewed);
                }
                let reviewer = Reviewer::new(&name)?;
                self.reviewed = true;
                self.reviewer = Some(reviewer.0);
            }
            Event::Publish => match phase {
                Phase::Draft => return Err(TransitionError::NeedsReview),
                Phase::Reviewed => self.published = true,
                Phase::Published => return Err(TransitionError::AlreadyPublished),
            },
            Event::Reset => {
                if phase == Phase::Published {
                    return Err(TransitionError::PublishedCannotReset);
                }
                self.reviewed = false;
                self.reviewer = None;
            }
        }
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
            [Err(TransitionError::AlreadyPublished), Err(TransitionError::AlreadyPublished), Err(TransitionError::PublishedCannotReset)],
        ];
        for (row, initial) in phases.into_iter().enumerate() {
            for (column, event) in [Event::Review("Bea".to_owned()), Event::Publish, Event::Reset].into_iter().enumerate() {
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
        assert_eq!(draft.apply(Event::Review(String::new())), Err(TransitionError::InvalidReviewer));
        assert_eq!(draft, Session::new());
        assert_eq!(reviewed().apply(Event::Review(String::new())), Err(TransitionError::AlreadyReviewed));
        assert_eq!(published().apply(Event::Review(String::new())), Err(TransitionError::AlreadyPublished));
    }

    #[test]
    fn only_three_of_eight_legacy_shapes_are_valid() {
        let mut valid = 0;
        for reviewed in [false, true] {
            for published in [false, true] {
                for reviewer in [None, Some("Alex".to_owned())] {
                    let input = Legacy { reviewed, published, reviewer };
                    let expected = if reviewed { input.reviewer.is_some() } else { !published && input.reviewer.is_none() };
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
        assert!(Reviewer::new(&"é".repeat(17)).is_err());
        assert_eq!(Reviewer::new(&"🦀".repeat(33)), Err(TransitionError::InvalidReviewer));
    }

    #[test]
    fn legacy_shape_errors_precede_invalid_reviewer_errors() {
        assert_eq!(Session::from_legacy(Legacy { reviewed: false, published: true, reviewer: Some(String::new()) }), Err(TransitionError::InvalidLegacyState));
        assert_eq!(Session::from_legacy(Legacy { reviewed: true, published: false, reviewer: Some(String::new()) }), Err(TransitionError::InvalidReviewer));
    }

    #[test]
    fn event_sequences_preserve_invariants_and_rejections_preserve_state() {
        let events = [Event::Review("Bea".to_owned()), Event::Review(String::new()), Event::Publish, Event::Reset];
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

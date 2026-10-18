#![deny(unsafe_op_in_unsafe_fn)]

pub const MAX_BYTES: usize = 8;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BoundaryError {
    TooLarge,
    Rejected,
    Protocol,
}

impl BoundaryError {
    pub fn code(self) -> &'static str {
        match self {
            Self::TooLarge => "too-large",
            Self::Rejected => "rejected",
            Self::Protocol => "protocol",
        }
    }
}

/// The safe baseline, retained as the behavior oracle.
pub fn safe_checksum(bytes: &[u8]) -> Result<u32, BoundaryError> {
    if bytes.len() > MAX_BYTES {
        return Err(BoundaryError::TooLarge);
    }
    Ok(bytes.iter().map(|value| u32::from(*value)).sum())
}

// CORE: start from the safe result. Audit bridge.rs before adding an ABI call.
#[cfg(test)]
mod bridge;

pub fn checksum(bytes: &[u8]) -> Result<u32, BoundaryError> {
    safe_checksum(bytes)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn empty_has_a_zero_sum() {
        assert_eq!(checksum(&[]), Ok(0));
    }

    #[test]
    fn ordinary_bytes_preserve_the_baseline() {
        assert_eq!(checksum(&[7, 17]), Ok(24));
        assert_eq!(checksum(&[7, 17]), safe_checksum(&[7, 17]));
    }

    #[test]
    fn maximum_input_and_values_fit_the_output() {
        assert_eq!(checksum(&[255; MAX_BYTES]), Ok(2040));
    }

    #[test]
    fn one_over_is_rejected_before_any_boundary_call() {
        assert_eq!(checksum(&[0; MAX_BYTES + 1]), Err(BoundaryError::TooLarge));
    }

    #[test]
    fn zeros_between_large_values_still_contribute_to_length() {
        assert_eq!(checksum(&[0, 255, 0, 0, 255, 0, 0, 255]), Ok(765));
    }

    #[test]
    fn caller_storage_is_not_modified_or_retained() {
        let mut bytes = vec![7, 17];
        assert_eq!(checksum(&bytes), Ok(24));
        assert_eq!(bytes, vec![7, 17]);
        bytes.clear();
        bytes.extend([1, 2, 3]);
        assert_eq!(checksum(&bytes), Ok(6));
    }
}

use state_model_lab::Phase;

fn label(phase: Phase) -> &'static str {
    match phase {
        Phase::Draft => "draft",
        Phase::Reviewed => "reviewed",
        Phase::Published => "published",
    }
}

fn main() {
    println!("{}", label(Phase::Published));
}

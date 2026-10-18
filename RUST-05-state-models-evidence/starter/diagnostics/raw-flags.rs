use state_model_lab::Session;

fn main() {
    let invalid = Session { reviewed: false, published: true, reviewer: None };
    println!("error={}", invalid.phase().unwrap_err().code());
}

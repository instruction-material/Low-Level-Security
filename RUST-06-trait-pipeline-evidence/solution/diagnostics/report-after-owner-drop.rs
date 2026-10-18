use trait_pipeline_lab::{MemoryRows, audit};

fn main() {
    let source = MemoryRows::new(vec!["alpha=7".to_owned()]);
    let report = audit(&source).expect("valid row");
    drop(source);
    println!("{}", report.labels[0]);
}

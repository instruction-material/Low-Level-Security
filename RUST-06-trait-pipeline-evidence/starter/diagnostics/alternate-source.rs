use trait_pipeline_lab::{RowSource, audit};

struct Alternate;

impl RowSource for Alternate {
    fn rows(&self) -> impl Iterator<Item = &str> {
        ["beta=5", "alpha=7"].into_iter()
    }
}

fn main() {
    let source = Alternate;
    let report = audit(&source).expect("valid rows");
    println!("count={} total={}", report.labels.len(), report.total);
}

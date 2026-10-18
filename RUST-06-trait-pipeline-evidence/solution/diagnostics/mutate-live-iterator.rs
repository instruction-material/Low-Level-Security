use trait_pipeline_lab::{MemoryRows, RowSource};

fn main() {
    let mut source = MemoryRows::new(vec!["alpha=7".to_owned()]);
    let mut iterator = source.rows();
    source.push("beta=17".to_owned());
    println!("{}", iterator.next().expect("one row"));
}

use trait_pipeline_lab::{MemoryRows, RowSource};

fn main() {
    let mut source = MemoryRows::new(vec!["alpha=7".to_owned()]);
    {
        let mut iterator = source.rows();
        assert_eq!(iterator.next(), Some("alpha=7"));
    }
    source.push("beta=17".to_owned());
    println!("rows={}", source.rows().count());
}

he-check-nf:
- nextflow pipeline that checks whether whole-slide images are h&e, using each slide's thumbnail colours
- one job per slide, then one job that combines the results
- input: csv samplesheet with columns `name`, `Address` (slide path), optional `stain_label`
- output: `he_check_results.tsv`, `he_check_summary.txt`, `thumbnails.html`, `thumbs/`
- options: `--samplesheet`, `--outdir` (default `results`), `--limit` (first n slides, default all)
```
nextflow run main.nf --samplesheet samplesheet.csv --limit 5
```

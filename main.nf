#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

params.samplesheet = null
params.outdir      = 'results'
params.limit       = -1

process HE_CHECK {
    tag "$name"

    input:
    tuple val(name), path(slide)

    output:
    path "${name}.tsv", emit: tsv
    path "${name}.jpg", emit: jpg, optional: true

    script:
    """
    he_check.py "${slide}" . "${name}"
    """
}

process HE_SUMMARY {
    publishDir params.outdir, mode: 'copy'

    input:
    path tsvs, stageAs: 'tsv/*'
    path jpgs, stageAs: 'jpg/*'
    path samplesheet

    output:
    path 'he_check_results.tsv'
    path 'he_check_summary.txt'
    path 'thumbnails.html'
    path 'thumbs'

    script:
    """
    he_summary.py "${samplesheet}" tsv jpg .
    """
}

workflow {
    if (!params.samplesheet) {
        error "Please give --samplesheet"
    }
    rows = Channel.fromPath(params.samplesheet, checkIfExists: true)
        .splitCsv(header: true)
        .map { row -> tuple(row.name, file(row.Address)) }
    slides = params.limit > 0 ? rows.take(params.limit as int) : rows

    HE_CHECK(slides)
    HE_SUMMARY(
        HE_CHECK.out.tsv.collect(),
        HE_CHECK.out.jpg.collect().ifEmpty([]),
        file(params.samplesheet)
    )
}

# [MUST BE USED] Main Claude Configuration
## About 
    --- 
    Project Type: Bioinformatics Analysis - Genomic Segment Annotation
    Session: Continuation
    Author: Samuel Ahuno (ekwame001@gmail.com) 
    ---

## Goal is to annotate genomic segments

** inputs is a tab delim file which can look like either of these 
- Bed3
- Bed6
- Bed12
- reference to all bed files are here https://en.wikipedia.org/wiki/BED_(file_format)

** Always Ask user which genome build to work with 

** TODO 
1. refactor this @/data1/greenbab/users/ahunos/apps/annOmics/annHMMSegments.R code to annotate. 
    - Read all columns of the table. 
    - maintain Metadata of a original table unless user asks you to drop. 
    - 

## General Instructions & Projects
- Do not use the following as variable names to avoid clashes with system variable names; [conditions, counts, results, sum, median, mean]
- In Genomic pipelines, Do not hardcode items like contig/chromosome names and sizes to ensure things don't break when we change codebase. Get contig names and sizes from the user supplied genome sizes file in the workflow.

### Visualization & Figures 
- Create 3 types of figures; png,pdf,svg for analysis place them under `png,pdf,svg` sub-directories.
- Figures should be of largest size possible
- Font type should always be Arial if font is available and of at least size 10. Headers should be Bold.
- Figure Axis should be legible, at least size 
- For multi-panel figures, the y-axis must be the fixed in order to standardize the comparison between groups ie. 3 multipanel boxplots comparing variables among groups should have fixed y-axis.
- prompt user to included appropriate statistical tests in figures. for example t-test with p-values when comparing groups

## Statistical analysis
- Defaults 
    - p value = 0.05
    - adjusted p value = 0.05
    - multiple test hypothesis test = bonferroni

## test 
```
Rscript /data1/greenbab/users/ahunos/apps/annOmics/scripts/annotate_genomic_segments.R \
-i /data1/greenbab/projects/triplicates_epigenetics_diyva/RNA/rerun_RNASeq_11032025/REP_locusSpecDE/outputs/repeats_DNAme_RNA/all_results_repeats_promoter.bed -g mm10 -o mouse_results -n treatment_group --formats png,pdf

```
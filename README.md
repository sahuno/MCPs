# MCPs - Model Context Protocol Servers

## annOmics - Genomic Segment Annotation MCP Server

A powerful MCP (Model Context Protocol) server for genomic segment annotation, built on top of a flexible R tool using the annotatr package. Provides AI-powered genomic analysis through natural language interfaces with Claude and other AI assistants.

## Features

- **Universal BED format support**: Automatically detects and handles BED3, BED6, and BED12 formats
- **Multiple genome builds**: Supports human (hg19, hg38), mouse (mm9, mm10), fly (dm3, dm6), and rat (rn4, rn5, rn6)
- **Comprehensive annotations**: CpG islands, shores, shelves, and genic features (promoters, exons, introns, etc.)
- **Batch processing**: Handle multiple files via directory scanning, file lists, or wildcards
- **Comparative analysis**: Cross-sample comparison plots and combined statistics
- **High-quality visualization**: Publication-ready plots in PNG, PDF, and SVG formats
- **Metadata preservation**: Maintains all original columns from input BED files
- **Robust error handling**: Graceful handling of various BED file formats and edge cases

## Usage

### Single File Processing
```bash
Rscript scripts/annotate_genomic_segments.R -i input.bed -g hg38 -o results
```

### Multiple Files Processing

#### Process directory of BED files
```bash
# Process all .bed files in a directory
Rscript scripts/annotate_genomic_segments.R \
  -i /path/to/bed/files/ \
  --pattern "*.bed" \
  -g mm10 \
  -o batch_results \
  --combine

# Process files with specific pattern
Rscript scripts/annotate_genomic_segments.R \
  -i /data/dmr_results/ \
  --pattern "*_segments.bed" \
  -g mm10 \
  -o dmr_annotations \
  --combine
```

#### Process comma-separated file list
```bash
# Specify exact files to process
Rscript scripts/annotate_genomic_segments.R \
  -i "control.bed,treatment1.bed,treatment2.bed" \
  -g hg38 \
  -o comparison_study \
  --combine

# Process files from different directories
Rscript scripts/annotate_genomic_segments.R \
  -i "/data/ctrl/regions.bed,/data/exp1/regions.bed,/data/exp2/regions.bed" \
  -g hg38 \
  -o multi_condition \
  --combine
```

#### Process with shell wildcards
```bash
# Use shell expansion for pattern matching
Rscript scripts/annotate_genomic_segments.R \
  -i "$(echo /path/to/files/*.bed | tr ' ' ',')" \
  -g mm10 \
  -o wildcard_results \
  --combine
```

### Use Case Examples

#### Epigenetic Analysis Pipeline
```bash
# Process DMR segmentation results
Rscript scripts/annotate_genomic_segments.R \
  -i /project/dmr_analysis/segmentation_results/ \
  --pattern "*_segmentation.bed" \
  -g mm10 \
  -o dmr_annotations \
  -n "DMR_study" \
  --combine \
  --formats png,pdf,svg
```

#### Multi-sample ChIP-seq Peak Analysis
```bash
# Annotate peak files from multiple samples
Rscript scripts/annotate_genomic_segments.R \
  -i "sample1_peaks.bed,sample2_peaks.bed,sample3_peaks.bed" \
  -g hg38 \
  -o chipseq_annotations \
  -n "ChIP_H3K4me3" \
  --combine \
  --formats pdf
```

#### ATAC-seq Accessibility Regions
```bash
# Process accessibility regions across conditions
Rscript scripts/annotate_genomic_segments.R \
  -i /atacseq/peak_calls/ \
  --pattern "*_accessible_regions.bed" \
  -g hg19 \
  -o accessibility_analysis \
  --combine
```

### Advanced Configuration
```bash
# Full feature example with custom settings
Rscript scripts/annotate_genomic_segments.R \
  -i /data/genomic_regions/ \
  --pattern "*.bed" \
  -g mm10 \
  -o comprehensive_analysis \
  -n "MyProject" \
  --combine \
  --formats png,pdf,svg \
  --cpg \
  --genic \
  --plots
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --input` | Input BED file(s), comma-separated list, or directory | - |
| `-g, --genome` | Genome build (required) | - |
| `-o, --output` | Output directory | annotation_results |
| `-n, --name` | Sample/condition name | sample |
| `--pattern` | File pattern when input is directory | *.bed |
| `--batch` | Enable batch mode for multiple files | FALSE |
| `--combine` | Create combined analysis across files | FALSE |
| `--cpg` | Include CpG annotations | TRUE |
| `--genic` | Include genic annotations | TRUE |
| `--plots` | Generate visualization plots | TRUE |
| `--formats` | Plot formats (comma-separated) | png,pdf,svg |

### Supported Genome Builds

- `hg19` - Human (GRCh37)
- `hg38` - Human (GRCh38)
- `mm9` - Mouse (NCBI37)
- `mm10` - Mouse (GRCh38)
- `dm3` - Drosophila (BDGP Release 5)
- `dm6` - Drosophila (BDGP Release 6)
- `rn4` - Rat (RGSC 3.4)
- `rn5` - Rat (RGSC 5.0)
- `rn6` - Rat (RGSC 6.0)

## Output Files

### Single File Processing
- `{name}_annotated.tsv` - Full annotated results with all metadata preserved
- `{name}_summary.tsv` - Summary statistics by annotation type
- `{name}_annotations.{format}` - Visualization plots in specified formats

### Multiple Files Processing
- `{sample_name}/` - Individual sample directories containing:
  - `{sample_name}_annotated.tsv` - Sample-specific annotated results
  - `{sample_name}_summary.tsv` - Sample-specific summary statistics
  - `{sample_name}_annotations.{format}` - Sample-specific plots
- `combined_annotations.tsv` - Combined data from all samples (with `--combine`)
- `combined_summary_stats.tsv` - Summary statistics across all samples
- `combined_comparison.{format}` - Comparison plots across samples

## BED File Formats

### BED3 (minimal)
```
chr1    1000    2000
chr1    3000    4000
```

### BED6 (with name, score, strand)
```
chr1    1000    2000    region1    100    +
chr1    3000    4000    region2    200    -
```

### BED12 (full format with blocks)
```
chr1    1000    4000    item1    100    +    1200    3800    0    2    400,400    0,2600
```

## Workflow Recommendations

### For Large-Scale Studies
1. **Organize by project**: Create separate directories for different experiments
2. **Use descriptive naming**: Include condition, replicate, and analysis type in filenames
3. **Enable combined analysis**: Always use `--combine` for multi-sample studies
4. **Standard formats**: Stick to consistent BED formats across your pipeline

### For Publication Figures
1. **Use PDF format**: Best for vector graphics and manuscript submission
2. **Large dimensions**: Plots are sized for clarity (14x10 inches)
3. **Arial fonts**: Following publication standards
4. **Combined plots**: Use comparison plots for multi-condition studies

### Performance Tips
1. **Batch processing**: Process multiple files in one run to reuse annotation databases
2. **Output organization**: Use project-specific output directories
3. **Format selection**: Choose only needed plot formats to save time

## Output Structure & Interpretation

### Individual Sample Results
```
sample_name/
├── sample_name_annotated.tsv    # Full annotation details
├── sample_name_summary.tsv      # Annotation type counts
└── pdf/sample_name_annotations.pdf  # Visualization
```

### Combined Analysis Results  
```
output_directory/
├── combined_annotations.tsv     # All samples merged
├── combined_summary_stats.tsv   # Cross-sample statistics
└── pdf/combined_comparison.pdf  # Comparative plots
```

### Key Output Columns
- **seqnames, start, end**: Genomic coordinates
- **width**: Region size in base pairs
- **annot.type**: Annotation category (e.g., mm10_cpg_islands)
- **annot.id**: Specific annotation identifier
- **sample**: Sample identifier (multi-file analysis)
- Original BED columns are preserved with metadata

## Troubleshooting

### Common Issues
1. **"Cannot determine seqnames"**: BED file has non-standard format - script handles this automatically
2. **Empty plots**: No overlaps found - check genome build matches your data
3. **Memory issues**: Process files individually instead of batch mode
4. **Missing annotations**: Verify genome build is correct (hg19 vs hg38, mm9 vs mm10)

### Performance Optimization
- Use SSD storage for annotation databases
- Increase R memory limit for large datasets: `R --max-mem-size=8G`
- Process subsets for very large studies (>100 files)

## Dependencies

- R packages: optparse, tidyverse, annotatr, GenomicRanges, data.table, ggplot2
- System: R ≥ 4.0, Cairo graphics library (for PDF rendering)

## Installation

```bash
# Install required R packages
Rscript -e "install.packages(c('optparse', 'tidyverse', 'data.table', 'ggplot2'))"
Rscript -e "if (!require('BiocManager', quietly = TRUE)) install.packages('BiocManager')"
Rscript -e "BiocManager::install(c('annotatr', 'GenomicRanges'))"

# Verify Cairo support for high-quality PDFs
Rscript -e "capabilities('cairo')"
```

## Citation

If you use annOmics in your research, please cite:
- annotatr package: Cavalcante RG, Sartor MA (2017). annotatr: genomic regions in context. Bioinformatics.
- This tool: [Your publication or GitHub repository]

---

*Part of the MCPs (Model Context Protocol Servers) collection for AI-powered scientific computing.*

# annOmics MCP Server Usage Guide

## Overview

The annOmics MCP (Model Context Protocol) server provides AI-powered genomic annotation tools that integrate seamlessly with Claude and other AI assistants. This server transforms complex genomic analysis tasks into natural language interactions.

## Installation

### Prerequisites
- Python ≥ 3.11
- R ≥ 4.0 with Bioconductor packages
- uv package manager (recommended)

### Install with uv (Recommended)
```bash
# Clone the repository
git clone <repository-url>
cd annOmics

# Install with uv
uv sync

# Install in development mode
uv sync --dev
```

### Install with pip
```bash
pip install annomics-mcp
```

### R Dependencies
Ensure R is installed with required packages:
```r
# Install Bioconductor
if (!require("BiocManager", quietly = TRUE))
    install.packages("BiocManager")

# Install required packages
BiocManager::install(c("annotatr", "GenomicRanges"))
install.packages(c("tidyverse", "data.table", "ggplot2", "optparse"))
```

## Starting the Server

### Local Development
```bash
# Using uv
uv run annomics-mcp

# Or directly
uv run python -m annomics_mcp.server
```

### Production
```bash
# Install globally
uv build
pip install dist/annomics_mcp-*.whl

# Run server
annomics-mcp
```

## Available MCP Tools

### 1. `annotate_genomic_regions`
**Purpose**: Annotate BED files with genomic features

**Parameters**:
- `input_files` (required): Single file, comma-separated list, or array
- `genome_build` (required): Target genome (hg19, hg38, mm9, mm10, dm3, dm6, rn4, rn5, rn6)
- `output_directory` (required): Output directory path
- `sample_name` (optional): Sample identifier
- `include_cpg` (optional): Include CpG annotations (default: true)
- `include_genic` (optional): Include genic annotations (default: true)
- `plot_formats` (optional): Output formats ["png", "pdf", "svg"] (default: ["png", "pdf"])
- `combine_analysis` (optional): Create combined analysis (default: false)
- `timeout` (optional): Execution timeout in seconds (default: 300)

### 2. `list_supported_genomes`
**Purpose**: List all supported genome builds

**Parameters**: None

### 3. `validate_bed_format`
**Purpose**: Validate BED file format and structure

**Parameters**:
- `file_path` (required): Path to BED file

### 4. `get_annotation_summary`
**Purpose**: Get summary of annotation results

**Parameters**:
- `results_directory` (required): Path to results directory
- `sample_name` (optional): Specific sample name

### 5. `create_comparison_plot`
**Purpose**: Create comparison plots (placeholder)

**Parameters**:
- `results_directories` (required): List of result directories
- `output_path` (required): Output plot path
- `plot_format` (optional): Format (default: "pdf")

## Usage Examples

### Natural Language with Claude

Once the MCP server is running, you can interact with it through Claude using natural language:

#### Basic Annotation
```
"Annotate these ChIP-seq peaks with the mouse mm10 genome"
- Input: /path/to/peaks.bed
- Output: Automatically annotated with CpG and genic features
```

#### Batch Processing
```
"Process all BED files in the /data/samples/ directory using hg38 genome and create comparison plots"
- Automatically detects all .bed files
- Processes each sample individually  
- Creates combined analysis
```

#### Validation
```
"Check if this BED file is properly formatted"
- Validates file structure
- Reports format (BED3/6/12)
- Shows preview of content
```

#### Results Summary
```
"Summarize the annotation results in /results/chipseq_analysis/"
- Lists all generated files
- Shows summary statistics
- Displays sample data preview
```

### Direct MCP Tool Calls

#### Single File Annotation
```json
{
  "tool": "annotate_genomic_regions",
  "arguments": {
    "input_files": "/data/sample1.bed",
    "genome_build": "hg38",
    "output_directory": "/results/sample1",
    "sample_name": "treatment_condition",
    "plot_formats": ["pdf", "png"]
  }
}
```

#### Multiple File Processing
```json
{
  "tool": "annotate_genomic_regions", 
  "arguments": {
    "input_files": ["/data/ctrl.bed", "/data/treat1.bed", "/data/treat2.bed"],
    "genome_build": "mm10",
    "output_directory": "/results/comparison_study",
    "combine_analysis": true,
    "plot_formats": ["pdf"]
  }
}
```

#### Directory Processing
```json
{
  "tool": "annotate_genomic_regions",
  "arguments": {
    "input_files": "/data/bed_files/",
    "genome_build": "hg19",
    "output_directory": "/results/batch_analysis",
    "combine_analysis": true
  }
}
```

## Integration with Claude

### Example Conversations

#### Research Workflow
```
User: "I have ChIP-seq peaks from a transcription factor study in mouse. 
      Can you annotate them and tell me about their genomic distribution?"

Claude: I'll help you annotate your ChIP-seq peaks and analyze their genomic distribution. 
        Let me start by annotating them with the mouse genome.

[Uses annotate_genomic_regions tool]

The annotation is complete! Your ChIP-seq peaks show:
- 45% in promoter regions (within 2kb of TSS)
- 23% in gene bodies (exons/introns)  
- 18% in intergenic regions
- 14% overlapping with CpG islands

This distribution suggests your transcription factor preferentially binds 
near transcriptionally active regions...
```

#### Quality Control
```
User: "Before I run my analysis, can you check if my BED files are properly formatted?"

Claude: I'll validate your BED files to ensure they're properly formatted.

[Uses validate_bed_format tool]

Your BED file is properly formatted as BED6 format with:
- Chromosome coordinates (chr1, chr2, etc.)
- Proper start < end coordinates
- Valid strand information
- All required fields present

The file is ready for genomic annotation!
```

### Best Practices for Claude Integration

1. **Be Specific**: Mention genome build, file types, and analysis goals
2. **Provide Context**: Explain the biological context (ChIP-seq, ATAC-seq, etc.)
3. **Ask for Interpretation**: Request biological interpretation of results
4. **Iterative Analysis**: Build on results with follow-up questions

## Output Structure

### Single File Analysis
```
output_directory/
├── sample_name_annotated.tsv    # Full annotations
├── sample_name_summary.tsv      # Summary statistics  
└── pdf/
    └── sample_name_annotations.pdf  # Visualization
```

### Multiple File Analysis
```
output_directory/
├── sample1/
│   ├── sample1_annotated.tsv
│   ├── sample1_summary.tsv
│   └── pdf/sample1_annotations.pdf
├── sample2/
│   └── ...
├── combined_annotations.tsv     # Merged data
├── combined_summary_stats.tsv   # Cross-sample stats
└── pdf/combined_comparison.pdf  # Comparison plot
```

### Key Output Columns

**Annotation Files**:
- `seqnames`, `start`, `end`: Genomic coordinates
- `width`: Region size in base pairs
- `annot.type`: Annotation category (e.g., mm10_cpg_islands)
- `annot.id`: Specific annotation identifier
- Original BED columns preserved

**Summary Files**:
- `annot.type`: Annotation category
- `count`: Number of regions
- `mean_width`: Average region size
- `median_width`: Median region size

## Troubleshooting

### Common Issues

#### R Environment Problems
```
Error: R script runner not initialized
```
**Solution**: Ensure R and required packages are installed
```bash
# Check R installation
which R
R --version

# Test package installation
Rscript -e "library(annotatr); library(GenomicRanges)"
```

#### File Permission Issues
```
Error: Cannot write to output directory
```
**Solution**: Check directory permissions
```bash
# Create output directory with proper permissions
mkdir -p /path/to/output
chmod 755 /path/to/output
```

#### Memory Issues
```
Error: R script execution timed out
```
**Solution**: Increase timeout or process smaller batches
```json
{
  "timeout": 600,  // Increase to 10 minutes
  "combine_analysis": false  // Disable for large datasets
}
```

#### Invalid Genome Build
```
Error: Unsupported genome build 'hg37'
```
**Solution**: Use supported genome names
```
Use: hg19, hg38, mm9, mm10, dm3, dm6, rn4, rn5, rn6
Not: hg37, GRCh38, etc.
```

### Debugging

#### Enable Verbose Logging
```bash
export PYTHONPATH=/path/to/annomics
export LOG_LEVEL=DEBUG
uv run annomics-mcp
```

#### Check R Script Directly
```bash
# Test R script manually
Rscript scripts/annotate_genomic_segments.R \
  -i tests/sample.bed \
  -g mm10 \
  -o test_output \
  --formats pdf
```

## Performance Optimization

### For Large Datasets
1. **Process in batches**: Avoid combining >50 files at once
2. **Use specific formats**: Only generate needed plot formats
3. **Disable plots**: Set `plot_formats: []` for data-only analysis
4. **Increase memory**: Set R memory limits if needed

### For Production Use
1. **Use SSD storage**: For annotation databases and temp files
2. **Enable caching**: Results are cached automatically
3. **Monitor resources**: Watch memory and CPU usage
4. **Set timeouts**: Appropriate for your dataset sizes

## Advanced Usage

### Custom R Scripts
To use custom R scripts, modify the server initialization:
```python
# In server.py
script_path = Path("/custom/path/to/script.R")
r_runner = RScriptRunner(script_path)
```

### Integration with Workflows
The MCP server can be integrated with:
- **Nextflow**: Call via Python subprocess
- **Snakemake**: Use as external tool
- **Galaxy**: Create tool wrapper
- **Jupyter**: Use in notebooks with MCP client

### API Extensions
Add custom tools by extending the server:
```python
@server.call_tool()
async def handle_custom_tool(name: str, arguments: Dict[str, Any]):
    if name == "my_custom_tool":
        # Custom implementation
        return [TextContent(type="text", text="Custom result")]
```

## Support and Contributing

### Getting Help
- **Issues**: Report bugs on GitHub
- **Discussions**: Ask questions in discussions
- **Documentation**: Check README and examples

### Contributing
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

### Development Setup
```bash
# Clone and setup
git clone <repo>
cd annOmics
uv sync --dev

# Run tests
uv run pytest

# Format code  
uv run ruff format

# Type check
uv run mypy src/
```
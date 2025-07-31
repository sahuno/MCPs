# annOmics MCP Server

A Model Context Protocol (MCP) server for genomic segment annotation using annotatr. This server provides AI-powered tools for annotating BED files with CpG and genic features across multiple genome builds.

## Features

- 🧬 **Universal BED format support**: Automatically handles BED3, BED6, and BED12 formats
- 🔬 **Multiple genome builds**: Supports human, mouse, fly, and rat genomes
- 🤖 **AI Integration**: Seamless integration with Claude and other AI tools
- 📊 **Batch processing**: Handle multiple files efficiently
- 📈 **Comprehensive annotations**: CpG islands, shores, shelves, and genic features
- 🎨 **Publication-ready plots**: High-quality visualizations in multiple formats

## Installation

```bash
# Install with uv (recommended)
uv add annomics-mcp

# Or install with pip
pip install annomics-mcp
```

## Quick Start

```bash
# Start the MCP server
annomics-mcp

# Or run directly
python -m annomics_mcp.server
```

## MCP Tools

- `annotate_genomic_regions`: Annotate BED files with genomic features
- `validate_bed_format`: Validate BED file format and structure
- `list_supported_genomes`: Get available genome builds
- `get_annotation_summary`: Summarize annotation results
- `create_comparison_plot`: Generate comparative visualizations

## Usage with Claude

Once the server is running, you can interact with it through Claude:

- "Annotate these ChIP-seq peaks with mm10 genome"
- "Validate this BED file format"
- "What genome builds are supported?"
- "Create a comparison plot for these samples"

## Requirements

- Python ≥ 3.11
- R ≥ 4.0 with required Bioconductor packages
- System dependencies for plotting (Cairo)

## Development

```bash
# Clone repository
git clone <repository-url>
cd annOmics

# Install with development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run ruff format

# Type checking
uv run mypy src/
```

## License

MIT License - see LICENSE file for details.
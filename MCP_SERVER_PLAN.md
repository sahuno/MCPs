# MCP Server Implementation Plan for annOmics

## Overview
Transform the annOmics genomic annotation tool into a Model Context Protocol (MCP) server to enable seamless integration with Claude and other AI tools for genomic analysis workflows.

## Current State Analysis

### Existing Components
- **Core R Script**: `scripts/annotate_genomic_segments.R`
- **Functionality**: Single/batch BED file annotation with multiple genome builds
- **Output**: TSV files, publication-quality plots, summary statistics
- **Features**: Multi-format support (BED3/6/12), comparative analysis, error handling

### Strengths to Leverage
- Robust command-line interface with optparse
- Comprehensive error handling and validation
- Flexible input/output handling
- Publication-ready visualization
- Multi-file batch processing

## MCP Server Architecture

### 1. Server Structure
```
annomics-mcp-server/
├── src/
│   ├── server.py              # Main MCP server implementation
│   ├── tools/
│   │   ├── annotate.py        # Core annotation tool wrapper
│   │   ├── validate.py        # Input validation utilities
│   │   └── visualize.py       # Plot generation utilities
│   ├── schemas/
│   │   ├── bed_formats.py     # BED file format definitions
│   │   └── genome_builds.py   # Supported genome configurations
│   └── utils/
│       ├── file_handler.py    # File I/O operations
│       └── r_interface.py     # R script execution wrapper
├── scripts/
│   └── annotate_genomic_segments.R  # Existing R script (unchanged)
├── config/
│   ├── genome_configs.json    # Genome build configurations
│   └── server_config.json     # MCP server settings
├── tests/
│   ├── test_server.py         # Server functionality tests
│   └── sample_data/           # Test BED files
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Package configuration
└── README.md                  # MCP server documentation
```

### 2. MCP Tools to Implement

#### Tool 1: `annotate_genomic_regions`
**Purpose**: Annotate single or multiple BED files with genomic features
**Parameters**:
- `input_files`: List of BED file paths or directory path
- `genome_build`: Target genome (hg19, hg38, mm9, mm10, etc.)
- `output_directory`: Where to save results
- `sample_name`: Optional sample identifier
- `include_cpg`: Boolean for CpG annotations
- `include_genic`: Boolean for genic annotations
- `plot_formats`: List of output formats (png, pdf, svg)
- `combine_analysis`: Boolean for cross-sample comparison

#### Tool 2: `validate_bed_format`
**Purpose**: Validate BED file format and detect issues
**Parameters**:
- `file_path`: Path to BED file
- `expected_format`: Optional expected format (bed3, bed6, bed12)

#### Tool 3: `list_supported_genomes`
**Purpose**: Return available genome builds and their features
**Parameters**: None

#### Tool 4: `get_annotation_summary`
**Purpose**: Get quick summary of annotation results
**Parameters**:
- `results_directory`: Path to annotation results
- `sample_name`: Specific sample or all samples

#### Tool 5: `create_comparison_plot`
**Purpose**: Generate comparison plots from existing results
**Parameters**:
- `results_directories`: List of result directories to compare
- `plot_type`: Type of comparison (annotation_counts, region_sizes, etc.)
- `output_path`: Where to save the plot

### 3. Implementation Phases

#### Phase 1: Core MCP Server Setup (Week 1)
- [ ] Set up Python MCP server framework
- [ ] Implement basic server structure and configuration
- [ ] Create R script wrapper with subprocess management
- [ ] Implement `annotate_genomic_regions` tool
- [ ] Add basic input validation and error handling
- [ ] Create unit tests for core functionality

#### Phase 2: Enhanced Tools & Validation (Week 2)
- [ ] Implement `validate_bed_format` tool
- [ ] Add `list_supported_genomes` tool
- [ ] Enhance error handling and user feedback
- [ ] Add comprehensive input sanitization
- [ ] Implement file format detection and conversion
- [ ] Add progress tracking for long-running operations

#### Phase 3: Advanced Features (Week 3)
- [ ] Implement `get_annotation_summary` tool
- [ ] Add `create_comparison_plot` tool
- [ ] Implement batch processing optimizations
- [ ] Add result caching mechanisms
- [ ] Create configuration management system
- [ ] Add logging and monitoring capabilities

#### Phase 4: Integration & Polish (Week 4)
- [ ] Claude integration testing
- [ ] Performance optimization
- [ ] Documentation and examples
- [ ] Error message improvements
- [ ] Security hardening
- [ ] Production deployment preparation

## Technical Implementation Details

### 1. MCP Server Core (`src/server.py`)
```python
from mcp import MCPServer, Tool
from typing import List, Dict, Any, Optional
import asyncio
import subprocess
import json
from pathlib import Path

class AnnOmicsServer:
    def __init__(self):
        self.server = MCPServer("annomics")
        self.r_script_path = Path(__file__).parent.parent / "scripts" / "annotate_genomic_segments.R"
        self.register_tools()
    
    def register_tools(self):
        """Register all available tools"""
        self.server.add_tool(self.annotate_genomic_regions)
        self.server.add_tool(self.validate_bed_format)
        # ... other tools
    
    async def annotate_genomic_regions(self, **kwargs) -> Dict[str, Any]:
        """Main annotation tool implementation"""
        # Input validation
        # R script execution
        # Result processing
        # Return structured response
```

### 2. R Script Interface (`src/utils/r_interface.py`)
```python
import subprocess
import json
from typing import List, Dict, Any
from pathlib import Path

class RScriptRunner:
    def __init__(self, script_path: Path):
        self.script_path = script_path
    
    async def run_annotation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute R script with parameters and return results"""
        # Build command line arguments
        # Execute with proper error handling
        # Parse output and return structured results
        
    def validate_r_environment(self) -> bool:
        """Check if R and required packages are available"""
        # Test R installation
        # Verify package availability
        # Return status
```

### 3. Input Validation (`src/tools/validate.py`)
```python
from typing import List, Optional, Tuple
from pathlib import Path
import pandas as pd

class BEDValidator:
    SUPPORTED_GENOMES = ["hg19", "hg38", "mm9", "mm10", "dm3", "dm6", "rn4", "rn5", "rn6"]
    
    def validate_bed_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """Validate BED file format and content"""
        # Check file existence
        # Detect BED format (3, 6, 12)
        # Validate coordinates
        # Check chromosome naming
        # Return (is_valid, format, error_message)
    
    def validate_genome_build(self, genome: str) -> bool:
        """Check if genome build is supported"""
        return genome in self.SUPPORTED_GENOMES
```

## Integration Points

### 1. Claude Integration
- **Natural language queries**: "Annotate these ChIP-seq peaks with mm10 genome"
- **File handling**: Automatic detection of BED files in conversations
- **Result interpretation**: AI-assisted analysis of annotation results
- **Workflow suggestions**: Recommend analysis parameters based on data type

### 2. File System Integration
- **Auto-discovery**: Scan directories for BED files
- **Format detection**: Automatically identify BED3/6/12 formats
- **Batch processing**: Handle multiple files seamlessly
- **Result organization**: Structured output directories

### 3. Error Handling & User Experience
- **Detailed error messages**: Clear explanations of issues
- **Suggestions**: Automatic fixes for common problems
- **Progress tracking**: Real-time updates for long operations
- **Result validation**: Verify output quality

## Configuration Management

### 1. Genome Configurations (`config/genome_configs.json`)
```json
{
  "genomes": {
    "hg38": {
      "description": "Human (GRCh38)",
      "annotations": ["cpg", "genic", "enhancers"],
      "chromosome_style": "chr1"
    },
    "mm10": {
      "description": "Mouse (GRCh38)",
      "annotations": ["cpg", "genic"],
      "chromosome_style": "chr1"
    }
  }
}
```

### 2. Server Configuration (`config/server_config.json`)
```json
{
  "server": {
    "name": "annomics",
    "version": "1.0.0",
    "max_file_size": "100MB",
    "timeout": 300,
    "cache_results": true
  },
  "r_environment": {
    "script_path": "./scripts/annotate_genomic_segments.R",
    "memory_limit": "8G",
    "required_packages": ["annotatr", "GenomicRanges", "tidyverse"]
  }
}
```

## Testing Strategy

### 1. Unit Tests
- Individual tool functionality
- Input validation logic
- R script interface
- Error handling scenarios

### 2. Integration Tests
- End-to-end annotation workflows
- Multi-file batch processing
- Claude integration scenarios
- Performance benchmarks

### 3. Test Data
- Sample BED files (BED3, BED6, BED12)
- Various genome builds
- Edge cases (malformed files, large datasets)
- Expected output validation

## Deployment Considerations

### 1. Dependencies
- **Python**: MCP framework, asyncio, subprocess management
- **R Environment**: R ≥ 4.0, Bioconductor packages
- **System**: Sufficient memory for large genomic datasets
- **Storage**: Space for annotation databases and results

### 2. Security
- **Input sanitization**: Prevent path traversal attacks
- **Resource limits**: Memory and CPU usage controls
- **File permissions**: Secure temporary file handling
- **Process isolation**: Sandboxed R script execution

### 3. Performance
- **Caching**: Store frequently used annotation databases
- **Parallel processing**: Multiple file handling
- **Memory management**: Efficient large file processing
- **Progress tracking**: User feedback for long operations

## Success Metrics

### 1. Functionality
- [ ] All BED formats supported (3, 6, 12)
- [ ] All genome builds working (9 total)
- [ ] Batch processing functional
- [ ] Error handling comprehensive
- [ ] Claude integration smooth

### 2. Performance
- [ ] Single file processing < 2 minutes
- [ ] Batch processing scales linearly
- [ ] Memory usage reasonable (< 4GB for typical files)
- [ ] Error recovery graceful

### 3. User Experience
- [ ] Clear error messages
- [ ] Intuitive tool parameters
- [ ] Helpful documentation
- [ ] Reliable operation

## Future Enhancements

### 1. Advanced Features
- **Custom annotations**: User-provided annotation tracks
- **Statistical analysis**: Built-in statistical tests
- **Interactive plots**: Web-based visualization
- **Database integration**: Direct access to genomic databases

### 2. Performance Improvements
- **Streaming processing**: Handle very large files
- **Distributed computing**: Multi-node processing
- **GPU acceleration**: Faster overlap calculations
- **Smart caching**: Intelligent result reuse

### 3. Integration Expansions
- **Workflow engines**: Nextflow, Snakemake integration
- **Cloud platforms**: AWS, GCP deployment
- **Databases**: Direct UCSC, Ensembl connections
- **Other tools**: Integration with popular genomics tools

This plan provides a comprehensive roadmap for transforming annOmics into a powerful MCP server that seamlessly integrates genomic annotation capabilities with AI-assisted analysis workflows.
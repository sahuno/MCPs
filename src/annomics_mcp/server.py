"""Main MCP Server for genomic annotation."""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .schemas.genome_builds import SupportedGenomes, GenomeBuild
from .utils.r_interface import RScriptRunner, RScriptError, REnvironmentError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("annomics-mcp")

# Global R script runner
r_runner: Optional[RScriptRunner] = None


def initialize_r_runner() -> None:
    """Initialize R script runner with default script path."""
    global r_runner
    
    # Try multiple possible script locations for flexibility
    possible_paths = [
        # Docker/production path (working directory is /app)
        Path("/app/scripts/annotate_genomic_segments.R"),
        # Development path relative to this file
        Path(__file__).parent.parent.parent.parent / "scripts" / "annotate_genomic_segments.R",
        # Relative to current working directory
        Path("scripts/annotate_genomic_segments.R"),
        # Absolute path if set via environment
        Path("./scripts/annotate_genomic_segments.R")
    ]
    
    script_path = None
    for path in possible_paths:
        if path.exists():
            script_path = path
            break
    
    if script_path is None:
        available_paths = [str(p) for p in possible_paths]
        raise FileNotFoundError(f"R script not found in any of these locations: {available_paths}")
    
    try:
        r_runner = RScriptRunner(script_path)
        logger.info(f"Initialized R script runner with script: {script_path}")
    except (FileNotFoundError, REnvironmentError) as e:
        logger.error(f"Failed to initialize R script runner: {e}")
        raise


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="annotate_genomic_regions",
            description="Annotate genomic regions from BED files with CpG and genic features",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_files": {
                        "type": ["string", "array"],
                        "description": "Single BED file path, comma-separated list, or array of file paths",
                        "items": {"type": "string"}
                    },
                    "genome_build": {
                        "type": "string",
                        "description": "Target genome build (hg19, hg38, mm9, mm10, dm3, dm6, rn4, rn5, rn6)",
                        "enum": SupportedGenomes.list_genomes()
                    },
                    "output_directory": {
                        "type": "string",
                        "description": "Output directory path"
                    },
                    "sample_name": {
                        "type": "string",
                        "description": "Optional sample name for output files",
                        "default": "sample"
                    },
                    "include_cpg": {
                        "type": "boolean",
                        "description": "Include CpG island annotations",
                        "default": True
                    },
                    "include_genic": {
                        "type": "boolean", 
                        "description": "Include genic feature annotations",
                        "default": True
                    },
                    "plot_formats": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["png", "pdf", "svg"]
                        },
                        "description": "Output plot formats",
                        "default": ["png", "pdf"]
                    },
                    "combine_analysis": {
                        "type": "boolean",
                        "description": "Create combined analysis for multiple files",
                        "default": False
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Execution timeout in seconds",
                        "default": 300
                    }
                },
                "required": ["input_files", "genome_build", "output_directory"]
            }
        ),
        Tool(
            name="list_supported_genomes",
            description="List all supported genome builds and their details",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="validate_bed_format",
            description="Validate BED file format and structure",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to BED file to validate"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="get_annotation_summary",
            description="Get summary of annotation results from output directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "results_directory": {
                        "type": "string",
                        "description": "Path to annotation results directory"
                    },
                    "sample_name": {
                        "type": "string",
                        "description": "Specific sample name (optional, defaults to all samples)"
                    }
                },
                "required": ["results_directory"]
            }
        ),
        Tool(
            name="create_comparison_plot",
            description="Create comparison plots from multiple annotation results",
            inputSchema={
                "type": "object",
                "properties": {
                    "results_directories": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of result directories to compare"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output path for comparison plot"
                    },
                    "plot_format": {
                        "type": "string",
                        "enum": ["png", "pdf", "svg"],
                        "description": "Output plot format",
                        "default": "pdf"
                    }
                },
                "required": ["results_directories", "output_path"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[Union[TextContent, ImageContent, EmbeddedResource]]:
    """Handle tool calls."""
    
    if r_runner is None:
        return [TextContent(
            type="text",
            text="Error: R script runner not initialized. Please check R environment setup."
        )]
    
    try:
        if name == "annotate_genomic_regions":
            return await handle_annotate_genomic_regions(arguments)
        
        elif name == "list_supported_genomes":
            return await handle_list_supported_genomes(arguments)
        
        elif name == "validate_bed_format":
            return await handle_validate_bed_format(arguments)
        
        elif name == "get_annotation_summary":
            return await handle_get_annotation_summary(arguments)
        
        elif name == "create_comparison_plot":
            return await handle_create_comparison_plot(arguments)
        
        else:
            return [TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]
            
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [TextContent(
            type="text", 
            text=f"Error executing {name}: {str(e)}"
        )]


async def handle_annotate_genomic_regions(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle genomic region annotation requests."""
    
    # Extract arguments with defaults
    input_files = arguments["input_files"]
    genome_build = arguments["genome_build"]
    output_directory = arguments["output_directory"]
    sample_name = arguments.get("sample_name")
    include_cpg = arguments.get("include_cpg", True)
    include_genic = arguments.get("include_genic", True)
    plot_formats = arguments.get("plot_formats", ["png", "pdf"])
    combine_analysis = arguments.get("combine_analysis", False)
    timeout = arguments.get("timeout", 300)
    
    # Validate genome build
    if not SupportedGenomes.is_supported(genome_build):
        available = ", ".join(SupportedGenomes.list_genomes())
        return [TextContent(
            type="text",
            text=f"Error: Unsupported genome build '{genome_build}'. Available: {available}"
        )]
    
    try:
        # Run annotation
        results = await r_runner.run_annotation(
            input_files=input_files,
            genome_build=genome_build,
            output_directory=output_directory,
            sample_name=sample_name,
            include_cpg=include_cpg,
            include_genic=include_genic,
            plot_formats=plot_formats,
            combine_analysis=combine_analysis,
            timeout=timeout
        )
        
        # Format response
        response_text = f"""✅ Genomic annotation completed successfully!

**Input**: {input_files}
**Genome Build**: {genome_build}
**Output Directory**: {results['output_directory']}

**Generated Files**:
- Annotation files: {len(results['generated_files']['annotation_files'])}
- Summary files: {len(results['generated_files']['summary_files'])}
- Plot files: {len(results['generated_files']['plot_files'])}
- Combined files: {len(results['generated_files']['combined_files'])}

**Key Output Files**:
{chr(10).join(f"- {f}" for f in results['generated_files']['annotation_files'][:5])}

You can find all results in: {results['output_directory']}
"""
        
        if results['generated_files']['plot_files']:
            response_text += f"\n**Visualizations created**: {', '.join(results['generated_files']['plot_files'][:3])}"
        
        return [TextContent(type="text", text=response_text)]
        
    except RScriptError as e:
        return [TextContent(
            type="text",
            text=f"❌ Annotation failed: {str(e)}"
        )]


async def handle_list_supported_genomes(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle requests to list supported genomes."""
    
    genomes_info = []
    for genome_name, genome_info in SupportedGenomes.GENOMES.items():
        genomes_info.append(
            f"**{genome_name}**: {genome_info.description}\n"
            f"  - Species: {genome_info.species}\n"
            f"  - Assembly: {genome_info.assembly}\n"
            f"  - Annotations: {', '.join(genome_info.annotations)}\n"
        )
    
    response_text = f"""🧬 **Supported Genome Builds**

{chr(10).join(genomes_info)}

**Usage**: Specify any of these genome names in the `genome_build` parameter when calling `annotate_genomic_regions`.

**Example**: Use "mm10" for mouse genome analysis or "hg38" for human genome analysis.
"""
    
    return [TextContent(type="text", text=response_text)]


async def handle_validate_bed_format(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle BED file validation requests."""
    
    file_path = arguments["file_path"]
    
    # Check if file exists
    if not Path(file_path).exists():
        return [TextContent(
            type="text",
            text=f"❌ File not found: {file_path}"
        )]
    
    try:
        # Import validation logic
        from .schemas.bed_formats import detect_bed_format
        import pandas as pd
        
        # Detect format
        bed_format = detect_bed_format(file_path)
        
        # Read first few lines for preview
        try:
            df = pd.read_csv(file_path, sep='\t', nrows=5, header=None)
            preview = df.to_string(index=False, header=False)
        except Exception:
            preview = "Could not read file content"
        
        response_text = f"""📋 **BED File Validation Results**

**File**: {file_path}
**Detected Format**: {bed_format.value.upper()}
**Status**: ✅ Valid BED format detected

**Preview** (first 5 lines):
```
{preview}
```

**Format Details**:
- BED3: chrom, chromStart, chromEnd (minimum required)
- BED6: + name, score, strand
- BED12: + thickStart, thickEnd, itemRgb, blockCount, blockSizes, blockStarts

This file can be used with the `annotate_genomic_regions` tool.
"""
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Validation error: {str(e)}"
        )]


async def handle_get_annotation_summary(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle annotation summary requests."""
    
    results_directory = arguments["results_directory"]
    sample_name = arguments.get("sample_name")
    
    results_path = Path(results_directory)
    
    if not results_path.exists():
        return [TextContent(
            type="text",
            text=f"❌ Results directory not found: {results_directory}"
        )]
    
    try:
        # Scan for summary files
        summary_files = list(results_path.rglob("*summary*.tsv"))
        annotation_files = list(results_path.rglob("*annotated*.tsv"))
        plot_files = list(results_path.rglob("*.png")) + list(results_path.rglob("*.pdf"))
        
        response_text = f"""📊 **Annotation Results Summary**

**Directory**: {results_directory}

**Files Found**:
- Summary files: {len(summary_files)}
- Annotation files: {len(annotation_files)}
- Plot files: {len(plot_files)}

**Summary Files**:
{chr(10).join(f"- {f.name}" for f in summary_files)}

**Annotation Files**:
{chr(10).join(f"- {f.name}" for f in annotation_files[:5])}

**Visualizations**:
{chr(10).join(f"- {f.name}" for f in plot_files[:5])}
"""
        
        # Try to read one summary file for details
        if summary_files:
            try:
                import pandas as pd
                summary_df = pd.read_csv(summary_files[0], sep='\t')
                
                response_text += f"""

**Sample Summary** (from {summary_files[0].name}):
```
{summary_df.head().to_string(index=False)}
```
"""
            except Exception:
                response_text += "\n(Could not read summary file details)"
        
        return [TextContent(type="text", text=response_text)]
        
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"❌ Error reading results: {str(e)}"
        )]


async def handle_create_comparison_plot(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle comparison plot creation requests."""
    
    # This is a placeholder - would need additional R script for comparison plots
    return [TextContent(
        type="text",
        text="🔧 Comparison plot creation is not yet implemented. Use the --combine flag in annotate_genomic_regions for basic comparisons."
    )]


async def main():
    """Main server entry point."""
    
    # Initialize R runner
    try:
        initialize_r_runner()
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        return
    
    # Start server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="annomics-mcp",
                server_version="1.0.0"
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
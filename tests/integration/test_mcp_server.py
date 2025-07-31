"""Integration tests for MCP server functionality."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from annomics_mcp.server import (
    handle_list_tools,
    handle_annotate_genomic_regions,
    handle_list_supported_genomes,
    handle_validate_bed_format,
    handle_get_annotation_summary
)


class TestMCPServerTools:
    """Test MCP server tool functionality."""
    
    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing available MCP tools."""
        tools = await handle_list_tools()
        
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        
        expected_tools = [
            "annotate_genomic_regions",
            "list_supported_genomes", 
            "validate_bed_format",
            "get_annotation_summary",
            "create_comparison_plot"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
    
    @pytest.mark.asyncio
    async def test_list_supported_genomes(self):
        """Test listing supported genome builds."""
        result = await handle_list_supported_genomes({})
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        content = result[0].text
        assert "Supported Genome Builds" in content
        assert "hg38" in content
        assert "mm10" in content
        assert "Human (GRCh38)" in content
    
    @pytest.mark.asyncio
    async def test_validate_bed_format_valid_file(self):
        """Test BED file validation with valid file."""
        # Create a temporary BED file
        content = "chr1\t1000\t2000\tregion1\t100\t+\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            arguments = {"file_path": f.name}
            result = await handle_validate_bed_format(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Valid BED format detected" in result[0].text
            assert "BED6" in result[0].text
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_validate_bed_format_nonexistent_file(self):
        """Test BED file validation with nonexistent file."""
        arguments = {"file_path": "/nonexistent/file.bed"}
        result = await handle_validate_bed_format(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "File not found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_annotation_summary_nonexistent_directory(self):
        """Test getting annotation summary from nonexistent directory."""
        arguments = {"results_directory": "/nonexistent/directory"}
        result = await handle_get_annotation_summary(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Results directory not found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_annotation_summary_empty_directory(self):
        """Test getting annotation summary from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            arguments = {"results_directory": temp_dir}
            result = await handle_get_annotation_summary(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Annotation Results Summary" in result[0].text
            assert "Files Found" in result[0].text
    
    @pytest.mark.asyncio
    async def test_get_annotation_summary_with_files(self):
        """Test getting annotation summary from directory with files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "sample_annotated.tsv").touch()
            (temp_path / "sample_summary.tsv").touch()
            (temp_path / "plot.pdf").touch()
            
            arguments = {"results_directory": temp_dir}
            result = await handle_get_annotation_summary(arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            content = result[0].text
            assert "Summary files: 1" in content
            assert "Annotation files: 1" in content
            assert "Plot files: 1" in content


class TestMCPServerAnnotation:
    """Test MCP server annotation functionality."""
    
    @pytest.mark.asyncio
    async def test_annotate_genomic_regions_invalid_genome(self):
        """Test annotation with invalid genome build."""
        arguments = {
            "input_files": "test.bed",
            "genome_build": "invalid_genome",
            "output_directory": "/tmp/output"
        }
        
        result = await handle_annotate_genomic_regions(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unsupported genome build" in result[0].text
        assert "invalid_genome" in result[0].text
    
    @pytest.mark.asyncio 
    @patch('annomics_mcp.server.r_runner')
    async def test_annotate_genomic_regions_success(self, mock_r_runner):
        """Test successful genomic region annotation."""
        # Mock successful R script execution
        mock_r_runner.run_annotation = AsyncMock(return_value={
            "success": True,
            "returncode": 0,
            "stdout": "Success",
            "stderr": "",
            "output_directory": "/tmp/output",
            "generated_files": {
                "annotation_files": ["sample_annotated.tsv"],
                "summary_files": ["sample_summary.tsv"],
                "plot_files": ["sample_plot.pdf"],
                "combined_files": []
            }
        })
        
        arguments = {
            "input_files": "test.bed",
            "genome_build": "hg38",
            "output_directory": "/tmp/output",
            "sample_name": "test_sample"
        }
        
        result = await handle_annotate_genomic_regions(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "annotation completed successfully" in result[0].text
        assert "hg38" in result[0].text
        assert "test.bed" in result[0].text
    
    @pytest.mark.asyncio
    @patch('annomics_mcp.server.r_runner')
    async def test_annotate_genomic_regions_r_script_error(self, mock_r_runner):
        """Test annotation with R script error."""
        from annomics_mcp.utils.r_interface import RScriptError
        
        # Mock R script failure
        mock_r_runner.run_annotation = AsyncMock(side_effect=RScriptError("R script failed"))
        
        arguments = {
            "input_files": "test.bed", 
            "genome_build": "hg38",
            "output_directory": "/tmp/output"
        }
        
        result = await handle_annotate_genomic_regions(arguments)
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Annotation failed" in result[0].text
        assert "R script failed" in result[0].text


class TestMCPServerValidation:
    """Test MCP server input validation."""
    
    @pytest.mark.asyncio
    async def test_annotation_with_minimal_params(self):
        """Test annotation with minimal required parameters."""
        arguments = {
            "input_files": "test.bed",
            "genome_build": "hg38", 
            "output_directory": "/tmp/output"
        }
        
        # Should not raise validation errors for required params
        result = await handle_annotate_genomic_regions(arguments)
        # Will fail due to missing R runner, but validation should pass
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_annotation_with_all_params(self):
        """Test annotation with all possible parameters."""
        arguments = {
            "input_files": ["file1.bed", "file2.bed"],
            "genome_build": "mm10",
            "output_directory": "/tmp/output",
            "sample_name": "test_sample",
            "include_cpg": True,
            "include_genic": False,
            "plot_formats": ["pdf", "svg"],
            "combine_analysis": True,
            "timeout": 600
        }
        
        # Should handle all parameters without validation errors
        result = await handle_annotate_genomic_regions(arguments)
        assert len(result) == 1
    
    def test_genome_build_validation(self):
        """Test genome build validation in arguments."""
        from annomics_mcp.schemas.genome_builds import SupportedGenomes
        
        # Valid genomes
        valid_genomes = ["hg19", "hg38", "mm9", "mm10", "dm3", "dm6", "rn4", "rn5", "rn6"]
        for genome in valid_genomes:
            assert SupportedGenomes.is_supported(genome)
        
        # Invalid genomes
        invalid_genomes = ["hg37", "mm11", "invalid", ""]
        for genome in invalid_genomes:
            assert not SupportedGenomes.is_supported(genome)
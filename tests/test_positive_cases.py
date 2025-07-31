"""Positive test cases for successful operations."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from annomics_mcp.server import handle_call_tool
from annomics_mcp.utils.r_interface import RScriptRunner
from annomics_mcp.schemas.bed_formats import detect_bed_format, BEDFormat
from annomics_mcp.schemas.genome_builds import SupportedGenomes


class TestPositiveCases:
    """Test positive cases and successful operations."""
    
    @pytest.mark.asyncio
    async def test_successful_tool_listing(self):
        """Test successful listing of all MCP tools."""
        result = await handle_call_tool("list_tools", {})
        
        # Should handle unknown tool gracefully, but we test the actual function
        from annomics_mcp.server import handle_list_tools
        tools = await handle_list_tools()
        
        assert len(tools) == 5
        expected_tools = {
            "annotate_genomic_regions",
            "list_supported_genomes",
            "validate_bed_format", 
            "get_annotation_summary",
            "create_comparison_plot"
        }
        
        actual_tools = {tool.name for tool in tools}
        assert actual_tools == expected_tools
        
        # Check that each tool has required properties
        for tool in tools:
            assert hasattr(tool, 'name')
            assert hasattr(tool, 'description')
            assert hasattr(tool, 'inputSchema')
            assert tool.description  # Non-empty description
    
    @pytest.mark.asyncio
    async def test_successful_genome_listing(self):
        """Test successful listing of supported genomes."""
        result = await handle_call_tool("list_supported_genomes", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        content = result[0].text
        assert "Supported Genome Builds" in content
        
        # Check that all expected genomes are mentioned
        expected_genomes = ["hg19", "hg38", "mm9", "mm10", "dm3", "dm6", "rn4", "rn5", "rn6"]
        for genome in expected_genomes:
            assert genome in content
        
        # Check that descriptions are included
        assert "Human" in content
        assert "Mouse" in content
        assert "Drosophila" in content
        assert "Rat" in content
    
    @pytest.mark.asyncio
    async def test_successful_bed_validation_bed3(self):
        """Test successful BED3 file validation."""
        content = "chr1\t1000\t2000\nchr2\t3000\t4000\nchr3\t5000\t6000\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            result = await handle_call_tool("validate_bed_format", {"file_path": f.name})
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_text = result[0].text
            assert "BED File Validation Results" in response_text
            assert "BED3" in response_text
            assert "Valid BED format detected" in response_text
            assert "chr1" in response_text  # Preview should show content
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_successful_bed_validation_bed6(self):
        """Test successful BED6 file validation."""
        content = "chr1\t1000\t2000\tregion1\t100\t+\nchr2\t3000\t4000\tregion2\t200\t-\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            result = await handle_call_tool("validate_bed_format", {"file_path": f.name})
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_text = result[0].text
            assert "BED6" in response_text
            assert "Valid BED format detected" in response_text
            assert "region1" in response_text
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_successful_bed_validation_bed12(self):
        """Test successful BED12 file validation."""
        content = "chr1\t1000\t4000\titem1\t100\t+\t1200\t3800\t0\t2\t400,400\t0,2600\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            result = await handle_call_tool("validate_bed_format", {"file_path": f.name})
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_text = result[0].text
            assert "BED12" in response_text
            assert "Valid BED format detected" in response_text
            assert "item1" in response_text
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_successful_bed_validation_with_header(self):
        """Test successful BED file validation with header comments."""
        content = """# BED file created by test
# Date: 2024-01-01
# Genome: hg38
chr1\t1000\t2000\tregion1\t100\t+
chr2\t3000\t4000\tregion2\t200\t-
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            result = await handle_call_tool("validate_bed_format", {"file_path": f.name})
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_text = result[0].text
            assert "Valid BED format detected" in response_text
            assert "BED6" in response_text
            # Should show data preview without header comments
            assert "region1" in response_text
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_successful_annotation_summary_with_files(self):
        """Test successful annotation summary with actual files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create realistic test files
            (temp_path / "sample1_annotated.tsv").write_text(
                "seqnames\tstart\tend\tannot.type\nkjnckjnsc\nkjnckjnsc\n"
            )
            (temp_path / "sample1_summary.tsv").write_text(
                "annot.type\tcount\nmm10_cpg_islands\t150\nmm10_genes_promoters\t75\n"
            )
            (temp_path / "sample2_annotated.tsv").write_text(
                "seqnames\tstart\tend\tannot.type\n"
            )
            (temp_path / "combined_annotations.tsv").write_text(
                "seqnames\tstart\tend\tsample\n"
            )
            (temp_path / "plot1.pdf").touch()
            (temp_path / "plot2.png").touch()
            
            result = await handle_call_tool("get_annotation_summary", {
                "results_directory": temp_dir
            })
            
            assert len(result) == 1
            assert result[0].type == "text"
            
            response_text = result[0].text
            assert "Annotation Results Summary" in response_text
            assert "Summary files: 1" in response_text
            assert "Annotation files: 2" in response_text
            assert "Plot files: 2" in response_text
            assert "sample1_summary.tsv" in response_text
            assert "sample1_annotated.tsv" in response_text
    
    @pytest.mark.asyncio
    @patch('annomics_mcp.server.r_runner')
    async def test_successful_annotation_single_file(self, mock_r_runner):
        """Test successful single file genomic annotation."""
        # Mock successful R script execution
        mock_r_runner.run_annotation = AsyncMock(return_value={
            "success": True,
            "returncode": 0,
            "stdout": "Annotation completed successfully",
            "stderr": "",
            "output_directory": "/tmp/test_output",
            "generated_files": {
                "annotation_files": ["sample_annotated.tsv"],
                "summary_files": ["sample_summary.tsv"],
                "plot_files": ["sample_plot.pdf", "sample_plot.png"],
                "combined_files": []
            }
        })
        
        result = await handle_call_tool("annotate_genomic_regions", {
            "input_files": "test_peaks.bed",
            "genome_build": "hg38",
            "output_directory": "/tmp/test_output",
            "sample_name": "chipseq_peaks",
            "include_cpg": True,
            "include_genic": True,
            "plot_formats": ["pdf", "png"]
        })
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        response_text = result[0].text
        assert "annotation completed successfully" in response_text
        assert "hg38" in response_text
        assert "test_peaks.bed" in response_text
        assert "Annotation files: 1" in response_text
        assert "Plot files: 2" in response_text
        assert "/tmp/test_output" in response_text
        
        # Verify R script was called with correct parameters
        mock_r_runner.run_annotation.assert_called_once()
        call_args = mock_r_runner.run_annotation.call_args[1]
        assert call_args["input_files"] == "test_peaks.bed"
        assert call_args["genome_build"] == "hg38"
        assert call_args["output_directory"] == "/tmp/test_output"
        assert call_args["sample_name"] == "chipseq_peaks"
        assert call_args["include_cpg"] is True
        assert call_args["include_genic"] is True
        assert call_args["plot_formats"] == ["pdf", "png"]
    
    @pytest.mark.asyncio
    @patch('annomics_mcp.server.r_runner')
    async def test_successful_annotation_multiple_files(self, mock_r_runner):
        """Test successful multiple file genomic annotation."""
        # Mock successful R script execution
        mock_r_runner.run_annotation = AsyncMock(return_value={
            "success": True,
            "returncode": 0,
            "stdout": "Batch annotation completed successfully",
            "stderr": "",
            "output_directory": "/tmp/batch_output",
            "generated_files": {
                "annotation_files": ["ctrl_annotated.tsv", "treat_annotated.tsv"],
                "summary_files": ["ctrl_summary.tsv", "treat_summary.tsv"],
                "plot_files": ["ctrl_plot.pdf", "treat_plot.pdf", "combined_comparison.pdf"],
                "combined_files": ["combined_annotations.tsv", "combined_summary.tsv"]
            }
        })
        
        result = await handle_call_tool("annotate_genomic_regions", {
            "input_files": ["control.bed", "treatment.bed"],
            "genome_build": "mm10",
            "output_directory": "/tmp/batch_output",
            "combine_analysis": True,
            "plot_formats": ["pdf"]
        })
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        response_text = result[0].text
        assert "annotation completed successfully" in response_text
        assert "mm10" in response_text
        assert "Annotation files: 2" in response_text
        assert "Combined files: 2" in response_text
        assert "Plot files: 3" in response_text
        
        # Verify R script was called with correct parameters
        call_args = mock_r_runner.run_annotation.call_args[1]
        assert call_args["input_files"] == ["control.bed", "treatment.bed"]
        assert call_args["combine_analysis"] is True
    
    def test_successful_bed_format_detection_all_types(self):
        """Test successful BED format detection for all supported types."""
        test_cases = [
            ("chr1\t1000\t2000", BEDFormat.BED3),
            ("chr1\t1000\t2000\tregion1\t100\t+", BEDFormat.BED6),
            ("chr1\t1000\t4000\titem1\t100\t+\t1200\t3800\t0\t2\t400,400\t0,2600", BEDFormat.BED12),
            ("chr1\t1000\t4000\titem1\t100\t+\t1200\t3800\t0\t2\t400,400\t0,2600\textra1\textra2", BEDFormat.BED12)
        ]
        
        for content, expected_format in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
                f.write(content + "\n")
                f.flush()
                
                detected_format = detect_bed_format(f.name)
                assert detected_format == expected_format, f"Failed for content: {content}"
                
                # Clean up
                Path(f.name).unlink()
    
    def test_successful_genome_validation_all_genomes(self):
        """Test successful validation of all supported genomes."""
        expected_genomes = ["hg19", "hg38", "mm9", "mm10", "dm3", "dm6", "rn4", "rn5", "rn6"]
        
        for genome in expected_genomes:
            # Test is_supported
            assert SupportedGenomes.is_supported(genome), f"Genome {genome} should be supported"
            
            # Test get_genome
            genome_info = SupportedGenomes.get_genome(genome)
            assert genome_info is not None, f"Should return info for {genome}"
            assert genome_info.name == genome
            assert genome_info.description
            assert genome_info.species
            assert genome_info.assembly
            assert genome_info.annotations
    
    def test_successful_r_script_command_building(self):
        """Test successful R script command argument building."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test R script\nprint('test')\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Test various parameter combinations
                test_cases = [
                    # Basic case
                    {
                        "input_files": "test.bed",
                        "genome_build": "hg38",
                        "output_directory": "/tmp/output",
                        "sample_name": "test",
                        "include_cpg": True,
                        "include_genic": True,
                        "plot_formats": ["pdf"],
                        "combine_analysis": False,
                        "pattern": "*.bed"
                    },
                    # Multiple files with combine
                    {
                        "input_files": ["file1.bed", "file2.bed"],
                        "genome_build": "mm10",
                        "output_directory": "/tmp/batch",
                        "sample_name": None,
                        "include_cpg": False,
                        "include_genic": True,
                        "plot_formats": ["png", "svg"],
                        "combine_analysis": True,
                        "pattern": "*_peaks.bed"
                    }
                ]
                
                for case in test_cases:
                    args = runner._build_command_args(**case)
                    
                    # Check required arguments are present
                    assert "Rscript" in args
                    assert str(f.name) in args
                    assert "-i" in args
                    assert "-g" in args
                    assert "-o" in args
                    
                    # Check genome build
                    genome_idx = args.index("-g") + 1
                    assert args[genome_idx] == case["genome_build"]
                    
                    # Check combine analysis flag
                    if case["combine_analysis"]:
                        assert "--combine" in args
                    else:
                        assert "--combine" not in args
                    
                    # Check sample name
                    if case["sample_name"]:
                        assert "-n" in args
                        name_idx = args.index("-n") + 1
                        assert args[name_idx] == case["sample_name"]
            
            # Clean up
            Path(f.name).unlink()
    
    def test_successful_output_file_scanning(self):
        """Test successful scanning of output files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    
                    # Create various test files
                    test_files = [
                        "sample1_annotated.tsv",
                        "sample2_annotated.tsv", 
                        "sample1_summary.tsv",
                        "combined_annotations.tsv",
                        "combined_summary.tsv",
                        "plot1.pdf",
                        "plot2.png",
                        "visualization.svg",
                        "readme.txt"  # Should be ignored
                    ]
                    
                    for file_name in test_files:
                        (temp_path / file_name).touch()
                    
                    # Create subdirectories with files
                    sub_dir = temp_path / "subdir"
                    sub_dir.mkdir()
                    (sub_dir / "nested_plot.pdf").touch()
                    
                    files = runner._scan_output_files(temp_path)
                    
                    # Check categorization
                    assert len(files["annotation_files"]) == 2  # sample1, sample2
                    assert len(files["summary_files"]) == 1    # sample1_summary
                    assert len(files["combined_files"]) == 2   # combined_annotations, combined_summary
                    assert len(files["plot_files"]) == 4      # 3 plots + 1 nested
                    
                    # Check that all expected files are found
                    all_found_files = (
                        files["annotation_files"] + 
                        files["summary_files"] + 
                        files["combined_files"] + 
                        files["plot_files"]
                    )
                    
                    assert "sample1_annotated.tsv" in all_found_files
                    assert "combined_annotations.tsv" in all_found_files
                    assert "plot1.pdf" in all_found_files
                    assert "subdir/nested_plot.pdf" in all_found_files
                    assert "readme.txt" not in str(all_found_files)  # Should be ignored
            
            # Clean up
            Path(f.name).unlink()
    
    def test_successful_genome_info_retrieval(self):
        """Test successful retrieval of genome information."""
        # Test specific genome details
        test_cases = [
            ("hg38", "Homo sapiens", "Human (GRCh38)"),
            ("mm10", "Mus musculus", "Mouse (GRCh38)"),
            ("dm6", "Drosophila melanogaster", "Drosophila (BDGP Release 6)"),
            ("rn6", "Rattus norvegicus", "Rat (RGSC 6.0)")
        ]
        
        for genome_name, expected_species, expected_description in test_cases:
            genome_info = SupportedGenomes.get_genome(genome_name)
            
            assert genome_info is not None
            assert genome_info.name == genome_name
            assert genome_info.species == expected_species
            assert genome_info.description == expected_description
            assert "cpg" in genome_info.annotations
            assert "genic" in genome_info.annotations
            assert genome_info.chromosome_style  # Should have chromosome style
            assert genome_info.assembly  # Should have assembly info
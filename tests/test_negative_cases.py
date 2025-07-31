"""Negative test cases for error handling and edge cases."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock
from annomics_mcp.server import handle_call_tool
from annomics_mcp.utils.r_interface import RScriptRunner, RScriptError, REnvironmentError
from annomics_mcp.schemas.bed_formats import detect_bed_format, BEDFormat


class TestNegativeCases:
    """Test negative cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_unknown_tool_call(self):
        """Test calling an unknown MCP tool."""
        result = await handle_call_tool("unknown_tool", {})
        
        assert len(result) == 1
        assert result[0].type == "text"
        assert "Unknown tool" in result[0].text
        assert "unknown_tool" in result[0].text
    
    @pytest.mark.asyncio
    async def test_tool_call_with_exception(self):
        """Test tool call that raises an exception."""
        with patch('annomics_mcp.server.handle_list_supported_genomes', 
                  side_effect=Exception("Test exception")):
            result = await handle_call_tool("list_supported_genomes", {})
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "Error executing" in result[0].text
            assert "Test exception" in result[0].text
    
    @pytest.mark.asyncio
    async def test_annotate_with_empty_arguments(self):
        """Test annotation with missing required arguments."""
        # Missing required fields should cause KeyError
        with pytest.raises(KeyError):
            await handle_call_tool("annotate_genomic_regions", {})
    
    @pytest.mark.asyncio
    async def test_validate_bed_with_corrupted_file(self):
        """Test BED validation with corrupted file."""
        # Create a file with binary data (corrupted)
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.bed', delete=False) as f:
            f.write(b'\x00\x01\x02\x03\xff\xfe')
            f.flush()
            
            arguments = {"file_path": f.name}
            result = await handle_call_tool("validate_bed_format", arguments)
            
            assert len(result) == 1
            assert result[0].type == "text"
            # Should handle the error gracefully
            assert "Validation error" in result[0].text or "Valid BED format" in result[0].text
            
            # Clean up
            Path(f.name).unlink()
    
    def test_r_script_runner_with_nonexistent_r(self):
        """Test R script runner when R is not available."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            # Mock subprocess to simulate R not found
            with patch('subprocess.run', side_effect=FileNotFoundError("R not found")):
                with pytest.raises(REnvironmentError):
                    RScriptRunner(f.name)
            
            # Clean up
            Path(f.name).unlink()
    
    def test_r_script_runner_with_failed_r_check(self):
        """Test R script runner when R version check fails."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            # Mock subprocess to simulate R failure
            with patch('subprocess.run', return_value=Mock(returncode=1, stderr="R error")):
                with pytest.raises(REnvironmentError):
                    RScriptRunner(f.name)
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_r_script_timeout(self):
        """Test R script execution timeout."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Mock asyncio timeout
                with patch('asyncio.wait_for', side_effect=TimeoutError("Timeout")):
                    with pytest.raises(RScriptError) as excinfo:
                        await runner.run_annotation(
                            input_files="test.bed",
                            genome_build="hg38", 
                            output_directory="/tmp",
                            timeout=1  # Very short timeout
                        )
                    
                    assert "timed out" in str(excinfo.value)
            
            # Clean up
            Path(f.name).unlink()
    
    def test_bed_format_detection_edge_cases(self):
        """Test BED format detection with edge cases."""
        
        # Empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("")
            f.flush()
            
            assert detect_bed_format(f.name) == BEDFormat.UNKNOWN
            Path(f.name).unlink()
        
        # File with only comments
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("# Comment 1\n# Comment 2\n")
            f.flush()
            
            assert detect_bed_format(f.name) == BEDFormat.UNKNOWN
            Path(f.name).unlink()
        
        # File with only whitespace
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("   \n\t\n  \n")
            f.flush()
            
            assert detect_bed_format(f.name) == BEDFormat.UNKNOWN
            Path(f.name).unlink()
        
        # File with insufficient columns
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t1000\n")  # Only 2 columns
            f.flush()
            
            assert detect_bed_format(f.name) == BEDFormat.UNKNOWN
            Path(f.name).unlink()
    
    def test_r_script_build_args_edge_cases(self):
        """Test R script argument building with edge cases."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Test with empty list of input files
                args = runner._build_command_args(
                    input_files=[],
                    genome_build="hg38",
                    output_directory="output",
                    sample_name=None,
                    include_cpg=True,
                    include_genic=True,
                    plot_formats=[],
                    combine_analysis=False,
                    pattern="*.bed"
                )
                
                # Should handle empty list
                assert "-i" in args
                file_idx = args.index("-i") + 1
                assert args[file_idx] == ""
                
                # Test with empty plot formats
                assert "--formats" in args
                format_idx = args.index("--formats") + 1
                assert args[format_idx] == ""
            
            # Clean up
            Path(f.name).unlink()
    
    def test_scan_output_files_nonexistent_directory(self):
        """Test scanning nonexistent output directory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Test with nonexistent directory
                result = runner._scan_output_files(Path("/nonexistent/directory"))
                
                # Should return empty dictionary
                assert result == {}
            
            # Clean up
            Path(f.name).unlink()
    
    @pytest.mark.asyncio
    async def test_r_script_execution_failure(self):
        """Test R script execution returning error code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Mock failed subprocess execution
                mock_process = Mock()
                mock_process.returncode = 1
                mock_process.communicate = AsyncMock(return_value=(b"", b"R script error"))
                
                with patch('asyncio.create_subprocess_exec', return_value=mock_process):
                    with pytest.raises(RScriptError) as excinfo:
                        await runner.run_annotation(
                            input_files="test.bed",
                            genome_build="hg38",
                            output_directory="/tmp"
                        )
                    
                    assert "R script failed with return code 1" in str(excinfo.value)
                    assert "R script error" in str(excinfo.value)
            
            # Clean up
            Path(f.name).unlink()
    
    def test_invalid_genome_validation(self):
        """Test validation of invalid genome builds."""
        from annomics_mcp.schemas.genome_builds import SupportedGenomes
        
        # Test various invalid genome formats
        invalid_genomes = [
            "",           # Empty string
            None,         # None value  
            "hg37",       # Common mistake (should be hg19)
            "GRCh38",     # Wrong format (should be hg38)
            "human",      # Too generic
            "mouse",      # Too generic
            "mm11",       # Non-existent version
            "invalid123", # Completely invalid
            " hg38 ",     # With whitespace
            "HG38",       # Wrong case
        ]
        
        for genome in invalid_genomes:
            if genome is not None:
                assert not SupportedGenomes.is_supported(genome), f"Genome '{genome}' should be invalid"
            assert SupportedGenomes.get_genome(genome) is None, f"Should return None for '{genome}'"
    
    @pytest.mark.asyncio
    async def test_server_without_r_runner_initialized(self):
        """Test MCP server tools when R runner is not initialized."""
        # Mock r_runner as None
        with patch('annomics_mcp.server.r_runner', None):
            result = await handle_call_tool("annotate_genomic_regions", {
                "input_files": "test.bed",
                "genome_build": "hg38", 
                "output_directory": "/tmp"
            })
            
            assert len(result) == 1
            assert result[0].type == "text"
            assert "R script runner not initialized" in result[0].text
    
    def test_process_results_with_empty_output_directory(self):
        """Test processing results when output directory is empty."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Directory exists but is empty
                    results = runner._process_results(
                        returncode=0,
                        stdout="Success",
                        stderr="",
                        output_directory=temp_dir
                    )
                    
                    # Should handle empty directory gracefully
                    assert results["success"] is True
                    files = results["generated_files"]
                    assert len(files["annotation_files"]) == 0
                    assert len(files["summary_files"]) == 0
                    assert len(files["plot_files"]) == 0
                    assert len(files["combined_files"]) == 0
            
            # Clean up
            Path(f.name).unlink()
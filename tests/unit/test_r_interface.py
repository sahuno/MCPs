"""Unit tests for R script interface."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from annomics_mcp.utils.r_interface import (
    RScriptRunner, 
    RScriptError, 
    REnvironmentError
)


class TestRScriptRunner:
    """Test R script runner functionality."""
    
    def test_init_with_valid_script(self):
        """Test initialization with valid script path."""
        # Create a temporary R script file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test R script\nprint('Hello')\n")
            f.flush()
            script_path = f.name
        
        with patch.object(RScriptRunner, '_validate_r_environment'):
            runner = RScriptRunner(script_path)
            assert runner.script_path == Path(script_path)
        
        # Clean up
        Path(script_path).unlink()
    
    def test_init_with_invalid_script(self):
        """Test initialization with invalid script path."""
        with pytest.raises(FileNotFoundError):
            RScriptRunner("/nonexistent/script.R")
    
    @patch('subprocess.run')
    def test_validate_r_environment_success(self, mock_run):
        """Test successful R environment validation."""
        # Mock successful Rscript --version call
        mock_run.return_value = Mock(returncode=0, stderr="R version 4.0.0")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            runner = RScriptRunner(f.name)  # Should not raise
            
            # Clean up
            Path(f.name).unlink()
    
    @patch('subprocess.run')
    def test_validate_r_environment_failure(self, mock_run):
        """Test R environment validation failure."""
        # Mock failed Rscript --version call
        mock_run.return_value = Mock(returncode=1, stderr="Command not found")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with pytest.raises(REnvironmentError):
                RScriptRunner(f.name)
            
            # Clean up
            Path(f.name).unlink()
    
    def test_build_command_args_basic(self):
        """Test building basic command arguments."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                args = runner._build_command_args(
                    input_files="test.bed",
                    genome_build="hg38",
                    output_directory="output",
                    sample_name="sample1",
                    include_cpg=True,
                    include_genic=True,
                    plot_formats=["pdf", "png"],
                    combine_analysis=False,
                    pattern="*.bed"
                )
                
                expected_args = [
                    "Rscript", f.name,
                    "-i", "test.bed",
                    "-g", "hg38", 
                    "-o", "output",
                    "--formats", "pdf,png",
                    "-n", "sample1"
                ]
                
                assert args == expected_args
            
            # Clean up
            Path(f.name).unlink()
    
    def test_build_command_args_multiple_files(self):
        """Test building command arguments with multiple input files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                args = runner._build_command_args(
                    input_files=["file1.bed", "file2.bed"],
                    genome_build="mm10",
                    output_directory="output",
                    sample_name=None,
                    include_cpg=True,
                    include_genic=True,
                    plot_formats=["pdf"],
                    combine_analysis=True,
                    pattern="*.bed"
                )
                
                assert "-i" in args
                file_idx = args.index("-i") + 1
                assert args[file_idx] == "file1.bed,file2.bed"
                assert "--combine" in args
            
            # Clean up
            Path(f.name).unlink()
    
    def test_process_results_success(self):
        """Test processing successful R script results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                # Create temporary output directory
                with tempfile.TemporaryDirectory() as output_dir:
                    # Create some test output files
                    (Path(output_dir) / "test_annotated.tsv").touch()
                    (Path(output_dir) / "test_summary.tsv").touch()
                    
                    results = runner._process_results(
                        returncode=0,
                        stdout="Success",
                        stderr="",
                        output_directory=output_dir
                    )
                    
                    assert results["success"] is True
                    assert results["returncode"] == 0
                    assert results["stdout"] == "Success"
                    assert "generated_files" in results
            
            # Clean up
            Path(f.name).unlink()
    
    def test_process_results_failure(self):
        """Test processing failed R script results."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                with pytest.raises(RScriptError):
                    runner._process_results(
                        returncode=1,
                        stdout="",
                        stderr="R script failed",
                        output_directory="/tmp"
                    )
            
            # Clean up
            Path(f.name).unlink()
    
    def test_scan_output_files(self):
        """Test scanning output directory for generated files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.R', delete=False) as f:
            f.write("# Test script\n")
            f.flush()
            
            with patch.object(RScriptRunner, '_validate_r_environment'):
                runner = RScriptRunner(f.name)
                
                with tempfile.TemporaryDirectory() as output_dir:
                    output_path = Path(output_dir)
                    
                    # Create test files
                    (output_path / "sample_annotated.tsv").touch()
                    (output_path / "sample_summary.tsv").touch()
                    (output_path / "combined_annotations.tsv").touch()
                    (output_path / "plot.pdf").touch()
                    (output_path / "plot.png").touch()
                    
                    files = runner._scan_output_files(output_path)
                    
                    assert len(files["annotation_files"]) == 1
                    assert len(files["summary_files"]) == 1
                    assert len(files["combined_files"]) == 1
                    assert len(files["plot_files"]) == 2
            
            # Clean up
            Path(f.name).unlink()


class TestRScriptErrorHandling:
    """Test R script error handling."""
    
    def test_r_script_error_creation(self):
        """Test RScriptError exception creation."""
        error = RScriptError("Test error")
        assert str(error) == "Test error"
    
    def test_r_environment_error_creation(self):
        """Test REnvironmentError exception creation."""
        error = REnvironmentError("Environment error")
        assert str(error) == "Environment error"
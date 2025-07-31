"""Unit tests for BED format detection and validation."""

import pytest
import tempfile
from pathlib import Path
from annomics_mcp.schemas.bed_formats import BEDFormat, detect_bed_format


class TestBEDFormatDetection:
    """Test BED format detection functionality."""
    
    def test_detect_bed3_format(self):
        """Test detection of BED3 format."""
        content = "chr1\t1000\t2000\nchr2\t3000\t4000\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.BED3
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_bed6_format(self):
        """Test detection of BED6 format."""
        content = "chr1\t1000\t2000\tregion1\t100\t+\nchr2\t3000\t4000\tregion2\t200\t-\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.BED6
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_bed12_format(self):
        """Test detection of BED12 format."""
        content = "chr1\t1000\t4000\titem1\t100\t+\t1200\t3800\t0\t2\t400,400\t0,2600\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.BED12
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_format_with_header(self):
        """Test format detection with header comments."""
        content = "# This is a BED file\n# Created by test\nchr1\t1000\t2000\tregion1\t100\t+\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.BED6
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_format_empty_file(self):
        """Test format detection with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("")
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.UNKNOWN
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_format_invalid_columns(self):
        """Test format detection with insufficient columns."""
        content = "chr1\t1000\n"  # Only 2 columns
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.UNKNOWN
            
            # Clean up
            Path(f.name).unlink()
    
    def test_detect_format_nonexistent_file(self):
        """Test format detection with nonexistent file."""
        format_detected = detect_bed_format("/nonexistent/file.bed")
        assert format_detected == BEDFormat.UNKNOWN
    
    def test_detect_format_extra_columns(self):
        """Test format detection with extra columns beyond BED12."""
        content = "chr1\t1000\t4000\titem1\t100\t+\t1200\t3800\t0\t2\t400,400\t0,2600\textra1\textra2\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write(content)
            f.flush()
            
            format_detected = detect_bed_format(f.name)
            assert format_detected == BEDFormat.BED12  # Still BED12 even with extra columns
            
            # Clean up
            Path(f.name).unlink()


class TestBEDFormatEnum:
    """Test BED format enumeration."""
    
    def test_bed_format_values(self):
        """Test BED format enum values."""
        assert BEDFormat.BED3.value == "bed3"
        assert BEDFormat.BED6.value == "bed6"
        assert BEDFormat.BED12.value == "bed12"
        assert BEDFormat.UNKNOWN.value == "unknown"
    
    def test_bed_format_comparison(self):
        """Test BED format comparison."""
        assert BEDFormat.BED3 == "bed3"
        assert BEDFormat.BED6 != "bed3"
        assert BEDFormat.UNKNOWN != BEDFormat.BED12
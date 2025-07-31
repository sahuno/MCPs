"""BED file format definitions and validation schemas."""

from typing import List, Optional, Tuple, Union
from pydantic import BaseModel, validator
from enum import Enum
import pandas as pd
from pathlib import Path


class BEDFormat(str, Enum):
    """Supported BED file formats."""
    BED3 = "bed3"
    BED6 = "bed6" 
    BED12 = "bed12"
    UNKNOWN = "unknown"


def detect_bed_format(file_path: Union[str, Path]) -> BEDFormat:
    """
    Detect BED file format based on number of columns.
    
    Args:
        file_path: Path to BED file
        
    Returns:
        Detected BED format
    """
    try:
        # Read first non-comment line
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                columns = line.split('\t')
                num_cols = len(columns)
                
                if num_cols >= 12:
                    return BEDFormat.BED12
                elif num_cols >= 6:
                    return BEDFormat.BED6
                elif num_cols >= 3:
                    return BEDFormat.BED3
                else:
                    return BEDFormat.UNKNOWN
                    
    except Exception:
        return BEDFormat.UNKNOWN
    
    return BEDFormat.UNKNOWN
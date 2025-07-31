"""Genome build configurations and validation schemas."""

from typing import Dict, List, Optional
from pydantic import BaseModel


class GenomeBuild(BaseModel):
    """Schema for genome build configuration."""
    
    name: str
    description: str
    annotations: List[str]
    chromosome_style: str
    species: str
    assembly: str


class SupportedGenomes:
    """Registry of supported genome builds."""
    
    GENOMES: Dict[str, GenomeBuild] = {
        "hg19": GenomeBuild(
            name="hg19",
            description="Human (GRCh37)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Homo sapiens",
            assembly="GRCh37"
        ),
        "hg38": GenomeBuild(
            name="hg38", 
            description="Human (GRCh38)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Homo sapiens",
            assembly="GRCh38"
        ),
        "mm9": GenomeBuild(
            name="mm9",
            description="Mouse (NCBI37)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Mus musculus",
            assembly="NCBI37"
        ),
        "mm10": GenomeBuild(
            name="mm10",
            description="Mouse (GRCh38)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1", 
            species="Mus musculus",
            assembly="GRCm38"
        ),
        "dm3": GenomeBuild(
            name="dm3",
            description="Drosophila (BDGP Release 5)",
            annotations=["cpg", "genic"],
            chromosome_style="chr2L",
            species="Drosophila melanogaster",
            assembly="BDGP Release 5"
        ),
        "dm6": GenomeBuild(
            name="dm6",
            description="Drosophila (BDGP Release 6)",
            annotations=["cpg", "genic"],
            chromosome_style="chr2L",
            species="Drosophila melanogaster", 
            assembly="BDGP Release 6"
        ),
        "rn4": GenomeBuild(
            name="rn4",
            description="Rat (RGSC 3.4)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Rattus norvegicus",
            assembly="RGSC 3.4"
        ),
        "rn5": GenomeBuild(
            name="rn5",
            description="Rat (RGSC 5.0)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Rattus norvegicus",
            assembly="RGSC 5.0"
        ),
        "rn6": GenomeBuild(
            name="rn6",
            description="Rat (RGSC 6.0)",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Rattus norvegicus",
            assembly="RGSC 6.0"
        )
    }
    
    @classmethod
    def get_genome(cls, name: str) -> Optional[GenomeBuild]:
        """Get genome build by name."""
        return cls.GENOMES.get(name)
    
    @classmethod
    def list_genomes(cls) -> List[str]:
        """List all supported genome names."""
        return list(cls.GENOMES.keys())
    
    @classmethod
    def is_supported(cls, name: str) -> bool:
        """Check if genome build is supported."""
        return name in cls.GENOMES
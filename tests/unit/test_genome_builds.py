"""Unit tests for genome build schemas and validation."""

import pytest
from annomics_mcp.schemas.genome_builds import SupportedGenomes, GenomeBuild


class TestGenomeBuild:
    """Test GenomeBuild schema validation."""
    
    def test_valid_genome_build(self):
        """Test creating a valid genome build."""
        genome = GenomeBuild(
            name="test_genome",
            description="Test genome build",
            annotations=["cpg", "genic"],
            chromosome_style="chr1",
            species="Test species",
            assembly="Test assembly"
        )
        
        assert genome.name == "test_genome"
        assert genome.species == "Test species"
        assert "cpg" in genome.annotations
    
    def test_genome_build_validation(self):
        """Test genome build field validation."""
        # Test required fields
        with pytest.raises(ValueError):
            GenomeBuild()


class TestSupportedGenomes:
    """Test SupportedGenomes registry."""
    
    def test_list_genomes(self):
        """Test listing all supported genomes."""
        genomes = SupportedGenomes.list_genomes()
        
        assert isinstance(genomes, list)
        assert len(genomes) > 0
        assert "hg38" in genomes
        assert "mm10" in genomes
        assert "dm6" in genomes
        assert "rn6" in genomes
    
    def test_get_genome_valid(self):
        """Test getting a valid genome build."""
        genome = SupportedGenomes.get_genome("hg38")
        
        assert genome is not None
        assert genome.name == "hg38"
        assert genome.species == "Homo sapiens"
        assert "cpg" in genome.annotations
        assert "genic" in genome.annotations
    
    def test_get_genome_invalid(self):
        """Test getting an invalid genome build."""
        genome = SupportedGenomes.get_genome("invalid_genome")
        assert genome is None
    
    def test_is_supported_valid(self):
        """Test checking if genome is supported (valid)."""
        assert SupportedGenomes.is_supported("hg38") is True
        assert SupportedGenomes.is_supported("mm10") is True
        assert SupportedGenomes.is_supported("dm6") is True
    
    def test_is_supported_invalid(self):
        """Test checking if genome is supported (invalid)."""
        assert SupportedGenomes.is_supported("hg37") is False
        assert SupportedGenomes.is_supported("invalid") is False
        assert SupportedGenomes.is_supported("") is False
    
    def test_all_genomes_have_required_fields(self):
        """Test that all genome builds have required fields."""
        for genome_name, genome in SupportedGenomes.GENOMES.items():
            assert genome.name == genome_name
            assert genome.description
            assert genome.species
            assert genome.assembly
            assert genome.chromosome_style
            assert isinstance(genome.annotations, list)
            assert len(genome.annotations) > 0
    
    def test_consistent_annotation_types(self):
        """Test that all genomes have consistent annotation types."""
        expected_annotations = {"cpg", "genic"}
        
        for genome in SupportedGenomes.GENOMES.values():
            genome_annotations = set(genome.annotations)
            assert genome_annotations == expected_annotations
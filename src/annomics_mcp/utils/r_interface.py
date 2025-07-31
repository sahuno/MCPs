"""R script interface for executing the genomic annotation pipeline."""

import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class RScriptError(Exception):
    """Exception raised when R script execution fails."""
    pass


class REnvironmentError(Exception):
    """Exception raised when R environment is not properly configured."""
    pass


class RScriptRunner:
    """Interface for running R annotation scripts."""
    
    def __init__(self, script_path: Union[str, Path]):
        """
        Initialize R script runner.
        
        Args:
            script_path: Path to the R annotation script
        """
        self.script_path = Path(script_path)
        if not self.script_path.exists():
            raise FileNotFoundError(f"R script not found: {script_path}")
        
        self._validate_r_environment()
    
    def _validate_r_environment(self) -> None:
        """Validate R environment and required packages."""
        try:
            # Check if Rscript is available
            result = subprocess.run(
                ["Rscript", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                raise REnvironmentError("Rscript not found or not working")
                
            logger.info(f"R version check passed: {result.stderr.strip()}")
            
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise REnvironmentError(f"R environment validation failed: {e}")
    
    async def run_annotation(
        self,
        input_files: Union[str, List[str]],
        genome_build: str,
        output_directory: str,
        sample_name: Optional[str] = None,
        include_cpg: bool = True,
        include_genic: bool = True,
        plot_formats: Optional[List[str]] = None,
        combine_analysis: bool = False,
        pattern: str = "*.bed",
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Run genomic annotation asynchronously.
        
        Args:
            input_files: Single file path or list of file paths
            genome_build: Target genome build
            output_directory: Output directory path
            sample_name: Optional sample name
            include_cpg: Include CpG annotations
            include_genic: Include genic annotations
            plot_formats: List of plot formats (png, pdf, svg)
            combine_analysis: Create combined analysis
            pattern: File pattern for directory processing
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        if plot_formats is None:
            plot_formats = ["png", "pdf"]
        
        # Build command arguments
        cmd_args = self._build_command_args(
            input_files=input_files,
            genome_build=genome_build,
            output_directory=output_directory,
            sample_name=sample_name,
            include_cpg=include_cpg,
            include_genic=include_genic,
            plot_formats=plot_formats,
            combine_analysis=combine_analysis,
            pattern=pattern
        )
        
        logger.info(f"Executing R script with args: {' '.join(cmd_args)}")
        
        try:
            # Execute R script asynchronously
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.script_path.parent.parent.parent  # Set working directory
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=timeout
            )
            
            # Process results
            return self._process_results(
                returncode=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                output_directory=output_directory
            )
            
        except asyncio.TimeoutError:
            raise RScriptError(f"R script execution timed out after {timeout} seconds")
            
        except Exception as e:
            raise RScriptError(f"R script execution failed: {e}")
    
    def _build_command_args(
        self,
        input_files: Union[str, List[str]],
        genome_build: str,
        output_directory: str,
        sample_name: Optional[str],
        include_cpg: bool,
        include_genic: bool,
        plot_formats: List[str], 
        combine_analysis: bool,
        pattern: str
    ) -> List[str]:
        """Build command line arguments for R script."""
        
        # Handle input files
        if isinstance(input_files, list):
            input_str = ",".join(input_files)
        else:
            input_str = input_files
        
        cmd_args = [
            "Rscript",
            str(self.script_path),
            "-i", input_str,
            "-g", genome_build,
            "-o", output_directory,
            "--formats", ",".join(plot_formats)
        ]
        
        if sample_name:
            cmd_args.extend(["-n", sample_name])
        
        if pattern != "*.bed":
            cmd_args.extend(["--pattern", pattern])
        
        if combine_analysis:
            cmd_args.append("--combine")
        
        return cmd_args
    
    def _process_results(
        self,
        returncode: int,
        stdout: str,
        stderr: str,
        output_directory: str
    ) -> Dict[str, Any]:
        """Process R script execution results."""
        
        if returncode != 0:
            raise RScriptError(f"R script failed with return code {returncode}:\n{stderr}")
        
        # Parse output directory for generated files
        output_path = Path(output_directory)
        results = {
            "success": True,
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
            "output_directory": str(output_path),
            "generated_files": self._scan_output_files(output_path)
        }
        
        return results
    
    def _scan_output_files(self, output_dir: Path) -> Dict[str, List[str]]:
        """Scan output directory for generated files."""
        if not output_dir.exists():
            return {}
        
        files = {
            "annotation_files": [],
            "summary_files": [],
            "plot_files": [],
            "combined_files": []
        }
        
        # Recursively find all files
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(output_dir))
                
                if file_path.suffix == ".tsv":
                    if "summary" in file_path.name:
                        files["summary_files"].append(rel_path)
                    elif "combined" in file_path.name:
                        files["combined_files"].append(rel_path)
                    else:
                        files["annotation_files"].append(rel_path)
                        
                elif file_path.suffix in [".png", ".pdf", ".svg"]:
                    files["plot_files"].append(rel_path)
        
        return files
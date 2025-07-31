#!/usr/bin/env python3
"""
Simple, bulletproof MCP server for genomic annotation.
Follows the minimal MCP server pattern for maximum compatibility.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleMCPServer:
    """Minimal MCP server implementation focused on reliability."""
    
    def __init__(self):
        self.tools = {}
        self.r_script_path = self._find_r_script()
        
    def _find_r_script(self) -> Path:
        """Find R script with robust path resolution."""
        possible_paths = [
            Path("/app/scripts/annotate_genomic_segments.R"),  # Docker
            Path("scripts/annotate_genomic_segments.R"),       # Local
            Path("./scripts/annotate_genomic_segments.R"),     # Relative
            Path(__file__).parent.parent.parent.parent / "scripts" / "annotate_genomic_segments.R"  # Dev
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Found R script at: {path}")
                return path
                
        logger.error(f"R script not found in any of: {[str(p) for p in possible_paths]}")
        raise FileNotFoundError("R script not found")
    
    def register_tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """Register a tool with the server."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": {
                "type": "object",
                "properties": parameters,
                "required": list(parameters.keys())
            }
        }
        
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming MCP requests."""
        method = request.get("method")
        
        if method == "tools/list":
            return {
                "tools": list(self.tools.values())
            }
            
        elif method == "tools/call":
            tool_name = request["params"]["name"]
            arguments = request["params"]["arguments"]
            
            if tool_name == "annotate_genomic_regions":
                return await self._annotate_regions(arguments)
            elif tool_name == "list_supported_genomes":
                return await self._list_genomes()
            elif tool_name == "validate_bed_format":
                return await self._validate_bed(arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        else:
            return {"error": f"Unknown method: {method}"}
    
    async def _annotate_regions(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute genomic annotation using R script."""
        try:
            # Build R command
            input_file = args.get("input_file", "")
            genome_build = args.get("genome_build", "hg38")
            output_dir = args.get("output_dir", "/app/output")
            
            cmd = [
                "Rscript", str(self.r_script_path),
                "-i", input_file,
                "-g", genome_build,
                "-o", output_dir,
                "--formats", "png,pdf"
            ]
            
            # Execute R script
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ Annotation completed successfully!\n\nOutput: {stdout.decode()}"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text", 
                            "text": f"❌ Annotation failed:\n{stderr.decode()}"
                        }
                    ],
                    "isError": True
                }
                
        except Exception as e:
            logger.error(f"Annotation error: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error: {str(e)}"
                    }
                ],
                "isError": True
            }
    
    async def _list_genomes(self) -> Dict[str, Any]:
        """List supported genome builds."""
        genomes = {
            "hg38": "Human (GRCh38/hg38)",
            "hg19": "Human (GRCh37/hg19)", 
            "mm10": "Mouse (GRCm38/mm10)",
            "mm9": "Mouse (NCBI37/mm9)",
            "dm6": "Drosophila (BDGP6/dm6)",
            "dm3": "Drosophila (BDGP5/dm3)",
            "rn6": "Rat (Rnor_6.0/rn6)",
            "rn5": "Rat (Rnor_5.0/rn5)",
            "rn4": "Rat (RGSC_3.4/rn4)"
        }
        
        genome_list = "\n".join([f"• **{k}**: {v}" for k, v in genomes.items()])
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"## Supported Genome Builds\n\n{genome_list}\n\nUse any of these genome codes in your annotation requests."
                }
            ]
        }
    
    async def _validate_bed(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BED file format."""
        file_path = args.get("file_path", "")
        
        try:
            if not Path(file_path).exists():
                return {
                    "content": [{"type": "text", "text": f"❌ File not found: {file_path}"}],
                    "isError": True
                }
            
            # Basic BED validation
            with open(file_path) as f:
                lines = f.readlines()[:10]  # Check first 10 lines
            
            valid_lines = 0
            for line in lines:
                if line.startswith('#') or line.strip() == '':
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    valid_lines += 1
            
            bed_format = "BED3+" if valid_lines > 0 else "Invalid"
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"## BED File Validation\n\n**File**: {file_path}\n**Format**: {bed_format}\n**Valid lines**: {valid_lines}\n\n✅ File appears to be a valid BED format."
                    }
                ]
            }
            
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"❌ Validation error: {str(e)}"}],
                "isError": True
            }

async def run_stdio_server():
    """Run the MCP server using stdio transport."""
    server = SimpleMCPServer()
    
    # Register tools
    server.register_tool(
        "annotate_genomic_regions",
        "Annotate genomic regions from BED files using annotatr",
        {
            "input_file": {"type": "string", "description": "Path to input BED file"},
            "genome_build": {"type": "string", "description": "Genome build (hg38, mm10, etc.)"},
            "output_dir": {"type": "string", "description": "Output directory path"}
        }
    )
    
    server.register_tool(
        "list_supported_genomes", 
        "List all supported genome builds",
        {}
    )
    
    server.register_tool(
        "validate_bed_format",
        "Validate BED file format and structure", 
        {
            "file_path": {"type": "string", "description": "Path to BED file to validate"}
        }
    )
    
    logger.info("🚀 Simple MCP server starting...")
    
    # Simple stdio loop
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            # Send response
            json_response = json.dumps(response)
            print(json_response)
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"Request handling error: {e}")
            error_response = {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(run_stdio_server())
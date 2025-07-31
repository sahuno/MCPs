#!/usr/bin/env python3
"""
Comprehensive test script for the simple MCP server setup.
Tests all components before deployment to ensure bulletproof operation.
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

def test_r_environment():
    """Test R installation and required packages."""
    print("🧪 Testing R environment...")
    
    try:
        # Test R base installation
        result = subprocess.run(['R', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ R not installed")
            return False
        print("✅ R installed")
        
        # Test required packages
        packages = ['annotatr', 'GenomicRanges', 'optparse', 'tidyverse']
        for pkg in packages:
            result = subprocess.run([
                'R', '-e', f'library({pkg}); cat("OK")'
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ R package {pkg} not available")
                return False
            print(f"✅ R package {pkg} available")
        
        return True
        
    except Exception as e:
        print(f"❌ R environment test failed: {e}")
        return False

def test_r_script():
    """Test the R annotation script."""
    print("\n🧪 Testing R annotation script...")
    
    script_path = Path("scripts/annotate_genomic_segments.R")
    if not script_path.exists():
        print(f"❌ R script not found: {script_path}")
        return False
    
    print("✅ R script found")
    
    # Test script help
    try:
        result = subprocess.run([
            'Rscript', str(script_path), '--help'
        ], capture_output=True, text=True, timeout=30)
        
        if 'Genome build' in result.stderr or 'Input BED file' in result.stderr:
            print("✅ R script help working")
            return True
        else:
            print("❌ R script help not working properly")
            return False
            
    except Exception as e:
        print(f"❌ R script test failed: {e}")
        return False

def test_simple_server():
    """Test the simple MCP server."""
    print("\n🧪 Testing simple MCP server...")
    
    try:
        # Import the simple server
        sys.path.insert(0, 'src')
        from annomics_mcp.simple_server import SimpleMCPServer
        
        server = SimpleMCPServer()
        print("✅ Simple server imports OK")
        
        # Test tool registration
        server.register_tool("test", "Test tool", {"param": {"type": "string"}})
        if "test" in server.tools:
            print("✅ Tool registration working")
        else:
            print("❌ Tool registration failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Simple server test failed: {e}")
        return False

async def test_server_requests():
    """Test server request handling."""
    print("\n🧪 Testing server request handling...")
    
    try:
        sys.path.insert(0, 'src')
        from annomics_mcp.simple_server import SimpleMCPServer
        
        server = SimpleMCPServer()
        server.register_tool("list_supported_genomes", "List genomes", {})
        
        # Test tools/list request
        request = {"method": "tools/list"}
        response = await server.handle_request(request)
        
        if "tools" in response and len(response["tools"]) > 0:
            print("✅ tools/list request working")
        else:
            print("❌ tools/list request failed")
            return False
            
        # Test list_supported_genomes
        request = {
            "method": "tools/call",
            "params": {
                "name": "list_supported_genomes",
                "arguments": {}
            }
        }
        response = await server.handle_request(request)
        
        if "content" in response:
            print("✅ list_supported_genomes working")
        else:
            print("❌ list_supported_genomes failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Server request test failed: {e}")
        return False

def test_docker_build():
    """Test Docker build process."""
    print("\n🧪 Testing Docker build...")
    
    try:
        result = subprocess.run([
            'docker', 'build', '-f', 'Dockerfile.simple', '-t', 'annomics-test', '.'
        ], capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Docker build successful")
            
            # Test running the container briefly
            result = subprocess.run([
                'docker', 'run', '--rm', '-t', 'annomics-test', 'python3', '-c', 
                'from pathlib import Path; print("Container test OK")'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ Docker container test successful")
                return True
            else:
                print(f"❌ Docker container test failed: {result.stderr}")
                return False
        else:
            print(f"❌ Docker build failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Running comprehensive test suite for annOmics MCP server\n")
    
    tests = [
        ("R Environment", test_r_environment),
        ("R Script", test_r_script), 
        ("Simple Server", test_simple_server),
        ("Server Requests", test_server_requests),
        ("Docker Build", test_docker_build)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {name}")
        print('='*50)
        
        if asyncio.iscoroutinefunction(test_func):
            success = await test_func()
        else:
            success = test_func()
            
        results.append((name, success))
        
        if success:
            print(f"✅ {name}: PASSED")
        else:
            print(f"❌ {name}: FAILED")
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Setup is bulletproof and ready for deployment.")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
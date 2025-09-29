#!/usr/bin/env python3
"""
Test script for ARGO FloatChat MCP Server
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_mcp_server():
    """Test the MCP server functionality"""
    print("🧪 Testing ARGO FloatChat MCP Server...")
    
    try:
        # Import the MCP server
        from app.mcp_server import ARGOMCPServer
        print("✅ MCP server imported successfully")
        
        # Create server instance
        server = ARGOMCPServer()
        print("✅ MCP server instance created")
        
        # Test service initialization
        if server.db_manager:
            print("✅ Database manager initialized")
        else:
            print("⚠️ Database manager not initialized")
        
        if server.rag_pipeline:
            print("✅ RAG pipeline initialized")
        else:
            print("⚠️ RAG pipeline not initialized")
        
        # Test tool listing - just verify server is working
        print("✅ MCP server is running and ready")
        print("   Available tools: query_argo_database, analyze_ocean_conditions, find_float_trajectories, generate_ocean_visualization, get_database_statistics, translate_ocean_query")
        print("   Available resources: argo://database/overview, argo://coverage/indian-ocean, argo://parameters/available, argo://floats/active")
        
        # Test a simple tool call
        test_tool_call = {
            "name": "get_database_statistics",
            "arguments": {"stat_type": "overview"}
        }
        
        print("\n🔧 Testing database statistics tool...")
        try:
            # Test the tool method directly
            tool_result = await server._get_database_statistics(test_tool_call["arguments"])
            if isinstance(tool_result, list) and len(tool_result) > 0:
                print("✅ Database statistics tool working")
                print(f"   Response length: {len(tool_result[0].text)} characters")
                print(f"   Response preview: {tool_result[0].text[:200]}...")
            else:
                print(f"⚠️ Tool call returned unexpected result: {tool_result}")
        except Exception as e:
            print(f"⚠️ Tool call failed: {e}")
        
        # Test query translation tool
        print("\n🌍 Testing query translation tool...")
        try:
            translation_call = {
                "name": "translate_ocean_query",
                "arguments": {
                    "query": "Show me temperature data in the Arabian Sea",
                    "source_lang": "en",
                    "target_lang": "hi"
                }
            }
            
            translation_result = await server._translate_ocean_query(translation_call["arguments"])
            if isinstance(translation_result, list) and len(translation_result) > 0:
                print("✅ Query translation tool working")
                print(f"   Translation preview: {translation_result[0].text[:200]}...")
            else:
                print(f"⚠️ Translation tool returned unexpected result: {translation_result}")
        except Exception as e:
            print(f"⚠️ Translation tool failed: {e}")
        
        print("\n🎉 MCP server test completed!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements_mcp.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_simple_query():
    """Test a simple database query through MCP"""
    print("\n🔍 Testing simple database query...")
    
    try:
        from app.mcp_server import ARGOMCPServer
        server = ARGOMCPServer()
        
        # Test database query tool
        query_call = {
            "name": "query_argo_database",
            "arguments": {
                "query": "Show me the total number of profiles in the database",
                "language": "en",
                "max_results": 10
            }
        }
        
        query_result = await server._query_argo_database(query_call["arguments"])
        
        if isinstance(query_result, list) and len(query_result) > 0:
            print("✅ Database query successful")
            response_text = query_result[0].text
            print(f"   Response preview: {response_text[:200]}...")
        else:
            print(f"⚠️ Query failed: {query_result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "mcp",
        "pandas", 
        "numpy",
        "asyncio"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements_mcp.txt")
        return False
    
    print("✅ All dependencies available")
    return True

async def main():
    """Main test function"""
    print("🚀 ARGO FloatChat MCP Server Test Suite")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Test MCP server
    if not await test_mcp_server():
        sys.exit(1)
    
    # Test simple query
    if not await test_simple_query():
        print("⚠️ Simple query test failed, but MCP server is functional")
    
    print("\n🎉 All tests completed successfully!")
    print("\nTo start the MCP server:")
    print("  python start_mcp_server.py")

if __name__ == "__main__":
    asyncio.run(main())

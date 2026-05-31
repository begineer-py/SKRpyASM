"""
Context Compression System - Integration Tests and Usage Examples

Demonstrates how to use the comprehensive compression system.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'c2_core.settings')
django.setup()

from django.contrib.auth.models import User
from apps.core.models.ai_models import Thread, Message
from apps.core.models import (
    ThreadCompressionState,
    GlobalContextOverview,
)
from apps.auto.compression import ContextCompressionManager

# Mock LLM for testing (replace with real LLM in production)
class MockLLM:
    def invoke(self, prompt: str):
        """Mock LLM response."""
        class Response:
            content = "Mock response to: " + prompt[:100]
        return Response()


def test_basic_compression_flow():
    """Test complete compression pipeline."""
    print("\n=== Test 1: Basic Compression Flow ===")
    
    # Create test user and thread
    user, _ = User.objects.get_or_create(username='test_user')
    thread = Thread.objects.create(
        name="Test Pentest Thread",
        created_by=user
    )
    print(f"✅ Created thread: {thread}")
    
    # Add sample messages
    for i in range(10):
        msg_type = 'human' if i % 2 == 0 else 'ai'
        message_data = {
            'type': msg_type,
            'content': f"Test message {i}" + " " * 500  # Add some bulk
        }
        Message.objects.create(thread=thread, message=message_data)
    
    print(f"✅ Added 10 messages to thread")
    
    # Initialize compression manager
    manager = ContextCompressionManager(
        thread=thread,
        llm_main=MockLLM(),
        llm_cheap=MockLLM()
    )
    
    # Check if compression is needed
    print(f"Should compress: {manager.should_compress()}")
    
    # Get compression metrics
    metrics = manager.get_compression_metrics()
    print(f"✅ Compression metrics: {metrics}")
    
    return thread


def test_tool_lifecycle():
    """Test tool output lifecycle management."""
    print("\n=== Test 2: Tool Output Lifecycle ===")
    
    from apps.auto.compression.tool_lifecycle import ToolOutputLifecycleManager
    
    user, _ = User.objects.get_or_create(username='test_user')
    thread = Thread.objects.create(
        name="Tool Lifecycle Test",
        created_by=user
    )
    
    # Create a tool output message
    tool_output = "Port 22 (ssh) is open\n" + "X" * 5000  # Large output
    message_data = {
        'type': 'tool',
        'name': 'nmap',
        'content': tool_output
    }
    message = Message.objects.create(
        thread=thread,
        message=message_data,
        is_tool_output=True
    )
    
    # Process with lifecycle manager
    manager = ToolOutputLifecycleManager(MockLLM())
    lifecycle = manager.process_tool_message(message)
    
    print(f"✅ Tool: {lifecycle.tool_name}")
    print(f"✅ Strategy: {lifecycle.strategy}")
    print(f"✅ Compression: {lifecycle.original_output_size} → {lifecycle.compressed_size} bytes")
    
    return message


def test_chunk_divider():
    """Test message chunking logic."""
    print("\n=== Test 3: Message Chunking ===")
    
    from apps.auto.compression.chunk_divider import ChunkDivider
    
    user, _ = User.objects.get_or_create(username='test_user')
    thread = Thread.objects.create(
        name="Chunk Divider Test",
        created_by=user
    )
    
    # Create THINK → ACT → RESULT cycle
    messages_data = [
        {'type': 'human', 'content': 'Scan the target'},
        {'type': 'ai', 'content': 'I will use nmap'},
        {'type': 'tool', 'name': 'nmap', 'content': 'Port 80 open'},
        {'type': 'human', 'content': 'Check for SQL injection'},
        {'type': 'ai', 'content': 'I will use sqlmap'},
        {'type': 'tool', 'name': 'sqlmap', 'content': 'SQLi found'},
    ]
    
    for msg_data in messages_data:
        Message.objects.create(thread=thread, message=msg_data)
    
    # Divide into chunks
    divider = ChunkDivider(thread)
    chunks = divider.divide()
    
    print(f"✅ Divided {len(thread.messages.all())} messages into {len(chunks)} chunks")
    for chunk in chunks:
        print(f"   - Chunk: {len(chunk.messages)} msgs, tools: {chunk.tool_calls}")
    
    return thread


def test_global_overview():
    """Test global overview generation."""
    print("\n=== Test 4: Global Overview Generation ===")
    
    from apps.auto.compression.overview_generator import GlobalOverviewGenerator
    
    user, _ = User.objects.get_or_create(username='test_user')
    thread = Thread.objects.create(
        name="Overview Test - Pentest 192.168.1.0/24",
        created_by=user
    )
    
    # Add sample conversation
    conversation = [
        "We need to pentest 192.168.1.0/24",
        "I'll start with network discovery",
        "Found 5 hosts",
        "Running vulnerability scan",
        "Found SQL injection at 192.168.1.10",
        "Attempting exploitation",
    ]
    
    for text in conversation:
        msg_type = 'human' if 'need' in text or 'Found' in text else 'ai'
        Message.objects.create(
            thread=thread,
            message={'type': msg_type, 'content': text}
        )
    
    # Generate overview
    generator = GlobalOverviewGenerator(thread, MockLLM())
    overview = generator.generate()
    
    print(f"✅ Generated overview")
    print(f"   Mission: {overview.mission}")
    print(f"   Phase: {overview.current_phase}")
    print(f"   Vulnerabilities: {overview.confirmed_vulnerabilities}")
    
    return overview


def test_full_compression_pipeline():
    """Test complete compression pipeline."""
    print("\n=== Test 5: Full Compression Pipeline ===")
    
    user, _ = User.objects.get_or_create(username='test_user')
    thread = Thread.objects.create(
        name="Full Pipeline Test",
        created_by=user
    )
    
    # Create a realistic conversation
    messages_data = [
        {'type': 'human', 'content': 'Pentest target.com'},
        {'type': 'ai', 'content': 'Starting reconnaissance'},
        {'type': 'tool', 'name': 'nmap', 'content': 'Nmap scan results: ' + 'X' * 3000},
        {'type': 'human', 'content': 'Check for web vulnerabilities'},
        {'type': 'ai', 'content': 'Running web scanner'},
        {'type': 'tool', 'name': 'sqlmap', 'content': 'SQL Injection found at /login'},
        {'type': 'human', 'content': 'Exploit it'},
        {'type': 'ai', 'content': 'Attempting exploitation'},
        {'type': 'tool', 'name': 'sqlmap', 'content': 'Database credentials extracted'},
    ]
    
    for msg_data in messages_data:
        Message.objects.create(thread=thread, message=msg_data)
    
    # Run full compression
    manager = ContextCompressionManager(thread, MockLLM(), MockLLM())
    result = manager.compress(force=True)
    
    print(f"✅ Compression result: {result}")
    
    # Get metrics
    metrics = manager.get_compression_metrics()
    print(f"✅ Final metrics:")
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    return result


def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("CONTEXT COMPRESSION SYSTEM - INTEGRATION TESTS")
    print("="*60)
    
    try:
        test_basic_compression_flow()
        test_tool_lifecycle()
        test_chunk_divider()
        test_global_overview()
        test_full_compression_pipeline()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()

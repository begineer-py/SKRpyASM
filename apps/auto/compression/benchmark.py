"""
Benchmark script for measuring compression system performance.

Measures:
- Token reduction ratio
- Compression time
- Quality of retained information
- Memory impact
"""

import time
import json
from typing import Dict, List
from django.utils import timezone
from apps.core.models import Thread
from apps.ai_assistant.compression_models import (
    ThreadCompressionState,
    MessageCompressionChunk,
)
from apps.auto.compression import ContextCompressionManager
from apps.core.llms import get_llm_instance


class CompressionBenchmark:
    """Benchmarking suite for compression system."""
    
    def __init__(self, thread: Thread):
        """Initialize benchmark with a thread."""
        self.thread = thread
        self.results: Dict[str, any] = {}
        self.llm = get_llm_instance()
    
    def run_full_benchmark(self) -> Dict:
        """Run complete benchmark suite."""
        print(f"\n{'='*70}")
        print(f"COMPRESSION BENCHMARK: Thread {self.thread.id} - {self.thread.name}")
        print(f"{'='*70}\n")
        
        # Get baseline metrics
        self.results['baseline'] = self._get_baseline_metrics()
        print(f"Baseline metrics collected")
        print(f"  - Total messages: {self.results['baseline']['total_messages']}")
        print(f"  - Total message bytes: {self.results['baseline']['total_bytes']}")
        print(f"  - Total tokens (estimated): {self.results['baseline']['estimated_tokens']}\n")
        
        # Run compression
        self.results['compression'] = self._run_compression_benchmark()
        print(f"\nCompression completed")
        
        # Calculate metrics
        self.results['metrics'] = self._calculate_metrics()
        print(f"\nCompression Metrics:")
        print(f"  - Compression ratio: {self.results['metrics']['compression_ratio']:.1%}")
        print(f"  - Token reduction: {self.results['metrics']['token_reduction']:.1%}")
        print(f"  - Compression time: {self.results['metrics']['compression_time']:.2f}s")
        print(f"  - Avg time per message: {self.results['metrics']['avg_time_per_msg']:.3f}s\n")
        
        # Memory analysis
        self.results['memory'] = self._analyze_memory_usage()
        print(f"Memory Impact:")
        print(f"  - Storage saved: {self.results['memory']['storage_saved_bytes']} bytes")
        print(f"  - Storage reduction: {self.results['memory']['storage_reduction']:.1%}")
        print(f"  - Chunks created: {self.results['memory']['chunks_count']}\n")
        
        # Quality assessment
        self.results['quality'] = self._assess_quality()
        print(f"Quality Assessment:")
        print(f"  - Overview generated: {self.results['quality']['overview_generated']}")
        print(f"  - Chunks properly divided: {self.results['quality']['chunks_divided']}")
        print(f"  - Messages updated: {self.results['quality']['messages_updated']}\n")
        
        return self.results
    
    def _get_baseline_metrics(self) -> Dict:
        """Collect baseline metrics before compression."""
        messages = list(self.thread.messages.all())
        total_bytes = sum(len(str(msg.message)) for msg in messages)
        
        # Rough token estimation: ~4 chars per token
        estimated_tokens = total_bytes // 4
        
        return {
            'total_messages': len(messages),
            'total_bytes': total_bytes,
            'estimated_tokens': estimated_tokens,
            'timestamp': timezone.now().isoformat(),
        }
    
    def _run_compression_benchmark(self) -> Dict:
        """Run compression and measure performance."""
        manager = ContextCompressionManager(
            thread=self.thread,
            llm_main=self.llm,
            llm_cheap=self.llm
        )
        
        # Measure compression time
        start_time = time.time()
        result = manager.compress(force=True)
        compression_time = time.time() - start_time
        
        return {
            'compression_result': result,
            'compression_time': compression_time,
            'success': result.get('compressed', False),
            'chunks_created': result.get('chunks_created', 0),
            'timestamp': timezone.now().isoformat(),
        }
    
    def _calculate_metrics(self) -> Dict:
        """Calculate derived compression metrics."""
        baseline = self.results['baseline']
        compression = self.results['compression']
        
        # Get actual compressed size
        chunks = self.thread.compression_chunks.all()
        compressed_bytes = sum(
            len(str(c.compressed_content)) for c in chunks 
            if c.compressed_content
        )
        original_bytes = baseline['total_bytes']
        
        # Calculate ratios
        compression_ratio = 1.0 - (compressed_bytes / original_bytes) if original_bytes > 0 else 0
        
        # Token reduction (assuming same 4 chars/token)
        compressed_tokens = compressed_bytes // 4
        token_reduction = 1.0 - (compressed_tokens / baseline['estimated_tokens']) if baseline['estimated_tokens'] > 0 else 0
        
        # Time per message
        total_messages = baseline['total_messages']
        avg_time_per_msg = compression['compression_time'] / total_messages if total_messages > 0 else 0
        
        return {
            'compression_ratio': compression_ratio,
            'token_reduction': token_reduction,
            'compression_time': compression['compression_time'],
            'avg_time_per_msg': avg_time_per_msg,
            'original_bytes': original_bytes,
            'compressed_bytes': compressed_bytes,
            'original_tokens': baseline['estimated_tokens'],
            'compressed_tokens': compressed_tokens,
        }
    
    def _analyze_memory_usage(self) -> Dict:
        """Analyze memory impact of compression."""
        chunks = self.thread.compression_chunks.all()
        
        total_original = sum(
            len(str(c.original_content)) for c in chunks 
            if c.original_content
        )
        total_compressed = sum(
            len(str(c.compressed_content)) for c in chunks
            if c.compressed_content
        )
        
        storage_saved = total_original - total_compressed
        storage_reduction = 1.0 - (total_compressed / total_original) if total_original > 0 else 0
        
        return {
            'original_storage': total_original,
            'compressed_storage': total_compressed,
            'storage_saved_bytes': storage_saved,
            'storage_reduction': storage_reduction,
            'chunks_count': chunks.count(),
            'avg_compression_per_chunk': storage_reduction,
        }
    
    def _assess_quality(self) -> Dict:
        """Assess quality of compression."""
        # Check if overview was created
        overview_exists = self.thread.global_overview is not None
        
        # Check chunks
        chunks_count = self.thread.compression_chunks.count()
        chunks_have_content = sum(
            1 for c in self.thread.compression_chunks.all()
            if c.compressed_content
        )
        
        # Check messages updated
        updated_messages = self.thread.messages.filter(
            compression_applied=True
        ).count()
        
        return {
            'overview_generated': overview_exists,
            'chunks_divided': chunks_count > 0,
            'chunks_count': chunks_count,
            'chunks_with_content': chunks_have_content,
            'messages_updated': updated_messages,
            'total_messages': self.thread.messages.count(),
            'update_percentage': (updated_messages / self.thread.messages.count() * 100) if self.thread.messages.count() > 0 else 0,
        }
    
    def export_results(self, filepath: str = None) -> str:
        """Export benchmark results to JSON."""
        if filepath is None:
            filepath = f"/tmp/compression_benchmark_thread_{self.thread.id}.json"
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\nResults exported to: {filepath}")
        return filepath


def run_benchmark_on_thread(thread_id: int):
    """Convenience function to run benchmark on a specific thread."""
    try:
        thread = Thread.objects.get(id=thread_id)
        bench = CompressionBenchmark(thread)
        results = bench.run_full_benchmark()
        bench.export_results()
        return results
    except Thread.DoesNotExist:
        print(f"Thread {thread_id} not found")
        return None


def run_benchmark_on_all_threads():
    """Run benchmark on all threads."""
    threads = Thread.objects.filter(messages__isnull=False).distinct()
    all_results = []
    
    for thread in threads:
        try:
            print(f"\nBenchmarking thread {thread.id}...")
            results = run_benchmark_on_thread(thread.id)
            if results:
                all_results.append({
                    'thread_id': thread.id,
                    'thread_name': thread.name,
                    **results['metrics']
                })
        except Exception as e:
            print(f"Error benchmarking thread {thread.id}: {e}")
    
    # Export summary
    summary_path = "/tmp/compression_benchmark_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\nBenchmark summary exported to: {summary_path}")
    return all_results


if __name__ == "__main__":
    # Example usage:
    # python manage.py shell < benchmark_compression.py
    
    print("\nCompression System Benchmark\n")
    print("To run benchmark on a specific thread:")
    print("  results = run_benchmark_on_thread(thread_id)")
    print("\nTo run on all threads:")
    print("  results = run_benchmark_on_all_threads()")

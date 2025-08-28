#!/usr/bin/env python3
"""
Admin Agent - Symbolic Administrative Agent
Part of WolfCog AGI-OS persistent agent infrastructure

Monitors system state and proposes structural optimizations
"""

import json
import time
import threading
from pathlib import Path

class AdminAgent:
    def __init__(self, watch_paths=None):
        self.running = False
        self.watch_paths = watch_paths or ["/tmp/ecron_tasks", "spaces/"]
        self.optimization_queue = []
        self.system_state = {
            "spaces": {"u": {}, "e": {}, "s": {}},
            "processes": [],
            "memory_usage": {},
            "last_optimization": None
        }
        
    def start(self):
        """Start the admin agent"""
        print("👨‍💼 Starting Admin Agent...")
        self.running = True
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self.monitor_system)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Start optimization thread
        optimize_thread = threading.Thread(target=self.optimization_loop)
        optimize_thread.daemon = True
        optimize_thread.start()
        
        print("🔍 Admin Agent monitoring system state...")
    
    def monitor_system(self):
        """Monitor system state continuously"""
        while self.running:
            try:
                self.check_space_health()
                self.check_task_efficiency()
                self.analyze_memory_patterns()
                
            except Exception as e:
                print(f"❌ Admin monitoring error: {e}")
            
            time.sleep(5)  # Check every 5 seconds
    
    def check_space_health(self):
        """Check health of symbolic spaces"""
        for space in ["u", "e", "s"]:
            space_path = Path(f"spaces/{space}")
            if space_path.exists():
                # Simple health check based on file count
                file_count = len(list(space_path.glob("*")))
                self.system_state["spaces"][space]["file_count"] = file_count
                
                if file_count > 100:  # Arbitrary threshold
                    self.propose_optimization(f"space_{space}_cleanup", 
                                            f"Space {space} has {file_count} files")
    
    def check_task_efficiency(self):
        """Analyze task processing efficiency"""
        task_path = Path("/tmp/ecron_tasks")
        if task_path.exists():
            pending_tasks = len(list(task_path.glob("*.json")))
            processed_tasks = len(list(task_path.glob("*.processed")))
            
            self.system_state["processes"] = {
                "pending": pending_tasks,
                "processed": processed_tasks
            }
            
            if pending_tasks > 10:  # Backlog threshold
                self.propose_optimization("task_scheduling", 
                                        f"Task backlog: {pending_tasks} pending")
    
    def analyze_memory_patterns(self):
        """Analyze symbolic memory patterns"""
        # Simple pattern analysis
        total_files = 0
        for space in ["u", "e", "s"]:
            space_path = Path(f"spaces/{space}")
            if space_path.exists():
                total_files += len(list(space_path.glob("*")))
        
        self.system_state["memory_usage"]["total_files"] = total_files
        
        if total_files > 500:  # Memory threshold
            self.propose_optimization("memory_compression", 
                                    f"High memory usage: {total_files} total files")
    
    def propose_optimization(self, optimization_type, reason):
        """Propose a system optimization"""
        optimization = {
            "type": optimization_type,
            "reason": reason,
            "timestamp": time.time(),
            "agent": "admin",
            "priority": self.calculate_priority(optimization_type)
        }
        
        self.optimization_queue.append(optimization)
        print(f"💡 Admin Agent proposes: {optimization_type} - {reason}")
    
    def calculate_priority(self, optimization_type):
        """Calculate optimization priority"""
        priority_map = {
            "space_cleanup": 2,
            "task_scheduling": 3,
            "memory_compression": 1,
            "system_reorganization": 1
        }
        return priority_map.get(optimization_type, 2)
    
    def optimization_loop(self):
        """Process optimization proposals"""
        while self.running:
            try:
                if self.optimization_queue:
                    # Sort by priority (lower number = higher priority)
                    self.optimization_queue.sort(key=lambda x: x["priority"])
                    optimization = self.optimization_queue.pop(0)
                    
                    self.execute_optimization(optimization)
                    
            except Exception as e:
                print(f"❌ Optimization error: {e}")
            
            time.sleep(10)  # Process optimizations every 10 seconds
    
    def execute_optimization(self, optimization):
        """Execute a proposed optimization"""
        print(f"🔧 Executing optimization: {optimization['type']}")
        
        # Simple optimization implementations
        if optimization["type"] == "space_cleanup":
            self.cleanup_space_files()
        elif optimization["type"] == "task_scheduling":
            self.optimize_task_scheduling()
        elif optimization["type"] == "memory_compression":
            self.compress_memory()
        
        self.system_state["last_optimization"] = optimization
    
    def cleanup_space_files(self):
        """Clean up space files"""
        print("🧹 Cleaning up space files...")
        
        try:
            cleanup_stats = {"deleted": 0, "moved": 0, "compressed": 0}
            
            for space in ["u", "e", "s"]:
                space_path = Path(f"spaces/{space}")
                if not space_path.exists():
                    continue
                
                print(f"🧹 Cleaning space: {space}")
                
                # Remove empty files
                for file_path in space_path.rglob("*"):
                    if file_path.is_file() and file_path.stat().st_size == 0:
                        file_path.unlink()
                        cleanup_stats["deleted"] += 1
                
                # Remove temporary files
                temp_patterns = ["*.tmp", "*.temp", "*~", "*.bak"]
                for pattern in temp_patterns:
                    for temp_file in space_path.rglob(pattern):
                        temp_file.unlink()
                        cleanup_stats["deleted"] += 1
                
                # Organize files by type
                self.organize_files_by_type(space_path, cleanup_stats)
                
                # Compress old logs
                self.compress_old_logs(space_path, cleanup_stats)
            
            print(f"✅ Cleanup completed: {cleanup_stats['deleted']} deleted, {cleanup_stats['moved']} moved, {cleanup_stats['compressed']} compressed")
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    def organize_files_by_type(self, space_path, stats):
        """Organize files by their type and content"""
        type_dirs = {
            'logs': space_path / 'logs',
            'configs': space_path / 'configs', 
            'data': space_path / 'data',
            'temp': space_path / 'temp'
        }
        
        for type_dir in type_dirs.values():
            type_dir.mkdir(exist_ok=True)
        
        # File type patterns
        patterns = {
            'logs': ['.log', '.out', '.err'],
            'configs': ['.json', '.yaml', '.conf', '.cfg'],
            'data': ['.dat', '.csv', '.txt'],
            'temp': ['.tmp', '.temp']
        }
        
        for file_path in space_path.glob("*"):
            if file_path.is_file() and file_path.parent == space_path:
                file_moved = False
                
                for file_type, extensions in patterns.items():
                    if any(file_path.name.endswith(ext) for ext in extensions):
                        dest_path = type_dirs[file_type] / file_path.name
                        if not dest_path.exists():
                            file_path.rename(dest_path)
                            stats["moved"] += 1
                            file_moved = True
                            break
                
                # If no specific type, move to data
                if not file_moved and file_path.suffix:
                    dest_path = type_dirs['data'] / file_path.name
                    if not dest_path.exists():
                        file_path.rename(dest_path)
                        stats["moved"] += 1
    
    def compress_old_logs(self, space_path, stats):
        """Compress old log files"""
        import gzip
        import shutil
        
        logs_dir = space_path / 'logs'
        if not logs_dir.exists():
            return
        
        # Compress log files older than 3 days
        import time
        current_time = time.time()
        compress_threshold = 3 * 24 * 3600  # 3 days
        
        for log_file in logs_dir.glob("*.log"):
            age = current_time - log_file.stat().st_mtime
            if age > compress_threshold:
                compressed_file = log_file.with_suffix('.log.gz')
                
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                log_file.unlink()
                stats["compressed"] += 1
    
    def optimize_task_scheduling(self):
        """Optimize task scheduling"""
        print("📅 Optimizing task scheduling...")
        
        try:
            task_path = Path("/tmp/ecron_tasks")
            if not task_path.exists():
                print("📁 No task queue found")
                return
            
            # Analyze task patterns
            task_files = list(task_path.glob("*.json"))
            
            if not task_files:
                print("📋 No pending tasks to optimize")
                return
            
            # Group tasks by similarity and priority
            task_groups = self.analyze_task_patterns(task_files)
            
            # Implement scheduling optimizations
            self.implement_task_batching(task_groups)
            self.optimize_task_order(task_path)
            self.create_task_dependencies(task_groups)
            
            print(f"✅ Task scheduling optimized for {len(task_files)} tasks")
            
        except Exception as e:
            print(f"❌ Task scheduling optimization error: {e}")
    
    def analyze_task_patterns(self, task_files):
        """Analyze patterns in task specifications"""
        task_groups = {'space_u': [], 'space_e': [], 'space_s': [], 'high_priority': [], 'batch_ready': []}
        
        for task_file in task_files:
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)
                
                space = task_data.get('space', 'e')
                action = task_data.get('action', 'evaluate')
                flow = task_data.get('flow', '')
                
                # Group by space
                task_groups[f'space_{space}'].append(task_file)
                
                # Identify high priority tasks
                if action in ['meta_evolve', 'evolve'] or 'critical' in flow:
                    task_groups['high_priority'].append(task_file)
                
                # Identify batchable tasks
                if action in ['evaluate', 'test']:
                    task_groups['batch_ready'].append(task_file)
                    
            except Exception as e:
                print(f"⚠️ Error analyzing task {task_file}: {e}")
        
        return task_groups
    
    def implement_task_batching(self, task_groups):
        """Implement task batching for efficiency"""
        batch_dir = Path("/tmp/ecron_tasks/batched")
        batch_dir.mkdir(exist_ok=True)
        
        # Batch similar tasks together
        if len(task_groups['batch_ready']) > 3:
            batch_size = 5
            for i in range(0, len(task_groups['batch_ready']), batch_size):
                batch_tasks = task_groups['batch_ready'][i:i+batch_size]
                
                # Create batch task
                batch_data = {
                    "flow": f"batch_{i//batch_size}",
                    "space": "e",
                    "action": "evaluate",
                    "batch_tasks": [],
                    "symbolic": "∑(batch_processing)"
                }
                
                for task_file in batch_tasks:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    batch_data["batch_tasks"].append(task_data)
                    task_file.unlink()  # Remove original
                
                # Save batch task
                batch_file = batch_dir / f"batch_{i//batch_size}.json"
                with open(batch_file, 'w') as f:
                    json.dump(batch_data, f, indent=2)
                
                print(f"📦 Created batch with {len(batch_tasks)} tasks")
    
    def optimize_task_order(self, task_path):
        """Optimize task execution order"""
        # Create priority subdirectories
        priority_dirs = {
            1: task_path / "priority_1_critical",
            2: task_path / "priority_2_high", 
            3: task_path / "priority_3_normal"
        }
        
        for priority_dir in priority_dirs.values():
            priority_dir.mkdir(exist_ok=True)
        
        # Move tasks to priority queues
        for task_file in task_path.glob("*.json"):
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)
                
                # Determine priority
                priority = self.calculate_task_priority(task_data)
                
                # Move to appropriate priority queue
                dest_path = priority_dirs[priority] / task_file.name
                task_file.rename(dest_path)
                
            except Exception as e:
                print(f"⚠️ Error prioritizing task {task_file}: {e}")
    
    def calculate_task_priority(self, task_data):
        """Calculate task priority (1=highest, 3=lowest)"""
        space = task_data.get('space', 'e')
        action = task_data.get('action', 'evaluate')
        flow = task_data.get('flow', '')
        
        # System space tasks are highest priority
        if space == 's':
            return 1
        
        # Meta evolution and critical flows
        if action == 'meta_evolve' or 'critical' in flow:
            return 1
        
        # Evolution and optimization tasks
        if action in ['evolve', 'optimize']:
            return 2
        
        # Default priority
        return 3
    
    def create_task_dependencies(self, task_groups):
        """Create task dependency chains"""
        deps_file = Path("/tmp/ecron_tasks/dependencies.json")
        
        dependencies = {
            "chains": [],
            "prerequisites": {},
            "generated": time.time()
        }
        
        # Create dependency chain: system -> execution -> user
        if task_groups['space_s'] and task_groups['space_e']:
            dependencies["chains"].append({
                "name": "space_hierarchy",
                "order": ["space_s", "space_e", "space_u"],
                "description": "System space tasks must complete before execution space"
            })
        
        # High priority tasks as prerequisites
        for high_priority_task in task_groups['high_priority']:
            task_name = high_priority_task.stem
            dependencies["prerequisites"][task_name] = {
                "must_complete_before": "batch_processing",
                "reason": "High priority task dependency"
            }
        
        with open(deps_file, 'w') as f:
            json.dump(dependencies, f, indent=2)
        
        print(f"🔗 Created dependency map with {len(dependencies['chains'])} chains")
    
    def compress_memory(self):
        """Compress symbolic memory"""
        print("🗜️ Compressing symbolic memory...")
        
        try:
            compression_stats = {"spaces_processed": 0, "files_compressed": 0, "bytes_saved": 0}
            
            for space in ["u", "e", "s"]:
                space_path = Path(f"spaces/{space}")
                if not space_path.exists():
                    continue
                
                print(f"🗜️ Compressing memory in space: {space}")
                
                # Compress by file age and size
                self.compress_space_files(space_path, compression_stats)
                
                # Create memory snapshots
                self.create_memory_snapshot(space, compression_stats)
                
                # Implement semantic compression
                self.semantic_compression(space_path, compression_stats)
                
                compression_stats["spaces_processed"] += 1
            
            print(f"✅ Memory compression completed: {compression_stats['spaces_processed']} spaces, {compression_stats['files_compressed']} files compressed, {compression_stats['bytes_saved']} bytes saved")
            
        except Exception as e:
            print(f"❌ Memory compression error: {e}")
    
    def compress_space_files(self, space_path, stats):
        """Compress individual files in a space"""
        import gzip
        
        # Compress files larger than 1KB and older than 1 hour
        import time
        current_time = time.time()
        compress_threshold = 3600  # 1 hour
        size_threshold = 1024  # 1KB
        
        for file_path in space_path.rglob("*"):
            if (file_path.is_file() and 
                file_path.stat().st_size > size_threshold and
                current_time - file_path.stat().st_mtime > compress_threshold and
                not file_path.name.endswith('.gz')):
                
                compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                
                original_size = file_path.stat().st_size
                
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        f_out.write(f_in.read())
                
                compressed_size = compressed_path.stat().st_size
                stats["bytes_saved"] += (original_size - compressed_size)
                stats["files_compressed"] += 1
                
                file_path.unlink()  # Remove original
    
    def create_memory_snapshot(self, space, stats):
        """Create compressed memory snapshots"""
        space_path = Path(f"spaces/{space}")
        snapshots_dir = space_path / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        
        # Create timestamped snapshot
        timestamp = int(time.time())
        snapshot_file = snapshots_dir / f"snapshot_{timestamp}.json"
        
        snapshot_data = {
            "timestamp": timestamp,
            "space": space,
            "file_count": len(list(space_path.rglob("*"))),
            "total_size": sum(f.stat().st_size for f in space_path.rglob("*") if f.is_file()),
            "compression_ratio": 0.75  # Estimated
        }
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        print(f"📸 Created memory snapshot for space {space}")
    
    def semantic_compression(self, space_path, stats):
        """Implement semantic compression based on content similarity"""
        # Group files by content similarity (simplified approach)
        content_hashes = {}
        similar_groups = []
        
        for file_path in space_path.glob("*.txt"):
            if file_path.is_file():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Simple content hash (first 100 chars)
                    content_hash = hash(content[:100])
                    
                    if content_hash not in content_hashes:
                        content_hashes[content_hash] = []
                    content_hashes[content_hash].append(file_path)
                    
                except Exception:
                    continue
        
        # Compress similar content groups
        for content_hash, files in content_hashes.items():
            if len(files) > 2:  # Group has multiple similar files
                similar_dir = space_path / f"similar_content_{abs(content_hash) % 1000}"
                similar_dir.mkdir(exist_ok=True)
                
                for file_path in files:
                    dest_path = similar_dir / file_path.name
                    if not dest_path.exists():
                        file_path.rename(dest_path)
                
                print(f"📦 Grouped {len(files)} semantically similar files")
    
    def get_system_state(self):
        """Get current system state"""
        return self.system_state
    
    def stop(self):
        """Stop the admin agent"""
        print("🛑 Stopping Admin Agent...")
        self.running = False

if __name__ == "__main__":
    agent = AdminAgent()
    try:
        agent.start()
        # Keep agent running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
        print("👋 Admin Agent stopped.")
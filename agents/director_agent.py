#!/usr/bin/env python3
"""
Director Agent - Symbolic Logic Director Agent
Part of WolfCog AGI-OS persistent agent infrastructure

Implements Prolog-style logical reasoning for system coordination
"""

import json
import time
import threading
import hashlib
from pathlib import Path

class DirectorAgent:
    def __init__(self):
        self.running = False
        self.facts = set()
        self.rules = []
        self.inference_queue = []
        self.decisions = []
        
        # Initialize basic facts and rules
        self.initialize_knowledge_base()
        
    def initialize_knowledge_base(self):
        """Initialize the symbolic knowledge base"""
        print("🧠 Initializing Director Agent knowledge base...")
        
        # Basic facts about the system
        self.add_fact("system(wolfcog)")
        self.add_fact("space(u)")
        self.add_fact("space(e)")
        self.add_fact("space(s)")
        self.add_fact("agent(admin)")
        self.add_fact("agent(director)")
        
        # Basic rules for system coordination
        self.add_rule(["space(X)", "task_in(X, T)"], "should_process(T)")
        self.add_rule(["high_load(X)", "space(X)"], "needs_optimization(X)")
        self.add_rule(["agent(A)", "overloaded(A)"], "redistribute_tasks(A)")
        self.add_rule(["memory_full(X)", "space(X)"], "compress_memory(X)")
        
    def start(self):
        """Start the director agent"""
        print("🎬 Starting Director Agent...")
        self.running = True
        
        # Start inference thread
        inference_thread = threading.Thread(target=self.inference_loop)
        inference_thread.daemon = True
        inference_thread.start()
        
        # Start coordination thread
        coordination_thread = threading.Thread(target=self.coordination_loop)
        coordination_thread.daemon = True
        coordination_thread.start()
        
        print("🎯 Director Agent coordinating system logic...")
    
    def add_fact(self, fact):
        """Add a fact to the knowledge base"""
        self.facts.add(fact)
        print(f"📝 Added fact: {fact}")
    
    def add_rule(self, conditions, conclusion):
        """Add a rule to the knowledge base"""
        rule = {"conditions": conditions, "conclusion": conclusion}
        self.rules.append(rule)
        print(f"⚖️ Added rule: {conditions} → {conclusion}")
    
    def inference_loop(self):
        """Main inference and reasoning loop"""
        while self.running:
            try:
                # Check system state and update facts
                self.update_facts_from_system()
                
                # Apply inference rules
                self.apply_inference_rules()
                
                # Process any new inferences
                self.process_inferences()
                
            except Exception as e:
                print(f"❌ Inference error: {e}")
            
            time.sleep(3)  # Inference cycle every 3 seconds
    
    def update_facts_from_system(self):
        """Update facts based on current system state"""
        # Check task queue status
        task_path = Path("/tmp/ecron_tasks")
        if task_path.exists():
            task_count = len(list(task_path.glob("*.json")))
            if task_count > 5:
                self.add_fact("high_load(e)")
            else:
                self.remove_fact("high_load(e)")
        
        # Check memory usage
        for space in ["u", "e", "s"]:
            space_path = Path(f"spaces/{space}")
            if space_path.exists():
                file_count = len(list(space_path.glob("*")))
                if file_count > 50:
                    self.add_fact(f"memory_full({space})")
                else:
                    self.remove_fact(f"memory_full({space})")
    
    def remove_fact(self, fact):
        """Remove a fact from the knowledge base"""
        self.facts.discard(fact)
    
    def apply_inference_rules(self):
        """Apply inference rules to derive new conclusions"""
        for rule in self.rules:
            if self.can_apply_rule(rule):
                conclusion = rule["conclusion"]
                if not self.is_conclusion_known(conclusion):
                    self.inference_queue.append(conclusion)
                    print(f"🧩 Inferred: {conclusion}")
    
    def can_apply_rule(self, rule):
        """Check if a rule can be applied given current facts"""
        for condition in rule["conditions"]:
            if not self.matches_facts(condition):
                return False
        return True
    
    def matches_facts(self, condition):
        """Check if a condition matches any known facts"""
        if condition in self.facts:
            return True
        
        # Simple pattern matching for variables (X, Y, etc.)
        if "(" in condition:
            predicate = condition.split("(")[0]
            for fact in self.facts:
                if fact.startswith(predicate + "("):
                    return True
        return False
    
    def is_conclusion_known(self, conclusion):
        """Check if a conclusion is already known"""
        # Simple check - in practice would need more sophisticated pattern matching
        return conclusion in self.facts or conclusion in [inf for inf in self.inference_queue]
    
    def process_inferences(self):
        """Process inferred conclusions and make decisions"""
        while self.inference_queue:
            inference = self.inference_queue.pop(0)
            decision = self.make_decision(inference)
            if decision:
                self.decisions.append(decision)
                self.execute_decision(decision)
    
    def make_decision(self, inference):
        """Make a decision based on an inference"""
        if "should_process" in inference:
            return {"type": "process_task", "inference": inference, "timestamp": time.time()}
        elif "needs_optimization" in inference:
            space = self.extract_space(inference)
            return {"type": "optimize_space", "space": space, "inference": inference, "timestamp": time.time()}
        elif "redistribute_tasks" in inference:
            agent = self.extract_agent(inference)
            return {"type": "redistribute", "agent": agent, "inference": inference, "timestamp": time.time()}
        elif "compress_memory" in inference:
            space = self.extract_space(inference)
            return {"type": "compress", "space": space, "inference": inference, "timestamp": time.time()}
        return None
    
    def extract_space(self, inference):
        """Extract space from inference string"""
        if "(" in inference and ")" in inference:
            return inference.split("(")[1].split(")")[0]
        return "unknown"
    
    def extract_agent(self, inference):
        """Extract agent from inference string"""
        if "(" in inference and ")" in inference:
            return inference.split("(")[1].split(")")[0]
        return "unknown"
    
    def execute_decision(self, decision):
        """Execute a decision"""
        print(f"⚡ Director executing decision: {decision['type']}")
        
        if decision["type"] == "optimize_space":
            self.coordinate_space_optimization(decision["space"])
        elif decision["type"] == "redistribute":
            self.coordinate_task_redistribution(decision["agent"])
        elif decision["type"] == "compress":
            self.coordinate_memory_compression(decision["space"])
        elif decision["type"] == "process_task":
            self.coordinate_task_processing()
    
    def coordinate_space_optimization(self, space):
        """Coordinate space optimization"""
        print(f"🔧 Coordinating optimization for space: {space}")
        
        try:
            space_path = Path(f"spaces/{space}")
            if not space_path.exists():
                print(f"⚠️ Space {space} does not exist")
                return
            
            # Analyze space efficiency
            files = list(space_path.glob("*"))
            file_sizes = [f.stat().st_size for f in files if f.is_file()]
            
            if not file_sizes:
                print(f"📁 Space {space} is empty, no optimization needed")
                return
            
            avg_size = sum(file_sizes) / len(file_sizes)
            small_files = [f for f in files if f.is_file() and f.stat().st_size < avg_size * 0.1]
            
            # Optimization strategies
            if len(small_files) > 10:
                print(f"🗂️ Consolidating {len(small_files)} small files in space {space}")
                self.consolidate_small_files(space, small_files)
            
            # Check for duplicate content
            self.deduplicate_space_content(space_path)
            
            # Organize by semantic similarity (simplified)
            self.organize_by_pattern(space_path)
            
            print(f"✅ Space {space} optimization completed")
            
        except Exception as e:
            print(f"❌ Space optimization error: {e}")
    
    def consolidate_small_files(self, space, small_files):
        """Consolidate small files into larger chunks"""
        consolidated_dir = Path(f"spaces/{space}/consolidated")
        consolidated_dir.mkdir(exist_ok=True)
        
        batch_size = 5
        for i in range(0, len(small_files), batch_size):
            batch = small_files[i:i+batch_size]
            consolidated_file = consolidated_dir / f"batch_{i//batch_size}.txt"
            
            with open(consolidated_file, 'w') as outfile:
                for file_path in batch:
                    if file_path.is_file():
                        outfile.write(f"=== {file_path.name} ===\n")
                        try:
                            with open(file_path, 'r') as infile:
                                outfile.write(infile.read())
                        except:
                            outfile.write(f"[Binary file: {file_path.name}]\n")
                        outfile.write("\n\n")
                        
                        # Remove original file
                        file_path.unlink()
        
        print(f"📦 Consolidated {len(small_files)} files into {len(range(0, len(small_files), batch_size))} batches")
    
    def deduplicate_space_content(self, space_path):
        """Remove duplicate files based on content hash"""
        file_hashes = {}
        duplicates = []
        
        for file_path in space_path.rglob("*"):
            if file_path.is_file():
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                    
                    if file_hash in file_hashes:
                        duplicates.append(file_path)
                    else:
                        file_hashes[file_hash] = file_path
                except:
                    continue
        
        for dup_file in duplicates:
            dup_file.unlink()
            print(f"🗑️ Removed duplicate: {dup_file}")
        
        if duplicates:
            print(f"✨ Removed {len(duplicates)} duplicate files")
    
    def organize_by_pattern(self, space_path):
        """Organize files by naming patterns and content types"""
        patterns = {
            'symbolic': r'.*[∇∂⊗Φ].*',
            'numeric': r'.*\d+.*',
            'temporal': r'.*time.*|.*[0-9]{4}[0-9]{2}[0-9]{2}.*',
            'config': r'.*\.json$|.*\.yaml$|.*\.conf$'
        }
        
        import re
        
        for pattern_name, pattern_regex in patterns.items():
            pattern_dir = space_path / pattern_name
            
            matching_files = []
            for file_path in space_path.glob("*"):
                if file_path.is_file() and re.match(pattern_regex, file_path.name):
                    matching_files.append(file_path)
            
            if matching_files:
                pattern_dir.mkdir(exist_ok=True)
                for file_path in matching_files:
                    dest_path = pattern_dir / file_path.name
                    if not dest_path.exists():
                        file_path.rename(dest_path)
                
                print(f"📂 Organized {len(matching_files)} files into {pattern_name} category")
    
    def coordinate_task_redistribution(self, agent):
        """Coordinate task redistribution"""
        print(f"🔄 Coordinating task redistribution for agent: {agent}")
        
        try:
            # Assess current task load
            task_path = Path("/tmp/ecron_tasks")
            if not task_path.exists():
                print("📁 No task queue found")
                return
            
            pending_tasks = list(task_path.glob("*.json"))
            
            if len(pending_tasks) <= 5:
                print("⚖️ Task load is manageable, no redistribution needed")
                return
            
            print(f"📊 Found {len(pending_tasks)} pending tasks, redistributing...")
            
            # Categorize tasks by priority and space
            task_categories = {'u': [], 'e': [], 's': [], 'unknown': []}
            
            for task_file in pending_tasks:
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    
                    space = task_data.get('space', 'unknown')
                    if space in task_categories:
                        task_categories[space].append(task_file)
                    else:
                        task_categories['unknown'].append(task_file)
                except:
                    task_categories['unknown'].append(task_file)
            
            # Redistribute based on load balancing
            self.redistribute_by_priority(task_categories)
            
        except Exception as e:
            print(f"❌ Task redistribution error: {e}")
    
    def redistribute_by_priority(self, task_categories):
        """Redistribute tasks based on priority and load balancing"""
        # Create priority queues
        priority_dirs = {
            'high_priority': Path("/tmp/ecron_tasks/high_priority"),
            'medium_priority': Path("/tmp/ecron_tasks/medium_priority"), 
            'low_priority': Path("/tmp/ecron_tasks/low_priority")
        }
        
        for dir_path in priority_dirs.values():
            dir_path.mkdir(exist_ok=True)
        
        # Redistribute system tasks to high priority
        for task_file in task_categories['s']:
            dest = priority_dirs['high_priority'] / task_file.name
            task_file.rename(dest)
        
        # Redistribute execution tasks to medium priority
        for task_file in task_categories['e']:
            dest = priority_dirs['medium_priority'] / task_file.name
            task_file.rename(dest)
        
        # Redistribute user tasks to low priority
        for task_file in task_categories['u']:
            dest = priority_dirs['low_priority'] / task_file.name
            task_file.rename(dest)
        
        # Handle unknown tasks
        for task_file in task_categories['unknown']:
            dest = priority_dirs['low_priority'] / task_file.name
            task_file.rename(dest)
        
        print(f"📋 Redistributed tasks: {len(task_categories['s'])} high, {len(task_categories['e'])} medium, {len(task_categories['u'])} low priority")
    
    def coordinate_memory_compression(self, space):
        """Coordinate memory compression"""
        print(f"🗜️ Coordinating memory compression for space: {space}")
        
        try:
            space_path = Path(f"spaces/{space}")
            if not space_path.exists():
                print(f"⚠️ Space {space} does not exist")
                return
            
            # Analyze memory usage
            total_files = list(space_path.rglob("*"))
            file_count = len([f for f in total_files if f.is_file()])
            
            if file_count < 50:
                print(f"📊 Space {space} has {file_count} files, compression not needed")
                return
            
            print(f"🗜️ Compressing {file_count} files in space {space}")
            
            # Implement compression strategies
            self.compress_by_age(space_path)
            self.compress_by_similarity(space_path)
            self.archive_old_content(space_path)
            
            print(f"✅ Memory compression completed for space {space}")
            
        except Exception as e:
            print(f"❌ Memory compression error: {e}")
    
    def compress_by_age(self, space_path):
        """Compress files by age"""
        import time
        current_time = time.time()
        old_threshold = 7 * 24 * 3600  # 7 days
        
        old_files = []
        for file_path in space_path.rglob("*"):
            if file_path.is_file():
                age = current_time - file_path.stat().st_mtime
                if age > old_threshold:
                    old_files.append(file_path)
        
        if old_files:
            archive_dir = space_path / "archived"
            archive_dir.mkdir(exist_ok=True)
            
            for old_file in old_files:
                archive_path = archive_dir / old_file.name
                old_file.rename(archive_path)
            
            print(f"📦 Archived {len(old_files)} old files")
    
    def compress_by_similarity(self, space_path):
        """Compress similar files together"""
        # Group files by size similarity (simple heuristic)
        size_groups = {}
        
        for file_path in space_path.glob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                size_bucket = size // 1024  # Group by KB
                
                if size_bucket not in size_groups:
                    size_groups[size_bucket] = []
                size_groups[size_bucket].append(file_path)
        
        # Compress groups with many similar-sized files
        for size_bucket, files in size_groups.items():
            if len(files) > 5:
                similar_dir = space_path / f"similar_size_{size_bucket}kb"
                similar_dir.mkdir(exist_ok=True)
                
                for file_path in files:
                    dest_path = similar_dir / file_path.name
                    if not dest_path.exists():
                        file_path.rename(dest_path)
                
                print(f"📂 Grouped {len(files)} similar files (~{size_bucket}KB each)")
    
    def archive_old_content(self, space_path):
        """Archive old content to reduce active memory"""
        archive_path = space_path / "archive"
        archive_path.mkdir(exist_ok=True)
        
        # Move files older than 30 days to archive
        import time
        current_time = time.time()
        archive_threshold = 30 * 24 * 3600  # 30 days
        
        archived_count = 0
        for file_path in space_path.glob("*"):
            if file_path.is_file():
                age = current_time - file_path.stat().st_mtime
                if age > archive_threshold:
                    archive_file = archive_path / file_path.name
                    if not archive_file.exists():
                        file_path.rename(archive_file)
                        archived_count += 1
        
        if archived_count > 0:
            print(f"🗃️ Archived {archived_count} old files")
    
    def coordinate_memory_compression(self, space):
        """Coordinate memory compression"""
        print(f"🗜️ Coordinating memory compression for space: {space}")
        # Previous implementation moved up
    
    def coordinate_task_processing(self):
        """Coordinate task processing"""
        print("📋 Coordinating task processing")
        # Placeholder for task coordination
    
    def coordination_loop(self):
        """Main coordination loop"""
        while self.running:
            try:
                # Monitor other agents and coordinate
                self.check_agent_status()
                
                # Coordinate system-wide activities
                self.coordinate_system_activities()
                
            except Exception as e:
                print(f"❌ Coordination error: {e}")
            
            time.sleep(5)  # Coordination cycle every 5 seconds
    
    def check_agent_status(self):
        """Check status of other agents"""
        # Placeholder for agent status checking
        pass
    
    def coordinate_system_activities(self):
        """Coordinate system-wide activities"""
        # Placeholder for system coordination
        pass
    
    def get_knowledge_base(self):
        """Get current knowledge base state"""
        return {
            "facts": list(self.facts),
            "rules": self.rules,
            "recent_decisions": self.decisions[-10:]  # Last 10 decisions
        }
    
    def stop(self):
        """Stop the director agent"""
        print("🛑 Stopping Director Agent...")
        self.running = False

if __name__ == "__main__":
    agent = DirectorAgent()
    try:
        agent.start()
        # Keep agent running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
        print("👋 Director Agent stopped.")
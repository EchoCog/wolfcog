#!/usr/bin/env python3
"""
Reflex Daemon - Reactive monitoring for WolfCog AGI-OS
Monitors shells and self-modifying symbols for reactive responses
"""

import time
import threading
import json
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReflexEventHandler(FileSystemEventHandler):
    def __init__(self, reflex_daemon):
        self.reflex_daemon = reflex_daemon
    
    def on_modified(self, event):
        if not event.is_directory:
            self.reflex_daemon.handle_file_change(event.src_path)
    
    def on_created(self, event):
        if not event.is_directory:
            self.reflex_daemon.handle_file_creation(event.src_path)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.reflex_daemon.handle_file_deletion(event.src_path)

class ReflexDaemon:
    def __init__(self):
        self.running = False
        self.observers = []
        self.watch_paths = [
            "spaces/",
            "kernels/",
            "/tmp/ecron_tasks",
            "agents/"
        ]
        self.reactions = []
        self.file_states = {}
        self.response_queue = []
        
    def start(self):
        """Start the reflex daemon"""
        print("⚡ Starting Reflex Daemon...")
        self.running = True
        
        # Start file system monitoring
        self.start_monitoring()
        
        # Start reactive response thread
        response_thread = threading.Thread(target=self.process_responses)
        response_thread.daemon = True
        response_thread.start()
        
        # Start symbolic monitoring thread
        symbolic_thread = threading.Thread(target=self.monitor_symbolic_changes)
        symbolic_thread.daemon = True
        symbolic_thread.start()
        
        print("👁️ Reflex Daemon monitoring for reactive responses...")
    
    def start_monitoring(self):
        """Start file system monitoring"""
        event_handler = ReflexEventHandler(self)
        
        for watch_path in self.watch_paths:
            path = Path(watch_path)
            if path.exists():
                observer = Observer()
                observer.schedule(event_handler, str(path), recursive=True)
                observer.start()
                self.observers.append(observer)
                print(f"👀 Monitoring: {watch_path}")
    
    def handle_file_change(self, file_path):
        """Handle file modification events"""
        print(f"📝 File modified: {file_path}")
        
        # Calculate file hash to detect actual changes
        current_hash = self.calculate_file_hash(file_path)
        previous_hash = self.file_states.get(file_path)
        
        if current_hash != previous_hash:
            self.file_states[file_path] = current_hash
            
            reaction = {
                "type": "file_modified",
                "path": file_path,
                "timestamp": time.time(),
                "hash": current_hash,
                "previous_hash": previous_hash
            }
            
            self.trigger_reaction(reaction)
    
    def handle_file_creation(self, file_path):
        """Handle file creation events"""
        print(f"✨ File created: {file_path}")
        
        reaction = {
            "type": "file_created",
            "path": file_path,
            "timestamp": time.time(),
            "hash": self.calculate_file_hash(file_path)
        }
        
        self.trigger_reaction(reaction)
    
    def handle_file_deletion(self, file_path):
        """Handle file deletion events"""
        print(f"🗑️ File deleted: {file_path}")
        
        reaction = {
            "type": "file_deleted",
            "path": file_path,
            "timestamp": time.time(),
            "previous_hash": self.file_states.get(file_path)
        }
        
        # Remove from tracked states
        if file_path in self.file_states:
            del self.file_states[file_path]
        
        self.trigger_reaction(reaction)
    
    def calculate_file_hash(self, file_path):
        """Calculate hash of file contents"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None
    
    def trigger_reaction(self, reaction):
        """Trigger a reactive response"""
        self.reactions.append(reaction)
        
        # Determine response based on reaction type and context
        response = self.determine_response(reaction)
        if response:
            self.response_queue.append(response)
            print(f"⚡ Triggered reaction: {reaction['type']} -> {response['action']}")
    
    def determine_response(self, reaction):
        """Determine appropriate response to a reaction"""
        file_path = reaction["path"]
        reaction_type = reaction["type"]
        
        # Response rules based on file type and location
        if "kernels/" in file_path:
            return self.handle_kernel_change(reaction)
        elif "spaces/" in file_path:
            return self.handle_space_change(reaction)
        elif "ecron_tasks" in file_path:
            return self.handle_task_change(reaction)
        elif "agents/" in file_path:
            return self.handle_agent_change(reaction)
        
        return None
    
    def handle_kernel_change(self, reaction):
        """Handle changes to kernel files"""
        if reaction["type"] == "file_modified":
            return {
                "action": "reload_kernel",
                "target": reaction["path"],
                "priority": 1,
                "timestamp": time.time()
            }
        return None
    
    def handle_space_change(self, reaction):
        """Handle changes to symbolic spaces"""
        if reaction["type"] == "file_created":
            return {
                "action": "index_memory",
                "target": reaction["path"],
                "priority": 2,
                "timestamp": time.time()
            }
        elif reaction["type"] == "file_modified":
            return {
                "action": "update_memory",
                "target": reaction["path"],
                "priority": 2,
                "timestamp": time.time()
            }
        return None
    
    def handle_task_change(self, reaction):
        """Handle changes to task files"""
        if reaction["type"] == "file_created":
            return {
                "action": "notify_scheduler",
                "target": reaction["path"],
                "priority": 1,
                "timestamp": time.time()
            }
        return None
    
    def handle_agent_change(self, reaction):
        """Handle changes to agent files"""
        if reaction["type"] == "file_modified":
            return {
                "action": "restart_agent",
                "target": reaction["path"],
                "priority": 2,
                "timestamp": time.time()
            }
        return None
    
    def process_responses(self):
        """Process reactive responses"""
        while self.running:
            try:
                if self.response_queue:
                    # Sort by priority (lower number = higher priority)
                    self.response_queue.sort(key=lambda x: x["priority"])
                    response = self.response_queue.pop(0)
                    
                    self.execute_response(response)
                
            except Exception as e:
                print(f"❌ Response processing error: {e}")
            
            time.sleep(1)  # Process responses every second
    
    def execute_response(self, response):
        """Execute a reactive response"""
        action = response["action"]
        target = response["target"]
        
        print(f"🎯 Executing reflex response: {action} on {target}")
        
        if action == "reload_kernel":
            self.reload_kernel(target)
        elif action == "index_memory":
            self.index_memory(target)
        elif action == "update_memory":
            self.update_memory(target)
        elif action == "notify_scheduler":
            self.notify_scheduler(target)
        elif action == "restart_agent":
            self.restart_agent(target)
    
    def reload_kernel(self, kernel_path):
        """Reload a modified kernel"""
        print(f"🔄 Reloading kernel: {kernel_path}")
        
        try:
            kernel_name = Path(kernel_path).stem
            
            # Determine kernel type and reload strategy
            if kernel_path.endswith('.lisp'):
                self.reload_lisp_kernel(kernel_path, kernel_name)
            elif kernel_path.endswith('.scm'):
                self.reload_guile_kernel(kernel_path, kernel_name)
            elif kernel_path.endswith('.wl'):
                self.reload_wolfram_kernel(kernel_path, kernel_name)
            elif kernel_path.endswith('.py'):
                self.reload_python_kernel(kernel_path, kernel_name)
            else:
                print(f"⚠️ Unknown kernel type: {kernel_path}")
                
        except Exception as e:
            print(f"❌ Kernel reload error: {e}")
    
    def reload_lisp_kernel(self, kernel_path, kernel_name):
        """Reload a Lisp kernel"""
        # Signal other components about kernel reload
        reload_signal = {
            "type": "kernel_reload",
            "kernel": kernel_name,
            "path": kernel_path,
            "language": "lisp",
            "timestamp": time.time()
        }
        
        self.broadcast_signal(reload_signal)
        print(f"🔄 Lisp kernel {kernel_name} reload signaled")
    
    def reload_guile_kernel(self, kernel_path, kernel_name):
        """Reload a Guile/Scheme kernel"""
        # Send reload command to Guile processes
        reload_signal = {
            "type": "kernel_reload", 
            "kernel": kernel_name,
            "path": kernel_path,
            "language": "guile",
            "timestamp": time.time()
        }
        
        self.broadcast_signal(reload_signal)
        print(f"🔄 Guile kernel {kernel_name} reload signaled")
    
    def reload_wolfram_kernel(self, kernel_path, kernel_name):
        """Reload a Wolfram Language kernel"""
        # Signal Wolfram kernel reload
        reload_signal = {
            "type": "kernel_reload",
            "kernel": kernel_name, 
            "path": kernel_path,
            "language": "wolfram",
            "timestamp": time.time()
        }
        
        self.broadcast_signal(reload_signal)
        print(f"🔄 Wolfram kernel {kernel_name} reload signaled")
    
    def reload_python_kernel(self, kernel_path, kernel_name):
        """Reload a Python kernel/module"""
        try:
            # Attempt to reload Python module if it's importable
            import importlib
            import sys
            
            # Convert path to module name
            module_name = kernel_name.replace('-', '_')
            
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                print(f"🔄 Python module {module_name} reloaded")
            else:
                print(f"🔄 Python module {module_name} not currently loaded")
                
        except Exception as e:
            print(f"⚠️ Python module reload failed: {e}")
    
    def broadcast_signal(self, signal):
        """Broadcast reload signal to system components"""
        signals_dir = Path("/tmp/wolfcog_signals")
        signals_dir.mkdir(exist_ok=True)
        
        signal_file = signals_dir / f"signal_{int(time.time())}_{signal['type']}.json"
        with open(signal_file, 'w') as f:
            json.dump(signal, f, indent=2)
        
        print(f"📡 Signal broadcasted: {signal['type']}")
    
    def index_memory(self, memory_path):
        """Index new memory structure"""
        print(f"📚 Indexing memory: {memory_path}")
        
        try:
            memory_file = Path(memory_path)
            
            if not memory_file.exists():
                print(f"⚠️ Memory file not found: {memory_path}")
                return
            
            # Determine memory space
            space = self.determine_memory_space(memory_path)
            
            # Create memory index entry
            index_entry = {
                "path": str(memory_path),
                "space": space,
                "indexed_at": time.time(),
                "file_size": memory_file.stat().st_size,
                "file_hash": self.calculate_file_hash(memory_path),
                "content_type": self.detect_content_type(memory_file)
            }
            
            # Add semantic analysis
            if memory_file.suffix in ['.txt', '.json', '.scm', '.lisp']:
                index_entry["semantic_tags"] = self.extract_semantic_tags(memory_file)
            
            # Save to memory index
            self.save_to_memory_index(space, index_entry)
            
            print(f"📊 Memory indexed: {space}/{memory_file.name}")
            
        except Exception as e:
            print(f"❌ Memory indexing error: {e}")
    
    def determine_memory_space(self, memory_path):
        """Determine which memory space a file belongs to"""
        if "/u/" in memory_path or memory_path.startswith("spaces/u"):
            return "u"
        elif "/e/" in memory_path or memory_path.startswith("spaces/e"):
            return "e" 
        elif "/s/" in memory_path or memory_path.startswith("spaces/s"):
            return "s"
        else:
            return "unknown"
    
    def detect_content_type(self, file_path):
        """Detect content type of memory file"""
        suffix = file_path.suffix.lower()
        
        type_map = {
            '.json': 'structured_data',
            '.txt': 'text',
            '.scm': 'scheme_code',
            '.lisp': 'lisp_code', 
            '.wl': 'wolfram_code',
            '.py': 'python_code',
            '.md': 'markdown',
            '.log': 'log_data'
        }
        
        return type_map.get(suffix, 'unknown')
    
    def extract_semantic_tags(self, file_path):
        """Extract semantic tags from file content"""
        tags = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Look for symbolic expressions
            symbolic_patterns = ['∇', '∂', '⊗', 'Φ', 'Ω', '∑']
            for pattern in symbolic_patterns:
                if pattern in content:
                    tags.append(f"symbolic_{pattern}")
            
            # Look for cognitive keywords
            cognitive_keywords = ['cognitive', 'symbolic', 'memory', 'evolution', 'meta', 'recursive']
            for keyword in cognitive_keywords:
                if keyword.lower() in content.lower():
                    tags.append(f"concept_{keyword}")
            
            # Detect code patterns
            if any(pattern in content for pattern in ['def ', 'define ', 'function']):
                tags.append("code_definitions")
            
            if any(pattern in content for pattern in ['import', 'require', 'use-modules']):
                tags.append("code_imports")
                
        except Exception:
            pass
        
        return tags
    
    def save_to_memory_index(self, space, index_entry):
        """Save index entry to memory index"""
        index_dir = Path(f"/tmp/wolfcog_memory_index/{space}")
        index_dir.mkdir(parents=True, exist_ok=True)
        
        index_file = index_dir / "index.json"
        
        # Load existing index
        index_data = []
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    index_data = json.load(f)
            except:
                pass
        
        # Add new entry
        index_data.append(index_entry)
        
        # Keep only last 1000 entries
        if len(index_data) > 1000:
            index_data = index_data[-1000:]
        
        # Save updated index
        with open(index_file, 'w') as f:
            json.dump(index_data, f, indent=2)
    
    def update_memory(self, memory_path):
        """Update existing memory structure"""
        print(f"🔄 Updating memory: {memory_path}")
        
        try:
            memory_file = Path(memory_path)
            
            if not memory_file.exists():
                print(f"⚠️ Memory file not found: {memory_path}")
                return
            
            # Find existing index entry
            space = self.determine_memory_space(memory_path)
            existing_entry = self.find_memory_index_entry(space, memory_path)
            
            if existing_entry:
                # Update existing entry
                existing_entry["last_updated"] = time.time()
                existing_entry["file_size"] = memory_file.stat().st_size
                existing_entry["file_hash"] = self.calculate_file_hash(memory_path)
                
                # Check for content changes
                if existing_entry["file_hash"] != existing_entry.get("previous_hash"):
                    existing_entry["change_detected"] = True
                    existing_entry["change_count"] = existing_entry.get("change_count", 0) + 1
                    existing_entry["previous_hash"] = existing_entry["file_hash"]
                
                self.update_memory_index_entry(space, existing_entry)
                print(f"📊 Memory updated: {space}/{memory_file.name}")
            else:
                # Create new index entry if not found
                print(f"📝 Memory not indexed, creating new entry")
                self.index_memory(memory_path)
                
        except Exception as e:
            print(f"❌ Memory update error: {e}")
    
    def find_memory_index_entry(self, space, memory_path):
        """Find existing memory index entry"""
        index_file = Path(f"/tmp/wolfcog_memory_index/{space}/index.json")
        
        if not index_file.exists():
            return None
        
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            for entry in index_data:
                if entry.get("path") == str(memory_path):
                    return entry
                    
        except Exception:
            pass
        
        return None
    
    def update_memory_index_entry(self, space, updated_entry):
        """Update an existing memory index entry"""
        index_file = Path(f"/tmp/wolfcog_memory_index/{space}/index.json")
        
        try:
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            
            # Find and update entry
            for i, entry in enumerate(index_data):
                if entry.get("path") == updated_entry.get("path"):
                    index_data[i] = updated_entry
                    break
            
            # Save updated index
            with open(index_file, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error updating memory index: {e}")
    
    def notify_scheduler(self, task_path):
        """Notify scheduler of new task"""
        print(f"📨 Notifying scheduler: {task_path}")
        
        try:
            task_file = Path(task_path)
            
            if not task_file.exists():
                print(f"⚠️ Task file not found: {task_path}")
                return
            
            # Create scheduler notification
            notification = {
                "type": "new_task",
                "task_path": str(task_path),
                "timestamp": time.time(),
                "source": "reflex_daemon",
                "priority": self.calculate_task_priority_from_path(task_path)
            }
            
            # Try to read task details
            try:
                with open(task_file, 'r') as f:
                    task_data = json.load(f)
                notification["task_summary"] = {
                    "flow": task_data.get("flow", "unknown"),
                    "space": task_data.get("space", "e"),
                    "action": task_data.get("action", "evaluate")
                }
            except:
                notification["task_summary"] = {"status": "unreadable"}
            
            # Send notification to scheduler
            notifications_dir = Path("/tmp/scheduler_notifications")
            notifications_dir.mkdir(exist_ok=True)
            
            notification_file = notifications_dir / f"notify_{int(time.time())}.json"
            with open(notification_file, 'w') as f:
                json.dump(notification, f, indent=2)
            
            print(f"📧 Scheduler notification sent: {notification['priority']} priority")
            
        except Exception as e:
            print(f"❌ Scheduler notification error: {e}")
    
    def calculate_task_priority_from_path(self, task_path):
        """Calculate task priority based on file path and name"""
        if "critical" in str(task_path).lower():
            return "high"
        elif "system" in str(task_path).lower() or "/s/" in str(task_path):
            return "high"
        elif "optimize" in str(task_path).lower() or "evolve" in str(task_path).lower():
            return "medium"
        else:
            return "normal"
    
    def restart_agent(self, agent_path):
        """Restart modified agent"""
        print(f"🔄 Restarting agent: {agent_path}")
        
        try:
            agent_file = Path(agent_path)
            agent_name = agent_file.stem
            
            # Create restart command
            restart_command = {
                "type": "agent_restart",
                "agent_name": agent_name,
                "agent_path": str(agent_path),
                "timestamp": time.time(),
                "reason": "file_modification"
            }
            
            # Check if agent is currently running
            if self.is_agent_running(agent_name):
                restart_command["was_running"] = True
                restart_command["action"] = "restart"
                print(f"🔄 Agent {agent_name} is running, scheduling restart")
            else:
                restart_command["was_running"] = False
                restart_command["action"] = "start"
                print(f"▶️ Agent {agent_name} not running, scheduling start")
            
            # Send restart command to coordinator
            commands_dir = Path("/tmp/coordinator_commands")
            commands_dir.mkdir(exist_ok=True)
            
            command_file = commands_dir / f"restart_{agent_name}_{int(time.time())}.json"
            with open(command_file, 'w') as f:
                json.dump(restart_command, f, indent=2)
            
            print(f"📋 Agent restart command queued: {agent_name}")
            
        except Exception as e:
            print(f"❌ Agent restart error: {e}")
    
    def is_agent_running(self, agent_name):
        """Check if an agent is currently running"""
        try:
            import subprocess
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            return f"{agent_name}.py" in result.stdout
        except:
            return False
    
    def monitor_symbolic_changes(self):
        """Monitor symbolic changes in the system"""
        while self.running:
            try:
                # Monitor for symbolic self-modifications
                self.check_symbolic_mutations()
                
                # Monitor for recursive changes
                self.check_recursive_modifications()
                
            except Exception as e:
                print(f"❌ Symbolic monitoring error: {e}")
            
            time.sleep(5)  # Symbolic monitoring every 5 seconds
    
    def check_symbolic_mutations(self):
        """Check for symbolic mutations in the system"""
        # Placeholder for symbolic mutation detection
        pass
    
    def check_recursive_modifications(self):
        """Check for recursive self-modifications"""
        # Placeholder for recursive modification detection
        pass
    
    def get_status(self):
        """Get reflex daemon status"""
        return {
            "running": self.running,
            "monitored_paths": len(self.watch_paths),
            "tracked_files": len(self.file_states),
            "pending_responses": len(self.response_queue),
            "total_reactions": len(self.reactions)
        }
    
    def stop(self):
        """Stop the reflex daemon"""
        print("🛑 Stopping Reflex Daemon...")
        self.running = False
        
        # Stop all observers
        for observer in self.observers:
            observer.stop()
            observer.join()

if __name__ == "__main__":
    # Install watchdog if not available
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("❌ watchdog package required. Install with: pip install watchdog")
        exit(1)
    
    daemon = ReflexDaemon()
    try:
        daemon.start()
        # Keep daemon running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
        print("👋 Reflex Daemon stopped.")
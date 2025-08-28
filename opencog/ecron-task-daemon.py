#!/usr/bin/env python3
"""
Ecron Task Daemon - AGI-OS Task Dispatcher

Listens to /kernels/ecron/ for symbolic task specifications
Parses them and sends commands to CogServer via telnet or IPC socket
"""

import os
import time
import json
import socket
import threading
from pathlib import Path

class EcronTaskDaemon:
    def __init__(self, ecron_path="/tmp/ecron_tasks", cog_host="localhost", cog_port=17001):
        self.ecron_path = Path(ecron_path)
        self.cog_host = cog_host
        self.cog_port = cog_port
        self.running = False
        self.feedback_queue = []
        self.processed_tasks = []
        
        # Ensure ecron task directory exists
        self.ecron_path.mkdir(parents=True, exist_ok=True)
        
    def start(self):
        """Start the task daemon"""
        print("🚀 Starting Ecron Task Daemon...")
        self.running = True
        
        # Start file watcher thread
        watcher_thread = threading.Thread(target=self.watch_ecron_files)
        watcher_thread.daemon = True
        watcher_thread.start()
        
        print(f"📁 Watching {self.ecron_path} for task specifications")
        
    def watch_ecron_files(self):
        """Watch for new ecron task files"""
        while self.running:
            try:
                if self.ecron_path.exists():
                    for task_file in self.ecron_path.glob("*.json"):
                        self.process_task_file(task_file)
            except Exception as e:
                print(f"❌ Error watching files: {e}")
            time.sleep(1)
            
    def process_task_file(self, task_file):
        """Process a symbolic task specification file"""
        try:
            print(f"📋 Processing task file: {task_file}")
            with open(task_file, 'r') as f:
                task_spec = json.load(f)
            
            # Validate task specification
            if not self.validate_task_spec(task_spec):
                print(f"❌ Invalid task specification in {task_file}")
                self.archive_invalid_task(task_file, "Invalid task specification")
                return
            
            # Extract task information
            flow = task_spec.get('flow', 'unknown')
            space = task_spec.get('space', 'e')
            symbolic_expr = task_spec.get('symbolic', '')
            action = task_spec.get('action', 'evaluate')
            
            print(f"🎯 Processing {flow} in {space} space")
            print(f"🔮 Symbolic expression: {symbolic_expr}")
            
            # Process based on space
            result = self.process_by_space(flow, space)
            
            # Send to CogServer
            self.send_to_cogserver(symbolic_expr, f"{action}_in_{space}")
            
            # Store processed task and create feedback
            self.processed_tasks.append({
                'task': task_spec,
                'result': result,
                'timestamp': time.time(),
                'space': space
            })
            
            # Generate feedback
            self.generate_feedback(task_spec, result)
            
            # Archive processed file
            task_file.rename(task_file.with_suffix('.processed'))
            
        except Exception as e:
            print(f"❌ Error processing {task_file}: {e}")
            self.archive_invalid_task(task_file, f"Processing error: {e}")
    
    def validate_task_spec(self, task_spec):
        """Validate task specification format and content"""
        required_fields = ['flow', 'space', 'action']
        
        # Check required fields
        for field in required_fields:
            if field not in task_spec:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate space
        valid_spaces = ['u', 'e', 's']
        if task_spec['space'] not in valid_spaces:
            print(f"❌ Invalid space: {task_spec['space']}. Must be one of {valid_spaces}")
            return False
        
        # Validate flow name
        flow = task_spec['flow']
        if not isinstance(flow, str) or len(flow) == 0:
            print(f"❌ Invalid flow name: {flow}")
            return False
        
        # Validate action
        valid_actions = ['evaluate', 'evolve', 'optimize', 'test', 'meta_evolve']
        if task_spec['action'] not in valid_actions:
            print(f"❌ Invalid action: {task_spec['action']}. Must be one of {valid_actions}")
            return False
        
        # Validate symbolic expression if present
        if 'symbolic' in task_spec:
            symbolic = task_spec['symbolic']
            if not isinstance(symbolic, str):
                print(f"❌ Invalid symbolic expression type: {type(symbolic)}")
                return False
        
        return True
    
    def archive_invalid_task(self, task_file, reason):
        """Archive invalid task with error information"""
        try:
            error_info = {
                "original_file": str(task_file),
                "error_reason": reason,
                "timestamp": time.time()
            }
            
            # Save error info
            error_file = task_file.with_suffix('.error')
            with open(error_file, 'w') as f:
                json.dump(error_info, f, indent=2)
            
            # Remove original file
            task_file.unlink()
            print(f"📁 Archived invalid task to {error_file}")
            
        except Exception as e:
            print(f"❌ Error archiving invalid task: {e}")
    
    def process_by_space(self, flow, space):
        """Process task according to symbolic space"""
        if space == "u":
            return self.process_user_space(flow)
        elif space == "e":
            return self.process_execution_space(flow)
        elif space == "s":
            return self.process_system_space(flow)
        else:
            return self.process_default(flow)
    
    def process_user_space(self, flow):
        """Process user space symbolic flow"""
        print("👤 User space processing")
        return {"space": "user", "processed": flow, "interactive": True}
    
    def process_execution_space(self, flow):
        """Process execution space symbolic flow"""
        print("⚡ Execution space processing")
        return {"space": "execution", "processed": flow, "runtime": True}
    
    def process_system_space(self, flow):
        """Process system space symbolic flow"""
        print("🔧 System space processing")
        return {"space": "system", "processed": flow, "meta": True}
    
    def process_default(self, flow):
        """Default processing"""
        print("🔄 Default processing")
        return {"space": "default", "processed": flow}
    
    def generate_feedback(self, task_data, result):
        """Generate feedback for the symbolic memory system"""
        feedback = {
            "type": "task_completion",
            "original_task": task_data,
            "result": result,
            "timestamp": time.time(),
            "feedback_id": len(self.feedback_queue)
        }
        
        self.feedback_queue.append(feedback)
        print(f"🔄 Generated feedback: {feedback['feedback_id']}")
        
        # Limit feedback queue size
        if len(self.feedback_queue) > 100:
            self.feedback_queue = self.feedback_queue[-50:]
            
    def send_to_cogserver(self, expr, action):
        """Send command to CogServer via telnet/socket"""
        try:
            print(f"📡 Sending to CogServer: {action}({expr})")
            
            # Try to connect to CogServer via telnet
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # 5 second timeout
            
            try:
                sock.connect((self.cog_host, self.cog_port))
                
                # Send scheme command to CogServer
                command = f"(cog-evaluate! (ParseNode \"{action}\" (ConceptNode \"{expr}\")))\n"
                sock.send(command.encode('utf-8'))
                
                # Read response
                response = sock.recv(1024).decode('utf-8')
                print(f"🧠 CogServer response: {response.strip()}")
                
                sock.close()
                return True
                
            except socket.error as se:
                # CogServer not available, fall back to file-based communication
                print(f"⚠️ CogServer not available ({se}), using file-based fallback")
                return self.send_to_cogserver_file(expr, action)
                
        except Exception as e:
            print(f"❌ CogServer connection error: {e}")
            return False
    
    def send_to_cogserver_file(self, expr, action):
        """Fallback: Send command via file-based interface"""
        try:
            # Create OpenCog command file
            cog_commands_dir = Path("/tmp/cogserver_commands")
            cog_commands_dir.mkdir(exist_ok=True)
            
            command_data = {
                "action": action,
                "expression": expr,
                "timestamp": time.time(),
                "source": "ecron-task-daemon"
            }
            
            command_file = cog_commands_dir / f"cmd_{int(time.time())}_{action}.json"
            with open(command_file, 'w') as f:
                json.dump(command_data, f, indent=2)
                
            print(f"📁 Command queued for CogServer: {command_file}")
            return True
            
        except Exception as e:
            print(f"❌ File-based CogServer communication error: {e}")
            return False
            
    def stop(self):
        """Stop the daemon"""
        print("🛑 Stopping Ecron Task Daemon...")
        self.running = False

if __name__ == "__main__":
    daemon = EcronTaskDaemon()
    try:
        daemon.start()
        # Keep daemon running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
        print("👋 Ecron Task Daemon stopped.")
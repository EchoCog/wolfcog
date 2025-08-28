#!/usr/bin/env python3
"""
Scheduler Daemon - Main scheduling engine for WolfCog AGI-OS
Runs ecron and schedules symbolic flows across the AGI system
"""

import time
import threading
import subprocess
import json
from pathlib import Path

class SchedulerDaemon:
    def __init__(self):
        self.running = False
        self.ecron_process = None
        self.task_queue = []
        self.active_flows = {}
        self.priorities = {}
        
    def start(self):
        """Start the scheduler daemon"""
        print("⏰ Starting Scheduler Daemon...")
        self.running = True
        
        # Start ecron scheduler thread
        ecron_thread = threading.Thread(target=self.run_ecron_scheduler)
        ecron_thread.daemon = True
        ecron_thread.start()
        
        # Start flow management thread
        flow_thread = threading.Thread(target=self.manage_flows)
        flow_thread.daemon = True
        flow_thread.start()
        
        # Start priority management thread
        priority_thread = threading.Thread(target=self.manage_priorities)
        priority_thread.daemon = True
        priority_thread.start()
        
        print("📅 Scheduler Daemon managing symbolic flows...")
    
    def run_ecron_scheduler(self):
        """Run the ecron symbolic scheduler"""
        while self.running:
            try:
                print("🔄 Running Ecron symbolic scheduler cycle...")
                
                # Simulate ecron execution (in real implementation would call Wolfram)
                self.process_symbolic_tasks()
                
                # Check for new tasks from ecron output
                self.collect_scheduled_tasks()
                
            except Exception as e:
                print(f"❌ Ecron scheduler error: {e}")
            
            time.sleep(5)  # Scheduler cycle every 5 seconds
    
    def process_symbolic_tasks(self):
        """Process symbolic tasks through ecron"""
        task_path = Path("/tmp/ecron_tasks")
        if task_path.exists():
            for task_file in task_path.glob("*.json"):
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    
                    # Schedule the task
                    self.schedule_task(task_data)
                    
                except Exception as e:
                    print(f"❌ Error processing task {task_file}: {e}")
    
    def schedule_task(self, task_data):
        """Schedule a symbolic task"""
        task_id = f"task_{len(self.task_queue)}"
        priority = self.calculate_priority(task_data)
        
        scheduled_task = {
            "id": task_id,
            "data": task_data,
            "priority": priority,
            "scheduled_time": time.time(),
            "status": "scheduled"
        }
        
        self.task_queue.append(scheduled_task)
        self.priorities[task_id] = priority
        
        print(f"📋 Scheduled task {task_id} with priority {priority}")
    
    def calculate_priority(self, task_data):
        """Calculate task priority based on space and type"""
        space = task_data.get("space", "e")
        flow_type = task_data.get("flow", "default")
        
        # Priority matrix
        space_priority = {"s": 1, "e": 2, "u": 3}  # System > Execution > User
        
        base_priority = space_priority.get(space, 2)
        
        # Adjust based on flow type
        if "critical" in str(flow_type):
            base_priority -= 1
        elif "background" in str(flow_type):
            base_priority += 1
            
        return max(1, base_priority)  # Ensure priority is at least 1
    
    def collect_scheduled_tasks(self):
        """Collect tasks that have been scheduled by ecron"""
        # Sort tasks by priority
        self.task_queue.sort(key=lambda x: x["priority"])
        
        # Process high priority tasks first
        while self.task_queue and self.task_queue[0]["priority"] <= 2:
            task = self.task_queue.pop(0)
            self.execute_task(task)
    
    def execute_task(self, task):
        """Execute a scheduled task"""
        task_id = task["id"]
        print(f"⚡ Executing task: {task_id}")
        
        task["status"] = "executing"
        task["execution_time"] = time.time()
        
        # Add to active flows
        self.active_flows[task_id] = task
        
        # Simulate task execution
        execution_thread = threading.Thread(target=self.simulate_execution, args=(task,))
        execution_thread.daemon = True
        execution_thread.start()
    
    def simulate_execution(self, task):
        """Simulate task execution"""
        task_id = task["id"]
        
        # Simulate variable execution time based on complexity
        execution_time = 1 + (task["priority"] * 0.5)
        time.sleep(execution_time)
        
        # Mark as completed
        task["status"] = "completed"
        task["completion_time"] = time.time()
        
        print(f"✅ Completed task: {task_id}")
        
        # Remove from active flows
        if task_id in self.active_flows:
            del self.active_flows[task_id]
    
    def manage_flows(self):
        """Manage symbolic flow coordination"""
        while self.running:
            try:
                # Monitor active flows
                self.monitor_active_flows()
                
                # Coordinate with other daemons
                self.coordinate_flows()
                
            except Exception as e:
                print(f"❌ Flow management error: {e}")
            
            time.sleep(3)  # Flow management cycle every 3 seconds
    
    def monitor_active_flows(self):
        """Monitor active symbolic flows"""
        if self.active_flows:
            print(f"🌊 Monitoring {len(self.active_flows)} active flows")
            
            # Check for stalled flows
            current_time = time.time()
            for task_id, task in list(self.active_flows.items()):
                execution_time = current_time - task.get("execution_time", current_time)
                if execution_time > 30:  # 30 second timeout
                    print(f"⚠️ Flow {task_id} appears stalled")
                    self.handle_stalled_flow(task_id)
    
    def handle_stalled_flow(self, task_id):
        """Handle a stalled flow"""
        print(f"🔄 Handling stalled flow: {task_id}")
        
        if task_id in self.active_flows:
            task = self.active_flows[task_id]
            task["status"] = "stalled"
            
            # Reschedule with lower priority
            task["priority"] += 1
            self.task_queue.append(task)
            
            del self.active_flows[task_id]
    
    def coordinate_flows(self):
        """Coordinate flows with other system components"""
        try:
            # Check for coordination signals from other daemons
            self.process_coordination_signals()
            
            # Coordinate with OpenCog AtomSpace
            self.coordinate_with_cogserver()
            
            # Coordinate with agent systems
            self.coordinate_with_agents()
            
            # Coordinate with reflex daemon
            self.coordinate_with_reflex_daemon()
            
        except Exception as e:
            print(f"❌ Flow coordination error: {e}")
    
    def process_coordination_signals(self):
        """Process coordination signals from other components"""
        signals_dir = Path("/tmp/wolfcog_signals")
        if not signals_dir.exists():
            return
        
        for signal_file in signals_dir.glob("signal_*.json"):
            try:
                with open(signal_file, 'r') as f:
                    signal_data = json.load(f)
                
                signal_type = signal_data.get("type")
                
                if signal_type == "kernel_reload":
                    self.handle_kernel_reload_signal(signal_data)
                elif signal_type == "priority_change":
                    self.handle_priority_change_signal(signal_data)
                elif signal_type == "flow_optimization":
                    self.handle_flow_optimization_signal(signal_data)
                
                # Remove processed signal
                signal_file.unlink()
                
            except Exception as e:
                print(f"⚠️ Error processing signal {signal_file}: {e}")
    
    def handle_kernel_reload_signal(self, signal_data):
        """Handle kernel reload signal"""
        kernel_name = signal_data.get("kernel")
        print(f"🔄 Handling kernel reload: {kernel_name}")
        
        # Pause tasks that depend on this kernel
        affected_tasks = []
        for task in self.task_queue:
            task_data = task.get("data", {})
            if kernel_name in str(task_data):
                task["status"] = "paused_for_kernel_reload"
                affected_tasks.append(task)
        
        print(f"⏸️ Paused {len(affected_tasks)} tasks for kernel reload")
    
    def handle_priority_change_signal(self, signal_data):
        """Handle priority change signal"""
        task_pattern = signal_data.get("task_pattern")
        new_priority = signal_data.get("priority", 2)
        
        updated_count = 0
        for task in self.task_queue:
            if task_pattern in str(task.get("data", {})):
                task["priority"] = new_priority
                updated_count += 1
        
        print(f"⚡ Updated priority for {updated_count} tasks")
    
    def handle_flow_optimization_signal(self, signal_data):
        """Handle flow optimization signal"""
        optimization_type = signal_data.get("optimization")
        
        if optimization_type == "batch_similar":
            self.batch_similar_tasks()
        elif optimization_type == "reorder_by_dependency":
            self.reorder_by_dependencies()
        
        print(f"🔧 Applied flow optimization: {optimization_type}")
    
    def coordinate_with_cogserver(self):
        """Coordinate task flows with OpenCog CogServer"""
        # Check for CogServer command responses
        cog_commands_dir = Path("/tmp/cogserver_commands")
        if cog_commands_dir.exists():
            processed_commands = len(list(cog_commands_dir.glob("*.json")))
            if processed_commands > 0:
                print(f"🧠 CogServer coordination: {processed_commands} commands pending")
        
        # Send scheduler status to CogServer
        if len(self.active_flows) > 0:
            self.send_scheduler_status_to_cog()
    
    def send_scheduler_status_to_cog(self):
        """Send scheduler status to CogServer"""
        status_data = {
            "active_flows": len(self.active_flows),
            "queued_tasks": len(self.task_queue),
            "timestamp": time.time(),
            "scheduler_status": "active"
        }
        
        # Create CogServer status command
        cog_commands_dir = Path("/tmp/cogserver_commands")
        cog_commands_dir.mkdir(exist_ok=True)
        
        status_file = cog_commands_dir / f"scheduler_status_{int(time.time())}.json"
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def coordinate_with_agents(self):
        """Coordinate with agent systems"""
        # Check for agent coordination requests
        agent_requests_dir = Path("/tmp/agent_requests")
        if agent_requests_dir.exists():
            for request_file in agent_requests_dir.glob("*.json"):
                try:
                    with open(request_file, 'r') as f:
                        request_data = json.load(f)
                    
                    self.handle_agent_request(request_data)
                    request_file.unlink()
                    
                except Exception as e:
                    print(f"⚠️ Error processing agent request: {e}")
    
    def handle_agent_request(self, request_data):
        """Handle coordination request from agents"""
        request_type = request_data.get("type")
        
        if request_type == "task_priority_boost":
            task_pattern = request_data.get("task_pattern")
            self.boost_task_priority(task_pattern)
        elif request_type == "schedule_optimization":
            optimization_params = request_data.get("params", {})
            self.apply_scheduling_optimization(optimization_params)
        elif request_type == "flow_analysis":
            self.provide_flow_analysis_to_agent(request_data.get("agent_id"))
    
    def boost_task_priority(self, task_pattern):
        """Boost priority of tasks matching pattern"""
        boosted_count = 0
        for task in self.task_queue:
            if task_pattern in str(task.get("data", {})):
                task["priority"] = max(1, task["priority"] - 1)
                boosted_count += 1
        
        print(f"⚡ Boosted priority for {boosted_count} tasks")
    
    def apply_scheduling_optimization(self, params):
        """Apply scheduling optimization based on agent recommendations"""
        optimization_type = params.get("type", "default")
        
        if optimization_type == "load_balance":
            self.balance_task_load()
        elif optimization_type == "minimize_latency":
            self.minimize_task_latency()
        elif optimization_type == "maximize_throughput":
            self.maximize_task_throughput()
    
    def balance_task_load(self):
        """Balance task load across different execution contexts"""
        # Group tasks by space
        space_groups = {'u': [], 'e': [], 's': []}
        
        for task in self.task_queue:
            space = task.get("data", {}).get("space", "e")
            if space in space_groups:
                space_groups[space].append(task)
        
        # Rebalance if one space is overloaded
        max_space = max(space_groups.keys(), key=lambda k: len(space_groups[k]))
        min_space = min(space_groups.keys(), key=lambda k: len(space_groups[k]))
        
        if len(space_groups[max_space]) > len(space_groups[min_space]) + 3:
            # Move some tasks to balance load
            tasks_to_move = space_groups[max_space][:2]
            for task in tasks_to_move:
                task["data"]["space"] = min_space
            
            print(f"⚖️ Balanced load: moved 2 tasks from {max_space} to {min_space}")
    
    def coordinate_with_reflex_daemon(self):
        """Coordinate with reflex daemon"""
        # Check for reflex notifications
        notifications_dir = Path("/tmp/scheduler_notifications")
        if notifications_dir.exists():
            for notification_file in notifications_dir.glob("notify_*.json"):
                try:
                    with open(notification_file, 'r') as f:
                        notification_data = json.load(f)
                    
                    self.handle_reflex_notification(notification_data)
                    notification_file.unlink()
                    
                except Exception as e:
                    print(f"⚠️ Error processing reflex notification: {e}")
    
    def handle_reflex_notification(self, notification_data):
        """Handle notification from reflex daemon"""
        notification_type = notification_data.get("type")
        
        if notification_type == "new_task":
            task_path = notification_data.get("task_path")
            priority = notification_data.get("priority", "normal")
            
            print(f"📨 Reflex daemon reports new task: {task_path} ({priority} priority)")
            
            # Adjust scheduling based on reflex priority
            if priority == "high":
                self.expedite_task_processing(task_path)
    
    def expedite_task_processing(self, task_path):
        """Expedite processing of a specific task"""
        task_name = Path(task_path).name
        
        # Find matching tasks in queue and boost priority
        for task in self.task_queue:
            if task_name in str(task.get("data", {})):
                task["priority"] = 1  # Highest priority
                print(f"⚡ Expedited task: {task_name}")
                break
    
    def manage_priorities(self):
        """Manage task priorities and dependencies"""
        while self.running:
            try:
                # Adjust priorities based on system state
                self.adjust_priorities()
                
                # Handle dependencies
                self.resolve_dependencies()
                
            except Exception as e:
                print(f"❌ Priority management error: {e}")
            
            time.sleep(10)  # Priority adjustment every 10 seconds
    
    def adjust_priorities(self):
        """Adjust task priorities based on system state"""
        # Increase priority of old tasks
        current_time = time.time()
        for task in self.task_queue:
            age = current_time - task["scheduled_time"]
            if age > 60:  # Tasks older than 1 minute
                task["priority"] = max(1, task["priority"] - 1)
                print(f"⬆️ Increased priority for aged task: {task['id']}")
    
    def resolve_dependencies(self):
        """Resolve task dependencies"""
        deps_file = Path("/tmp/ecron_tasks/dependencies.json")
        
        if not deps_file.exists():
            return
        
        try:
            with open(deps_file, 'r') as f:
                dependencies = json.load(f)
            
            # Process dependency chains
            for chain in dependencies.get("chains", []):
                self.process_dependency_chain(chain)
            
            # Process prerequisites
            prerequisites = dependencies.get("prerequisites", {})
            self.process_task_prerequisites(prerequisites)
            
        except Exception as e:
            print(f"❌ Dependency resolution error: {e}")
    
    def process_dependency_chain(self, chain):
        """Process a dependency chain"""
        chain_order = chain.get("order", [])
        
        if len(chain_order) < 2:
            return
        
        # Ensure tasks execute in dependency order
        for i in range(len(chain_order) - 1):
            current_stage = chain_order[i]
            next_stage = chain_order[i + 1]
            
            # Find tasks in current and next stages
            current_tasks = [t for t in self.task_queue if current_stage in str(t.get("data", {}))]
            next_tasks = [t for t in self.task_queue if next_stage in str(t.get("data", {}))]
            
            # Set dependencies
            for next_task in next_tasks:
                next_task["depends_on"] = current_stage
                next_task["priority"] += 1  # Lower priority until dependency met
        
        print(f"🔗 Processed dependency chain: {' → '.join(chain_order)}")
    
    def process_task_prerequisites(self, prerequisites):
        """Process task prerequisites"""
        for task_name, prereq_info in prerequisites.items():
            must_complete_before = prereq_info.get("must_complete_before")
            
            # Find prerequisite and dependent tasks
            prereq_tasks = [t for t in self.task_queue if task_name in str(t.get("data", {}))]
            dependent_tasks = [t for t in self.task_queue if must_complete_before in str(t.get("data", {}))]
            
            # Adjust priorities
            for prereq_task in prereq_tasks:
                prereq_task["priority"] = 1  # Highest priority
            
            for dependent_task in dependent_tasks:
                dependent_task["priority"] += 2  # Lower priority
                dependent_task["depends_on"] = task_name
        
        print(f"📋 Processed {len(prerequisites)} task prerequisites")
    
    def get_status(self):
        """Get scheduler daemon status"""
        return {
            "running": self.running,
            "queue_size": len(self.task_queue),
            "active_flows": len(self.active_flows),
            "total_priorities": len(self.priorities)
        }
    
    def stop(self):
        """Stop the scheduler daemon"""
        print("🛑 Stopping Scheduler Daemon...")
        self.running = False
        
        if self.ecron_process:
            self.ecron_process.terminate()

if __name__ == "__main__":
    daemon = SchedulerDaemon()
    try:
        daemon.start()
        # Keep daemon running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()
        print("👋 Scheduler Daemon stopped.")
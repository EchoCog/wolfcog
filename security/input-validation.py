#!/usr/bin/env python3
"""
WolfCog Input Validation and Safety System
Comprehensive input validation, sanitization, and safety enforcement
"""

import re
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

class WolfCogInputValidator:
    """Comprehensive input validation and safety system for WolfCog"""
    
    def __init__(self):
        self.validation_rules = self.load_validation_rules()
        self.safety_limits = self.load_safety_limits()
        self.violation_log = []
        
    def load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for different input types"""
        return {
            "task_spec": {
                "required_fields": ["flow", "space", "action"],
                "valid_spaces": ["u", "e", "s"],
                "valid_actions": ["evaluate", "evolve", "optimize", "test", "meta_evolve"],
                "max_flow_length": 100,
                "max_symbolic_length": 1000,
                "allowed_symbolic_chars": r"[∇∂⊗ΦΩ∑αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]",
                "forbidden_patterns": [
                    r"<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>",  # Script injection
                    r"javascript:",  # JavaScript URLs
                    r"eval\s*\(",  # Eval calls
                    r"exec\s*\(",  # Exec calls
                    r"__import__",  # Import injection
                    r"system\s*\(",  # System calls
                    r"subprocess",  # Subprocess calls
                    r"os\.system",  # OS system calls
                    r"rm\s+-rf",  # Dangerous file operations
                    r"\.\.\/",  # Path traversal
                ]
            },
            "agent_command": {
                "max_length": 500,
                "allowed_commands": [
                    "status", "restart", "stop", "start", "optimize", 
                    "coordinate", "analyze", "report", "monitor"
                ],
                "forbidden_commands": [
                    "delete", "destroy", "corrupt", "hack", "exploit",
                    "shell", "bash", "cmd", "powershell"
                ]
            },
            "memory_path": {
                "max_depth": 10,
                "allowed_extensions": [".txt", ".json", ".scm", ".lisp", ".wl", ".py", ".md"],
                "forbidden_paths": [
                    "/etc/passwd", "/etc/shadow", "/boot", "/sys", "/proc",
                    "/.ssh", "/root", "/home/*/.ssh"
                ],
                "max_path_length": 255
            },
            "symbolic_expression": {
                "max_length": 2000,
                "max_nesting_depth": 20,
                "allowed_functions": [
                    "∇", "∂", "⊗", "Φ", "Ω", "∑", "sin", "cos", "exp", "log",
                    "D", "Integrate", "Simplify", "Expand", "Factor"
                ],
                "forbidden_functions": [
                    "Delete", "DeleteFile", "DeleteDirectory", "Run", "RunProcess",
                    "Import", "Export", "Get", "Put", "OpenWrite", "SystemOpen"
                ]
            }
        }
    
    def load_safety_limits(self) -> Dict[str, Any]:
        """Load safety limits for system operations"""
        return {
            "max_task_rate": 10,  # tasks per second
            "max_memory_usage": 1024 * 1024 * 1024,  # 1GB
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "max_recursion_depth": 15,
            "max_concurrent_operations": 50,
            "max_symbolic_complexity": 1000,
            "rate_limit_window": 60,  # seconds
            "max_violations_per_hour": 10
        }
    
    def validate_task_specification(self, task_spec: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate task specification input"""
        errors = []
        rules = self.validation_rules["task_spec"]
        
        # Check required fields
        for field in rules["required_fields"]:
            if field not in task_spec:
                errors.append(f"Missing required field: {field}")
        
        # Validate space
        if "space" in task_spec:
            if task_spec["space"] not in rules["valid_spaces"]:
                errors.append(f"Invalid space: {task_spec['space']}. Must be one of {rules['valid_spaces']}")
        
        # Validate action
        if "action" in task_spec:
            if task_spec["action"] not in rules["valid_actions"]:
                errors.append(f"Invalid action: {task_spec['action']}. Must be one of {rules['valid_actions']}")
        
        # Validate flow name
        if "flow" in task_spec:
            flow = task_spec["flow"]
            if not isinstance(flow, str):
                errors.append("Flow must be a string")
            elif len(flow) > rules["max_flow_length"]:
                errors.append(f"Flow name too long: {len(flow)} > {rules['max_flow_length']}")
            elif not self.is_safe_string(flow):
                errors.append("Flow name contains unsafe characters")
        
        # Validate symbolic expression
        if "symbolic" in task_spec:
            symbolic = task_spec["symbolic"]
            if isinstance(symbolic, str):
                if len(symbolic) > rules["max_symbolic_length"]:
                    errors.append(f"Symbolic expression too long: {len(symbolic)} > {rules['max_symbolic_length']}")
                
                # Check for forbidden patterns
                for pattern in rules["forbidden_patterns"]:
                    if re.search(pattern, symbolic, re.IGNORECASE):
                        errors.append(f"Forbidden pattern detected in symbolic expression")
                        self.log_security_violation("forbidden_pattern", pattern, symbolic)
        
        return len(errors) == 0, errors
    
    def validate_agent_command(self, command: str, agent_type: str = "") -> Tuple[bool, List[str]]:
        """Validate agent command input"""
        errors = []
        rules = self.validation_rules["agent_command"]
        
        if len(command) > rules["max_length"]:
            errors.append(f"Command too long: {len(command)} > {rules['max_length']}")
        
        # Check for forbidden commands
        for forbidden in rules["forbidden_commands"]:
            if forbidden.lower() in command.lower():
                errors.append(f"Forbidden command detected: {forbidden}")
                self.log_security_violation("forbidden_command", forbidden, command)
        
        # Check command injection patterns
        injection_patterns = [
            r";\s*\w+",  # Command chaining
            r"\|\s*\w+",  # Pipe to command
            r"&&\s*\w+",  # AND command
            r"\|\|\s*\w+",  # OR command
            r"`[^`]+`",  # Backtick execution
            r"\$\([^)]+\)"  # Command substitution
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, command):
                errors.append("Potential command injection detected")
                self.log_security_violation("command_injection", pattern, command)
        
        return len(errors) == 0, errors
    
    def validate_memory_path(self, path: str) -> Tuple[bool, List[str]]:
        """Validate memory/file path input"""
        errors = []
        rules = self.validation_rules["memory_path"]
        
        if len(path) > rules["max_path_length"]:
            errors.append(f"Path too long: {len(path)} > {rules['max_path_length']}")
        
        # Check for forbidden paths
        for forbidden in rules["forbidden_paths"]:
            if path.startswith(forbidden.replace("*", "")):
                errors.append(f"Access to forbidden path: {forbidden}")
                self.log_security_violation("forbidden_path", forbidden, path)
        
        # Check for path traversal
        if ".." in path:
            errors.append("Path traversal detected")
            self.log_security_violation("path_traversal", "..", path)
        
        # Check path depth
        path_depth = len(Path(path).parts)
        if path_depth > rules["max_depth"]:
            errors.append(f"Path depth exceeds limit: {path_depth} > {rules['max_depth']}")
        
        # Check file extension if it's a file
        if "." in path:
            extension = Path(path).suffix
            if extension and extension not in rules["allowed_extensions"]:
                errors.append(f"Invalid file extension: {extension}")
        
        return len(errors) == 0, errors
    
    def validate_symbolic_expression(self, expression: str) -> Tuple[bool, List[str]]:
        """Validate symbolic mathematical expression"""
        errors = []
        rules = self.validation_rules["symbolic_expression"]
        
        if len(expression) > rules["max_length"]:
            errors.append(f"Expression too long: {len(expression)} > {rules['max_length']}")
        
        # Check nesting depth
        nesting_depth = self.calculate_nesting_depth(expression)
        if nesting_depth > rules["max_nesting_depth"]:
            errors.append(f"Expression nesting too deep: {nesting_depth} > {rules['max_nesting_depth']}")
        
        # Check for forbidden functions
        for forbidden in rules["forbidden_functions"]:
            if forbidden in expression:
                errors.append(f"Forbidden function detected: {forbidden}")
                self.log_security_violation("forbidden_function", forbidden, expression)
        
        # Check complexity
        complexity = self.calculate_symbolic_complexity(expression)
        if complexity > self.safety_limits["max_symbolic_complexity"]:
            errors.append(f"Expression complexity too high: {complexity} > {self.safety_limits['max_symbolic_complexity']}")
        
        return len(errors) == 0, errors
    
    def is_safe_string(self, s: str) -> bool:
        """Check if string contains only safe characters"""
        # Allow alphanumeric, common punctuation, and symbolic mathematical characters
        safe_pattern = r"^[a-zA-Z0-9\s\-_.,!?()[\]{}∇∂⊗ΦΩ∑αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ]+$"
        return re.match(safe_pattern, s) is not None
    
    def calculate_nesting_depth(self, expression: str) -> int:
        """Calculate the maximum nesting depth of brackets/parentheses"""
        max_depth = 0
        current_depth = 0
        
        for char in expression:
            if char in "([{":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in ")]}":
                current_depth = max(0, current_depth - 1)
        
        return max_depth
    
    def calculate_symbolic_complexity(self, expression: str) -> int:
        """Calculate complexity score of symbolic expression"""
        complexity = 0
        
        # Base complexity from length
        complexity += len(expression)
        
        # Add complexity for special symbols
        symbolic_chars = "∇∂⊗ΦΩ∑"
        complexity += sum(expression.count(char) * 10 for char in symbolic_chars)
        
        # Add complexity for nesting
        complexity += self.calculate_nesting_depth(expression) * 5
        
        # Add complexity for function calls
        function_pattern = r"\w+\s*\("
        complexity += len(re.findall(function_pattern, expression)) * 3
        
        return complexity
    
    def sanitize_input(self, input_data: Any, input_type: str = "general") -> Any:
        """Sanitize input data based on type"""
        if isinstance(input_data, str):
            return self.sanitize_string(input_data, input_type)
        elif isinstance(input_data, dict):
            return self.sanitize_dict(input_data, input_type)
        elif isinstance(input_data, list):
            return [self.sanitize_input(item, input_type) for item in input_data]
        else:
            return input_data
    
    def sanitize_string(self, s: str, input_type: str = "general") -> str:
        """Sanitize string input"""
        # Remove null bytes
        s = s.replace('\x00', '')
        
        # Remove control characters except common whitespace
        s = ''.join(char for char in s if ord(char) >= 32 or char in '\t\n\r')
        
        # Limit length based on type
        max_lengths = {
            "task_spec": 1000,
            "agent_command": 500,
            "memory_path": 255,
            "symbolic_expression": 2000,
            "general": 1000
        }
        
        max_length = max_lengths.get(input_type, 1000)
        if len(s) > max_length:
            s = s[:max_length]
        
        return s
    
    def sanitize_dict(self, d: Dict[str, Any], input_type: str = "general") -> Dict[str, Any]:
        """Sanitize dictionary input"""
        sanitized = {}
        
        for key, value in d.items():
            # Sanitize key
            clean_key = self.sanitize_string(str(key), input_type)
            
            # Sanitize value
            clean_value = self.sanitize_input(value, input_type)
            
            sanitized[clean_key] = clean_value
        
        return sanitized
    
    def check_rate_limit(self, operation_type: str, identifier: str = "default") -> bool:
        """Check if operation is within rate limits"""
        current_time = time.time()
        window_start = current_time - self.safety_limits["rate_limit_window"]
        
        # Clean old entries
        self.clean_rate_limit_log(window_start)
        
        # Count recent operations
        recent_ops = self.count_recent_operations(operation_type, identifier, window_start)
        
        if recent_ops >= self.safety_limits["max_task_rate"]:
            self.log_security_violation("rate_limit_exceeded", operation_type, f"{identifier}:{recent_ops}")
            return False
        
        # Log this operation
        self.log_operation(operation_type, identifier, current_time)
        return True
    
    def log_security_violation(self, violation_type: str, details: str, context: str):
        """Log security violation"""
        violation = {
            "timestamp": time.time(),
            "type": violation_type,
            "details": details,
            "context_hash": hashlib.md5(context.encode()).hexdigest(),
            "severity": self.get_violation_severity(violation_type)
        }
        
        self.violation_log.append(violation)
        
        # Log to file
        violations_dir = Path("/tmp/wolfcog_security_violations")
        violations_dir.mkdir(exist_ok=True)
        
        violation_file = violations_dir / f"violation_{int(time.time())}.json"
        with open(violation_file, 'w') as f:
            json.dump(violation, f, indent=2)
        
        print(f"🚨 Security violation logged: {violation_type} - {details}")
    
    def get_violation_severity(self, violation_type: str) -> str:
        """Get severity level for violation type"""
        severity_map = {
            "forbidden_pattern": "high",
            "forbidden_command": "high",
            "command_injection": "critical",
            "forbidden_path": "high",
            "path_traversal": "critical",
            "forbidden_function": "medium",
            "rate_limit_exceeded": "medium"
        }
        return severity_map.get(violation_type, "low")
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        current_time = time.time()
        hour_ago = current_time - 3600
        
        recent_violations = [v for v in self.violation_log if v["timestamp"] > hour_ago]
        
        return {
            "total_violations": len(self.violation_log),
            "recent_violations": len(recent_violations),
            "critical_violations": len([v for v in recent_violations if v["severity"] == "critical"]),
            "high_violations": len([v for v in recent_violations if v["severity"] == "high"]),
            "security_level": self.calculate_security_level(recent_violations),
            "last_violation": max([v["timestamp"] for v in self.violation_log]) if self.violation_log else None
        }
    
    def calculate_security_level(self, recent_violations: List[Dict]) -> str:
        """Calculate current security threat level"""
        if not recent_violations:
            return "secure"
        
        critical_count = len([v for v in recent_violations if v["severity"] == "critical"])
        high_count = len([v for v in recent_violations if v["severity"] == "high"])
        
        if critical_count > 0:
            return "critical"
        elif high_count > 3:
            return "high"
        elif high_count > 0 or len(recent_violations) > 5:
            return "medium"
        else:
            return "low"
    
    # Helper methods for rate limiting
    def clean_rate_limit_log(self, window_start: float):
        """Clean old rate limit log entries"""
        if not hasattr(self, 'rate_limit_log'):
            self.rate_limit_log = []
        
        self.rate_limit_log = [entry for entry in self.rate_limit_log if entry["timestamp"] > window_start]
    
    def count_recent_operations(self, operation_type: str, identifier: str, window_start: float) -> int:
        """Count recent operations of specified type"""
        if not hasattr(self, 'rate_limit_log'):
            return 0
        
        return len([
            entry for entry in self.rate_limit_log
            if (entry["operation_type"] == operation_type and 
                entry["identifier"] == identifier and 
                entry["timestamp"] > window_start)
        ])
    
    def log_operation(self, operation_type: str, identifier: str, timestamp: float):
        """Log an operation for rate limiting"""
        if not hasattr(self, 'rate_limit_log'):
            self.rate_limit_log = []
        
        self.rate_limit_log.append({
            "operation_type": operation_type,
            "identifier": identifier,
            "timestamp": timestamp
        })

# Global validator instance
wolfcog_validator = WolfCogInputValidator()

def validate_input(input_data: Any, input_type: str) -> Tuple[bool, List[str], Any]:
    """
    Validate and sanitize input data
    
    Returns:
        (is_valid, errors, sanitized_data)
    """
    # Sanitize input first
    sanitized_data = wolfcog_validator.sanitize_input(input_data, input_type)
    
    # Validate based on type
    if input_type == "task_spec" and isinstance(sanitized_data, dict):
        is_valid, errors = wolfcog_validator.validate_task_specification(sanitized_data)
    elif input_type == "agent_command" and isinstance(sanitized_data, str):
        is_valid, errors = wolfcog_validator.validate_agent_command(sanitized_data)
    elif input_type == "memory_path" and isinstance(sanitized_data, str):
        is_valid, errors = wolfcog_validator.validate_memory_path(sanitized_data)
    elif input_type == "symbolic_expression" and isinstance(sanitized_data, str):
        is_valid, errors = wolfcog_validator.validate_symbolic_expression(sanitized_data)
    else:
        # Basic validation for unknown types
        is_valid = True
        errors = []
    
    return is_valid, errors, sanitized_data

if __name__ == "__main__":
    # Test the validation system
    print("🛡️ WolfCog Input Validation and Safety System")
    print("=" * 50)
    
    # Test task specification validation
    test_task = {
        "flow": "test_flow",
        "space": "e", 
        "action": "evaluate",
        "symbolic": "∇(x^2 + y^2)"
    }
    
    is_valid, errors, sanitized = validate_input(test_task, "task_spec")
    print(f"Task validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
    if errors:
        for error in errors:
            print(f"  - {error}")
    
    # Test security status
    status = wolfcog_validator.get_security_status()
    print(f"\nSecurity status: {status}")
    
    print("\n✅ Validation system initialized")
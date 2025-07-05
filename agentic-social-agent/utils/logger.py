import logging
import json
import time
import traceback
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import os

class WorkflowLogger:
    """Structured logger for LangGraph workflow with error handling and performance tracking"""
    
    def __init__(self, workflow_id: Optional[str] = None):
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup structured logger with file and console handlers"""
        logger = logging.getLogger(f"workflow_{self.workflow_id}")
        logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        
        # File handler for detailed logs
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(
            f"{log_dir}/workflow_{self.workflow_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler for important messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def log_step_start(self, step_name: str, input_data: Dict[str, Any]) -> None:
        """Log the start of a workflow step"""
        self.logger.info(f"🚀 STEP_START: {step_name}", extra={
            'step_name': step_name,
            'workflow_id': self.workflow_id,
            'input_keys': list(input_data.keys()),
            'timestamp': datetime.now().isoformat()
        })
    
    def log_step_success(self, step_name: str, output_data: Dict[str, Any], duration: float) -> None:
        """Log successful completion of a workflow step"""
        self.logger.info(f"✅ STEP_SUCCESS: {step_name} completed in {duration:.2f}s", extra={
            'step_name': step_name,
            'workflow_id': self.workflow_id,
            'output_keys': list(output_data.keys()),
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_step_error(self, step_name: str, error: Exception, duration: float) -> None:
        """Log error in workflow step with full traceback"""
        error_info = {
            'step_name': step_name,
            'workflow_id': self.workflow_id,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'duration': duration,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.error(f"❌ STEP_ERROR: {step_name} failed after {duration:.2f}s", extra=error_info)
        
        # Also log to console for immediate visibility
        print(f"❌ ERROR in {step_name}: {error}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Error: {type(error).__name__}: {error}")
    
    def log_api_call(self, service: str, endpoint: str, status: str, duration: float, **kwargs) -> None:
        """Log API calls for monitoring and debugging"""
        self.logger.info(f"🌐 API_CALL: {service} {endpoint} - {status} ({duration:.2f}s)", extra={
            'service': service,
            'endpoint': endpoint,
            'status': status,
            'duration': duration,
            'workflow_id': self.workflow_id,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        })
    
    def log_data_metrics(self, step_name: str, metrics: Dict[str, Any]) -> None:
        """Log data processing metrics"""
        self.logger.info(f"📊 DATA_METRICS: {step_name}", extra={
            'step_name': step_name,
            'workflow_id': self.workflow_id,
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    def log_workflow_complete(self, total_duration: float, steps_completed: int, steps_failed: int) -> None:
        """Log workflow completion summary"""
        self.logger.info(f"🎉 WORKFLOW_COMPLETE: {steps_completed} steps, {steps_failed} failed, {total_duration:.2f}s total", extra={
            'workflow_id': self.workflow_id,
            'total_duration': total_duration,
            'steps_completed': steps_completed,
            'steps_failed': steps_failed,
            'timestamp': datetime.now().isoformat()
        })

def with_error_handling(logger: WorkflowLogger, step_name: str):
    """Decorator to add error handling and logging to agent functions"""
    def decorator(func):
        @wraps(func)
        def wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
            step_start = time.time()
            logger.log_step_start(step_name, state)
            
            try:
                # Execute the agent function
                result = func(state)
                
                # Log success
                duration = time.time() - step_start
                logger.log_step_success(step_name, result, duration)
                
                return result
                
            except Exception as e:
                # Log error and return graceful fallback
                duration = time.time() - step_start
                logger.log_step_error(step_name, e, duration)
                
                # Return state with error information
                error_state = {
                    **state,
                    f"{step_name}_error": {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "timestamp": datetime.now().isoformat()
                    },
                    f"{step_name}_status": "failed"
                }
                
                # Add step-specific fallback data
                if step_name == "search_articles":
                    error_state["articles"] = []
                elif step_name == "extract_info":
                    error_state["articles"] = state.get("articles", [])
                elif step_name == "store_articles":
                    error_state["storage_status"] = "failed"
                elif step_name == "embed_articles":
                    error_state["embedding_status"] = "failed"
                elif step_name == "summarize_articles":
                    error_state["summaries"] = {}
                
                return error_state
                
        return wrapper
    return decorator

def create_workflow_logger(workflow_id: Optional[str] = None) -> WorkflowLogger:
    """Factory function to create a workflow logger"""
    return WorkflowLogger(workflow_id) 
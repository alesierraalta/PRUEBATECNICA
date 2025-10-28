#!/bin/bash
# Entrypoint script for LLM Summarization Microservice
# Handles graceful startup, signal handling, and health checks

set -e

# Function to handle shutdown signals
shutdown() {
    echo "Received shutdown signal, gracefully stopping..."
    # Send SIGTERM to uvicorn process
    if [ ! -z "$UVICORN_PID" ]; then
        kill -TERM "$UVICORN_PID" 2>/dev/null || true
        wait "$UVICORN_PID" 2>/dev/null || true
    fi
    echo "Application stopped gracefully"
    exit 0
}

# Set up signal handlers
trap shutdown SIGTERM SIGINT

# Function to wait for dependencies
wait_for_dependencies() {
    echo "Waiting for dependencies to be ready..."
    
    # Wait for Redis if REDIS_URL is set
    if [ ! -z "$REDIS_URL" ]; then
        echo "Waiting for Redis..."
        python -c "
import redis
import time
import os
import sys

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
max_retries = 30
retry_count = 0

while retry_count < max_retries:
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print('Redis is ready')
        sys.exit(0)
    except Exception as e:
        retry_count += 1
        print(f'Redis not ready, retrying... ({retry_count}/{max_retries})')
        time.sleep(2)

print('Redis connection failed after maximum retries')
sys.exit(1)
"
    fi
    
    echo "All dependencies are ready"
}

# Function to run database migrations (if any)
run_migrations() {
    echo "Running migrations..."
    # Add migration commands here if needed
    # python -m alembic upgrade head
    echo "Migrations completed"
}

# Function to preload ML models
preload_models() {
    echo "Preloading ML models..."
    python -c "
import os
os.environ.setdefault('ENABLE_AUTO_EVALUATION', 'true')

try:
    from app.services.evaluation import SummaryEvaluator
    evaluator = SummaryEvaluator()
    print('Evaluation models preloaded successfully')
except Exception as e:
    print(f'Warning: Could not preload evaluation models: {e}')
"
    echo "Model preloading completed"
}

# Function to start the application
start_app() {
    echo "Starting LLM Summarization Microservice..."
    
    # Set default environment variables
    export WORKERS=${WORKERS:-1}
    export HOST=${HOST:-0.0.0.0}
    export PORT=${PORT:-8000}
    export LOG_LEVEL=${LOG_LEVEL:-INFO}
    
    # Build uvicorn command
    UVICORN_CMD="uvicorn app.main:app"
    UVICORN_CMD="$UVICORN_CMD --host $HOST"
    UVICORN_CMD="$UVICORN_CMD --port $PORT"
    UVICORN_CMD="$UVICORN_CMD --workers $WORKERS"
    UVICORN_CMD="$UVICORN_CMD --log-level $LOG_LEVEL"
    
    # Add proxy headers if behind reverse proxy
    if [ "$BEHIND_PROXY" = "true" ]; then
        UVICORN_CMD="$UVICORN_CMD --proxy-headers"
    fi
    
    # Add reload for development
    if [ "$ENVIRONMENT" = "development" ]; then
        UVICORN_CMD="$UVICORN_CMD --reload"
    fi
    
    echo "Running: $UVICORN_CMD"
    
    # Start uvicorn in background
    $UVICORN_CMD &
    UVICORN_PID=$!
    
    # Wait for uvicorn process
    wait $UVICORN_PID
}

# Main execution
main() {
    echo "=== LLM Summarization Microservice Entrypoint ==="
    echo "Environment: ${ENVIRONMENT:-production}"
    echo "Python version: $(python --version)"
    echo "Working directory: $(pwd)"
    echo "User: $(whoami)"
    echo "=================================================="
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Run migrations
    run_migrations
    
    # Preload models
    preload_models
    
    # Start the application
    start_app
}

# Run main function
main "$@"

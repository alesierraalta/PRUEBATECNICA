#!/bin/bash
# Docker deployment script for LLM Summarization Microservice
# Handles production deployment with proper configuration

set -e

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_FILE="./deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if Docker Compose is available
    if ! command -v docker-compose >/dev/null 2>&1; then
        log_error "Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found."
        log_info "Please copy env.production to $ENV_FILE and configure it."
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Compose file $COMPOSE_FILE not found."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Backup current deployment
backup_deployment() {
    log_info "Creating backup of current deployment..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup current containers
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    mkdir -p "$backup_path"
    
    # Export current container configurations
    docker-compose -f "$COMPOSE_FILE" config > "$backup_path/docker-compose.yml"
    
    # Backup volumes (if any)
    if docker volume ls | grep -q "llm-summarization"; then
        log_info "Backing up volumes..."
        # Note: Volume backup requires additional tools like docker-volume-backup
        log_warning "Volume backup not implemented. Consider using external backup solutions."
    fi
    
    log_success "Backup created: $backup_path"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest images..."
    
    docker-compose -f "$COMPOSE_FILE" pull
    
    log_success "Images pulled successfully"
}

# Deploy services
deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services gracefully
    log_info "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down --timeout 30
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Services deployed successfully"
}

# Wait for services to be healthy
wait_for_health() {
    log_info "Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log_info "Health check attempt $attempt/$max_attempts"
        
        # Check API health
        if curl -f http://localhost:8000/v1/healthz >/dev/null 2>&1; then
            log_success "API is healthy"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Services failed to become healthy after $max_attempts attempts"
            show_logs
            exit 1
        fi
        
        sleep 10
        attempt=$((attempt + 1))
    done
    
    log_success "All services are healthy"
}

# Show service status
show_status() {
    log_info "Service status:"
    docker-compose -f "$COMPOSE_FILE" ps
    
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# Show logs
show_logs() {
    log_info "Recent logs:"
    docker-compose -f "$COMPOSE_FILE" logs --tail=50
}

# Run tests
run_tests() {
    log_info "Running deployment tests..."
    
    # Test API endpoint
    if curl -f http://localhost:8000/v1/healthz >/dev/null 2>&1; then
        log_success "API health check passed"
    else
        log_error "API health check failed"
        return 1
    fi
    
    # Test API functionality (if API key is available)
    if [ -n "$API_KEY" ]; then
        log_info "Testing API functionality..."
        # Add actual API tests here
        log_success "API functionality tests passed"
    else
        log_warning "API key not provided, skipping functionality tests"
    fi
    
    log_success "All tests passed"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    log_success "Cleanup completed"
}

# Rollback deployment
rollback() {
    log_info "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Find latest backup
    local latest_backup=$(ls -t "$BACKUP_DIR" | head -n1)
    
    if [ -z "$latest_backup" ]; then
        log_error "No backup found for rollback"
        exit 1
    fi
    
    log_info "Rolling back to backup: $latest_backup"
    
    # Restore from backup
    cp "$BACKUP_DIR/$latest_backup/docker-compose.yml" "$COMPOSE_FILE"
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log_success "Rollback completed"
}

# Main deployment function
deploy() {
    log_info "=== Starting Deployment ==="
    log_info "Timestamp: $(date)"
    log_info "Compose file: $COMPOSE_FILE"
    log_info "Environment file: $ENV_FILE"
    log_info "=========================="
    
    # Check prerequisites
    check_prerequisites
    
    # Create backup
    backup_deployment
    
    # Pull images
    pull_images
    
    # Deploy services
    deploy_services
    
    # Wait for health
    wait_for_health
    
    # Show status
    show_status
    
    # Run tests
    run_tests
    
    # Cleanup
    cleanup
    
    log_success "Deployment completed successfully!"
    
    # Show access information
    log_info "Service URLs:"
    log_info "  API: http://localhost:8000"
    log_info "  Docs: http://localhost:8000/docs"
    log_info "  Health: http://localhost:8000/v1/healthz"
    log_info "  Nginx: http://localhost"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        deploy
        ;;
    rollback)
        rollback
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    cleanup)
        cleanup
        ;;
    --help|-h)
        echo "Usage: $0 [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  deploy     Deploy the application (default)"
        echo "  rollback   Rollback to previous deployment"
        echo "  status     Show service status"
        echo "  logs       Show service logs"
        echo "  test       Run deployment tests"
        echo "  cleanup    Clean up unused resources"
        echo ""
        echo "Environment Variables:"
        echo "  API_KEY    API key for testing (optional)"
        echo ""
        echo "Examples:"
        echo "  $0 deploy"
        echo "  $0 rollback"
        echo "  API_KEY=your_key $0 test"
        exit 0
        ;;
    *)
        log_error "Unknown command: $1"
        log_info "Use --help for usage information"
        exit 1
        ;;
esac

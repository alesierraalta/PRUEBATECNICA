#!/bin/bash
# Docker build script for LLM Summarization Microservice
# Builds optimized production images with proper tagging

set -e

# Configuration
IMAGE_NAME="llm-summarization-api"
VERSION=${1:-latest}
REGISTRY=${2:-""}
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    log_success "Docker is running"
}

# Build the image
build_image() {
    local full_image_name
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    else
        full_image_name="${IMAGE_NAME}:${VERSION}"
    fi
    
    log_info "Building Docker image: $full_image_name"
    
    # Build with build args
    docker build \
        --build-arg BUILD_DATE="$BUILD_DATE" \
        --build-arg GIT_COMMIT="$GIT_COMMIT" \
        --build-arg VERSION="$VERSION" \
        --tag "$full_image_name" \
        --tag "${IMAGE_NAME}:latest" \
        --file Dockerfile \
        .
    
    log_success "Image built successfully: $full_image_name"
}

# Test the image
test_image() {
    local full_image_name
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    else
        full_image_name="${IMAGE_NAME}:${VERSION}"
    fi
    
    log_info "Testing Docker image: $full_image_name"
    
    # Run basic tests
    docker run --rm "$full_image_name" python --version
    docker run --rm "$full_image_name" python -c "import app.main; print('App imports successfully')"
    
    log_success "Image tests passed"
}

# Security scan (if trivy is available)
security_scan() {
    local full_image_name
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    else
        full_image_name="${IMAGE_NAME}:${VERSION}"
    fi
    
    if command -v trivy >/dev/null 2>&1; then
        log_info "Running security scan with Trivy"
        trivy image --severity HIGH,CRITICAL "$full_image_name"
        log_success "Security scan completed"
    else
        log_warning "Trivy not found, skipping security scan"
        log_info "Install Trivy for security scanning: https://aquasecurity.github.io/trivy/"
    fi
}

# Show image information
show_image_info() {
    local full_image_name
    
    if [ -n "$REGISTRY" ]; then
        full_image_name="${REGISTRY}/${IMAGE_NAME}:${VERSION}"
    else
        full_image_name="${IMAGE_NAME}:${VERSION}"
    fi
    
    log_info "Image information:"
    docker images "$full_image_name"
    
    log_info "Image size:"
    docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" "$full_image_name"
}

# Clean up old images
cleanup() {
    log_info "Cleaning up old images..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old versions (keep last 3)
    docker images "${IMAGE_NAME}" --format "{{.Tag}}" | grep -v latest | sort -V | head -n -3 | xargs -r -I {} docker rmi "${IMAGE_NAME}:{}" || true
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    log_info "=== Docker Build Script ==="
    log_info "Image: $IMAGE_NAME"
    log_info "Version: $VERSION"
    log_info "Registry: ${REGISTRY:-local}"
    log_info "Build Date: $BUILD_DATE"
    log_info "Git Commit: $GIT_COMMIT"
    log_info "=========================="
    
    # Check prerequisites
    check_docker
    
    # Build image
    build_image
    
    # Test image
    test_image
    
    # Security scan
    security_scan
    
    # Show image info
    show_image_info
    
    # Cleanup
    cleanup
    
    log_success "Build process completed successfully!"
    
    # Show usage instructions
    log_info "To run the image:"
    log_info "  docker run -p 8000:8000 $IMAGE_NAME:$VERSION"
    log_info ""
    log_info "To run with Docker Compose:"
    log_info "  docker-compose -f docker-compose.prod.yml up -d"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [VERSION] [REGISTRY]"
        echo ""
        echo "Arguments:"
        echo "  VERSION    Image version tag (default: latest)"
        echo "  REGISTRY   Docker registry URL (optional)"
        echo ""
        echo "Examples:"
        echo "  $0                    # Build with 'latest' tag"
        echo "  $0 1.0.0             # Build with '1.0.0' tag"
        echo "  $0 1.0.0 myregistry.io # Build and tag for registry"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac

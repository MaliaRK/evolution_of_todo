#!/bin/bash
# Performance Tuning Script for Todo AI System
# Script to tune system performance for optimal operation

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/todo-app/performance-tuning.log"
CONFIG_FILE="/etc/todo-app/performance.conf"

# Default values
DEFAULT_MAX_CONNECTIONS=1000
DEFAULT_MEMORY_LIMIT="2G"
DEFAULT_CPU_SHARES=512

# Function to log messages
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log_message "INFO" "Checking prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_message "ERROR" "This script must be run as root"
        exit 1
    fi
    
    # Check if required tools are available
    local required_tools=("kubectl" "docker" "sysctl" "free" "df")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_message "ERROR" "Required tool $tool is not installed"
            exit 1
        fi
    done
    
    log_message "INFO" "All prerequisites satisfied"
}

# Function to tune kernel parameters
tune_kernel_parameters() {
    log_message "INFO" "Tuning kernel parameters..."
    
    # Network tuning
    sysctl -w net.core.somaxconn=65535
    sysctl -w net.core.netdev_max_backlog=5000
    sysctl -w net.ipv4.tcp_max_syn_backlog=65535
    sysctl -w net.ipv4.ip_local_port_range="1024 65535"
    sysctl -w net.ipv4.tcp_fin_timeout=30
    sysctl -w net.ipv4.tcp_keepalive_time=1200
    sysctl -w net.ipv4.tcp_keepalive_intvl=60
    sysctl -w net.ipv4.tcp_keepalive_probes=3
    
    # Memory tuning
    sysctl -w vm.swappiness=1
    sysctl -w vm.dirty_ratio=15
    sysctl -w vm.dirty_background_ratio=5
    
    # Apply changes
    sysctl -p
    
    log_message "INFO" "Kernel parameters tuned successfully"
}

# Function to tune Docker daemon
tune_docker_daemon() {
    log_message "INFO" "Tuning Docker daemon..."
    
    # Create Docker daemon configuration directory if it doesn't exist
    mkdir -p /etc/docker
    
    # Create Docker daemon configuration
    cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": {
      "Hard": 64000,
      "Name": "nofile",
      "Soft": 64000
    }
  },
  "max-concurrent-downloads": 10,
  "max-concurrent-uploads": 10,
  "storage-driver": "overlay2",
  "userland-proxy": false
}
EOF
    
    # Restart Docker daemon to apply changes
    systemctl restart docker
    
    log_message "INFO" "Docker daemon tuned successfully"
}

# Function to tune Kubernetes resources
tune_kubernetes_resources() {
    log_message "INFO" "Tuning Kubernetes resources..."
    
    # Get current resource usage
    log_message "INFO" "Current resource usage:"
    kubectl top nodes
    kubectl top pods --all-namespaces
    
    # Scale resources based on current usage
    local cpu_usage=$(kubectl top nodes --no-headers | awk '{sum+=$3} END {print sum/NR}')
    local memory_usage=$(kubectl top nodes --no-headers | awk '{sum+=$5} END {print sum/NR}')
    
    log_message "INFO" "Average CPU usage: $cpu_usage"
    log_message "INFO" "Average memory usage: $memory_usage"
    
    # Adjust resource limits if needed
    if [[ $(echo "$cpu_usage > 80" | bc -l) -eq 1 ]]; then
        log_message "WARNING" "High CPU usage detected, consider scaling up"
        # Scale up deployments
        kubectl scale deployment --all --replicas=2 -n todo-app
    fi
    
    if [[ $(echo "$memory_usage > 85" | bc -l) -eq 1 ]]; then
        log_message "WARNING" "High memory usage detected, consider scaling up"
        # Scale up deployments
        kubectl scale deployment --all --replicas=2 -n todo-app
    fi
    
    log_message "INFO" "Kubernetes resources tuned"
}

# Function to tune application-specific parameters
tune_application_parameters() {
    log_message "INFO" "Tuning application-specific parameters..."
    
    # Check if configuration file exists, create if not
    if [[ ! -f "$CONFIG_FILE" ]]; then
        log_message "INFO" "Creating default configuration file..."
        mkdir -p "$(dirname "$CONFIG_FILE")"
        cat > "$CONFIG_FILE" << EOF
# Performance configuration for Todo AI System
MAX_CONNECTIONS=$DEFAULT_MAX_CONNECTIONS
MEMORY_LIMIT=$DEFAULT_MEMORY_LIMIT
CPU_SHARES=$DEFAULT_CPU_SHARES
EOF
    fi
    
    # Load configuration
    source "$CONFIG_FILE"
    
    # Tune application parameters
    log_message "INFO" "Setting max connections to: $MAX_CONNECTIONS"
    log_message "INFO" "Setting memory limit to: $MEMORY_LIMIT"
    log_message "INFO" "Setting CPU shares to: $CPU_SHARES"
    
    # Update Kubernetes deployments with new resource limits
    kubectl patch deployment todo-app -n todo-app -p "{\"spec\":{\"template\":{\"spec\":{\"containers\":[{\"name\":\"todo-app\",\"resources\":{\"requests\":{\"memory\":\"${MEMORY_LIMIT%?}Mi\",\"cpu\":\"${CPU_SHARES}m\"},\"limits\":{\"memory\":\"${MEMORY_LIMIT%?}Mi\",\"cpu\":\"${CPU_SHARES}m\"}}]}}}}"
    
    log_message "INFO" "Application parameters tuned"
}

# Function to tune database performance
tune_database_performance() {
    log_message "INFO" "Tuning database performance..."
    
    # Get database pod name
    DB_POD=$(kubectl get pods -n todo-app -l app=postgres -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$DB_POD" ]]; then
        log_message "INFO" "Tuning database in pod: $DB_POD"
        
        # Apply PostgreSQL performance tuning
        kubectl exec -n todo-app "$DB_POD" -- psql -U postgres -c "
            ALTER SYSTEM SET shared_buffers = '256MB';
            ALTER SYSTEM SET effective_cache_size = '1GB';
            ALTER SYSTEM SET maintenance_work_mem = '64MB';
            ALTER SYSTEM SET checkpoint_completion_target = '0.9';
            ALTER SYSTEM SET wal_buffers = '16MB';
            ALTER SYSTEM SET default_statistics_target = '100';
            ALTER SYSTEM SET random_page_cost = '1.1';
            ALTER SYSTEM SET effective_io_concurrency = '200';
            ALTER SYSTEM SET work_mem = '4MB';
            ALTER SYSTEM SET min_wal_size = '1GB';
            ALTER SYSTEM SET max_wal_size = '4GB';
            ALTER SYSTEM SET max_worker_processes = '2';
            ALTER SYSTEM SET max_parallel_workers_per_gather = '1';
            ALTER SYSTEM SET max_parallel_workers = '2';
            ALTER SYSTEM SET max_parallel_maintenance_workers = '1';
        "
        
        # Reload PostgreSQL configuration
        kubectl exec -n todo-app "$DB_POD" -- psql -U postgres -c "SELECT pg_reload_conf();"
        
        log_message "INFO" "Database performance tuned"
    else
        log_message "WARNING" "Database pod not found, skipping database tuning"
    fi
}

# Function to tune caching layer
tune_caching_layer() {
    log_message "INFO" "Tuning caching layer..."
    
    # Get Redis pod name
    REDIS_POD=$(kubectl get pods -n todo-app -l app=redis -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
    
    if [[ -n "$REDIS_POD" ]]; then
        log_message "INFO" "Tuning Redis in pod: $REDIS_POD"
        
        # Apply Redis performance tuning
        kubectl exec -n todo-app "$REDIS_POD" -- redis-cli CONFIG SET maxmemory 512mb
        kubectl exec -n todo-app "$REDIS_POD" -- redis-cli CONFIG SET maxmemory-policy allkeys-lru
        kubectl exec -n todo-app "$REDIS_POD" -- redis-cli CONFIG SET tcp-keepalive 300
        kubectl exec -n todo-app "$REDIS_POD" -- redis-cli CONFIG SET timeout 300
        kubectl exec -n todo-app "$REDIS_POD" -- redis-cli CONFIG SET databases 2
        
        log_message "INFO" "Caching layer tuned"
    else
        log_message "WARNING" "Redis pod not found, skipping cache tuning"
    fi
}

# Function to tune monitoring and logging
tune_monitoring_logging() {
    log_message "INFO" "Tuning monitoring and logging..."
    
    # Optimize Prometheus configuration
    local PROMETHEUS_CM=$(kubectl get configmap -n monitoring prometheus-server -o jsonpath='{.data.prometheus\\.yml}' 2>/dev/null || echo "")
    
    if [[ -n "$PROMETHEUS_CM" ]]; then
        # Update Prometheus scrape intervals for performance
        kubectl patch configmap prometheus-server -n monitoring -p "{\"data\":{\"prometheus.yml\":\"$(echo "$PROMETHEUS_CM" | sed 's/scrape_interval: 30s/scrape_interval: 60s/g')\"}}"
        
        log_message "INFO" "Monitoring configuration tuned"
    fi
    
    log_message "INFO" "Monitoring and logging tuned"
}

# Function to run performance tests
run_performance_tests() {
    log_message "INFO" "Running performance tests..."
    
    # Install required tools if not present
    if ! command -v hey &> /dev/null; then
        log_message "INFO" "Installing hey load testing tool..."
        go install github.com/rakyll/hey@latest
    fi
    
    # Get service endpoint
    local SERVICE_ENDPOINT=$(kubectl get svc todo-app -n todo-app -o jsonpath='{.spec.clusterIP}:{.spec.ports[0].port}' 2>/dev/null || echo "")
    
    if [[ -n "$SERVICE_ENDPOINT" ]]; then
        log_message "INFO" "Running performance test against: $SERVICE_ENDPOINT"
        
        # Run basic performance test
        hey -n 1000 -c 10 "http://$SERVICE_ENDPOINT/healthz" > /tmp/performance_test_results.txt 2>&1
        
        # Analyze results
        local avg_latency=$(grep "Average" /tmp/performance_test_results.txt | awk '{print $2}')
        local rps=$(grep "Requests/sec" /tmp/performance_test_results.txt | awk '{print $2}')
        
        log_message "INFO" "Performance test results - Avg Latency: $avg_latency, RPS: $rps"
        
        # Check if performance meets requirements
        if (( $(echo "$avg_latency > 0.5" | bc -l) )); then
            log_message "WARNING" "Average latency exceeds 500ms threshold: $avg_latency"
        fi
        
        if (( $(echo "$rps < 100" | bc -l) )); then
            log_message "WARNING" "Throughput below 100 RPS threshold: $rps"
        fi
    else
        log_message "WARNING" "Service endpoint not found, skipping performance tests"
    fi
}

# Function to generate performance report
generate_performance_report() {
    log_message "INFO" "Generating performance report..."
    
    local REPORT_FILE="/tmp/performance_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Performance Report - $(date)"
        echo "=================================="
        echo ""
        echo "System Resources:"
        echo "-----------------"
        free -h
        echo ""
        df -h
        echo ""
        echo "Kubernetes Resources:"
        echo "---------------------"
        kubectl top nodes
        echo ""
        kubectl top pods --all-namespaces
        echo ""
        echo "Application Metrics:"
        echo "--------------------"
        kubectl get pods -n todo-app
        echo ""
        kubectl logs -n todo-app -l app=todo-app --tail=10
        echo ""
        echo "Database Performance:"
        echo "---------------------"
        kubectl exec -n todo-app -it $(kubectl get pods -n todo-app -l app=postgres -o jsonpath='{.items[0].metadata.name}') -- psql -U postgres -c "SELECT now() - pg_postmaster_start_time() as uptime;" 2>/dev/null || echo "Could not get database uptime"
        echo ""
        echo "Cache Performance:"
        echo "------------------"
        kubectl exec -n todo-app -it $(kubectl get pods -n todo-app -l app=redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli INFO stats 2>/dev/null | head -20 || echo "Could not get cache stats"
    } > "$REPORT_FILE"
    
    log_message "INFO" "Performance report generated: $REPORT_FILE"
}

# Function to optimize disk usage
optimize_disk_usage() {
    log_message "INFO" "Optimizing disk usage..."
    
    # Clean up Docker system
    docker system prune -f --volumes
    
    # Clean up Kubernetes logs
    find /var/log/pods -name "*.log" -size +100M -delete
    
    # Clean up temporary files
    find /tmp -name "todo_*" -atime +7 -delete
    
    log_message "INFO" "Disk usage optimized"
}

# Function to tune network settings
tune_network_settings() {
    log_message "INFO" "Tuning network settings..."
    
    # Tune network interface settings
    for iface in /sys/class/net/*; do
        local iface_name=$(basename "$iface")
        if [[ "$iface_name" != "lo" ]]; then
            # Increase network buffer sizes
            echo 65536 > "${iface}/rx_buffer_len" 2>/dev/null || true
            echo 65536 > "${iface}/tx_buffer_len" 2>/dev/null || true
        fi
    done
    
    log_message "INFO" "Network settings tuned"
}

# Main function
main() {
    log_message "INFO" "Starting performance tuning process..."
    
    # Parse command line arguments
    local action="${1:-all}"
    
    case "$action" in
        "kernel")
            check_prerequisites
            tune_kernel_parameters
            ;;
        "docker")
            check_prerequisites
            tune_docker_daemon
            ;;
        "kubernetes")
            check_prerequisites
            tune_kubernetes_resources
            ;;
        "application")
            check_prerequisites
            tune_application_parameters
            ;;
        "database")
            check_prerequisites
            tune_database_performance
            ;;
        "cache")
            check_prerequisites
            tune_caching_layer
            ;;
        "monitoring")
            check_prerequisites
            tune_monitoring_logging
            ;;
        "test")
            check_prerequisites
            run_performance_tests
            ;;
        "report")
            check_prerequisites
            generate_performance_report
            ;;
        "disk")
            check_prerequisites
            optimize_disk_usage
            ;;
        "network")
            check_prerequisites
            tune_network_settings
            ;;
        "all")
            check_prerequisites
            tune_kernel_parameters
            tune_docker_daemon
            tune_kubernetes_resources
            tune_application_parameters
            tune_database_performance
            tune_caching_layer
            tune_monitoring_logging
            optimize_disk_usage
            tune_network_settings
            run_performance_tests
            generate_performance_report
            ;;
        *)
            echo "Usage: $0 [all|kernel|docker|kubernetes|application|database|cache|monitoring|test|report|disk|network]"
            echo "  all         - Run all tuning operations (default)"
            echo "  kernel      - Tune kernel parameters"
            echo "  docker      - Tune Docker daemon"
            echo "  kubernetes  - Tune Kubernetes resources"
            echo "  application - Tune application parameters"
            echo "  database    - Tune database performance"
            echo "  cache       - Tune caching layer"
            echo "  monitoring  - Tune monitoring and logging"
            echo "  test        - Run performance tests"
            echo "  report      - Generate performance report"
            echo "  disk        - Optimize disk usage"
            echo "  network     - Tune network settings"
            exit 1
            ;;
    esac
    
    log_message "INFO" "Performance tuning process completed"
}

# Run main function with all arguments
main "$@"
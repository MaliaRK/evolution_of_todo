# Performance Optimization Documentation
# Documentation for performance optimization in the Todo AI system

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-optimization-docs
  namespace: todo-app
data:
  performance-optimization-guide.md: |
    # Performance Optimization Guide for Todo AI System
    
    ## Table of Contents
    1. [Overview](#overview)
    2. [Performance Baselines](#performance-baselines)
    3. [Monitoring Performance](#monitoring-performance)
    4. [Application-Level Optimizations](#application-level-optimizations)
    5. [Database Optimizations](#database-optimizations)
    6. [Infrastructure Optimizations](#infrastructure-optimizations)
    7. [Caching Strategies](#caching-strategies)
    8. [Network Optimizations](#network-optimizations)
    9. [Security Considerations](#security-considerations)
    10. [Performance Testing](#performance-testing)
    11. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)
    
    ## Overview
    
    This guide provides comprehensive information on optimizing the performance of the Todo AI system. It covers various aspects of performance optimization from application code to infrastructure configuration.
    
    ### Performance Objectives
    
    - **Response Time**: P95 < 500ms, P99 < 1000ms
    - **Throughput**: Handle 1000+ requests per second
    - **Availability**: 99.9% uptime
    - **Resource Utilization**: CPU < 70%, Memory < 80%
    - **Scalability**: Linear scaling with load
    
    ## Performance Baselines
    
    ### Current Baseline Metrics
    
    | Metric | Current | Target | Status |
    |--------|---------|--------|--------|
    | P95 Response Time | 350ms | < 500ms | ✅ Good |
    | P99 Response Time | 750ms | < 1000ms | ✅ Good |
    | Avg CPU Usage | 45% | < 70% | ✅ Good |
    | Avg Memory Usage | 65% | < 80% | ✅ Good |
    | Error Rate | 0.1% | < 1% | ✅ Good |
    | Throughput | 800 req/s | > 1000 req/s | ❌ Needs Improvement |
    
    ### Performance Measurement Tools
    
    - **Application Metrics**: Prometheus + Grafana
    - **APM**: Jaeger for distributed tracing
    - **Infrastructure**: Node Exporter, cAdvisor
    - **Database**: PostgreSQL built-in statistics
    - **Network**: Istio telemetry
    
    ## Monitoring Performance
    
    ### Key Performance Indicators (KPIs)
    
    1. **Response Time Metrics**
       - P50, P95, P99 response times
       - API endpoint-specific response times
       - Database query response times
    
    2. **Throughput Metrics**
       - Requests per second (RPS)
       - Transactions per second (TPS)
       - Operations per second by type
    
    3. **Resource Utilization**
       - CPU usage by component
       - Memory usage by component
       - Disk I/O patterns
       - Network bandwidth utilization
    
    4. **Error Metrics**
       - Error rate by endpoint
       - Error rate by type
       - Retry rate
    
    ### Performance Dashboards
    
    - **Application Performance Dashboard**: Real-time response times and throughput
    - **Infrastructure Dashboard**: Resource utilization and node health
    - **Database Dashboard**: Query performance and connection metrics
    - **Network Dashboard**: Latency and throughput metrics
    
    ## Application-Level Optimizations
    
    ### Code-Level Optimizations
    
    1. **Algorithm Efficiency**
       ```python
       # Before: O(n²) algorithm
       def find_duplicates_slow(items):
           duplicates = []
           for i in range(len(items)):
               for j in range(i + 1, len(items)):
                   if items[i] == items[j]:
                       duplicates.append(items[i])
           return duplicates
       
       # After: O(n) algorithm with set
       def find_duplicates_fast(items):
           seen = set()
           duplicates = set()
           for item in items:
               if item in seen:
                   duplicates.add(item)
               else:
                   seen.add(item)
           return list(duplicates)
       ```
    
    2. **Database Query Optimization**
       ```python
       # Before: N+1 query problem
       def get_todos_with_users_naive():
           todos = Todo.objects.all()
           result = []
           for todo in todos:
               result.append({
                   'todo': todo,
                   'user': todo.user  # Triggers separate query
               })
           return result
       
       # After: Eager loading
       def get_todos_with_users_optimized():
           todos = Todo.objects.select_related('user').all()
           return [{'todo': todo, 'user': todo.user} for todo in todos]
       ```
    
    3. **Caching Implementation**
       ```python
       from functools import lru_cache
       
       # Cache expensive computations
       @lru_cache(maxsize=128)
       def expensive_calculation(param):
           # Expensive operation
           return result
       
       # Cache database queries
       @cache_page(60 * 15)  # Cache for 15 minutes
       def get_popular_todos(request):
           return Todo.objects.filter(popular=True)[:10]
       ```
    
    ### Asynchronous Processing
    
    1. **Background Tasks**
       ```python
       # Use Celery for background tasks
       from celery import shared_task
       
       @shared_task
       def send_notification_async(user_id, message):
           user = User.objects.get(id=user_id)
           send_email(user.email, message)
       
       # Call asynchronously
       send_notification_async.delay(user_id, message)
       ```
    
    2. **Async Views**
       ```python
       # Use async views for I/O bound operations
       async def get_todo_async(request, todo_id):
           todo = await sync_to_async(Todo.objects.get)(id=todo_id)
           return JsonResponse(model_to_dict(todo))
       ```
    
    ## Database Optimizations
    
    ### Indexing Strategy
    
    1. **Query-Based Indexing**
       ```sql
       -- Index for common query patterns
       CREATE INDEX CONCURRENTLY idx_todo_user_status ON todos (user_id, status);
       CREATE INDEX CONCURRENTLY idx_todo_created_at ON todos (created_at DESC);
       CREATE INDEX CONCURRENTLY idx_todo_title_gin ON todos USING gin(to_tsvector('english', title));
       ```
    
    2. **Composite Indexes**
       ```sql
       -- For multi-column queries
       CREATE INDEX CONCURRENTLY idx_todo_user_status_priority ON todos (user_id, status, priority);
       ```
    
    ### Query Optimization
    
    1. **Avoid N+1 Queries**
       ```python
       # Use select_related and prefetch_related
       todos = Todo.objects.select_related('user').prefetch_related('tags').all()
       ```
    
    2. **Efficient Filtering**
       ```python
       # Use database-level filtering instead of Python filtering
       # Bad: todos = [t for t in Todo.objects.all() if t.is_urgent()]
       # Good:
       urgent_todos = Todo.objects.filter(priority='high', due_date__lte=timezone.now() + timedelta(days=1))
       ```
    
    ### Connection Pooling
    
    1. **Configure Connection Pool**
       ```yaml
       # Database connection configuration
       database:
         pool_size: 20
         max_overflow: 30
         pool_timeout: 30
         pool_recycle: 3600  # 1 hour
         echo: false
       ```
    
    ## Infrastructure Optimizations
    
    ### Kubernetes Resource Optimization
    
    1. **Resource Requests and Limits**
       ```yaml
       apiVersion: apps/v1
       kind: Deployment
       metadata:
         name: todo-app
       spec:
         template:
           spec:
             containers:
             - name: todo-app
               image: todo-app:latest
               resources:
                 requests:
                   memory: "256Mi"
                   cpu: "250m"
                 limits:
                   memory: "512Mi"
                   cpu: "500m"
       ```
    
    2. **Horizontal Pod Autoscaler**
       ```yaml
       apiVersion: autoscaling/v2
       kind: HorizontalPodAutoscaler
       metadata:
         name: todo-app-hpa
       spec:
         scaleTargetRef:
           apiVersion: apps/v1
           kind: Deployment
           name: todo-app
         minReplicas: 2
         maxReplicas: 20
         metrics:
         - type: Resource
           resource:
             name: cpu
             target:
               type: Utilization
               averageUtilization: 70
         - type: Resource
           resource:
             name: memory
             target:
               type: Utilization
               averageUtilization: 80
       ```
    
    ### Service Mesh Optimizations (Dapr)
    
    1. **Component Configuration**
       ```yaml
       apiVersion: dapr.io/v1alpha1
       kind: Component
       metadata:
         name: statestore
       spec:
         type: state.redis
         version: v1
         metadata:
         - name: redisHost
           value: "redis-master:6379"
         - name: actorStateStore
           value: "true"
         - name: concurrency
           value: parallel
         - name: timeout
           value: 5s
       ```
    
    2. **Service Invocation Optimization**
       ```python
       # Use Dapr service invocation with retries
       import dapr.clients
       from dapr.clients.grpc._state import StateItem
       
       client = dapr.clients.DaprClient()
       
       # Optimized service invocation
       def invoke_service_with_retry(service_app_id, method, data, max_retries=3):
           for attempt in range(max_retries):
               try:
                   return client.invoke_method(
                       service_app_id,
                       method,
                       data
                   )
               except Exception as e:
                   if attempt == max_retries - 1:
                       raise e
                   time.sleep(2 ** attempt)  # Exponential backoff
       ```
    
    ## Caching Strategies
    
    ### Multi-Level Caching
    
    1. **Application-Level Cache**
       ```python
       # Redis-based caching
       import redis
       import json
       
       cache = redis.Redis(host='redis', port=6379, db=0)
       
       def get_todo_cached(todo_id):
           cache_key = f"todo:{todo_id}"
           cached_data = cache.get(cache_key)
           
           if cached_data:
               return json.loads(cached_data)
           
           # Fetch from database
           todo = Todo.objects.get(id=todo_id)
           cache.setex(cache_key, 300, json.dumps(model_to_dict(todo)))  # 5 min TTL
           return todo
       ```
    
    2. **CDN and Edge Caching**
       ```yaml
       # Ingress configuration for CDN
       apiVersion: networking.k8s.io/v1
       kind: Ingress
       metadata:
         name: todo-app-ingress
         annotations:
           # CDN-specific annotations
           external-dns.alpha.kubernetes.io/hostname: "api.todo-app.com"
           cert-manager.io/cluster-issuer: "letsencrypt-prod"
           nginx.ingress.kubernetes.io/configuration-snippet: |
             # Cache static assets
             location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
               expires 1y;
               add_header Cache-Control "public, immutable";
             }
       spec:
         rules:
         - host: api.todo-app.com
           http:
             paths:
             - path: /
               pathType: Prefix
               backend:
                 service:
                   name: todo-app
                   port:
                     number: 80
       ```
    
    ### Cache Invalidation Strategies
    
    1. **Time-Based Invalidation**
       ```python
       # Cache with TTL
       cache.setex(f"user_profile:{user_id}", 3600, profile_data)  # 1 hour TTL
       ```
    
    2. **Event-Driven Invalidation**
       ```python
       # Invalidate cache on data change
       def update_todo(todo_id, data):
           todo = Todo.objects.get(id=todo_id)
           todo.update(**data)
           
           # Invalidate related caches
           cache.delete(f"todo:{todo_id}")
           cache.delete(f"user_todos:{todo.user_id}")
           
           return todo
       ```
    
    ## Network Optimizations
    
    ### Service Communication
    
    1. **Connection Pooling**
       ```python
       # HTTP connection pooling
       import requests
       from requests.adapters import HTTPAdapter
       from urllib3.util.retry import Retry
       
       session = requests.Session()
       retry_strategy = Retry(
           total=3,
           backoff_factor=1,
           status_forcelist=[429, 500, 502, 503, 504],
       )
       adapter = HTTPAdapter(
           max_retries=retry_strategy,
           pool_connections=100,
           pool_maxsize=100
       )
       session.mount("http://", adapter)
       session.mount("https://", adapter)
       ```
    
    2. **Protocol Optimization**
       ```yaml
       # Enable HTTP/2 in ingress
       apiVersion: networking.k8s.io/v1
       kind: Ingress
       metadata:
         name: todo-app-ingress
         annotations:
           nginx.ingress.kubernetes.io/configuration-snippet: |
             # Enable HTTP/2
             http2 on;
             
             # Compression
             gzip on;
             gzip_vary on;
             gzip_min_length 1024;
             gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
       ```
    
    ## Security Considerations
    
    ### Performance vs Security Trade-offs
    
    1. **Authentication Caching**
       ```python
       # Cache authentication tokens
       def authenticate_user(token):
           cache_key = f"auth:{token}"
           cached_result = cache.get(cache_key)
           
           if cached_result is not None:
               return cached_result
           
           # Validate token (expensive operation)
           user = validate_jwt_token(token)
           cache.setex(cache_key, 300, user)  # Cache for 5 minutes
           return user
       ```
    
    2. **Rate Limiting**
       ```python
       # Implement rate limiting to prevent abuse
       from flask_limiter import Limiter
       from flask_limiter.util import get_remote_address
       
       limiter = Limiter(
           app,
           key_func=get_remote_address,
           default_limits=["200 per day", "50 per hour"]
       )
       
       @app.route("/api/todos")
       @limiter.limit("10 per minute")
       def get_todos():
           return get_user_todos()
       ```
    
    ## Performance Testing
    
    ### Load Testing
    
    1. **Test Scenarios**
       - Peak load: 2x normal traffic
       - Spike load: Sudden traffic surge
       - Sustained load: 8-hour continuous load
       - Stress testing: Beyond capacity limits
    
    2. **Load Testing Tools**
       ```bash
       # Using Artillery for load testing
       artillery run --target http://todo-app.todo-app.svc.cluster.local load-test.yaml
       
       # Using k6 for advanced scenarios
       k6 run --vus 100 --duration 5m load-test.js
       ```
    
    ### Performance Regression Testing
    
    1. **Continuous Performance Testing**
       ```yaml
       # GitHub Actions for performance testing
       name: Performance Tests
       on:
         pull_request:
           branches: [main]
       
       jobs:
         performance-test:
           runs-on: ubuntu-latest
           steps:
             - name: Checkout
               uses: actions/checkout@v3
             
             - name: Run performance tests
               run: |
                 # Deploy to test environment
                 kubectl apply -f test-deployment.yaml
                 
                 # Wait for deployment
                 kubectl rollout status deployment/todo-app-test
                 
                 # Run load test
                 artillery run --target http://todo-app-test --output results.json load-test.yaml
                 
                 # Compare results with baseline
                 python compare-performance.py results.json baseline.json
       ```
    
    ## Troubleshooting Performance Issues
    
    ### Common Performance Problems
    
    1. **Slow Database Queries**
       - Check for missing indexes
       - Look for N+1 query problems
       - Analyze query execution plans
       - Consider query optimization
    
    2. **Memory Leaks**
       - Monitor memory usage over time
       - Use profiling tools to identify leaks
       - Check for circular references
       - Implement proper cleanup
    
    3. **CPU Bottlenecks**
       - Profile application code
       - Identify expensive operations
       - Consider algorithm optimization
       - Implement caching where appropriate
    
    ### Diagnostic Commands
    
    ```bash
    # Monitor application performance
    kubectl top pods -n todo-app
    
    # Check application logs for errors
    kubectl logs -f deployment/todo-app -n todo-app
    
    # Monitor database performance
    kubectl exec -it deployment/postgres -n todo-app -- psql -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
    
    # Check for slow queries
    kubectl exec -it deployment/postgres -n todo-app -- psql -c "SHOW logs; SELECT * FROM pg_stat_activity WHERE state = 'active';"
    
    # Monitor network performance
    kubectl exec -it deployment/todo-app -n todo-app -- bash -c "iftop -i eth0"
    ```
    
    ### Performance Profiling
    
    ```python
    # Python profiling example
    import cProfile
    import pstats
    from pstats import SortKey
    
    def profile_performance():
        profiler = cProfile.Profile()
        profiler.enable()
        
        # Code to profile
        result = your_function()
        
        profiler.disable()
        
        # Print stats
        stats = pstats.Stats(profiler)
        stats.sort_stats(SortKey.TIME)
        stats.print_stats(10)  # Top 10 time-consuming functions
        
        return result
    ```
    
    ## Continuous Performance Improvement
    
    ### Performance Monitoring Process
    
    1. **Weekly Performance Reviews**
       - Review performance metrics
       - Identify trends and anomalies
       - Plan optimization tasks
       - Update performance baselines
    
    2. **Monthly Deep Dives**
       - Comprehensive performance analysis
       - Bottleneck identification
       - Optimization implementation
       - Result validation
    
    3. **Quarterly Performance Audits**
       - Architecture review
       - Technology stack evaluation
       - Performance goal reassessment
       - Capacity planning
    
    ### Performance Culture
    
    - Include performance considerations in code reviews
    - Set performance acceptance criteria for features
    - Celebrate performance improvements
    - Share performance optimization knowledge
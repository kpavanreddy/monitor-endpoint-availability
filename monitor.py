import yaml
import requests
import time
from collections import defaultdict
from urllib.parse import urlparse

# Load the YAML configuration file containing endpoint definitions.
def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# Extract the domain (without port) from a URL.
def extract_domain(url):
    parsed = urlparse(url)
    return parsed.hostname.lower() if parsed.hostname else None

# Perform a health check.
def check_health(endpoint):
    url = endpoint['url']
    method = endpoint.get('method', 'GET').upper()
    headers = endpoint.get('headers', {}).copy()  # Copy to avoid mutating original
    body = endpoint.get('body', None)

    request_kwargs = {'headers': headers, 'timeout': 0.5}
    if body is not None:
        request_kwargs['data'] = body
        # Ensure Content-Type is set to application/json if not already present
        if not any(k.lower() == 'content-type' for k in headers):
            request_kwargs['headers']['Content-Type'] = 'application/json'

    try:
        start = time.time()
        response = requests.request(method, url, **request_kwargs)
        elapsed_ms = (time.time() - start) * 1000
        is_up = 200 <= response.status_code < 300 and elapsed_ms <= 500
        return {
            "name": endpoint.get("name", url),
            "domain": extract_domain(url),
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "available": is_up
        }
    except requests.RequestException as e:
        return {
            "name": endpoint.get("name", url),
            "domain": extract_domain(url),
            "status_code": None,
            "elapsed_ms": None,
            "available": False,
            "error": str(e)
        }

# Main monitoring loop which loads configuration, checks all endpoints every 15 seconds, logs availability of endpoints.
def monitor_endpoints(file_path):
    config = load_config(file_path)

    # Cumulative stats
    endpoint_cumulative = defaultdict(lambda: {"up": 0, "total": 0})
    domain_cumulative = defaultdict(lambda: {"up": 0, "total": 0})

    while True:
        cycle_start = time.time()
        results = []
        for endpoint in config:
            result = check_health(endpoint)
            results.append(result)
            # Update endpoint cumulative stats
            endpoint_cumulative[result['name']]["total"] += 1
            if result['available']:
                endpoint_cumulative[result['name']]["up"] += 1

        # Aggregate by domain: domain is UP only if all its endpoints are UP
        domain_status = defaultdict(list)
        for r in results:
            if r['domain']:
                domain_status[r['domain']].append(r['available'])

        domain_availability = {domain: all(statuses) for domain, statuses in domain_status.items()}

        # Update domain cumulative stats
        for domain, available in domain_availability.items():
            domain_cumulative[domain]["total"] += 1
            if available:
                domain_cumulative[domain]["up"] += 1

        # Log results
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[{timestamp}] Endpoint Results:")
        for r in results:
            if r['elapsed_ms'] is not None:
                elapsed_str = f"{r['elapsed_ms']:.1f}ms"
            else:
                elapsed_str = "N/A"
            print(f"  - {r['name']} ({r['domain']}): "
                  f"status={r['status_code']} "
                  f"elapsed={elapsed_str} "
                  f"available={r['available']}")
        print("Domain Availability:")
        for domain, available in domain_availability.items():
            print(f"  - {domain}: {available}")

        # Log cumulative stats
        print("\nCumulative Endpoint Availability:")
        for name, stats in endpoint_cumulative.items():
            percent = 100 * stats["up"] / stats["total"] if stats["total"] else 0
            print(f"  - {name}: {percent:.1f}% ({stats['up']}/{stats['total']})")

        print("Cumulative Domain Availability:")
        for domain, stats in domain_cumulative.items():
            percent = 100 * stats["up"] / stats["total"] if stats["total"] else 0
            print(f"  - {domain}: {percent:.1f}% ({stats['up']}/{stats['total']})")
        print("---")

        # Ensure each cycle starts every 15 seconds
        elapsed = time.time() - cycle_start
        sleep_time = max(0, 15 - elapsed)
        time.sleep(sleep_time)

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python monitor.py <config_file_path>")
        sys.exit(1)
    config_file = sys.argv[1]
    try:
        monitor_endpoints(config_file)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

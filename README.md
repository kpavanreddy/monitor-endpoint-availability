# Monitor Endpoint Availability
This is a Python tool developed to check the availability of HTTP/HTTPS endpoints as specified in a YAML configuration file. The monitor will check each endpoint every 15 seconds, the availability is determined by domain only (ignoring port numbers) and logs the results for each cycle. Endpoints are only considered available if they return a 2xx success status code and respond to the request within 500ms.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [YAML Configuration Format](#yaml-configuration-format)
- [How Issues Were Identified and Fixed](#how-issues-were-identified-and-fixed)

### Installation

1. **Clone the repository (or copy the code into a file named monitor.py):**

<pre>git clone &lt;your-repo-url&gt; 
cd &lt;your-repo-directory&gt; </pre>

2. **Install dependencies:**
   This project requires Python 3.7+ and the following packages:
    - `pyyaml`
    - `requests`
<pre>pip install pyyaml requests </pre>

### Usage
1. **Prepare your YAML configuration file** (see [YAML Configuration Format](#yaml-configuration-format)).
2. **Run the monitor:**
    <pre>python monitor.py path/to/your_config.yaml </pre>

The script will check all endpoints every 15 seconds and print both per-cycle and cumulative availability statistics.

3. **Stop monitoring:** Press Ctrl+C in the terminal.

### Yaml Configuration Format

- name (string, required): A free text name to describe the HTTP endpoint.

- url (string, required): The URL of the HTTP endpoint (must be valid HTTP/HTTPS).

- method (string, optional): HTTP method (e.g., GET, POST). Defaults to GET if omitted.

- headers (dict, optional): HTTP headers to include in the request.

- body (string, optional): JSON-encoded string to send as the HTTP body. If omitted, no body is sent.

<pre>
- body: '{"foo":"bar"}'
  headers:
    content-type: application/json
  method: POST
  name: sample body up
  url: https://dev-sre-take-home-exercise-rubric.us-east-1.recruiting-public.fetchrewards.com/body
- name: sample index up
  url: https://dev-sre-take-home-exercise-rubric.us-east-1.recruiting-public.fetchrewards.com/
- body: "{}"
  headers:
    content-type: application/json
  method: POST
  name: sample body down
  url: https://dev-sre-take-home-exercise-rubric.us-east-1.recruiting-public.fetchrewards.com/body
- name: sample error down
  url: https://dev-sre-take-home-exercise-rubric.us-east-1.recruiting-public.fetchrewards.com/error </pre>

  
### How Issues Were Identified and Fixed

This section explains how each issue in the original code was identified and why each change was made:

1. **Default Values for Optional Fields**
   - **Issue:**  The original code did not provide defaults for method, headers, or body, which could cause errors if these fields were omitted in the YAML.
   - **Fix:**  The code now uses endpoint.get('method', 'GET').upper() for the HTTP method, endpoint.get('headers', {}) for headers, and only includes the body if present. This ensures robust handling of optional fields.

2. **Body Handling**
   - **Issue:** The original code used json=body, which is incorrect because the YAML spec provides the body as a JSON-encoded string, not a Python dictionary.
   - **Fix:** The code now uses data=body to send the body as a raw string, and ensures the Content-Type: application/json header is set if a body is present. This matches the YAML specification and HTTP standards.

3. **Timeout and Response Time Measurement**
   - **Issue:** The original code did not enforce a 500ms timeout or measure response time, which could result in inaccurate availability checks.
   - **Fix:** The code now uses timeout=0.5 in the request and measures the elapsed time. An endpoint is only considered available if it responds within 500ms and returns a 2xx status code.

4. **Domain Extraction**
   - **Issue:** The original code extracted the domain using string splitting, which could include port numbers and was not robust.
   - **Fix:** The code now uses urllib.parse.urlparse to extract the domain, ensuring port numbers are ignored and the domain is accurately determined.

5. **Per-Cycle Availability Calculation**
   - **Issue:** The original code accumulated statistics over all time and calculated cumulative percentages, rather than per-cycle availability.
   - **Fix:** The code now determines and logs availability for each endpoint and domain during every check cycle, as required.

6. **Cumulative Availability Tracking**
   - **Issue:** The original code did not track or display cumulative availability statistics for endpoints or domains.
   - **Fix:** The code now maintains counters for each endpoint and domain, tracking how many times they were checked and how many times they were available. After each cycle, it logs both per-cycle and cumulative availability percentages.

7. **Check Cycle Timing**
   - **Issue:** The original code waited 15 seconds after each check cycle, which could cause drift if checks took a long time.
   - **Fix:** The code now records the start time of each cycle and sleeps only for the remainder of the 15 seconds, ensuring that cycles start every 15 seconds regardless of endpoint count or response times.

8. **Logging**
   - **Issue:** The original code logged cumulative percentages, not per-cycle results.
   - **Fix:** The code now logs the status, response time, and availability of each endpoint and the overall availability of each domain for every cycle.

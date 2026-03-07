const ivm = require("isolated-vm");
const fs = require("fs");

// Security endpoint extractor using isolated-vm sandbox
class SecurityEndpointExtractor {
  constructor() {
    this.isolate = new ivm.Isolate({
      memoryLimit: 128, // 128MB memory limit
      inspector: false,
    });

    this.context = this.isolate.createContextSync();
    this.global = this.context.global;

    // Setup secure environment
    this.setupSecureEnvironment();
  }

  setupSecureEnvironment() {
    // Create safe JavaScript environment in the sandbox
    const setupScript = this.context.compileSync(`
            // Create safe console
            global.console = {
                log: (...args) => console.log('[SANDBOX]', ...args)
            };
            
            // Mock browser APIs
            global.window = {
                location: {
                    href: 'http://localhost'
                }
            };
            
            global.document = {
                location: {
                    href: 'http://localhost'
                }
            };
            
            // Mock fetch and axios for tracking
            global.fetch = null;
            global.axios = null;
            global.XMLHttpRequest = null;
            
            // Initialize tracking array
            global._trackedCalls = [];
        `);
    setupScript.runSync(this.context);

    // Setup HTTP tracking functions
    this.setupHTTPTracking();
  }

  setupHTTPTracking() {
    // Override fetch to track calls
    const fetchTracker = this.context.compileSync(`
            global.fetch = function(url, options = {}) {
                const callInfo = {
                    type: 'fetch',
                    url: url,
                    method: (options.method || 'GET').toUpperCase(),
                    headers: options.headers || {},
                    body: options.body || null,
                    timestamp: Date.now()
                };
                
                // Store the call info for extraction
                if (!global._trackedCalls) {
                    global._trackedCalls = [];
                }
                global._trackedCalls.push(callInfo);
                
                // Return a mock Promise
                return Promise.resolve({
                    ok: true,
                    status: 200,
                    json: () => Promise.resolve({}),
                    text: () => Promise.resolve('')
                });
            };
        `);
    fetchTracker.runSync(this.context);

    // Override axios to track calls
    const axiosTracker = this.context.compileSync(`
            global.axios = {
                get: function(url, config = {}) {
                    return trackAxiosCall('GET', url, null, config);
                },
                post: function(url, data, config = {}) {
                    return trackAxiosCall('POST', url, data, config);
                },
                put: function(url, data, config = {}) {
                    return trackAxiosCall('PUT', url, data, config);
                },
                patch: function(url, data, config = {}) {
                    return trackAxiosCall('PATCH', url, data, config);
                },
                delete: function(url, config = {}) {
                    return trackAxiosCall('DELETE', url, null, config);
                }
            };
            
            function trackAxiosCall(method, url, data, config) {
                const callInfo = {
                    type: 'axios',
                    url: url,
                    method: method,
                    data: data || null,
                    config: config || {},
                    timestamp: Date.now()
                };
                
                if (!global._trackedCalls) {
                    global._trackedCalls = [];
                }
                global._trackedCalls.push(callInfo);
                
                return Promise.resolve({
                    data: {},
                    status: 200,
                    statusText: 'OK'
                });
            }
        `);
        axiosTracker.runSync(this.context);

    // Override XMLHttpRequest to track calls
    const xhrTracker = this.context.compileSync(`
            global.XMLHttpRequest = function() {
                this._method = null;
                this._url = null;
                this._headers = {};
                this._body = null;
                this.readyState = 0;
                this.status = 0;
                this.responseText = '';
                this.onreadystatechange = null;
            };
            
            global.XMLHttpRequest.prototype.open = function(method, url, async) {
                this._method = method.toUpperCase();
                this._url = url;
                this._async = async !== false;
            };
            
            global.XMLHttpRequest.prototype.setRequestHeader = function(name, value) {
                this._headers[name] = value;
            };
            
            global.XMLHttpRequest.prototype.send = function(body) {
                this._body = body;
                
                const callInfo = {
                    type: 'xhr',
                    url: this._url,
                    method: this._method || 'GET',
                    headers: this._headers,
                    body: this._body,
                    timestamp: Date.now()
                };
                
                if (!global._trackedCalls) {
                    global._trackedCalls = [];
                }
                global._trackedCalls.push(callInfo);
                
                // Execute synchronously for sandbox
                this.readyState = 4;
                this.status = 200;
                this.responseText = '{}';
                if (this.onreadystatechange) {
                    this.onreadystatechange();
                }
            };
        `);
    xhrTracker.runSync(this.context);
  }

  async extractEndpoints(jsCode) {
    try {
      // Clear previous tracked calls (in place to keep reference)
      await this.context.evalSync("global._trackedCalls.length = 0;");

      // Wrap the user code in a try-catch to handle errors gracefully
      const wrappedCode = `
                try {
                    ${jsCode}
                } catch (error) {
                    console.log('Code execution error:', error.message);
                }
                
                // Return tracked calls
                global._trackedCalls || [];
            `;

      // Execute the code in the sandbox
      const result = await this.context.eval(wrappedCode, {
        timeout: 5000, // 5 second timeout
      });

      // Process and return the tracked calls
      return this.processTrackedCalls(result);
    } catch (error) {
      console.error("Sandbox execution error:", error);
      return [];
    }
  }

  processTrackedCalls(calls) {
    if (!Array.isArray(calls)) {
      return [];
    }

    return calls.map((call) => {
      const endpoint = {
        type: call.type,
        url: this.extractURL(call),
        method: call.method,
        parameters: this.extractParameters(call),
        timestamp: call.timestamp,
      };

      return endpoint;
    });
  }

  extractURL(call) {
    if (typeof call.url === "string") {
      return call.url;
    }

    // Handle template literals and complex expressions
    if (call.url && typeof call.url === "object") {
      // Try to convert to string representation
      try {
        return String(call.url);
      } catch (e) {
        return "[unknown_url]";
      }
    }

    return "[unknown_url]";
  }

  extractParameters(call) {
    const parameters = [];

    if (call.type === "fetch") {
      // Extract from fetch body
      if (call.body) {
        const parsed = this.parseBodyContent(call.body);
        if (parsed) {
          parameters.push(...this.extractObjectParams(parsed, "body"));
        }
      }
    } else if (call.type === "axios") {
      // Extract from axios data
      if (call.data) {
        const parsed = this.parseBodyContent(call.data);
        if (parsed) {
          parameters.push(...this.extractObjectParams(parsed, "body"));
        }
      }

      // Extract from axios config (for GET requests with params)
      if (call.config && call.config.params) {
        parameters.push(
          ...this.extractObjectParams(call.config.params, "query")
        );
      }
    } else if (call.type === "xhr") {
      // Extract from XHR body
      if (call.body) {
        const parsed = this.parseBodyContent(call.body);
        if (parsed) {
          parameters.push(...this.extractObjectParams(parsed, "body"));
        }
      }
    }

    return parameters;
  }

  parseBodyContent(body) {
    if (typeof body === "object") {
      return body;
    }

    if (typeof body === "string") {
      try {
        return JSON.parse(body);
      } catch (e) {
        // Not JSON, return as string parameter
        return { _raw_body: body };
      }
    }

    return null;
  }

  extractObjectParams(obj, prefix = "", path = "") {
    const params = [];

    if (!obj || typeof obj !== "object") {
      return params;
    }

    for (const [key, value] of Object.entries(obj)) {
      const paramPath = path ? `${path}.${key}` : key;
      const paramName = prefix ? `${prefix}.${paramPath}` : paramPath;

      if (value && typeof value === "object" && !Array.isArray(value)) {
        // Recursively handle nested objects
        params.push(...this.extractObjectParams(value, prefix, paramPath));
      } else {
        // Add parameter info
        params.push({
          name: paramName,
          value: value,
          type: this.getValueType(value),
          source: "javascript",
        });
      }
    }

    return params;
  }

  getValueType(value) {
    if (value === null) return "null";
    if (Array.isArray(value)) return "array";
    if (typeof value === "boolean") return "boolean";
    if (typeof value === "number") return "number";
    if (typeof value === "string") return "string";
    if (typeof value === "object") return "object";
    return "unknown";
  }

  dispose() {
    if (this.isolate) {
      this.isolate.dispose();
    }
  }
}

// Main execution handler
async function main() {
  const jsCode = fs.readFileSync(0, "utf8"); // Read from stdin

  const extractor = new SecurityEndpointExtractor();

  try {
    const endpoints = await extractor.extractEndpoints(jsCode);
    console.log(JSON.stringify(endpoints, null, 2));
  } catch (error) {
    console.error("Extraction failed:", error);
    console.log("[]");
  } finally {
    extractor.dispose();
  }
}

// Export for testing
module.exports = { SecurityEndpointExtractor };

// Run if called directly
if (require.main === module) {
  main().catch(console.error);
}

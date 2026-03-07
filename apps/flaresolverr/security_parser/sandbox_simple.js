const { VM } = require("vm2");

// Simple endpoint extractor using vm2 sandbox
class SimpleEndpointExtractor {
  constructor() {
    this.vm = new VM({
      timeout: 5000,
      sandbox: this.createSecureSandbox(),
    });
  }

  createSecureSandbox() {
    const sandbox = {
      console: {
        log: (...args) => console.log("[SANDBOX]", ...args),
      },
      window: {
        location: {
          href: "http://localhost",
        },
      },
      document: {
        location: {
          href: "http://localhost",
        },
      },
      _trackedCalls: [],
    };

    // Add trackAxiosCall function to sandbox
    sandbox.trackAxiosCall = function (method, url, data, config) {
      const callInfo = {
        type: "axios",
        url: url,
        method: method,
        data: data || null,
        config: config || {},
        timestamp: Date.now(),
      };

      this._trackedCalls.push(callInfo);

      return Promise.resolve({
        data: {},
        status: 200,
        statusText: "OK",
      });
    }.bind(sandbox);

    // Mock fetch
    sandbox.fetch = function (url, options = {}) {
      const callInfo = {
        type: "fetch",
        url: url,
        method: (options.method || "GET").toUpperCase(),
        headers: options.headers || {},
        body: options.body || null,
        timestamp: Date.now(),
      };

      this._trackedCalls.push(callInfo);

      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
        text: () => Promise.resolve(""),
      });
    }.bind(sandbox);

    // Mock axios
    sandbox.axios = {
      get: function (url, config) {
        return sandbox.trackAxiosCall("GET", url, null, config);
      },
      post: function (url, data, config) {
        return sandbox.trackAxiosCall("POST", url, data, config);
      },
      put: function (url, data, config) {
        return sandbox.trackAxiosCall("PUT", url, data, config);
      },
      patch: function (url, data, config) {
        return sandbox.trackAxiosCall("PATCH", url, data, config);
      },
      delete: function (url, config) {
        return sandbox.trackAxiosCall("DELETE", url, null, config);
      },
    };

    // Store reference for XHR
    const trackedCalls = sandbox._trackedCalls;

    // Mock XMLHttpRequest
    sandbox.XMLHttpRequest = function () {
      this._method = null;
      this._url = null;
      this._headers = {};
      this._body = null;
      this.readyState = 0;
      this.status = 0;
      this.responseText = "";
      this.onreadystatechange = null;
    };

    sandbox.XMLHttpRequest.prototype.open = function (method, url, async) {
      this._method = method.toUpperCase();
      this._url = url;
      this._async = async !== false;
    };

    sandbox.XMLHttpRequest.prototype.setRequestHeader = function (name, value) {
      this._headers[name] = value;
    };

    sandbox.XMLHttpRequest.prototype.send = function (body) {
      this._body = body;

      const callInfo = {
        type: "xhr",
        url: this._url,
        method: this._method || "GET",
        headers: this._headers,
        body: this._body,
        timestamp: Date.now(),
      };

      trackedCalls.push(callInfo);

      // Execute synchronously for sandbox
      this.readyState = 4;
      this.status = 200;
      this.responseText = "{}";
      if (this.onreadystatechange) {
        this.onreadystatechange();
      }
    };

    return sandbox;
  }

  extractEndpoints(jsCode) {
    try {
      // Clear previous calls (in place to keep reference)
      this.vm.sandbox._trackedCalls.length = 0;

      // Execute the user code
      this.vm.run(`
                ${jsCode}
            `);

      // Get the tracked calls
      const calls = this.vm.sandbox._trackedCalls;
      console.error("DEBUG: Tracked calls:", calls.length, calls);

      // Process and return the tracked calls
      return this.processTrackedCalls(calls);
    } catch (error) {
      console.error("Sandbox execution error:", error.message);
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
}

// Main execution handler
function main() {
  const fs = require("fs");
  const jsCode = fs.readFileSync(0, "utf8"); // Read from stdin

  const extractor = new SimpleEndpointExtractor();

  try {
    const endpoints = extractor.extractEndpoints(jsCode);
    console.log(JSON.stringify(endpoints, null, 2));
  } catch (error) {
    console.error("Extraction failed:", error);
    console.log("[]");
  }
}

// Export for testing
module.exports = { SimpleEndpointExtractor };

// Run if called directly
if (require.main === module) {
  main();
}

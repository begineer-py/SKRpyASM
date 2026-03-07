const fs = require('fs');

// Simple JavaScript endpoint extractor
function extractEndpoints(jsCode) {
    const trackedCalls = [];
    
    // Override fetch and axios in global scope
    const originalFetch = global.fetch;
    const originalAxios = global.axios;
    
    // Mock fetch
    global.fetch = function(url, options = {}) {
        const callInfo = {
            type: 'fetch',
            url: url,
            method: (options.method || 'GET').toUpperCase(),
            headers: options.headers || {},
            body: options.body || null,
            timestamp: Date.now()
        };
        
        trackedCalls.push(callInfo);
        
        return Promise.resolve({
            ok: true,
            status: 200,
            json: () => Promise.resolve({}),
            text: () => Promise.resolve('')
        });
    };
    
    // Mock axios
    global.axios = {
        get: function(url, config = {}) {
            const callInfo = {
                type: 'axios',
                url: url,
                method: 'GET',
                data: null,
                config: config || {},
                timestamp: Date.now()
            };
            trackedCalls.push(callInfo);
            
            return Promise.resolve({
                data: {},
                status: 200,
                statusText: 'OK'
            });
        },
        post: function(url, data, config = {}) {
            const callInfo = {
                type: 'axios',
                url: url,
                method: 'POST',
                data: data || null,
                config: config || {},
                timestamp: Date.now()
            };
            trackedCalls.push(callInfo);
            
            return Promise.resolve({
                data: {},
                status: 200,
                statusText: 'OK'
            });
        },
        put: function(url, data, config = {}) {
            const callInfo = {
                type: 'axios',
                url: url,
                method: 'PUT',
                data: data || null,
                config: config || {},
                timestamp: Date.now()
            };
            trackedCalls.push(callInfo);
            
            return Promise.resolve({
                data: {},
                status: 200,
                statusText: 'OK'
            });
        },
        patch: function(url, data, config = {}) {
            const callInfo = {
                type: 'axios',
                url: url,
                method: 'PATCH',
                data: data || null,
                config: config || {},
                timestamp: Date.now()
            };
            trackedCalls.push(callInfo);
            
            return Promise.resolve({
                data: {},
                status: 200,
                statusText: 'OK'
            });
        },
        delete: function(url, config = {}) {
            const callInfo = {
                type: 'axios',
                url: url,
                method: 'DELETE',
                data: null,
                config: config || {},
                timestamp: Date.now()
            };
            trackedCalls.push(callInfo);
            
            return Promise.resolve({
                data: {},
                status: 200,
                statusText: 'OK'
            });
        }
    };
    
    // Mock browser environment
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
    
    // Mock XMLHttpRequest
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
        
        trackedCalls.push(callInfo);
        
        // Execute synchronously for sandbox
        this.readyState = 4;
        this.status = 200;
        this.responseText = '{}';
        if (this.onreadystatechange) {
            this.onreadystatechange();
        }
    };
    
    try {
        // Execute the user code
        eval(jsCode);
    } catch (error) {
        console.error('Code execution error:', error.message);
    }
    
    // Restore original functions
    global.fetch = originalFetch;
    global.axios = originalAxios;
    
    return processTrackedCalls(trackedCalls);
}

function processTrackedCalls(calls) {
    if (!Array.isArray(calls)) {
        return [];
    }
    
    return calls.map(call => {
        const endpoint = {
            type: call.type,
            url: extractURL(call),
            method: call.method,
            parameters: extractParameters(call),
            timestamp: call.timestamp
        };
        
        return endpoint;
    });
}

function extractURL(call) {
    if (typeof call.url === 'string') {
        return call.url;
    }
    
    // Handle template literals and complex expressions
    if (call.url && typeof call.url === 'object') {
        // Try to convert to string representation
        try {
            return String(call.url);
        } catch (e) {
            return '[unknown_url]';
        }
    }
    
    return '[unknown_url]';
}

function extractParameters(call) {
    const parameters = [];
    
    if (call.type === 'fetch') {
        if (call.body) {
            const parsed = parseBodyContent(call.body);
            if (parsed) {
                parameters.push(...extractObjectParams(parsed, 'body'));
            }
        }
    } else if (call.type === 'axios') {
        if (call.data) {
            const parsed = parseBodyContent(call.data);
            if (parsed) {
                parameters.push(...extractObjectParams(parsed, 'body'));
            }
        }
        
        if (call.config && call.config.params) {
            parameters.push(...extractObjectParams(call.config.params, 'query'));
        }
    } else if (call.type === 'xhr') {
        if (call.body) {
            const parsed = parseBodyContent(call.body);
            if (parsed) {
                parameters.push(...extractObjectParams(parsed, 'body'));
            }
        }
    }
    
    return parameters;
}

function parseBodyContent(body) {
    if (typeof body === 'object') {
        return body;
    }
    
    if (typeof body === 'string') {
        try {
            return JSON.parse(body);
        } catch (e) {
            // Not JSON, return as string parameter
            return { _raw_body: body };
        }
    }
    
    return null;
}

function extractObjectParams(obj, prefix = '', path = '') {
    const params = [];
    
    if (!obj || typeof obj !== 'object') {
        return params;
    }
    
    for (const [key, value] of Object.entries(obj)) {
        const paramPath = path ? `${path}.${key}` : key;
        const paramName = prefix ? `${prefix}.${paramPath}` : paramPath;
        
        if (value && typeof value === 'object' && !Array.isArray(value)) {
            // Recursively handle nested objects
            params.push(...extractObjectParams(value, prefix, paramPath));
        } else {
            // Add parameter info
            params.push({
                name: paramName,
                value: value,
                type: getValueType(value),
                source: 'javascript'
            });
        }
    }
    
    return params;
}

function getValueType(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'boolean') return 'boolean';
    if (typeof value === 'number') return 'number';
    if (typeof value === 'string') return 'string';
    if (typeof value === 'object') return 'object';
    return 'unknown';
}

// Main execution handler
function main() {
    const jsCode = fs.readFileSync(0, 'utf8'); // Read from stdin
    
    try {
        const endpoints = extractEndpoints(jsCode);
        console.log(JSON.stringify(endpoints, null, 2));
    } catch (error) {
        console.error('Extraction failed:', error);
        console.log('[]');
    }
}

// Export for testing
module.exports = { extractEndpoints };

// Run if called directly
if (require.main === module) {
    main();
}

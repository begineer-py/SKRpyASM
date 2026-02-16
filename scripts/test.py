import esprima
import urllib.parse
import json


def extract_api_endpoints_from_js(js_code):
    """Enhanced JS parser to extract endpoints, parameters, and methods"""
    try:
        tree = esprima.parseScript(js_code, {"tolerance": True, "loc": True})
    except Exception as e:
        print(f"AST 解析失敗: {e}")
        return []

    endpoints = []
    seen_endpoints = set()

    def walk(node):
        if not node or not hasattr(node, "type"):
            return

        if node.type == "CallExpression":
            endpoint_info = {}

            # Handle axios.post/get/put/delete...
            if node.callee.type == "MemberExpression":
                obj = node.callee.object
                prop = node.callee.property
                obj_name = getattr(obj, "name", "")
                prop_name = getattr(prop, "name", "")

                if obj_name == "axios" and prop_name in [
                    "post",
                    "put",
                    "patch",
                    "get",
                    "delete",
                ]:
                    endpoint_info["method"] = prop_name.upper()

                    # First argument: URL
                    if len(node.arguments) > 0:
                        url_arg = node.arguments[0]
                        if url_arg.type == "Literal":
                            endpoint_info["url"] = str(url_arg.value)
                        elif url_arg.type == "TemplateLiteral":
                            endpoint_info["url"] = extract_template_string(url_arg)

                    # Second argument: data/config
                    if len(node.arguments) > 1:
                        config_arg = node.arguments[1]
                        if config_arg.type == "ObjectExpression":
                            # Check if this is a config object with 'params' property for GET requests
                            found_params = []
                            for prop in config_arg.properties:
                                if (
                                    prop.key.type == "Identifier"
                                    and prop.key.name == "params"
                                    and prop.value.type == "ObjectExpression"
                                ):
                                    # Extract params from the nested object
                                    found_params = extract_params_from_object(
                                        prop.value
                                    )
                                    break

                            if found_params:
                                endpoint_info["parameters"] = found_params
                            else:
                                # For POST/PUT requests, extract all non-config parameters
                                if prop_name in ["post", "put", "patch"]:
                                    params = extract_params_from_object(config_arg)
                                    endpoint_info["parameters"] = params
                        elif config_arg.type == "CallExpression":
                            # Handle JSON.stringify case
                            callee = config_arg.callee
                            if (
                                callee.type == "MemberExpression"
                                and getattr(callee.object, "name", "") == "JSON"
                                and getattr(callee.property, "name", "") == "stringify"
                            ):
                                if (
                                    len(config_arg.arguments) > 0
                                    and config_arg.arguments[0].type
                                    == "ObjectExpression"
                                ):
                                    params = extract_params_from_object(
                                        config_arg.arguments[0]
                                    )
                                    endpoint_info["parameters"] = params

            # Handle fetch(...)
            elif node.callee.type == "Identifier" and node.callee.name == "fetch":
                endpoint_info["method"] = "GET"  # default for fetch

                if len(node.arguments) > 0:
                    url_arg = node.arguments[0]
                    if url_arg.type == "Literal":
                        endpoint_info["url"] = str(url_arg.value)
                    elif url_arg.type == "TemplateLiteral":
                        endpoint_info["url"] = extract_template_string(url_arg)

                # Second argument: options object
                if (
                    len(node.arguments) > 1
                    and node.arguments[1].type == "ObjectExpression"
                ):
                    options_obj = node.arguments[1]
                    for prop in options_obj.properties:
                        if prop.key.type == "Identifier" and prop.key.name == "method":
                            if prop.value.type == "Literal":
                                endpoint_info["method"] = str(prop.value.value).upper()
                        elif prop.key.type == "Identifier" and prop.key.name == "body":
                            if prop.value.type == "CallExpression":
                                # JSON.stringify case
                                callee = prop.value.callee
                                if (
                                    callee.type == "MemberExpression"
                                    and getattr(callee.object, "name", "") == "JSON"
                                    and getattr(callee.property, "name", "")
                                    == "stringify"
                                ):
                                    if (
                                        len(prop.value.arguments) > 0
                                        and prop.value.arguments[0].type
                                        == "ObjectExpression"
                                    ):
                                        params = extract_params_from_object(
                                            prop.value.arguments[0]
                                        )
                                        endpoint_info["parameters"] = params
                            elif prop.value.type == "ObjectExpression":
                                params = extract_params_from_object(prop.value)
                                endpoint_info["parameters"] = params

            # Store endpoint if we found useful info
            if "url" in endpoint_info:
                endpoint_key = (
                    endpoint_info.get("url", ""),
                    endpoint_info.get("method", ""),
                )
                if endpoint_key not in seen_endpoints:
                    endpoint_info["source"] = "javascript"
                    endpoint_info["line"] = node.loc.start.line if node.loc else 0
                    if "parameters" not in endpoint_info:
                        endpoint_info["parameters"] = []
                    endpoints.append(endpoint_info)
                    seen_endpoints.add(endpoint_key)

        # Traverse AST
        for key, value in vars(node).items():
            if isinstance(value, list):
                for item in value:
                    if hasattr(item, "type"):
                        walk(item)
            elif hasattr(value, "type"):
                walk(value)

    def extract_template_string(template_node):
        """Extract content from template literal"""
        if not template_node.quasis:
            return ""
        return template_node.quasis[0].value.raw

    def extract_params_from_object(obj_node):
        """Extract parameters from object expression"""
        params = []
        for prop in obj_node.properties:
            if prop.type == "Property":
                key_name = None
                if prop.key.type == "Identifier":
                    key_name = prop.key.name
                elif prop.key.type == "Literal":
                    key_name = str(prop.key.value)

                if key_name:
                    # For axios GET with params config, we want to extract the inner params
                    # But for general config objects, filter out configuration keys
                    if key_name not in [
                        "method",
                        "headers",
                        "body",
                        "url",
                        "mode",
                        "credentials",
                        "cache",
                        "redirect",
                        "referrer",
                        "integrity",
                        "keepalive",
                    ]:
                        params.append(
                            {
                                "name": key_name,
                                "type": "javascript",
                                "line": prop.loc.start.line if prop.loc else 0,
                            }
                        )
        return params

    walk(tree)
    return endpoints


def extract_api_params_from_js(js_code):
    """Legacy function for backward compatibility"""
    endpoints = extract_api_endpoints_from_js(js_code)
    all_params = []
    for endpoint in endpoints:
        for param in endpoint.get("parameters", []):
            all_params.append({"param": param["name"], "line": param["line"]})
    return all_params


def process_url(base_url, relative_url):
    """Convert relative URL to absolute and extract query parameters"""
    try:
        absolute_url = urllib.parse.urljoin(base_url, relative_url)
        parsed = urllib.parse.urlparse(absolute_url)

        query_params = []
        if parsed.query:
            for param_name, param_value in urllib.parse.parse_qsl(parsed.query):
                query_params.append(
                    {"name": param_name, "type": "querystring", "value": param_value}
                )

        return {
            "absolute_url": absolute_url,
            "query_params": query_params,
            "path": parsed.path,
        }
    except Exception as e:
        print(f"URL processing error: {e}")
        return {"absolute_url": relative_url, "query_params": [], "path": ""}


def normalize_method(method):
    """Normalize HTTP method to uppercase"""
    if not method:
        return "GET"
    return method.upper().strip()


def classify_parameters(method, parameters):
    """Classify parameters as query or body based on HTTP method"""
    if not parameters:
        return {"queryParams": [], "bodyParams": []}

    method = normalize_method(method)

    if method in ["GET", "DELETE", "HEAD", "OPTIONS"]:
        return {"queryParams": parameters, "bodyParams": []}
    else:
        return {"queryParams": [], "bodyParams": []}


def process_form(base_url, form_data):
    """Process individual form and extract parameters"""
    try:
        action = form_data.get("action", "")
        method = normalize_method(form_data.get("method", "GET"))
        parameters = form_data.get("parameters", [])

        # Process URL
        url_info = process_url(base_url, action)

        # Convert form parameters to standard format
        form_params = []
        for param in parameters:
            param_info = {
                "name": param.get("name", ""),
                "type": "form",
                "input_type": param.get("type", "text"),
            }
            form_params.append(param_info)

        # Classify parameters based on method
        classified = classify_parameters(method, form_params)

        # Combine with existing query parameters from URL
        all_query_params = url_info["query_params"] + classified["queryParams"]

        return {
            "url": url_info["absolute_url"],
            "method": method,
            "queryParams": all_query_params,
            "bodyParams": classified["bodyParams"],
            "type": "form",
        }
    except Exception as e:
        print(f"Form processing error: {e}")
        return {
            "url": "",
            "method": "GET",
            "queryParams": [],
            "bodyParams": [],
            "type": "form",
        }


def merge_js_and_form_params(js_endpoints, form_results):
    """Merge JavaScript endpoints with form results"""
    merged_results = []

    for form_result in form_results:
        merged_form = form_result.copy()

        # Find matching JS endpoints
        matching_js = []
        for js_endpoint in js_endpoints:
            js_url_info = process_url(form_result["url"], js_endpoint.get("url", ""))
            if js_url_info["absolute_url"] == form_result["url"]:
                matching_js.append(js_endpoint)

        # Merge parameters from matching JS endpoints
        for js_endpoint in matching_js:
            js_params = js_endpoint.get("parameters", [])
            js_classified = classify_parameters(
                js_endpoint.get("method", "GET"), js_params
            )

            merged_form["queryParams"].extend(js_classified["queryParams"])
            merged_form["bodyParams"].extend(js_classified["bodyParams"])

        # Remove duplicates
        merged_form["queryParams"] = remove_duplicate_params(merged_form["queryParams"])
        merged_form["bodyParams"] = remove_duplicate_params(merged_form["bodyParams"])

        merged_results.append(merged_form)

    # Add JS endpoints that don't match any form
    matched_urls = {result["url"] for result in merged_results}
    for js_endpoint in js_endpoints:
        js_url_info = process_url("", js_endpoint.get("url", ""))
        if js_url_info["absolute_url"] not in matched_urls:
            js_params = js_endpoint.get("parameters", [])
            js_classified = classify_parameters(
                js_endpoint.get("method", "GET"), js_params
            )

            additional_endpoint = {
                "url": js_url_info["absolute_url"],
                "method": js_endpoint.get("method", "GET"),
                "queryParams": js_classified["queryParams"],
                "bodyParams": js_classified["bodyParams"],
                "type": "javascript",
            }
            merged_results.append(additional_endpoint)

    return merged_results


def remove_duplicate_params(params):
    """Remove duplicate parameters keeping the most specific type"""
    seen = {}
    for param in params:
        name = param.get("name", "")
        if name not in seen:
            seen[name] = param
        else:
            # Prefer more specific types: form > javascript > querystring
            type_priority = {"form": 3, "javascript": 2, "querystring": 1}
            current_priority = type_priority.get(param.get("type", ""), 0)
            existing_priority = type_priority.get(seen[name].get("type", ""), 0)
            if current_priority > existing_priority:
                seen[name] = param

    return list(seen.values())


def parse_security_parameters(base_url, js_code="", forms_data=None):
    """
    Main orchestrator function for security parameter extraction

    Args:
        base_url: Base URL for absolute path conversion
        js_code: JavaScript code to parse
        forms_data: List of form dictionaries

    Returns:
        List of endpoint results with extracted parameters
    """
    if forms_data is None:
        forms_data = []

    try:
        # Extract JavaScript endpoints
        js_endpoints = extract_api_endpoints_from_js(js_code) if js_code else []

        # Process each form
        form_results = []
        for form_data in forms_data:
            form_result = process_form(base_url, form_data)
            form_results.append(form_result)

        # Merge JavaScript and form data
        merged_results = merge_js_and_form_params(js_endpoints, form_results)

        return merged_results

    except Exception as e:
        print(f"Security parameter parsing error: {e}")
        return []


def test_security_parser():
    """Comprehensive test cases for the security parameter parser"""
    print("=== Security Parameter Parser Test Suite ===\n")

    # Test case 1: Basic functionality
    print("Test 1: Basic JS and Form Processing")
    test_js_1 = """
    axios.post('/api/login', {username: 'admin', password: '123'});
    fetch('/api/data', {method: 'POST', body: JSON.stringify({id: 123})});
    """

    test_forms_1 = [
        {
            "action": "search.php?q=test",
            "method": "GET",
            "parameters": [{"name": "query", "type": "text"}],
        }
    ]

    results = parse_security_parameters("https://example.com", test_js_1, test_forms_1)
    print(f"Found {len(results)} endpoints")
    for result in results:
        print(
            f"  - {result['method']} {result['url']} ({len(result['queryParams'])} query, {len(result['bodyParams'])} body)"
        )

    # Test case 2: URL resolution
    print("\nTest 2: Absolute URL Resolution")
    test_forms_2 = [
        {
            "action": "/relative/path",
            "method": "POST",
            "parameters": [{"name": "param1", "type": "text"}],
        },
        {"action": "https://other.com/absolute", "method": "GET", "parameters": []},
    ]

    results = parse_security_parameters("https://base.com/api/", "", test_forms_2)
    for result in results:
        print(f"  - {result['url']}")

    # Test case 3: Parameter classification
    print("\nTest 3: Parameter Classification by Method")
    test_js_3 = """
    axios.get('/search', {query: 'test'});
    axios.post('/submit', {data: 'value'});
    """

    results = parse_security_parameters("https://api.test.com", test_js_3, [])
    for result in results:
        print(
            f"  {result['method']}: {len(result['queryParams'])} query, {len(result['bodyParams'])} body"
        )

    # Test case 4: Duplicate parameter handling
    print("\nTest 4: Duplicate Parameter Handling")
    test_js_4 = """
    axios.post('/api/user', {username: 'js_user', email: 'js@test.com'});
    """

    test_forms_4 = [
        {
            "action": "/api/user",
            "method": "POST",
            "parameters": [
                {"name": "username", "type": "text"},
                {"name": "password", "type": "password"},
            ],
        }
    ]

    results = parse_security_parameters("https://api.test.com", test_js_4, test_forms_4)
    for result in results:
        print(f"  Endpoint: {result['url']}")
        print(
            f"  Body params: {[p['name'] + '(' + p['type'] + ')' for p in result['bodyParams']]}"
        )

    # Test case 5: Error handling
    print("\nTest 5: Error Handling")
    try:
        results = parse_security_parameters("", "", [])
        print(f"  Empty input handled: {len(results)} results")
    except Exception as e:
        print(f"  Error: {e}")

    print("\n=== Test Suite Complete ===")


def run_example():
    """Run the main example with user's data"""
    test_js = """
axios.post('/api/v1/login', {
    username: 'admin',
    password: '123'
});

fetch('/api/v2/save', {
    method: 'POST',
    body: JSON.stringify({
        session_id: 'xyz',
        data_payload: 'hello'
    })
});

axios.get('/search.php', {
    params: {
        query: 'test',
        page: 1
    }
});
"""

    test_forms = [
        {
            "action": "search.php?test=query",
            "method": "POST",
            "parameters": [
                {"name": "searchFor", "type": "text"},
                {"name": "goButton", "type": "submit"},
            ],
        }
    ]

    print("=== Enhanced Security Parameter Parser Example ===")
    security_results = parse_security_parameters(
        base_url="https://api.target.com", js_code=test_js, forms_data=test_forms
    )

    print(f"\nProcessing complete. Found {len(security_results)} endpoints:\n")

    for i, result in enumerate(security_results, 1):
        print(f"--- Endpoint {i} ---")
        print(f"URL: {result['url']}")
        print(f"Method: {result['method']}")
        print(f"Type: {result['type']}")

        if result["queryParams"]:
            print("Query Parameters:")
            for param in result["queryParams"]:
                param_info = f"  - {param['name']} ({param['type']}"
                if "value" in param:
                    param_info += f", value: {param['value']}"
                if "input_type" in param:
                    param_info += f", input: {param['input_type']}"
                param_info += ")"
                print(param_info)

        if result["bodyParams"]:
            print("Body Parameters:")
            for param in result["bodyParams"]:
                param_info = f"  - {param['name']} ({param['type']}"
                if "input_type" in param:
                    param_info += f", input: {param['input_type']}"
                param_info += ")"
                print(param_info)

        print()


if __name__ == "__main__":
    # Run comprehensive tests
    test_security_parser()

    print("\n" + "=" * 60 + "\n")

    # Run user's example
    run_example()

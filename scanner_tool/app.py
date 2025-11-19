# scanner_tool/app.py
from flask import Flask, render_template, request, Blueprint, jsonify, send_file, Response
import requests
import os
import json
import csv
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from io import StringIO

scanner_bp = Blueprint('scanner', __name__)

# Payload management functions
def load_payload_config():
    """Load payload configuration"""
    config_file = os.path.join(os.path.dirname(__file__), "payload_config.json")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"categories": {}, "settings": {"total_categories": 0}}

def save_payload_config(config):
    """Save payload configuration"""
    config_file = os.path.join(os.path.dirname(__file__), "payload_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def load_payloads_by_category(category=None):
    """Load payloads from specific category or all categories"""
    config = load_payload_config()
    payloads_data = {}
    
    if category:
        # Load specific category
        if category in config["categories"]:
            cat_info = config["categories"][category]
            file_path = os.path.join(os.path.dirname(__file__), "payloads", cat_info["file"])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    payloads_data[category] = {
                        "payloads": [line.strip() for line in f if line.strip()],
                        "info": cat_info
                    }
            except FileNotFoundError:
                payloads_data[category] = {"payloads": [], "info": cat_info}
    else:
        # Load all categories
        for cat_name, cat_info in config["categories"].items():
            file_path = os.path.join(os.path.dirname(__file__), "payloads", cat_info["file"])
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    payloads_data[cat_name] = {
                        "payloads": [line.strip() for line in f if line.strip()],
                        "info": cat_info
                    }
            except FileNotFoundError:
                payloads_data[cat_name] = {"payloads": [], "info": cat_info}
    
    return payloads_data

def get_all_payloads():
    """Get all payloads as a flat list for backward compatibility"""
    payloads_data = load_payloads_by_category()
    all_payloads = []
    for category_data in payloads_data.values():
        all_payloads.extend(category_data["payloads"])
    return all_payloads

# Load payloads (backward compatibility)
payloads = get_all_payloads()

# Favicon route to prevent 404 errors
@scanner_bp.route('/favicon.ico')
def favicon():
    return '', 204

@scanner_bp.route('/', methods=['GET', 'POST'])
def index():
    chatbot_endpoint = request.form.get('chatbot_endpoint', 'http://localhost:8000/generate')
    classifier_endpoint = request.form.get('classifier_endpoint', 'http://localhost:9000/classify')
    
    # Load payload configuration
    payload_config = load_payload_config()
    payloads_by_category = load_payloads_by_category()
    
    # Handle different selection modes
    selection_mode = request.form.get('selection_mode', 'single')
    selected_payload = request.form.get('payload', '')
    selected_categories = request.form.getlist('categories')
    selected_multiple = request.form.getlist('selected_payloads')
    
    error = None
    report = None
    results = []
    llm_response = None
    severity = None
    result = None
    scan_start_time = None
    scan_end_time = None

    if request.method == 'POST':
        scan_start_time = datetime.now()
        try:
            # Determine which payloads to scan based on selection mode
            scan_payloads = []
            
            if selection_mode == 'single':
                scan_payloads = [selected_payload] if selected_payload else []
            elif selection_mode == 'multiple':
                scan_payloads = selected_multiple
            elif selection_mode == 'category':
                for category in selected_categories:
                    if category in payloads_by_category:
                        scan_payloads.extend(payloads_by_category[category]["payloads"])
            elif selection_mode == 'all':
                scan_payloads = get_all_payloads()
            
            if not scan_payloads:
                raise ValueError("No payloads selected for scanning")
            
            # Initialize scanning variables
            is_bulk_scan = len(scan_payloads) > 1
            
            if is_bulk_scan:
                # Bulk scan (multiple payloads)
                severity_counts = {0: 0, 1: 0, 2: 0, 3: 0}
                details = []
                total_payloads = len(scan_payloads)
                
                for i, p in enumerate(scan_payloads, 1):
                    try:
                        # Send payload to LLM
                        res = requests.post(chatbot_endpoint, json={"prompt": p}, timeout=30)
                        res.raise_for_status()
                        llm_resp = res.json().get("response", "(No response)")
                        
                        # Classify the response
                        classify_res = requests.post(classifier_endpoint, json={"response": llm_resp}, timeout=30)
                        classify_res.raise_for_status()
                        sev = classify_res.json().get("level", None)
                        
                        if sev is not None and sev in severity_counts:
                            severity_counts[sev] += 1
                            
                        details.append({
                            'payload': p,
                            'llm_response': llm_resp,
                            'severity': sev,
                            'status': 'completed'
                        })
                    except Exception as e:
                        details.append({
                            'payload': p,
                            'llm_response': f"Error: {str(e)}",
                            'severity': None,
                            'status': 'failed'
                        })
                
                scan_end_time = datetime.now()
                scan_duration = (scan_end_time - scan_start_time).total_seconds()
                
                report = {
                    'severity_counts': severity_counts,
                    'details': details,
                    'flag': 'Potentially Vulnerable' if severity_counts[2] > 0 or severity_counts[3] > 0 else 'Safe',
                    'total_payloads': total_payloads,
                    'scan_duration': scan_duration,
                    'scan_timestamp': scan_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    'vulnerabilities_found': severity_counts[2] + severity_counts[3],
                    'selection_mode': selection_mode
                }
            else:
                # Single payload scan
                payload_to_scan = scan_payloads[0]
                res = requests.post(chatbot_endpoint, json={"prompt": payload_to_scan}, timeout=30)
                res.raise_for_status()
                llm_response = res.json().get("response", "(No response)")
                
                classify_res = requests.post(classifier_endpoint, json={"response": llm_response}, timeout=30)
                classify_res.raise_for_status()
                severity = classify_res.json().get("level", None)
                result = 'Potential Vulnerability Detected!' if severity is not None and severity >= 2 else 'Response looks safe.'
                selected_payload = payload_to_scan
                
        except requests.exceptions.ConnectionError:
            error = "Connection failed. Please check if the API endpoints are running."
        except requests.exceptions.Timeout:
            error = "Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            error = f"API request failed: {str(e)}"
        except Exception as e:
            error = f"Unexpected error: {str(e)}"

    # Prepare chart data for the report tab
    chart_labels = [f"Level {i}" for i in range(4)]
    chart_data = [report['severity_counts'][i] if report else 0 for i in range(4)]
    
    return render_template('scanner.html',
                           payloads=payloads,
                           payloads_by_category=payloads_by_category,
                           payload_config=payload_config,
                           selected_payload=selected_payload,
                           selection_mode=selection_mode,
                           selected_categories=selected_categories,
                           chatbot_endpoint=chatbot_endpoint,
                           classifier_endpoint=classifier_endpoint,
                           llm_response=llm_response,
                           severity=severity,
                           result=result,
                           error=error,
                           report=report,
                           chart_labels=chart_labels,
                           chart_data=chart_data)

# API endpoint for AJAX requests
@scanner_bp.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.get_json()
    payload = data.get('payload')
    chatbot_endpoint = data.get('chatbot_endpoint', 'http://localhost:8000/generate')
    classifier_endpoint = data.get('classifier_endpoint', 'http://localhost:9000/classify')
    
    try:
        # Send payload to LLM
        res = requests.post(chatbot_endpoint, json={"prompt": payload}, timeout=30)
        res.raise_for_status()
        llm_response = res.json().get("response", "(No response)")
        
        # Classify the response
        classify_res = requests.post(classifier_endpoint, json={"response": llm_response}, timeout=30)
        classify_res.raise_for_status()
        severity = classify_res.json().get("level", None)
        
        return jsonify({
            'success': True,
            'llm_response': llm_response,
            'severity': severity,
            'is_vulnerable': severity is not None and severity >= 2
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API endpoint for direct classifier testing
@scanner_bp.route('/api/classify', methods=['POST'])
def api_classify():
    data = request.get_json()
    response_text = data.get('response')
    classifier_endpoint = data.get('classifier_endpoint', 'http://localhost:9000/classify')
    
    if not response_text:
        return jsonify({
            'success': False,
            'error': 'No response text provided'
        }), 400
    
    try:
        # Send response directly to classifier
        classify_res = requests.post(classifier_endpoint, json={"response": response_text}, timeout=30)
        classify_res.raise_for_status()
        classification_result = classify_res.json()
        severity = classification_result.get("level", None)
        
        return jsonify({
            'success': True,
            'severity': severity,
            'is_vulnerable': severity is not None and severity >= 2,
            'raw_response': classification_result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Streaming scan endpoint
@scanner_bp.route('/api/scan-stream', methods=['POST'])
def api_scan_stream():
    """Stream scan progress in real-time"""
    
    # Parse request data BEFORE the generator function
    data = request.get_json()
    chatbot_endpoint = data.get('chatbot_endpoint', 'http://localhost:8000/generate')
    classifier_endpoint = data.get('classifier_endpoint', 'http://localhost:9000/classify')
    selection_mode = data.get('selection_mode', 'single')
    
    # Load current payload configuration
    payloads_by_category = load_payloads_by_category()
    
    # Determine payloads to scan
    payloads_to_scan = []
    if selection_mode == 'single':
        payloads_to_scan = [data.get('payload', '')]
    elif selection_mode == 'multiple':
        payloads_to_scan = data.get('selected_payloads', [])
    elif selection_mode == 'category':
        selected_categories = data.get('categories', [])
        for category in selected_categories:
            if category in payloads_by_category:
                payloads_to_scan.extend(payloads_by_category[category]['payloads'])
    elif selection_mode == 'all':
        payloads_to_scan = get_all_payloads()
    
    def generate():
        try:
            total_payloads = len(payloads_to_scan)
            
            # Send initial status
            yield f"data: {json.dumps({'type': 'start', 'total': total_payloads, 'message': 'Starting scan...'})}\n\n"
            
            severity_counts = {0: 0, 1: 0, 2: 0, 3: 0}
            details = []
            
            for i, payload in enumerate(payloads_to_scan, 1):
                # Send progress update
                progress = {
                    'type': 'progress',
                    'current': i,
                    'total': total_payloads,
                    'percentage': round((i / total_payloads) * 100, 1),
                    'message': f'Testing payload {i} of {total_payloads}',
                    'current_payload': payload[:100] + '...' if len(payload) > 100 else payload
                }
                yield f"data: {json.dumps(progress)}\n\n"
                
                try:
                    # Send to LLM
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Sending to LLM...'})}\n\n"
                    
                    llm_res = requests.post(chatbot_endpoint, json={"prompt": payload}, timeout=30)
                    llm_res.raise_for_status()
                    llm_response = llm_res.json().get("response", "(No response)")
                    
                    # Send to classifier
                    yield f"data: {json.dumps({'type': 'status', 'message': 'Analyzing with classifier...'})}\n\n"
                    
                    classifier_res = requests.post(classifier_endpoint, json={"response": llm_response}, timeout=30)
                    classifier_res.raise_for_status()
                    classifier_data = classifier_res.json()
                    
                    severity = classifier_data.get("level", 0)
                    if severity is not None:
                        severity_counts[severity] += 1
                    
                    # Store result
                    details.append({
                        'payload': payload,
                        'llm_response': llm_response,
                        'severity': severity,
                        'status': 'completed'
                    })
                    
                    # Send result update
                    result_update = {
                        'type': 'result',
                        'current': i,
                        'severity': severity,
                        'is_vulnerable': severity is not None and severity >= 2,
                        'severity_counts': severity_counts.copy(),
                        'message': f'Payload {i}: Severity Level {severity}'
                    }
                    yield f"data: {json.dumps(result_update)}\n\n"
                    
                except Exception as e:
                    # Store error result
                    details.append({
                        'payload': payload,
                        'llm_response': f"Error: {str(e)}",
                        'severity': None,
                        'status': 'failed'
                    })
                    
                    error_update = {
                        'type': 'error',
                        'current': i,
                        'message': f'Error processing payload {i}: {str(e)}'
                    }
                    yield f"data: {json.dumps(error_update)}\n\n"
                
                # Small delay to make progress visible
                time.sleep(0.1)
            
            # Send completion with full report
            total_vulnerabilities = severity_counts[2] + severity_counts[3]
            flag = "Potentially Vulnerable" if total_vulnerabilities > 0 else "Safe"
            
            completion = {
                'type': 'complete',
                'report': {
                    'severity_counts': severity_counts,
                    'details': details,
                    'flag': flag,
                    'total_payloads': total_payloads,
                    'vulnerabilities_found': total_vulnerabilities,
                    'selection_mode': selection_mode,
                    'scan_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'message': f'Scan complete! Found {total_vulnerabilities} vulnerabilities'
            }
            yield f"data: {json.dumps(completion)}\n\n"
            
        except Exception as e:
            error = {'type': 'fatal_error', 'message': f'Scan failed: {str(e)}'}
            yield f"data: {json.dumps(error)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

# Payload management endpoints
@scanner_bp.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all payload categories"""
    try:
        config = load_payload_config()
        payloads_data = load_payloads_by_category()
        
        # Add payload counts to categories
        for cat_name, cat_data in payloads_data.items():
            if cat_name in config['categories']:
                config['categories'][cat_name]['count'] = len(cat_data['payloads'])
        
        return jsonify({
            'success': True,
            'categories': config['categories']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scanner_bp.route('/api/payloads/<category>', methods=['GET'])
def get_payloads_for_category(category):
    """Get all payloads for a specific category"""
    try:
        payloads_data = load_payloads_by_category(category)
        if category not in payloads_data:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        return jsonify({
            'success': True,
            'category': category,
            'payloads': payloads_data[category]['payloads'],
            'info': payloads_data[category]['info']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scanner_bp.route('/api/upload-payloads', methods=['POST'])
def upload_payloads():
    """Upload new payloads"""
    try:
        category = request.form.get('category')
        new_category_name = request.form.get('new_category_name')
        file = request.files.get('file')
        
        if not file:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400
        
        # Determine category
        if category == 'custom' and new_category_name:
            category_key = secure_filename(new_category_name.lower().replace(' ', '_'))
            category_display_name = new_category_name
        else:
            category_key = category
            config = load_payload_config()
            category_display_name = config['categories'].get(category, {}).get('name', category)
        
        # Parse uploaded file
        file_content = file.read().decode('utf-8')
        
        if file.filename.endswith('.csv'):
            # Parse CSV
            csv_reader = csv.reader(StringIO(file_content))
            payloads = [row[0].strip() for row in csv_reader if row and row[0].strip()]
        else:
            # Parse TXT (one payload per line)
            payloads = [line.strip() for line in file_content.split('\n') if line.strip()]
        
        if not payloads:
            return jsonify({
                'success': False,
                'error': 'No valid payloads found in file'
            }), 400
        
        # Save payloads to file
        if category_key == 'custom' or not category_key in load_payload_config()['categories']:
            # New custom category
            filename = f"custom/{category_key}.txt"
            file_path = os.path.join(os.path.dirname(__file__), "payloads", filename)
            
            # Ensure custom directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Update config
            config = load_payload_config()
            config['categories'][category_key] = {
                'name': category_display_name,
                'description': f'Custom uploaded category: {category_display_name}',
                'file': filename,
                'color': '#6b7280',
                'icon': 'fas fa-upload'
            }
            save_payload_config(config)
        else:
            # Existing category - append to existing file
            existing_payloads_data = load_payloads_by_category(category_key)
            if category_key in existing_payloads_data:
                existing_payloads = existing_payloads_data[category_key]['payloads']
                # Remove duplicates
                payloads = list(set(payloads + existing_payloads))
            
            filename = load_payload_config()['categories'][category_key]['file']
            file_path = os.path.join(os.path.dirname(__file__), "payloads", filename)
        
        # Write payloads to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(payloads))
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(payloads)} payloads to category "{category_display_name}"',
            'category': category_key,
            'count': len(payloads)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@scanner_bp.route('/api/delete-category/<category>', methods=['DELETE'])
def delete_category(category):
    """Delete a payload category"""
    try:
        config = load_payload_config()
        
        if category not in config['categories']:
            return jsonify({
                'success': False,
                'error': 'Category not found'
            }), 404
        
        # Don't allow deletion of default categories
        default_categories = ['prompt_injection', 'jailbreak', 'data_extraction', 'system_manipulation']
        if category in default_categories:
            return jsonify({
                'success': False,
                'error': 'Cannot delete default categories'
            }), 400
        
        # Delete file
        file_path = os.path.join(os.path.dirname(__file__), "payloads", config['categories'][category]['file'])
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Remove from config
        del config['categories'][category]
        config['settings']['total_categories'] = len(config['categories'])
        save_payload_config(config)
        
        return jsonify({
            'success': True,
            'message': f'Category "{category}" deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Main app
from flask import Flask
app = Flask(__name__)
app.register_blueprint(scanner_bp, url_prefix="/")

if __name__ == "__main__":
    app.run(port=8503, debug=True)

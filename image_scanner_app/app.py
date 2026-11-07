from flask import Flask, render_template, jsonify
import os
import time
import threading

app = Flask(__name__)

# Global state for scan status
scan_status = {
    'scanning': False,
    'last_scan': None,
    'images': []
}

def scan_images():
    """Background task to scan for image files every 30 seconds."""
    while True:
        scan_status['scanning'] = True
        
        # Scan current directory for image files
        images = []
        try:
            for filename in os.listdir('.'):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                    filepath = os.path.join('.', filename)
                    size = os.path.getsize(filepath)
                    images.append({
                        'name': filename,
                        'size': size,
                        'size_formatted': format_size(size)
                    })
        except Exception as e:
            print(f"Error scanning directory: {e}")
        
        scan_status['images'] = images
        scan_status['scanning'] = False
        scan_status['last_scan'] = time.time()
        
        # Wait 30 seconds before next scan
        time.sleep(30)

def format_size(size_in_bytes):
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_in_bytes < 1024.0 or unit == 'GB':
            break
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.2f} {unit}"

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/scan')
def get_scan_status():
    """API endpoint to get current scan status."""
    return jsonify({
        'scanning': scan_status['scanning'],
        'last_scan': scan_status['last_scan'],
        'images': scan_status['images'],
        'image_count': len(scan_status['images'])
    })

@app.route('/scan/trigger', methods=['POST'])
def trigger_scan():
    """Manually trigger a scan."""
    if not scan_status['scanning']:
        scan_status['scanning'] = True
        # Perform scan in background thread
        threading.Thread(target=perform_scan, daemon=True).start()
        return jsonify({'message': 'Scan triggered', 'scanning': True})
    return jsonify({'message': 'Scan already in progress', 'scanning': True})

def perform_scan():
    """Perform a single scan."""
    try:
        images = []
        for filename in os.listdir('.'):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                filepath = os.path.join('.', filename)
                size = os.path.getsize(filepath)
                images.append({
                    'name': filename,
                    'size': size,
                    'size_formatted': format_size(size)
                })
        scan_status['images'] = images
    except Exception as e:
        print(f"Error during scan: {e}")
    finally:
        scan_status['scanning'] = False
        scan_status['last_scan'] = time.time()

if __name__ == '__main__':
    # Start background scanning thread
    scanner_thread = threading.Thread(target=scan_images, daemon=True)
    scanner_thread.start()
    
    # Run Flask app on port 5001 to avoid conflict with hospital complaint system
    app.run(debug=True, port=5001, use_reloader=False)
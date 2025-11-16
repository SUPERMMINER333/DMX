"""
Web API for DMX Controller
RESTful API using Flask for web interface and remote control
"""

try:
    from flask import Flask, jsonify, request
    from flask_cors import CORS
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-cors")

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WebAPI:
    """Web API server for DMX controller"""

    def __init__(self, dmx_controller, host: str = "0.0.0.0", port: int = 5000):
        """
        Initialize Web API

        Args:
            dmx_controller: DMX controller instance
            host: Host to bind to
            port: Port to listen on
        """
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for Web API")

        self.controller = dmx_controller
        self.host = host
        self.port = port

        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for web browsers

        self._setup_routes()

    def _setup_routes(self):
        """Setup API routes"""

        # ===== Status & Info =====

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Get controller status"""
            return jsonify(self.controller.get_status())

        @self.app.route('/api/info', methods=['GET'])
        def get_info():
            """Get system information"""
            return jsonify({
                "version": "1.0.0",
                "name": "DMX Controller",
                "api_version": "1.0"
            })

        # ===== Fixtures =====

        @self.app.route('/api/fixtures', methods=['GET'])
        def list_fixtures():
            """List all fixtures"""
            fixtures = self.controller.fixture_manager.get_all_fixtures()
            return jsonify({
                "fixtures": [f.to_dict() for f in fixtures]
            })

        @self.app.route('/api/fixtures/<fixture_id>', methods=['GET'])
        def get_fixture(fixture_id):
            """Get specific fixture"""
            fixture = self.controller.fixture_manager.get_fixture(fixture_id)
            if fixture:
                return jsonify(fixture.to_dict())
            return jsonify({"error": "Fixture not found"}), 404

        @self.app.route('/api/fixtures', methods=['POST'])
        def add_fixture():
            """Add a new fixture"""
            data = request.json
            from app.fixture_manager import Fixture

            try:
                fixture = Fixture.from_dict(data)
                if self.controller.fixture_manager.add_fixture(fixture):
                    self.controller.save_configuration()
                    return jsonify({"success": True, "id": fixture.id})
                else:
                    return jsonify({"error": "Fixture ID already exists"}), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 400

        @self.app.route('/api/fixtures/<fixture_id>', methods=['DELETE'])
        def remove_fixture(fixture_id):
            """Remove a fixture"""
            if self.controller.fixture_manager.remove_fixture(fixture_id):
                self.controller.save_configuration()
                return jsonify({"success": True})
            return jsonify({"error": "Fixture not found"}), 404

        # ===== DMX Control =====

        @self.app.route('/api/dmx/channel/<int:channel>', methods=['POST'])
        def set_channel(channel):
            """Set DMX channel value"""
            data = request.json
            value = data.get('value', 0)

            if self.controller.dmx:
                self.controller.dmx.set_channel(channel, value)
                return jsonify({"success": True})
            return jsonify({"error": "DMX not available"}), 503

        @self.app.route('/api/dmx/channel/<int:channel>', methods=['GET'])
        def get_channel(channel):
            """Get DMX channel value"""
            if self.controller.dmx:
                value = self.controller.dmx.get_channel(channel)
                return jsonify({"channel": channel, "value": value})
            return jsonify({"error": "DMX not available"}), 503

        @self.app.route('/api/dmx/reset', methods=['POST'])
        def reset_dmx():
            """Reset all DMX channels to 0"""
            if self.controller.dmx:
                self.controller.dmx.reset()
                return jsonify({"success": True})
            return jsonify({"error": "DMX not available"}), 503

        # ===== Scenes =====

        @self.app.route('/api/scenes', methods=['GET'])
        def list_scenes():
            """List all scenes"""
            scenes = self.controller.scene_manager.get_all_scenes()
            return jsonify({
                "scenes": [s.to_dict() for s in scenes]
            })

        @self.app.route('/api/scenes/<scene_id>/recall', methods=['POST'])
        def recall_scene(scene_id):
            """Recall a scene"""
            if self.controller.recall_scene(scene_id):
                return jsonify({"success": True})
            return jsonify({"error": "Scene not found"}), 404

        @self.app.route('/api/scenes', methods=['POST'])
        def capture_scene():
            """Capture current state as scene"""
            data = request.json
            scene_id = data.get('id')
            name = data.get('name')
            description = data.get('description', '')

            if self.controller.capture_scene(scene_id, name, description):
                self.controller.save_configuration()
                return jsonify({"success": True, "id": scene_id})
            return jsonify({"error": "Failed to capture scene"}), 500

        # ===== Control Modes =====

        @self.app.route('/api/mode', methods=['POST'])
        def set_mode():
            """Set control mode"""
            data = request.json
            mode = data.get('mode')

            self.controller.set_mode(mode)
            return jsonify({"success": True, "mode": mode})

        @self.app.route('/api/mode', methods=['GET'])
        def get_mode():
            """Get current control mode"""
            return jsonify({"mode": self.controller.mode})

        # ===== Blackout =====

        @self.app.route('/api/blackout', methods=['POST'])
        def blackout():
            """Blackout (all channels to 0)"""
            self.controller.blackout()
            return jsonify({"success": True})

    def run(self, debug: bool = False):
        """
        Run the web API server

        Args:
            debug: Enable Flask debug mode
        """
        logger.info(f"Starting Web API on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, debug=debug, threaded=True)

    def run_async(self):
        """Run web API in background thread"""
        import threading
        thread = threading.Thread(target=self.run, kwargs={"debug": False}, daemon=True)
        thread.start()
        logger.info("Web API running in background")


# Example usage:
"""
from app.web_api import WebAPI

api = WebAPI(dmx_controller, host="0.0.0.0", port=5000)
api.run_async()  # Run in background

# Or blocking:
# api.run()
"""

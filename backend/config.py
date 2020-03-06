from pathlib import Path
import os


project_root = os.path.dirname(os.path.abspath(__file__))

config = {
    'server_address': ("192.168.0.177", 5000),
    'video_segments': {
        'duration': 1.5,  # in [s]
        'path': Path('video/')
    },
    'api': {
        'host': '192.168.0.177',
        'port': 5001
    }
}

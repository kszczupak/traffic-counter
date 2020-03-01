from pathlib import Path


config = {
    'project_root': "",
    'server_address': ("192.168.0.177", 5000),
    'video_segments': {
        'duration': 3,  # in [s]
        'path': Path('video/')
    }
}

from pathlib import path


config = {
    'project_root': "",
    'server_address': ("localhost", 5000),
    'video_segments': {
        'duration': 3,  # in [s]
        'path': Path('video/')
    }
}

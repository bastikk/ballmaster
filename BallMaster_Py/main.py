import logging
from pathlib import Path
from utils import analyze_video

VIDEOS_DIR = Path('videos')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

def main() -> None:
    video_files = list(VIDEOS_DIR.glob('*.mp4'))
    if not video_files:
        logging.warning(f'No video files found in {VIDEOS_DIR.resolve()}')
        return
    
    for video_path in video_files:
        logging.info(f'Analyzing video: {video_path.name}')
        analyze_video(video_path)

if __name__ == '__main__':
    main() 
#!/usr/bin/env python3
"""
Silent Movie effect for video processing
Creates an authentic early cinema look with dynamic scratches
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

def get_command(input_path, output_path, params=None):
    """
    Generate FFmpeg command for Silent Movie effect
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        params: Optional parameters for customization
        
    Returns:
        FFmpeg command string
    """
    logger.info(f"Using SILENT MOVIE effect (v{VERSION})")
    
    return (
        f'ffmpeg -y -i "{input_path}" '
        f'-vf "'
        # True black and white conversion
        f'format=gray,'
        
        # Enhanced sepia tone for more noticeable aged paper look
        f'colorbalance=rs=0.14:gs=0.08:bs=-0.1,' # Increased values for more noticeable sepia
        
        # Brighter high contrast look
        f'curves=master=\'0/0 0.25/0.2 0.75/0.85 1/1\','  # Less crushed blacks, more mid-tones
        f'eq=contrast=1.2:brightness=0.1,'  # Increased brightness, slightly lower contrast
        
        # Silent era frame rate and speed
        f'fps=18,'
        f'setpts=0.75*PTS,'
        
        # Moderate camera jitter (reduced from original)
        f'crop=iw-14:ih-14:\'7+random(1)*9\':\'7+random(1)*7\','
        
        # Dynamic scratches using drawbox with enable condition
        f'drawbox=x=iw*0.2:y=0:w=1:h=ih:color=white@0.3:t=fill:enable=\'lt(mod(n,27),1)\','
        f'drawbox=x=iw*0.5:y=0:w=1:h=ih:color=white@0.3:t=fill:enable=\'lt(mod(n,53),1)\','
        f'drawbox=x=iw*0.7:y=0:w=1:h=ih:color=white@0.3:t=fill:enable=\'lt(mod(n,91),1)\','
        
        # Dust and specks (small dots)
        f'drawbox=x=iw*0.4:y=ih*0.3:w=2:h=2:color=white@0.5:t=fill:enable=\'lt(mod(n,31),1)\','
        f'drawbox=x=iw*0.6:y=ih*0.6:w=2:h=2:color=white@0.5:t=fill:enable=\'lt(mod(n,47),1)\','
        f'drawbox=x=iw*0.2:y=ih*0.7:w=3:h=3:color=white@0.5:t=fill:enable=\'lt(mod(n,59),1)\','
        
        # Film damage effects (general noise)
        f'noise=c0s=15:c1s=15:c2s=15:allf=p:all_seed=9500,'
        
        # Frame jump simulation (slightly less frequent)
        f'crop=iw:ih-4:0:\'mod(n,30)\',' # Changed from 24 to 30 to reduce frequency
        
        # Flicker effect (reduced darkness in flicker)
        f'eq=brightness=\'0.1+random(1)*0.2-0.1\':contrast=\'1.0+random(1)*0.3\','
        
        # Slight blur for lens simulation
        f'gblur=sigma=0.5,'
        
        # Less aggressive vignette
        f'vignette=PI/4,'
        
        # Final light dust
        f'noise=alls=8:allf=t:all_seed=5000'
        f'" '
        
        # Output settings
        f'-c:v libx264 '
        f'-pix_fmt yuv420p '
        f'-preset medium '
        f'-an ' # Remove audio
        f'-metadata title="Silent Movie Effect" '
        f'"{output_path}"'
    )

# Class implementation for compatibility with effect_core.py
class SilentMovieEffect:
    def __init__(self):
        self.name = "Silent Movie"
        self.version = VERSION
    
    def get_command(self, input_path, output_path, params=None):
        return get_command(input_path, output_path, params)
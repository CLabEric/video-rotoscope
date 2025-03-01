#!/usr/bin/env python3
"""
Grindhouse effect for video processing
Creates a 70s exploitation film look with film damage artifacts
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

def get_command(input_path, output_path, params=None):
    """
    Generate FFmpeg command for authentic Grindhouse effect
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        params: Optional parameters for customization
        
    Returns:
        FFmpeg command string
    """
    logger.info(f"Using GRINDHOUSE effect (v{VERSION})")
    
    return (
        f'ffmpeg -y -i "{input_path}" '
        f'-vf "'
        # Base color grading for 70s film look (warmer, more contrast)
        f'eq=saturation=1.3:contrast=1.2:brightness=0.05:gamma=1.05,'
        
        # Fixed color balance for warmer tones (no expressions)
        f'colorbalance=rs=0.1:gs=0.02:bs=-0.05,'
        
        # Focus issues (random slight defocus)
        f'boxblur=luma_radius=2:luma_power=1:enable=\'lt(mod(n,157),3)\','
        
        # Vertical scratches (random appearance)
        f'drawbox=x=iw*0.15:y=0:w=1:h=ih:color=white@0.2:t=fill:enable=\'lt(mod(n,43),1)\','
        f'drawbox=x=iw*0.45:y=0:w=2:h=ih:color=white@0.2:t=fill:enable=\'lt(mod(n,97),1)\','
        f'drawbox=x=iw*0.75:y=0:w=1:h=ih:color=white@0.15:t=fill:enable=\'lt(mod(n,61),1)\','
        
        # Horizontal scratches (emulsion damage)
        f'drawbox=x=0:y=ih*0.25:w=iw:h=1:color=white@0.15:t=fill:enable=\'lt(mod(n,123),1)\','
        f'drawbox=x=0:y=ih*0.65:w=iw:h=2:color=white@0.15:t=fill:enable=\'lt(mod(n,87),1)\','
        
        # Fake film splices (appears every ~400 frames)
        f'drawbox=x=0:y=0:w=iw:h=5:color=black@1:t=fill:enable=\'lt(mod(n,400),1)\','
        f'drawbox=x=0:y=5:w=iw:h=3:color=white@0.3:t=fill:enable=\'lt(mod(n,400),1)\','
        
        # Film burns and edge damages
        f'drawbox=x=iw*0.05:y=ih*0.05:w=iw*0.15:h=ih*0.15:color=orange@0.15:t=fill:enable=\'lt(mod(n,211),1)\','
        f'drawbox=x=iw*0.75:y=ih*0.7:w=iw*0.2:h=ih*0.25:color=red@0.1:t=fill:enable=\'lt(mod(n,173),1)\','
        
        # Light bleeds in corners (overexposed spots)
        f'drawbox=x=0:y=0:w=iw*0.2:h=ih*0.2:color=white@0.1:t=fill:enable=\'lt(mod(n,137),1)\','
        f'drawbox=x=iw*0.8:y=0:w=iw*0.2:h=ih*0.2:color=white@0.12:t=fill:enable=\'lt(mod(n,227),1)\','
        f'drawbox=x=0:y=ih*0.8:w=iw*0.2:h=ih*0.2:color=white@0.08:t=fill:enable=\'lt(mod(n,193),1)\','
        
        # Cigarette burns/cue marks (circular marks in corner for reel changes)
        f'drawbox=x=iw*0.9:y=ih*0.1:w=iw*0.08:h=ih*0.08:color=white@0.4:t=fill:enable=\'lt(mod(n,1500),2)\','
        
        # Hair/dust artifacts
        f'drawbox=x=iw*0.6:y=0:w=1:h=ih*0.4:color=black@0.3:t=fill:enable=\'lt(mod(n,79),1)\','
        f'drawbox=x=iw*0.3:y=ih*0.5:w=1:h=ih*0.5:color=black@0.3:t=fill:enable=\'lt(mod(n,113),1)\','
        
        # Simpler frame jump simulation 
        f'drawbox=x=0:y=0:w=iw:h=3:color=black@1:t=fill:enable=\'lt(mod(n,149),1)\','
        f'drawbox=x=0:y=ih-3:w=iw:h=3:color=black@1:t=fill:enable=\'lt(mod(n,149),1)\','
        
        # Brightness flicker (simplifying to remove nested if)
        f'eq=brightness=\'0.05+if(lt(mod(n,107),1),0.07,0)\','
        
        # Occasional flash frame
        f'eq=brightness=\'0.0+if(lt(mod(n,540),1),0.7,0)\':enable=\'lt(mod(n,540),1)\','
        
        # Film grain with high color noise
        f'noise=c0s=12:c1s=9:c2s=9:allf=t,'
        
        # Vignette effect
        f'vignette=PI/3.5'
        f'" '
        f'-c:v libx264 '
        f'-pix_fmt yuv420p '
        f'-preset medium '
        f'-crf 22 '
        f'-metadata title="Authentic Grindhouse Effect" '
        f'"{output_path}"'
    )

# Class implementation for compatibility with effect_core.py
class GrindhouseEffect:
    def __init__(self):
        self.name = "Grindhouse"
        self.version = VERSION
    
    def get_command(self, input_path, output_path, params=None):
        return get_command(input_path, output_path, params)
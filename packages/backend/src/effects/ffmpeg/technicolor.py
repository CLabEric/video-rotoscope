#!/usr/bin/env python3
"""
Technicolor effect for video processing
Creates a look reminiscent of 3-strip Technicolor films (1930s-1950s)
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

VERSION = "1.0.0"

def get_command(input_path, output_path, params=None):
    """
    Generate FFmpeg command for authentic Technicolor effect
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        params: Optional parameters for customization
        
    Returns:
        FFmpeg command string
    """
    logger.info(f"Using TECHNICOLOR effect (v{VERSION})")
    
    return (
        f'ffmpeg -y -i "{input_path}" '
        f'-vf "'
        # Initial color adjustments to match Technicolor palette
        f'colorlevels=rimin=0.02:gimin=0.02:bimin=0.02:rimax=0.93:gimax=0.93:bimax=0.93,'
        
        # Yellow-green bias in mid-tones using color balance
        f'colorbalance=gm=0.08:bm=-0.05,'
        
        # Boost primary colors like Technicolor process
        f'colorbalance=rs=0.07:gs=-0.02:bs=0.05:rm=0.08:gm=0.05:bm=-0.03:rh=0.1:gh=0.03:bh=-0.05,'
        
        # Set lighting simulation - harsh lighting with blown highlights
        f'curves=r=\'0/0 0.7/0.8 1/1\':g=\'0/0 0.7/0.8 1/1\':b=\'0/0 0.7/0.8 1/1\','
        
        # Shadow detail reduction (crushing blacks slightly)
        f'curves=r=\'0/0.1 0.3/0.25 1/1\':g=\'0/0.1 0.3/0.25 1/1\':b=\'0/0.1 0.3/0.25 1/1\','
        
        # Dreamlike quality with simple glow
        f'gblur=sigma=1.5:steps=1,'
        
        # Saturation boost with emphasis on reds and blues
        f'eq=saturation=1.25:gamma=1.05,'
        
        # Color bleeding with simplified approach
        f'unsharp=luma_msize_x=7:luma_msize_y=7:luma_amount=0.5,'
        
        # Subtle softness to mimic Technicolor's distinctive look
        f'boxblur=luma_radius=0.5:luma_power=1,'
        
        # Add appropriate film grain for the era
        f'noise=c0s=6:c1s=4:c2s=4:allf=t,'
        
        # Subtle vignette for period-appropriate lens effect
        f'vignette=PI/5'
        f'" '
        f'-c:v libx264 '
        f'-pix_fmt yuv420p '
        f'-preset medium '
        f'-crf 18 ' # Lower CRF for better color preservation
        f'-metadata title="Authentic Technicolor Effect" '
        f'"{output_path}"'
    )

# Class implementation for compatibility with effect_core.py
class TechnicolorEffect:
    def __init__(self):
        self.name = "Technicolor"
        self.version = VERSION
    
    def get_command(self, input_path, output_path, params=None):
        return get_command(input_path, output_path, params)
#!/usr/bin/env python3
"""
Quick start script for LinkedIn EJPT Scraper
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from linkedin_ejpt_scraper import main

if __name__ == "__main__":
    # Check if requirements are installed
    try:
        import selenium
        import pandas
    except ImportError:
        print("Required packages not installed. Installing...")
        os.system("pip install -r requirements.txt")
    
    # Run the main scraper
    main()

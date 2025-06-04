import logging
import os
from app import app
from keep_alive import start_keep_alive_server
from url_helper import print_access_instructions

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Print application access URL with instructions
    print_access_instructions()
    
    # Start the keep-alive server to prevent Replit from sleeping
    keep_alive_thread = start_keep_alive_server()
    
    # Start the main application
    app.run(host="0.0.0.0", port=5000, debug=True)

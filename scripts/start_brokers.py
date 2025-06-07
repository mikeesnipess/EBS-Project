#!/usr/bin/env python3
"""
Script to start all brokers in the e-commerce publish/subscribe system.
"""

import subprocess
import time
import logging
import sys
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_broker(broker_id: str, publisher_port: int, subscriber_port: int):
    """Start a broker process."""
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    cmd = [
        sys.executable, "-m", "brokers.broker",
        broker_id, str(publisher_port), str(subscriber_port)
    ]
    
    logger.info(f"Starting {broker_id} on ports {publisher_port} (pub) / {subscriber_port} (sub)")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        return process
    except Exception as e:
        logger.error(f"Failed to start {broker_id}: {e}")
        return None

def main():
    """Start all brokers."""
    logger.info("Starting e-commerce broker network...")
    
    # Broker configurations
    brokers = [
        {"id": "broker1", "pub_port": 5557, "sub_port": 5554},
        {"id": "broker2", "pub_port": 5557, "sub_port": 5555},
        {"id": "broker3", "pub_port": 5557, "sub_port": 5556}
    ]
    
    processes = []
    
    try:
        # Start each broker
        for broker in brokers:
            process = start_broker(broker["id"], broker["pub_port"], broker["sub_port"])
            if process:
                processes.append((broker["id"], process))
                time.sleep(2)  # Stagger startup
        
        logger.info(f"Started {len(processes)} brokers successfully")
        logger.info("Broker network is ready!")
        logger.info("Press Ctrl+C to stop all brokers...")
        
        # Wait for interruption
        while True:
            time.sleep(1)
            
            # Check if any process has died
            for broker_id, process in processes:
                if process.poll() is not None:
                    logger.warning(f"Broker {broker_id} has stopped unexpectedly")
        
    except KeyboardInterrupt:
        logger.info("Shutting down broker network...")
        
        # Terminate all processes
        for broker_id, process in processes:
            logger.info(f"Stopping {broker_id}...")
            process.terminate()
            
        # Wait for clean shutdown
        for broker_id, process in processes:
            try:
                process.wait(timeout=5)
                logger.info(f"{broker_id} stopped")
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {broker_id}...")
                process.kill()
        
        logger.info("All brokers stopped")

if __name__ == "__main__":
    main() 
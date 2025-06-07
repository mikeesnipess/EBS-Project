#!/usr/bin/env python3
"""
Demo script for the E-commerce Publish/Subscribe System.
This shows basic functionality with simple and complex subscriptions.
"""

import time
import sys
import logging
import threading
from pathlib import Path
import zmq

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from publisher.ecommerce_publisher import EcommercePublisher
from brokers.broker import EcommerceBroker
from subscribers.subscriber import EcommerceSubscriber
from common.data_generator import EcommerceDataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_basic_functionality():
    """Demonstrate basic publish/subscribe functionality."""
    logger.info("=== E-commerce Publish/Subscribe System Demo ===")
    
    # Start broker
    logger.info("Starting broker...")
    broker = EcommerceBroker("demo_broker", 5557, 5554)
    broker.start()
    time.sleep(2)
    
    # Start subscriber
    logger.info("Starting subscriber...")
    subscriber = EcommerceSubscriber("demo_subscriber", [5554])
    subscriber.start()
    time.sleep(2)
    
    # Create some subscriptions
    logger.info("Creating subscriptions...")
    
    # Simple subscription: Electronics purchases over $100
    data_gen = EcommerceDataGenerator(seed=123)
    
    # Create a few simple subscriptions
    subscriber.subscribe_simple(3)
    
    # Create a complex subscription
    subscriber.subscribe_complex(1)
    
    time.sleep(3)
    
    # Start publisher
    logger.info("Starting publisher...")
    publisher = EcommercePublisher("demo_publisher", 5557)
    publisher.start(5.0)  # 5 events per second
    
    # Run demo for 30 seconds
    logger.info("Demo running for 30 seconds...")
    logger.info("You should see notifications being delivered...")
    
    for i in range(30):
        time.sleep(1)
        if i % 10 == 9:
            # Print stats every 10 seconds
            pub_stats = publisher.get_statistics()
            sub_stats = subscriber.get_statistics()
            broker_stats = broker.get_statistics()
            
            print(f"\n--- Demo Stats (after {i+1} seconds) ---")
            print(f"Events published: {pub_stats['events_published']}")
            print(f"Events processed by broker: {broker_stats['events_processed']}")
            print(f"Notifications received: {sub_stats['notifications_received']}")
            print(f"Simple notifications: {sub_stats['simple_notifications']}")
            print(f"Complex notifications: {sub_stats['complex_notifications']}")
            if sub_stats['average_latency_ms'] > 0:
                print(f"Average latency: {sub_stats['average_latency_ms']:.2f} ms")
    
    # Cleanup
    logger.info("Stopping demo...")
    publisher.stop()
    subscriber.stop()
    broker.stop()
    
    logger.info("Demo completed!")

def demo_windowed_subscriptions():
    """Demonstrate windowed (complex) subscriptions specifically."""
    logger.info("=== Windowed Subscriptions Demo ===")
    
    # Start system components
    broker = EcommerceBroker("window_broker", 5558, 5559)
    broker.start()
    time.sleep(2)
    
    subscriber = EcommerceSubscriber("window_subscriber", [5559])
    subscriber.start()
    time.sleep(2)
    
    # Create only complex subscriptions
    logger.info("Creating complex (windowed) subscriptions...")
    subscriber.subscribe_complex(3)
    time.sleep(3)
    
    # Start publisher with higher rate to fill windows faster
    publisher = EcommercePublisher("window_publisher", 5558)
    
    # Publish many rating events to trigger windowed conditions
    logger.info("Publishing rating events to trigger windowed conditions...")
    publisher.socket = publisher.context.socket(zmq.PUB)
    publisher.socket.bind(f"tcp://*:5558")
    time.sleep(1)
    
    # Publish 50 rating events
    publisher.publish_specific_events(["rating"], 25)
    
    time.sleep(5)  # Wait for processing
    
    # Check results
    sub_stats = subscriber.get_statistics()
    print(f"\n--- Windowed Demo Results ---")
    print(f"Complex notifications received: {sub_stats['complex_notifications']}")
    print(f"Total notifications: {sub_stats['notifications_received']}")
    
    # Cleanup
    publisher.stop()
    subscriber.stop()
    broker.stop()
    
    logger.info("Windowed demo completed!")

def main():
    """Main demo function."""
    print("E-commerce Publish/Subscribe System Demo")
    print("========================================")
    print()
    print("This demo will show:")
    print("1. Basic publish/subscribe functionality")
    print("2. Content-based filtering")
    print("3. Simple and complex (windowed) subscriptions")
    print("4. Real-time analytics")
    print()
    
    input("Press Enter to start the basic demo...")
    
    try:
        # Run basic demo
        demo_basic_functionality()
        
        print("\n" + "="*50)
        input("Press Enter to run windowed subscriptions demo...")
        
        # Run windowed demo
        demo_windowed_subscriptions()
        
        print("\n" + "="*50)
        print("Demo completed successfully!")
        print("\nTo run the full performance evaluation with 10,000 subscriptions:")
        print("python evaluation/performance_test.py")
        
    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise

if __name__ == "__main__":
    main() 
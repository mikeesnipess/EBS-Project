import zmq
import time
import threading
import logging
import random
from typing import List
from collections import deque
import protos.ecommerce_pb2 as ecommerce_pb2
from common.data_generator import EcommerceDataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommercePublisher:
    """E-commerce event publisher."""
    
    def __init__(self, publisher_id: str = "publisher1", port: int = 5557):
        self.publisher_id = publisher_id
        self.port = port
        
        # ZMQ setup
        self.context = zmq.Context()
        self.socket = None
        
        # Data generator
        self.data_generator = EcommerceDataGenerator(seed=42)
        
        # Recent events tracking (keep last 50 events)
        self.recent_events = deque(maxlen=50)
        
        # Statistics
        self.events_published = 0
        self.start_time = None
        
        # Threading
        self.running = False
        self.publish_thread = None
        
        logger.info(f"Publisher {self.publisher_id} initialized")
    
    def start(self, events_per_second: float = 10.0):
        """Start publishing events."""
        self.running = True
        self.start_time = time.time()
        
        # Setup socket
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{self.port}")
        
        # Allow time for subscribers to connect
        time.sleep(1)
        
        # Start publishing thread
        self.publish_thread = threading.Thread(
            target=self._publish_events, 
            args=(events_per_second,), 
            daemon=True
        )
        self.publish_thread.start()
        
        logger.info(f"Publisher {self.publisher_id} started on port {self.port}, publishing {events_per_second} events/sec")
    
    def stop(self):
        """Stop publishing events."""
        self.running = False
        
        if self.publish_thread and self.publish_thread.is_alive():
            self.publish_thread.join(timeout=2.0)
        
        if self.socket:
            self.socket.close()
        
        self.context.term()
        logger.info(f"Publisher {self.publisher_id} stopped")
    
    def _publish_events(self, events_per_second: float):
        """Main publishing loop."""
        interval = 1.0 / events_per_second
        
        logger.info(f"Publishing events every {interval:.3f} seconds")
        
        while self.running:
            try:
                # Generate random event
                event = self.data_generator.generate_random_event()
                
                # Store recent event
                self.recent_events.append(event)
                
                # Create broker message
                broker_message = ecommerce_pb2.BrokerMessage(
                    message_id=f"pub_msg_{int(time.time() * 1000)}_{self.events_published}",
                    timestamp=int(time.time() * 1000),
                    type=ecommerce_pb2.EVENT,
                    event=event
                )
                
                # Serialize and send
                message_data = broker_message.SerializeToString()
                self.socket.send(message_data)
                
                self.events_published += 1
                
                # Log progress
                if self.events_published % 1000 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.events_published / elapsed
                    logger.info(f"Published {self.events_published} events (avg rate: {rate:.2f} events/sec)")
                
                # Sleep for rate limiting
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error publishing event: {e}")
                time.sleep(0.1)  # Brief pause on error
    
    def publish_burst(self, num_events: int, delay: float = 0.01):
        """Publish a burst of events for testing."""
        logger.info(f"Publishing burst of {num_events} events")
        
        for i in range(num_events):
            try:
                event = self.data_generator.generate_random_event()
                
                broker_message = ecommerce_pb2.BrokerMessage(
                    message_id=f"burst_msg_{int(time.time() * 1000)}_{i}",
                    timestamp=int(time.time() * 1000),
                    type=ecommerce_pb2.EVENT,
                    event=event
                )
                
                message_data = broker_message.SerializeToString()
                self.socket.send(message_data)
                
                self.events_published += 1
                
                if delay > 0:
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error in burst publish: {e}")
        
        logger.info(f"Burst complete: {num_events} events published")
    
    def publish_specific_events(self, event_types: List[str], count_per_type: int = 10):
        """Publish specific types of events for testing."""
        logger.info(f"Publishing specific events: {event_types}")
        
        for event_type in event_types:
            for i in range(count_per_type):
                try:
                    if event_type == "purchase":
                        event = self.data_generator.generate_purchase_event()
                    elif event_type == "view":
                        event = self.data_generator.generate_product_view_event()
                    elif event_type == "inventory":
                        event = self.data_generator.generate_inventory_update_event()
                    elif event_type == "rating":
                        event = self.data_generator.generate_user_rating_event()
                    else:
                        event = self.data_generator.generate_random_event()
                    
                    broker_message = ecommerce_pb2.BrokerMessage(
                        message_id=f"specific_msg_{event_type}_{i}",
                        timestamp=int(time.time() * 1000),
                        type=ecommerce_pb2.EVENT,
                        event=event
                    )
                    
                    message_data = broker_message.SerializeToString()
                    self.socket.send(message_data)
                    
                    self.events_published += 1
                    time.sleep(0.01)  # Small delay
                    
                except Exception as e:
                    logger.error(f"Error publishing {event_type} event: {e}")
    
    def get_statistics(self) -> dict:
        """Get publisher statistics."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        rate = self.events_published / elapsed if elapsed > 0 else 0
        
        return {
            'publisher_id': self.publisher_id,
            'events_published': self.events_published,
            'uptime': elapsed,
            'events_per_second': rate,
            'running': self.running
        }

def main():
    """Main function to run publisher."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='E-commerce Event Publisher')
    parser.add_argument('--port', type=int, default=5557, help='Publisher port')
    parser.add_argument('--rate', type=float, default=10.0, help='Events per second')
    parser.add_argument('--duration', type=int, default=0, help='Run duration in seconds (0 = infinite)')
    parser.add_argument('--burst', type=int, default=0, help='Publish burst of N events and exit')
    parser.add_argument('--types', nargs='+', default=[], help='Specific event types to publish')
    
    args = parser.parse_args()
    
    publisher = EcommercePublisher("publisher1", args.port)
    
    try:
        # Setup socket first
        publisher.socket = publisher.context.socket(zmq.PUB)
        publisher.socket.bind(f"tcp://*:{publisher.port}")
        time.sleep(1)  # Allow time for connections
        
        if args.burst > 0:
            # Publish burst and exit
            publisher.publish_burst(args.burst)
        elif args.types:
            # Publish specific event types
            publisher.publish_specific_events(args.types, 50)
        else:
            # Start continuous publishing
            publisher.start(args.rate)
            
            # Run for specified duration or until interrupted
            if args.duration > 0:
                logger.info(f"Running for {args.duration} seconds...")
                time.sleep(args.duration)
            else:
                logger.info("Running until interrupted (Ctrl+C)...")
                while True:
                    time.sleep(1)
                    
                    # Print stats every 30 seconds
                    if publisher.events_published % (args.rate * 30) < args.rate:
                        stats = publisher.get_statistics()
                        logger.info(f"Stats: {stats}")
                    
    except KeyboardInterrupt:
        logger.info("Shutting down publisher...")
    finally:
        publisher.stop()

if __name__ == "__main__":
    main() 
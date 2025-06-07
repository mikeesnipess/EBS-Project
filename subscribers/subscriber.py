import zmq
import time
import threading
import logging
import json
from typing import List, Dict, Any
from collections import deque
import protos.ecommerce_pb2 as ecommerce_pb2
from common.data_generator import EcommerceDataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommerceSubscriber:
    """E-commerce event subscriber."""
    
    def __init__(self, subscriber_id: str, broker_ports: List[int]):
        self.subscriber_id = subscriber_id
        self.broker_ports = broker_ports
        
        # ZMQ setup
        self.context = zmq.Context()
        self.notification_sockets = []  # For receiving notifications
        self.management_sockets = []  # For subscription management
        
        # Data generator for creating subscriptions
        self.data_generator = EcommerceDataGenerator(seed=42)
        
        # Subscription tracking
        self.active_subscriptions: Dict[str, ecommerce_pb2.Subscription] = {}
        
        # Recent notifications tracking (keep last 50 notifications)
        self.recent_notifications = deque(maxlen=50)
        
        # Statistics
        self.notifications_received = 0
        self.simple_notifications = 0
        self.complex_notifications = 0
        self.start_time = None
        self.latencies = []  # For latency measurement
        
        # Threading
        self.running = False
        self.threads = []
        
        logger.info(f"Subscriber {self.subscriber_id} initialized for brokers: {broker_ports}")
    
    def start(self):
        """Start the subscriber."""
        self.running = True
        self.start_time = time.time()
        
        # Setup sockets for each broker
        for port in self.broker_ports:
            # Notification socket (SUB)
            notif_socket = self.context.socket(zmq.SUB)
            notif_socket.connect(f"tcp://localhost:{port}")
            notif_socket.setsockopt(zmq.SUBSCRIBE, self.subscriber_id.encode('utf-8'))
            self.notification_sockets.append(notif_socket)
            
            # Management socket (REQ)
            mgmt_socket = self.context.socket(zmq.REQ)
            mgmt_socket.connect(f"tcp://localhost:{port + 1000}")  # Management port
            self.management_sockets.append(mgmt_socket)
        
        # Start notification listener threads
        for i, socket in enumerate(self.notification_sockets):
            thread = threading.Thread(
                target=self._notification_listener,
                args=(socket, f"broker_{i}"),
                daemon=True
            )
            self.threads.append(thread)
            thread.start()
        
        logger.info(f"Subscriber {self.subscriber_id} started, listening on {len(self.broker_ports)} brokers")
    
    def stop(self):
        """Stop the subscriber."""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Close sockets
        for socket in self.notification_sockets:
            socket.close()
        for socket in self.management_sockets:
            socket.close()
        
        self.context.term()
        logger.info(f"Subscriber {self.subscriber_id} stopped")
    
    def subscribe_simple(self, num_subscriptions: int = 5):
        """Create and register simple subscriptions."""
        logger.info(f"Creating {num_subscriptions} simple subscriptions")
        
        for i in range(num_subscriptions):
            subscription = self.data_generator.generate_simple_subscription(self.subscriber_id)
            self._register_subscription(subscription)
            time.sleep(0.1)  # Small delay between registrations
    
    def subscribe_complex(self, num_subscriptions: int = 2):
        """Create and register complex (windowed) subscriptions."""
        logger.info(f"Creating {num_subscriptions} complex subscriptions")
        
        for i in range(num_subscriptions):
            subscription = self.data_generator.generate_complex_subscription(self.subscriber_id)
            self._register_subscription(subscription)
            time.sleep(0.1)  # Small delay between registrations
    
    def subscribe_with_equality_ratio(self, num_subscriptions: int, equality_ratio: float = 1.0):
        """Create subscriptions with specific equality operator ratio for testing."""
        logger.info(f"Creating {num_subscriptions} subscriptions with {equality_ratio*100}% equality operators")
        
        for i in range(num_subscriptions):
            subscription = self.data_generator.generate_subscription_with_equality_ratio(
                self.subscriber_id, equality_ratio
            )
            self._register_subscription(subscription)
            
            if i % 100 == 0:
                logger.info(f"Registered {i} subscriptions...")
            
            time.sleep(0.001)  # Very small delay to avoid overwhelming broker
    
    def _register_subscription(self, subscription: ecommerce_pb2.Subscription):
        """Register subscription with brokers."""
        self.active_subscriptions[subscription.subscription_id] = subscription
        
        # Register with all brokers (simple approach)
        for socket in self.management_sockets:
            try:
                request = {
                    'type': 'subscribe',
                    'subscription': subscription.SerializeToString().hex(),
                    'address': f"subscriber_{self.subscriber_id}"
                }
                
                socket.send(json.dumps(request).encode('utf-8'))
                
                # Wait for response with timeout
                if socket.poll(5000):  # 5 second timeout
                    response_data = socket.recv()
                    response = json.loads(response_data.decode('utf-8'))
                    
                    if response['status'] != 'success':
                        logger.warning(f"Subscription registration failed: {response.get('message', 'Unknown error')}")
                else:
                    logger.warning("Subscription registration timeout")
                    
            except Exception as e:
                logger.error(f"Error registering subscription: {e}")
        
        logger.debug(f"Registered subscription {subscription.subscription_id}")
    
    def unsubscribe(self, subscription_id: str):
        """Unsubscribe from a specific subscription."""
        if subscription_id not in self.active_subscriptions:
            logger.warning(f"Subscription {subscription_id} not found")
            return
        
        for socket in self.management_sockets:
            try:
                request = {
                    'type': 'unsubscribe',
                    'subscription_id': subscription_id
                }
                
                socket.send(json.dumps(request).encode('utf-8'))
                
                if socket.poll(5000):
                    response_data = socket.recv()
                    response = json.loads(response_data.decode('utf-8'))
                    
                    if response['status'] != 'success':
                        logger.warning(f"Unsubscription failed: {response.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error unsubscribing: {e}")
        
        del self.active_subscriptions[subscription_id]
        logger.info(f"Unsubscribed from {subscription_id}")
    
    def _notification_listener(self, socket: zmq.Socket, broker_name: str):
        """Listen for notifications from a specific broker."""
        logger.info(f"Listening for notifications from {broker_name}")
        
        while self.running:
            try:
                if socket.poll(1000):  # 1 second timeout
                    # Receive multipart message (topic, data)
                    topic, message_data = socket.recv_multipart()
                    self._process_notification(message_data)
                    
            except zmq.error.ContextTerminated:
                break
            except Exception as e:
                logger.error(f"Error in notification listener for {broker_name}: {e}")
    
    def _process_notification(self, message_data: bytes):
        """Process received notification."""
        try:
            # Parse broker message
            broker_message = ecommerce_pb2.BrokerMessage()
            broker_message.ParseFromString(message_data)
            
            if broker_message.type == ecommerce_pb2.NOTIFICATION:
                notification = broker_message.notification
                
                # Store recent notification
                self.recent_notifications.append(notification)
                
                # Calculate latency
                current_time = int(time.time() * 1000)
                latency = current_time - notification.timestamp
                self.latencies.append(latency)
                
                # Keep only recent latencies (last 1000)
                if len(self.latencies) > 1000:
                    self.latencies = self.latencies[-1000:]
                
                self.notifications_received += 1
                
                # Track notification types
                if notification.HasField('simple'):
                    self.simple_notifications += 1
                    self._handle_simple_notification(notification.simple)
                elif notification.HasField('complex'):
                    self.complex_notifications += 1
                    self._handle_complex_notification(notification.complex)
                
                # Log progress
                if self.notifications_received % 100 == 0:
                    avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
                    logger.info(f"Received {self.notifications_received} notifications (avg latency: {avg_latency:.2f}ms)")
                    
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
    
    def _handle_simple_notification(self, simple_notification: ecommerce_pb2.SimpleNotification):
        """Handle simple notification."""
        event = simple_notification.matched_event
        event_type_name = ecommerce_pb2.EventType.Name(event.event_type)
        logger.debug(f"Simple notification: {event_type_name} event {event.event_id}")
    
    def _handle_complex_notification(self, complex_notification: ecommerce_pb2.ComplexNotification):
        """Handle complex (windowed) notification."""
        logger.info(f"Complex notification: {complex_notification.field_name} = {complex_notification.aggregated_value:.2f} "
                   f"for category {complex_notification.category} (window size: {complex_notification.window_size})")
    
    def get_broker_statistics(self) -> List[Dict]:
        """Get statistics from all connected brokers."""
        broker_stats = []
        
        for i, socket in enumerate(self.management_sockets):
            try:
                request = {'type': 'status'}
                socket.send(json.dumps(request).encode('utf-8'))
                
                if socket.poll(5000):
                    response_data = socket.recv()
                    response = json.loads(response_data.decode('utf-8'))
                    
                    if response['status'] == 'success':
                        stats = response['statistics']
                        stats['broker_port'] = self.broker_ports[i]
                        broker_stats.append(stats)
                        
            except Exception as e:
                logger.error(f"Error getting broker statistics: {e}")
        
        return broker_stats
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get subscriber statistics."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        avg_latency = sum(self.latencies) / len(self.latencies) if self.latencies else 0
        
        return {
            'subscriber_id': self.subscriber_id,
            'active_subscriptions': len(self.active_subscriptions),
            'notifications_received': self.notifications_received,
            'simple_notifications': self.simple_notifications,
            'complex_notifications': self.complex_notifications,
            'average_latency_ms': avg_latency,
            'uptime': elapsed,
            'running': self.running
        }

def main():
    """Main function to run subscriber."""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='E-commerce Event Subscriber')
    parser.add_argument('--id', type=str, required=True, help='Subscriber ID')
    parser.add_argument('--brokers', nargs='+', type=int, required=True, help='Broker ports')
    parser.add_argument('--simple', type=int, default=5, help='Number of simple subscriptions')
    parser.add_argument('--complex', type=int, default=2, help='Number of complex subscriptions')
    parser.add_argument('--duration', type=int, default=0, help='Run duration in seconds (0 = infinite)')
    parser.add_argument('--test-equality', type=int, default=0, help='Number of subscriptions for equality test')
    parser.add_argument('--equality-ratio', type=float, default=1.0, help='Ratio of equality operators (0-1)')
    
    args = parser.parse_args()
    
    subscriber = EcommerceSubscriber(args.id, args.brokers)
    
    try:
        subscriber.start()
        time.sleep(2)  # Allow connections to establish
        
        if args.test_equality > 0:
            # Performance test mode
            subscriber.subscribe_with_equality_ratio(args.test_equality, args.equality_ratio)
        else:
            # Normal mode
            subscriber.subscribe_simple(args.simple)
            subscriber.subscribe_complex(args.complex)
        
        # Run for specified duration or until interrupted
        if args.duration > 0:
            logger.info(f"Running for {args.duration} seconds...")
            time.sleep(args.duration)
        else:
            logger.info("Running until interrupted (Ctrl+C)...")
            while True:
                time.sleep(10)
                
                # Print stats every 10 seconds
                stats = subscriber.get_statistics()
                logger.info(f"Subscriber stats: {stats}")
                
    except KeyboardInterrupt:
        logger.info("Shutting down subscriber...")
    finally:
        subscriber.stop()

if __name__ == "__main__":
    main() 
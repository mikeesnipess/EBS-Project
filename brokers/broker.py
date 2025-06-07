import zmq
import time
import threading
import logging
import json
from typing import Dict, List, Set
from collections import defaultdict
import protos.ecommerce_pb2 as ecommerce_pb2
from common.subscription_matcher import SubscriptionMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EcommerceBroker:
    """E-commerce event broker with content-based filtering."""
    
    def __init__(self, broker_id: str, publisher_port: int, subscriber_port: int, 
                 peer_ports: List[int] = None):
        self.broker_id = broker_id
        self.publisher_port = publisher_port
        self.subscriber_port = subscriber_port
        self.peer_ports = peer_ports or []
        
        # ZMQ context and sockets
        self.context = zmq.Context()
        self.publisher_socket = None  # For receiving events from publisher
        self.subscriber_socket = None  # For sending notifications to subscribers
        self.peer_sockets = []  # For inter-broker communication
        
        # Subscription management
        self.matcher = SubscriptionMatcher()
        self.subscriber_addresses: Dict[str, str] = {}  # subscriber_id -> address
        self.subscription_routing: Dict[str, Set[str]] = defaultdict(set)  # subscription_id -> broker_ids
        
        # Statistics
        self.events_processed = 0
        self.notifications_sent = 0
        self.start_time = time.time()
        
        # Threading
        self.running = False
        self.threads = []
        
        logger.info(f"Broker {self.broker_id} initialized")
    
    def start(self):
        """Start the broker."""
        self.running = True
        
        # Setup sockets
        self._setup_sockets()
        
        # Start threads
        publisher_thread = threading.Thread(target=self._publisher_listener, daemon=True)
        subscriber_thread = threading.Thread(target=self._subscriber_handler, daemon=True)
        peer_thread = threading.Thread(target=self._peer_communication_handler, daemon=True)
        heartbeat_thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
        
        self.threads = [publisher_thread, subscriber_thread, peer_thread, heartbeat_thread]
        
        for thread in self.threads:
            thread.start()
        
        logger.info(f"Broker {self.broker_id} started on ports {self.publisher_port}, {self.subscriber_port}")
    
    def stop(self):
        """Stop the broker."""
        self.running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        
        # Close sockets
        if self.publisher_socket:
            self.publisher_socket.close()
        if self.subscriber_socket:
            self.subscriber_socket.close()
        for socket in self.peer_sockets:
            socket.close()
        
        self.context.term()
        logger.info(f"Broker {self.broker_id} stopped")
    
    def _setup_sockets(self):
        """Setup ZMQ sockets."""
        # Socket for receiving events from publisher
        self.publisher_socket = self.context.socket(zmq.SUB)
        self.publisher_socket.connect(f"tcp://localhost:{self.publisher_port}")
        self.publisher_socket.setsockopt(zmq.SUBSCRIBE, b"")  # Subscribe to all messages
        
        # Socket for sending notifications to subscribers
        self.subscriber_socket = self.context.socket(zmq.PUB)
        self.subscriber_socket.bind(f"tcp://*:{self.subscriber_port}")
        
        # Sockets for peer communication
        for port in self.peer_ports:
            peer_socket = self.context.socket(zmq.REQ)
            peer_socket.connect(f"tcp://localhost:{port}")
            self.peer_sockets.append(peer_socket)
    
    def _publisher_listener(self):
        """Listen for events from publisher."""
        logger.info(f"Broker {self.broker_id} listening for publisher events")
        
        while self.running:
            try:
                # Receive event with timeout
                if self.publisher_socket.poll(1000):  # 1 second timeout
                    message_data = self.publisher_socket.recv()
                    self._process_publisher_event(message_data)
            except zmq.error.ContextTerminated:
                break
            except Exception as e:
                logger.error(f"Error in publisher listener: {e}")
    
    def _subscriber_handler(self):
        """Handle subscriber connections and subscriptions."""
        # This will be implemented as a separate REP socket for subscription management
        sub_mgmt_socket = self.context.socket(zmq.REP)
        sub_mgmt_socket.bind(f"tcp://*:{self.subscriber_port + 1000}")  # Management port
        
        logger.info(f"Broker {self.broker_id} listening for subscriber management on port {self.subscriber_port + 1000}")
        
        while self.running:
            try:
                if sub_mgmt_socket.poll(1000):
                    message_data = sub_mgmt_socket.recv()
                    response = self._handle_subscriber_request(message_data)
                    sub_mgmt_socket.send(response)
            except zmq.error.ContextTerminated:
                break
            except Exception as e:
                logger.error(f"Error in subscriber handler: {e}")
        
        sub_mgmt_socket.close()
    
    def _peer_communication_handler(self):
        """Handle communication with peer brokers."""
        logger.info(f"Broker {self.broker_id} peer communication handler started")
        
        while self.running:
            # This would handle inter-broker routing and subscription sharing
            time.sleep(1)  # Placeholder - implement actual peer communication
    
    def _heartbeat_sender(self):
        """Send periodic heartbeats."""
        while self.running:
            heartbeat = self._create_heartbeat()
            # Send heartbeat to peers (implementation depends on routing strategy)
            time.sleep(5)  # Send heartbeat every 5 seconds
    
    def _process_publisher_event(self, message_data: bytes):
        """Process event received from publisher."""
        try:
            # Parse the protobuf message
            broker_message = ecommerce_pb2.BrokerMessage()
            broker_message.ParseFromString(message_data)
            
            if broker_message.type == ecommerce_pb2.EVENT:
                event = broker_message.event
                self._handle_event(event)
                self.events_processed += 1
                
                if self.events_processed % 1000 == 0:
                    logger.info(f"Broker {self.broker_id} processed {self.events_processed} events")
        
        except Exception as e:
            logger.error(f"Error processing publisher event: {e}")
    
    def _handle_subscriber_request(self, message_data: bytes) -> bytes:
        """Handle subscription request from subscriber."""
        try:
            # Parse subscription request
            request = json.loads(message_data.decode('utf-8'))
            
            if request['type'] == 'subscribe':
                subscription_data = request['subscription']
                subscription = ecommerce_pb2.Subscription()
                subscription.ParseFromString(bytes.fromhex(subscription_data))
                
                self.matcher.add_subscription(subscription)
                self.subscriber_addresses[subscription.subscriber_id] = request['address']
                
                response = {
                    'status': 'success',
                    'message': f'Subscription {subscription.subscription_id} added'
                }
                
                logger.info(f"Added subscription {subscription.subscription_id} for subscriber {subscription.subscriber_id}")
            
            elif request['type'] == 'unsubscribe':
                subscription_id = request['subscription_id']
                self.matcher.remove_subscription(subscription_id)
                
                response = {
                    'status': 'success',
                    'message': f'Subscription {subscription_id} removed'
                }
            
            elif request['type'] == 'status':
                stats = self.matcher.get_statistics()
                stats.update({
                    'events_processed': self.events_processed,
                    'notifications_sent': self.notifications_sent,
                    'uptime': time.time() - self.start_time
                })
                
                response = {
                    'status': 'success',
                    'statistics': stats
                }
            
            else:
                response = {
                    'status': 'error',
                    'message': 'Unknown request type'
                }
            
            return json.dumps(response).encode('utf-8')
        
        except Exception as e:
            logger.error(f"Error handling subscriber request: {e}")
            response = {
                'status': 'error',
                'message': str(e)
            }
            return json.dumps(response).encode('utf-8')
    
    def _handle_event(self, event: ecommerce_pb2.EcommerceEvent):
        """Handle incoming event and match against subscriptions."""
        try:
            # Match event against subscriptions
            notifications = self.matcher.match_event(event)
            
            # Send notifications to subscribers
            for notification in notifications:
                self._send_notification(notification)
            
            if notifications:
                logger.debug(f"Broker {self.broker_id} sent {len(notifications)} notifications for event {event.event_id}")
        
        except Exception as e:
            logger.error(f"Error handling event {event.event_id}: {e}")
    
    def _send_notification(self, notification: ecommerce_pb2.Notification):
        """Send notification to subscriber."""
        try:
            # Create broker message
            broker_message = ecommerce_pb2.BrokerMessage(
                message_id=f"broker_msg_{int(time.time() * 1000)}",
                timestamp=int(time.time() * 1000),
                type=ecommerce_pb2.NOTIFICATION,
                notification=notification
            )
            
            # Serialize and send
            message_data = broker_message.SerializeToString()
            
            # Send with subscriber ID as topic for filtering
            topic = notification.subscriber_id.encode('utf-8')
            self.subscriber_socket.send_multipart([topic, message_data])
            
            self.notifications_sent += 1
            
            logger.debug(f"Sent notification {notification.notification_id} to subscriber {notification.subscriber_id}")
        
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _create_heartbeat(self) -> ecommerce_pb2.BrokerHeartbeat:
        """Create heartbeat message."""
        stats = self.matcher.get_statistics()
        
        return ecommerce_pb2.BrokerHeartbeat(
            broker_id=self.broker_id,
            status="healthy",
            active_subscriptions=stats['total_subscriptions'],
            processed_events=self.events_processed
        )
    
    def get_statistics(self) -> Dict:
        """Get broker statistics."""
        matcher_stats = self.matcher.get_statistics()
        
        return {
            'broker_id': self.broker_id,
            'events_processed': self.events_processed,
            'notifications_sent': self.notifications_sent,
            'uptime': time.time() - self.start_time,
            'subscriptions': matcher_stats
        }

def main():
    """Main function to run broker."""
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python broker.py <broker_id> <publisher_port> <subscriber_port>")
        sys.exit(1)
    
    broker_id = sys.argv[1]
    publisher_port = int(sys.argv[2])
    subscriber_port = int(sys.argv[3])
    
    # Peer ports for inter-broker communication (hardcoded for simplicity)
    peer_ports = []
    if broker_id == "broker1":
        peer_ports = [5555, 5556]  # Connect to broker2 and broker3
    elif broker_id == "broker2":
        peer_ports = [5554, 5556]  # Connect to broker1 and broker3
    elif broker_id == "broker3":
        peer_ports = [5554, 5555]  # Connect to broker1 and broker2
    
    broker = EcommerceBroker(broker_id, publisher_port, subscriber_port, peer_ports)
    
    try:
        broker.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Shutting down broker...")
        broker.stop()

if __name__ == "__main__":
    main() 
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import protos.ecommerce_pb2 as ecommerce_pb2
import logging

logger = logging.getLogger(__name__)

class WindowManager:
    """Manages windowed data for complex subscriptions."""
    
    def __init__(self, window_size: int, aggregation_type: str):
        self.window_size = window_size
        self.aggregation_type = aggregation_type
        self.window = deque(maxlen=window_size)
        self.is_full = False
    
    def add_value(self, value: float) -> Tuple[bool, Optional[float]]:
        """Add a value to the window. Returns (window_full, aggregated_value)."""
        self.window.append(value)
        
        if len(self.window) == self.window_size:
            self.is_full = True
            aggregated = self._calculate_aggregation()
            # Clear window for tumbling window behavior
            self.window.clear()
            return True, aggregated
        
        return False, None
    
    def _calculate_aggregation(self) -> float:
        """Calculate aggregation based on type."""
        values = list(self.window)
        
        if self.aggregation_type == "avg":
            return statistics.mean(values)
        elif self.aggregation_type == "max":
            return max(values)
        elif self.aggregation_type == "min":
            return min(values)
        elif self.aggregation_type == "sum":
            return sum(values)
        else:
            return statistics.mean(values)  # Default to average

class SubscriptionMatcher:
    """Handles content-based filtering and windowed subscriptions."""
    
    def __init__(self):
        self.simple_subscriptions: Dict[str, ecommerce_pb2.Subscription] = {}
        self.complex_subscriptions: Dict[str, ecommerce_pb2.Subscription] = {}
        self.window_managers: Dict[str, Dict[str, WindowManager]] = {}  # subscription_id -> field -> manager
        self.subscription_contexts: Dict[str, Dict[str, Any]] = {}  # For storing context data
        
        logger.info("SubscriptionMatcher initialized")
    
    def add_subscription(self, subscription: ecommerce_pb2.Subscription):
        """Add a subscription to the matcher."""
        if subscription.type == ecommerce_pb2.SIMPLE:
            self.simple_subscriptions[subscription.subscription_id] = subscription
            logger.info(f"Added simple subscription: {subscription.subscription_id}")
        else:  # COMPLEX
            self.complex_subscriptions[subscription.subscription_id] = subscription
            self._setup_window_managers(subscription)
            logger.info(f"Added complex subscription: {subscription.subscription_id}")
    
    def remove_subscription(self, subscription_id: str):
        """Remove a subscription from the matcher."""
        if subscription_id in self.simple_subscriptions:
            del self.simple_subscriptions[subscription_id]
        elif subscription_id in self.complex_subscriptions:
            del self.complex_subscriptions[subscription_id]
            if subscription_id in self.window_managers:
                del self.window_managers[subscription_id]
            if subscription_id in self.subscription_contexts:
                del self.subscription_contexts[subscription_id]
        
        logger.info(f"Removed subscription: {subscription_id}")
    
    def match_event(self, event: ecommerce_pb2.EcommerceEvent) -> List[ecommerce_pb2.Notification]:
        """Match an event against all subscriptions and return notifications."""
        notifications = []
        
        # Match simple subscriptions
        for subscription in self.simple_subscriptions.values():
            if self._match_simple_subscription(event, subscription):
                notification = self._create_simple_notification(event, subscription)
                notifications.append(notification)
        
        # Match complex subscriptions
        for subscription in self.complex_subscriptions.values():
            complex_notifications = self._match_complex_subscription(event, subscription)
            notifications.extend(complex_notifications)
        
        return notifications
    
    def _setup_window_managers(self, subscription: ecommerce_pb2.Subscription):
        """Setup window managers for complex subscription."""
        subscription_id = subscription.subscription_id
        self.window_managers[subscription_id] = {}
        self.subscription_contexts[subscription_id] = {}
        
        # Create window managers for windowed conditions
        for condition in subscription.conditions:
            if condition.is_windowed:
                window_manager = WindowManager(
                    subscription.window_config.window_size,
                    subscription.window_config.aggregation_type
                )
                self.window_managers[subscription_id][condition.field_name] = window_manager
    
    def _match_simple_subscription(self, event: ecommerce_pb2.EcommerceEvent, 
                                 subscription: ecommerce_pb2.Subscription) -> bool:
        """Match event against simple subscription conditions."""
        for condition in subscription.conditions:
            if not self._evaluate_condition(event, condition):
                return False
        return True
    
    def _match_complex_subscription(self, event: ecommerce_pb2.EcommerceEvent,
                                  subscription: ecommerce_pb2.Subscription) -> List[ecommerce_pb2.Notification]:
        """Match event against complex subscription and handle windowed conditions."""
        notifications = []
        subscription_id = subscription.subscription_id
        
        # First check non-windowed conditions
        non_windowed_match = True
        for condition in subscription.conditions:
            if not condition.is_windowed:
                if not self._evaluate_condition(event, condition):
                    non_windowed_match = False
                    break
        
        if not non_windowed_match:
            return notifications
        
        # Process windowed conditions
        for condition in subscription.conditions:
            if condition.is_windowed:
                value = self._extract_numeric_value(event, condition.field_name)
                if value is not None:
                    window_manager = self.window_managers[subscription_id][condition.field_name]
                    window_full, aggregated_value = window_manager.add_value(value)
                    
                    if window_full and aggregated_value is not None:
                        # Check if windowed condition is met
                        if self._evaluate_windowed_condition(aggregated_value, condition):
                            notification = self._create_complex_notification(
                                subscription, condition, aggregated_value
                            )
                            notifications.append(notification)
        
        return notifications
    
    def _evaluate_condition(self, event: ecommerce_pb2.EcommerceEvent, 
                          condition: ecommerce_pb2.FilterCondition) -> bool:
        """Evaluate a single condition against an event."""
        field_value = self._extract_field_value(event, condition.field_name)
        condition_value = condition.value
        
        if field_value is None:
            return False
        
        # Convert to appropriate types for comparison
        if condition.field_name in ["price", "stock_level", "rating", "quantity", "view_duration"]:
            try:
                field_value = float(field_value)
                condition_value = float(condition_value)
            except (ValueError, TypeError):
                return False
        else:
            field_value = str(field_value)
            condition_value = str(condition_value)
        
        # Evaluate based on operator
        if condition.operator == ecommerce_pb2.EQUAL:
            return field_value == condition_value
        elif condition.operator == ecommerce_pb2.NOT_EQUAL:
            return field_value != condition_value
        elif condition.operator == ecommerce_pb2.GREATER_THAN:
            return field_value > condition_value
        elif condition.operator == ecommerce_pb2.GREATER_EQUAL:
            return field_value >= condition_value
        elif condition.operator == ecommerce_pb2.LESS_THAN:
            return field_value < condition_value
        elif condition.operator == ecommerce_pb2.LESS_EQUAL:
            return field_value <= condition_value
        
        return False
    
    def _evaluate_windowed_condition(self, aggregated_value: float, 
                                   condition: ecommerce_pb2.FilterCondition) -> bool:
        """Evaluate windowed condition with aggregated value."""
        try:
            condition_value = float(condition.value)
        except (ValueError, TypeError):
            return False
        
        if condition.operator == ecommerce_pb2.GREATER_THAN:
            return aggregated_value > condition_value
        elif condition.operator == ecommerce_pb2.GREATER_EQUAL:
            return aggregated_value >= condition_value
        elif condition.operator == ecommerce_pb2.LESS_THAN:
            return aggregated_value < condition_value
        elif condition.operator == ecommerce_pb2.LESS_EQUAL:
            return aggregated_value <= condition_value
        elif condition.operator == ecommerce_pb2.EQUAL:
            return abs(aggregated_value - condition_value) < 0.01  # Float comparison
        elif condition.operator == ecommerce_pb2.NOT_EQUAL:
            return abs(aggregated_value - condition_value) >= 0.01
        
        return False
    
    def _extract_field_value(self, event: ecommerce_pb2.EcommerceEvent, field_name: str) -> Any:
        """Extract field value from event based on field name."""
        if event.event_type == ecommerce_pb2.PURCHASE:
            purchase = event.purchase
            if field_name == "user_id":
                return purchase.user_id
            elif field_name == "product_id":
                return purchase.product_id
            elif field_name == "category":
                return purchase.category
            elif field_name == "price":
                return purchase.price
            elif field_name == "quantity":
                return purchase.quantity
            elif field_name == "warehouse_id":
                return purchase.warehouse_id
        
        elif event.event_type == ecommerce_pb2.PRODUCT_VIEW:
            view = event.product_view
            if field_name == "user_id":
                return view.user_id
            elif field_name == "product_id":
                return view.product_id
            elif field_name == "category":
                return view.category
            elif field_name == "view_duration":
                return view.view_duration
            elif field_name == "source":
                return view.source
        
        elif event.event_type == ecommerce_pb2.INVENTORY_UPDATE:
            inventory = event.inventory_update
            if field_name == "product_id":
                return inventory.product_id
            elif field_name == "category":
                return inventory.category
            elif field_name == "stock_level":
                return inventory.stock_level
            elif field_name == "warehouse_id":
                return inventory.warehouse_id
            elif field_name == "operation":
                return inventory.operation
        
        elif event.event_type == ecommerce_pb2.USER_RATING:
            rating = event.user_rating
            if field_name == "user_id":
                return rating.user_id
            elif field_name == "product_id":
                return rating.product_id
            elif field_name == "category":
                return rating.category
            elif field_name == "rating":
                return rating.rating
            elif field_name == "review_text":
                return rating.review_text
        
        return None
    
    def _extract_numeric_value(self, event: ecommerce_pb2.EcommerceEvent, field_name: str) -> Optional[float]:
        """Extract numeric value for windowed conditions."""
        base_field = field_name.replace("avg_", "").replace("max_", "").replace("min_", "")
        value = self._extract_field_value(event, base_field)
        
        if value is not None:
            try:
                return float(value)
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _create_simple_notification(self, event: ecommerce_pb2.EcommerceEvent,
                                  subscription: ecommerce_pb2.Subscription) -> ecommerce_pb2.Notification:
        """Create notification for simple subscription match."""
        simple_notification = ecommerce_pb2.SimpleNotification(
            matched_event=event
        )
        
        return ecommerce_pb2.Notification(
            notification_id=f"notif_{int(time.time() * 1000)}_{subscription.subscription_id}",
            subscription_id=subscription.subscription_id,
            subscriber_id=subscription.subscriber_id,
            timestamp=int(time.time() * 1000),
            simple=simple_notification
        )
    
    def _create_complex_notification(self, subscription: ecommerce_pb2.Subscription,
                                   condition: ecommerce_pb2.FilterCondition,
                                   aggregated_value: float) -> ecommerce_pb2.Notification:
        """Create notification for complex subscription match."""
        # Extract category from subscription conditions
        category = "unknown"
        for cond in subscription.conditions:
            if cond.field_name == "category" and cond.operator == ecommerce_pb2.EQUAL:
                category = cond.value
                break
        
        complex_notification = ecommerce_pb2.ComplexNotification(
            category=category,
            field_name=condition.field_name,
            aggregated_value=aggregated_value,
            window_size=subscription.window_config.window_size,
            condition_met=True
        )
        
        return ecommerce_pb2.Notification(
            notification_id=f"complex_notif_{int(time.time() * 1000)}_{subscription.subscription_id}",
            subscription_id=subscription.subscription_id,
            subscriber_id=subscription.subscriber_id,
            timestamp=int(time.time() * 1000),
            complex=complex_notification
        )
    
    def get_statistics(self) -> Dict[str, int]:
        """Get matcher statistics."""
        return {
            "simple_subscriptions": len(self.simple_subscriptions),
            "complex_subscriptions": len(self.complex_subscriptions),
            "total_subscriptions": len(self.simple_subscriptions) + len(self.complex_subscriptions)
        } 
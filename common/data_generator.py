import random
import time
import uuid
from faker import Faker
from typing import Dict, List, Any
import protos.ecommerce_pb2 as ecommerce_pb2

class EcommerceDataGenerator:
    def __init__(self, seed: int = None):
        """Initialize the e-commerce data generator."""
        self.fake = Faker()
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        
        # Predefined data for consistency
        self.categories = [
            "Electronics", "Clothing", "Books", "Home & Garden", "Sports",
            "Beauty", "Toys", "Automotive", "Food", "Health"
        ]
        
        self.products = {
            "Electronics": ["LAPTOP123", "PHONE456", "TABLET789", "CAMERA001", "HEADPHONE002"],
            "Clothing": ["SHIRT001", "PANTS002", "DRESS003", "JACKET004", "SHOES005"],
            "Books": ["BOOK001", "BOOK002", "BOOK003", "BOOK004", "BOOK005"],
            "Home & Garden": ["CHAIR001", "TABLE002", "LAMP003", "PLANT004", "TOOL005"],
            "Sports": ["BALL001", "BIKE002", "SHOES003", "BAG004", "WATCH005"],
            "Beauty": ["LIPSTICK001", "CREAM002", "PERFUME003", "BRUSH004", "MASK005"],
            "Toys": ["DOLL001", "CAR002", "PUZZLE003", "GAME004", "ROBOT005"],
            "Automotive": ["TIRE001", "OIL002", "BATTERY003", "FILTER004", "TOOL005"],
            "Food": ["SNACK001", "DRINK002", "CANDY003", "SAUCE004", "SPICE005"],
            "Health": ["VITAMIN001", "MEDICINE002", "BANDAGE003", "CREAM004", "SUPPLEMENT005"]
        }
        
        self.warehouses = ["WH001", "WH002", "WH003", "WH004", "WH005"]
        self.sources = ["web", "mobile", "app"]
        
        # User pool for consistency
        self.users = [f"user_{i:04d}" for i in range(1, 1001)]
    
    def generate_purchase_event(self) -> ecommerce_pb2.EcommerceEvent:
        """Generate a purchase event."""
        category = random.choice(self.categories)
        product_id = random.choice(self.products[category])
        
        purchase = ecommerce_pb2.Purchase(
            user_id=random.choice(self.users),
            product_id=product_id,
            category=category,
            price=round(random.uniform(10.0, 2000.0), 2),
            quantity=random.randint(1, 5),
            warehouse_id=random.choice(self.warehouses)
        )
        
        return ecommerce_pb2.EcommerceEvent(
            event_id=str(uuid.uuid4()),
            timestamp=int(time.time() * 1000),
            event_type=ecommerce_pb2.PURCHASE,
            purchase=purchase
        )
    
    def generate_product_view_event(self) -> ecommerce_pb2.EcommerceEvent:
        """Generate a product view event."""
        category = random.choice(self.categories)
        product_id = random.choice(self.products[category])
        
        product_view = ecommerce_pb2.ProductView(
            user_id=random.choice(self.users),
            product_id=product_id,
            category=category,
            view_duration=random.randint(5, 300),  # 5 seconds to 5 minutes
            source=random.choice(self.sources)
        )
        
        return ecommerce_pb2.EcommerceEvent(
            event_id=str(uuid.uuid4()),
            timestamp=int(time.time() * 1000),
            event_type=ecommerce_pb2.PRODUCT_VIEW,
            product_view=product_view
        )
    
    def generate_inventory_update_event(self) -> ecommerce_pb2.EcommerceEvent:
        """Generate an inventory update event."""
        category = random.choice(self.categories)
        product_id = random.choice(self.products[category])
        operations = ["restock", "sale", "return"]
        
        inventory_update = ecommerce_pb2.InventoryUpdate(
            product_id=product_id,
            category=category,
            stock_level=random.randint(0, 1000),
            warehouse_id=random.choice(self.warehouses),
            operation=random.choice(operations)
        )
        
        return ecommerce_pb2.EcommerceEvent(
            event_id=str(uuid.uuid4()),
            timestamp=int(time.time() * 1000),
            event_type=ecommerce_pb2.INVENTORY_UPDATE,
            inventory_update=inventory_update
        )
    
    def generate_user_rating_event(self) -> ecommerce_pb2.EcommerceEvent:
        """Generate a user rating event."""
        category = random.choice(self.categories)
        product_id = random.choice(self.products[category])
        
        user_rating = ecommerce_pb2.UserRating(
            user_id=random.choice(self.users),
            product_id=product_id,
            category=category,
            rating=round(random.uniform(1.0, 5.0), 1),
            review_text=self.fake.text(max_nb_chars=200)
        )
        
        return ecommerce_pb2.EcommerceEvent(
            event_id=str(uuid.uuid4()),
            timestamp=int(time.time() * 1000),
            event_type=ecommerce_pb2.USER_RATING,
            user_rating=user_rating
        )
    
    def generate_random_event(self) -> ecommerce_pb2.EcommerceEvent:
        """Generate a random e-commerce event."""
        event_generators = [
            self.generate_purchase_event,
            self.generate_product_view_event,
            self.generate_inventory_update_event,
            self.generate_user_rating_event
        ]
        
        # Weight the events (purchases and views more common)
        weights = [0.3, 0.4, 0.2, 0.1]
        generator = random.choices(event_generators, weights=weights)[0]
        return generator()
    
    def generate_simple_subscription(self, subscriber_id: str) -> ecommerce_pb2.Subscription:
        """Generate a simple subscription."""
        conditions = []
        
        # Generate 1-3 conditions
        num_conditions = random.randint(1, 3)
        
        for _ in range(num_conditions):
            condition = self._generate_condition(is_windowed=False)
            conditions.append(condition)
        
        return ecommerce_pb2.Subscription(
            subscription_id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            type=ecommerce_pb2.SIMPLE,
            conditions=conditions
        )
    
    def generate_complex_subscription(self, subscriber_id: str) -> ecommerce_pb2.Subscription:
        """Generate a complex (windowed) subscription."""
        conditions = []
        
        # Generate 1-2 regular conditions + 1 windowed condition
        num_regular = random.randint(1, 2)
        for _ in range(num_regular):
            condition = self._generate_condition(is_windowed=False)
            conditions.append(condition)
        
        # Add windowed condition
        windowed_condition = self._generate_condition(is_windowed=True)
        conditions.append(windowed_condition)
        
        window_config = ecommerce_pb2.WindowConfig(
            window_size=random.randint(5, 20),
            aggregation_type=random.choice(["avg", "max", "min"])
        )
        
        return ecommerce_pb2.Subscription(
            subscription_id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            type=ecommerce_pb2.COMPLEX,
            conditions=conditions,
            window_config=window_config
        )
    
    def _generate_condition(self, is_windowed: bool = False) -> ecommerce_pb2.FilterCondition:
        """Generate a filter condition."""
        if is_windowed:
            # Windowed conditions (avg_, max_, min_)
            field_choices = ["avg_rating", "avg_price", "max_price", "min_rating"]
            field_name = random.choice(field_choices)
            operator = random.choice([
                ecommerce_pb2.GREATER_THAN, ecommerce_pb2.LESS_THAN,
                ecommerce_pb2.GREATER_EQUAL, ecommerce_pb2.LESS_EQUAL
            ])
            
            if "price" in field_name:
                value = str(round(random.uniform(10.0, 1000.0), 2))
            else:  # rating
                value = str(round(random.uniform(1.0, 5.0), 1))
        else:
            # Regular conditions
            field_choices = ["category", "product_id", "user_id", "price", "stock_level", "rating"]
            field_name = random.choice(field_choices)
            
            if field_name == "category":
                operator = ecommerce_pb2.EQUAL
                value = random.choice(self.categories)
            elif field_name == "product_id":
                operator = ecommerce_pb2.EQUAL
                category = random.choice(self.categories)
                value = random.choice(self.products[category])
            elif field_name == "user_id":
                operator = ecommerce_pb2.EQUAL
                value = random.choice(self.users)
            elif field_name in ["price", "stock_level", "rating"]:
                operator = random.choice([
                    ecommerce_pb2.GREATER_THAN, ecommerce_pb2.LESS_THAN,
                    ecommerce_pb2.GREATER_EQUAL, ecommerce_pb2.LESS_EQUAL
                ])
                if field_name == "price":
                    value = str(round(random.uniform(10.0, 1000.0), 2))
                elif field_name == "stock_level":
                    value = str(random.randint(1, 100))
                else:  # rating
                    value = str(round(random.uniform(1.0, 5.0), 1))
            else:
                operator = ecommerce_pb2.EQUAL
                value = "default"
        
        return ecommerce_pb2.FilterCondition(
            field_name=field_name,
            operator=operator,
            value=value,
            is_windowed=is_windowed
        )
    
    def generate_subscription_with_equality_ratio(self, subscriber_id: str, equality_ratio: float = 1.0) -> ecommerce_pb2.Subscription:
        """Generate subscription with specific equality operator ratio for performance testing."""
        conditions = []
        num_conditions = random.randint(1, 3)
        
        for i in range(num_conditions):
            if random.random() < equality_ratio:
                # Force equality operator
                condition = self._generate_equality_condition()
            else:
                # Use other operators
                condition = self._generate_condition(is_windowed=False)
            conditions.append(condition)
        
        return ecommerce_pb2.Subscription(
            subscription_id=str(uuid.uuid4()),
            subscriber_id=subscriber_id,
            type=ecommerce_pb2.SIMPLE,
            conditions=conditions
        )
    
    def _generate_equality_condition(self) -> ecommerce_pb2.FilterCondition:
        """Generate a condition with equality operator."""
        field_choices = ["category", "product_id", "user_id"]
        field_name = random.choice(field_choices)
        
        if field_name == "category":
            value = random.choice(self.categories)
        elif field_name == "product_id":
            category = random.choice(self.categories)
            value = random.choice(self.products[category])
        else:  # user_id
            value = random.choice(self.users)
        
        return ecommerce_pb2.FilterCondition(
            field_name=field_name,
            operator=ecommerce_pb2.EQUAL,
            value=value,
            is_windowed=False
        ) 
from enum import Enum


class OrderStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELED = "canceled"

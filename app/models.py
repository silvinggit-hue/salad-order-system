from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    order_type = db.Column(db.String(20), nullable=False, default="매장")
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.id} - {self.customer_name} - {self.order_type}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)

    category = db.Column(db.String(50), nullable=False)
    menu_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    sauce = db.Column(db.String(50), nullable=True)
    item_total = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<OrderItem {self.menu_name} x {self.quantity}>"

class AppSetting(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<AppSetting {self.key}={self.value}>"

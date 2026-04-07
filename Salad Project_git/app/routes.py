from collections import defaultdict, OrderedDict
from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for
from app.menu_data import MENU_DATA, SAUCE_OPTIONS, PEOPLE_OPTIONS
from app.models import db, Order, OrderItem

main = Blueprint("main", __name__)


def build_menu_index():
    menu_index = {}
    for category, items in MENU_DATA.items():
        for item in items:
            menu_index[item["id"]] = {
                "category": category,
                "name": item["name"],
                "price": item["price"],
                "requires_sauce": item["requires_sauce"]
            }
    return menu_index


def format_order_items_text(order):
    lines = []
    for item in order.items:
        item_text = f"- {item.menu_name} {item.quantity}개"
        if item.sauce:
            item_text += f" ({item.sauce})"
        lines.append(item_text)
    return "\n".join(lines)


def build_sms_text(orders):
    dine_in_orders = [o for o in orders if o.order_type == "매장"]
    takeout_orders = [o for o in orders if o.order_type == "포장"]

    def aggregate_items(order_list):
        aggregated = OrderedDict()

        for order in order_list:
            for item in order.items:
                key = (item.menu_name, item.sauce or "")
                if key not in aggregated:
                    aggregated[key] = 0
                aggregated[key] += item.quantity

        return aggregated

    def section_lines(title, order_list):
        lines = [f"[{title}]"]

        aggregated = aggregate_items(order_list)

        if not aggregated:
            lines.append("없음")
            return lines

        for (menu_name, sauce), total_qty in aggregated.items():
            if sauce:
                lines.append(f"{menu_name} {total_qty}개({sauce})")
            else:
                lines.append(f"{menu_name} {total_qty}개")

        return lines

    lines = []
    lines.extend(section_lines("매장", dine_in_orders))
    lines.append("")
    lines.extend(section_lines("포장", takeout_orders))

    return "\n".join(lines).strip()

def cleanup_old_orders():
    today = date.today()
    orders = Order.query.all()

    for order in orders:
        if order.created_at.date() != today:
            db.session.delete(order)

    db.session.commit()


@main.route("/")
def index():
    cleanup_old_orders()
    edit_order_id = request.args.get("edit_order_id", type=int)

    selected_customer = ""
    selected_order_type = "매장"
    prefill_data = {}

    if edit_order_id:
        order = Order.query.get_or_404(edit_order_id)
        selected_customer = order.customer_name
        selected_order_type = order.order_type

        menu_index = build_menu_index()

        for order_item in order.items:
            matched_menu_id = None
            for item_id, info in menu_index.items():
                if info["name"] == order_item.menu_name and info["category"] == order_item.category:
                    matched_menu_id = item_id
                    break

            if matched_menu_id:
                prefill_data[matched_menu_id] = {
                    "quantity": order_item.quantity,
                    "sauce": order_item.sauce or ""
                }

    return render_template(
        "index.html",
        menu_data=MENU_DATA,
        sauce_options=SAUCE_OPTIONS,
        people_options=PEOPLE_OPTIONS,
        selected_customer=selected_customer,
        selected_order_type=selected_order_type,
        prefill_data=prefill_data,
        edit_order_id=edit_order_id
    )


@main.route("/submit", methods=["POST"])
def submit_order():
    customer_name = request.form.get("customer_name", "").strip()
    order_type = request.form.get("order_type", "").strip()

    if not customer_name:
        return "주문자를 선택해주세요.", 400

    if order_type not in ["매장", "포장"]:
        return "주문 유형을 선택해주세요.", 400

    ordered_items = []
    total_price = 0

    for category, items in MENU_DATA.items():
        for item in items:
            qty_str = request.form.get(f"qty_{item['id']}", "0").strip()

            if not qty_str:
                qty_str = "0"

            try:
                quantity = int(qty_str)
            except ValueError:
                quantity = 0

            if quantity <= 0:
                continue

            sauce = ""
            if item["requires_sauce"]:
                sauce = request.form.get(f"sauce_{item['id']}", "").strip()
                if not sauce:
                    return f"{item['name']}의 소스를 선택해주세요.", 400

            item_total = item["price"] * quantity
            total_price += item_total

            ordered_items.append({
                "category": category,
                "name": item["name"],
                "price": item["price"],
                "quantity": quantity,
                "sauce": sauce,
                "item_total": item_total
            })

    if not ordered_items:
        return "최소 1개 이상의 메뉴 수량을 입력해주세요.", 400

    existing_orders = Order.query.filter_by(customer_name=customer_name).all()
    for existing_order in existing_orders:
        db.session.delete(existing_order)
    db.session.flush()

    new_order = Order(customer_name=customer_name, order_type=order_type)
    db.session.add(new_order)
    db.session.flush()

    for item in ordered_items:
        order_item = OrderItem(
            order_id=new_order.id,
            category=item["category"],
            menu_name=item["name"],
            price=item["price"],
            quantity=item["quantity"],
            sauce=item["sauce"] if item["sauce"] else None,
            item_total=item["item_total"]
        )
        db.session.add(order_item)

    db.session.commit()

    return render_template(
        "result.html",
        customer_name=customer_name,
        order_type=order_type,
        ordered_items=ordered_items,
        total_price=total_price
    )


@main.route("/admin")
def admin():
    cleanup_old_orders()
    orders = Order.query.order_by(Order.created_at.desc()).all()

    dine_in_orders = [o for o in orders if o.order_type == "매장"]
    takeout_orders = [o for o in orders if o.order_type == "포장"]

    grand_total = 0
    menu_summary = defaultdict(int)
    person_summary = defaultdict(int)
    type_summary = {"매장": 0, "포장": 0}

    for order in orders:
        person_total = 0
        for item in order.items:
            grand_total += item.item_total
            person_total += item.item_total
            menu_summary[item.menu_name] += item.quantity

        person_summary[order.customer_name] += person_total
        type_summary[order.order_type] += person_total

    person_count = len(orders)
    limit_per_person = 10000
    expected_total = person_count * limit_per_person
    difference = grand_total - expected_total

    menu_summary = dict(sorted(menu_summary.items(), key=lambda x: x[0]))
    person_summary = dict(sorted(person_summary.items(), key=lambda x: x[0]))

    sms_text = build_sms_text(orders)

    return render_template(
        "admin.html",
        orders=orders,
        dine_in_orders=dine_in_orders,
        takeout_orders=takeout_orders,
        grand_total=grand_total,
        menu_summary=menu_summary,
        person_summary=person_summary,
        type_summary=type_summary,
        sms_text=sms_text,

        person_count=person_count,
        expected_total=expected_total,
        difference=difference
    )


@main.route("/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return redirect(url_for("main.admin"))


@main.route("/edit/<int:order_id>")
def edit_order(order_id):
    return redirect(url_for("main.index", edit_order_id=order_id))

@main.route("/delete-all", methods=["POST"])
def delete_all_orders():
    OrderItem.query.delete()
    Order.query.delete()
    db.session.commit()
    return redirect(url_for("main.admin"))
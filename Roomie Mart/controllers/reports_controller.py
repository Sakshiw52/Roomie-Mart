from flask import Blueprint, render_template, jsonify
from database.db_connection import get_db_connection

reports_bp = Blueprint('reports_bp', __name__)


@reports_bp.route('/analytics')
def analytics_dashboard():
    """Render the analytics dashboard"""
    return render_template('analytics.html')


@reports_bp.route('/analytics/api/category_distribution')
def api_category_distribution():
    """Return items count per category"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM items
        WHERE status = 'available'
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    categories = [row['category'] for row in rows]
    counts = [row['count'] for row in rows]
    
    return jsonify({
        'labels': categories,
        'data': counts,
        'backgroundColor': [
            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF',
            '#FF9F40', '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384'
        ]
    })


@reports_bp.route('/analytics/api/sold_vs_available')
def api_sold_vs_available():
    """Return count of sold vs available items"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM items
        GROUP BY status
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    data = {row['status']: row['count'] for row in rows}
    available = data.get('available', 0)
    sold = data.get('sold', 0)
    
    return jsonify({
        'labels': ['Available', 'Sold'],
        'data': [available, sold],
        'backgroundColor': ['#36A2EB', '#FF6384']
    })


@reports_bp.route('/analytics/api/monthly_orders')
def api_monthly_orders():
    """Return monthly order/sales count"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get last 12 months of orders
    cursor.execute('''
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM orders
        GROUP BY month
        ORDER BY month DESC
        LIMIT 12
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    # Sort chronologically
    data = sorted([(row['month'], row['count']) for row in rows])
    months = [m for m, c in data]
    counts = [c for m, c in data]
    
    return jsonify({
        'labels': months,
        'data': counts,
        'borderColor': '#36A2EB',
        'backgroundColor': 'rgba(54, 162, 235, 0.1)'
    })


@reports_bp.route('/analytics/api/top_categories')
def api_top_categories():
    """Return top 5 most sold categories"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.category, COUNT(o.id) as sales_count
        FROM items i
        LEFT JOIN orders o ON i.id = o.item_id
        GROUP BY i.category
        ORDER BY sales_count DESC
        LIMIT 5
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    categories = [row['category'] for row in rows]
    sales = [row['sales_count'] for row in rows]
    
    return jsonify({
        'labels': categories,
        'data': sales,
        'backgroundColor': '#4BC0C0'
    })


@reports_bp.route('/analytics/api/user_growth')
def api_user_growth():
    """Return monthly user registration growth"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%Y-%m', created_at) as month, COUNT(*) as count
        FROM users
        GROUP BY month
        ORDER BY month
        LIMIT 12
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    months = [row['month'] for row in rows]
    counts = [row['count'] for row in rows]
    
    return jsonify({
        'labels': months,
        'data': counts,
        'borderColor': '#9966FF',
        'backgroundColor': 'rgba(153, 102, 255, 0.1)'
    })


@reports_bp.route('/analytics/api/revenue')
def api_revenue():
    """Return monthly revenue analysis"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT strftime('%Y-%m', created_at) as month, SUM(total) as revenue
        FROM orders
        GROUP BY month
        ORDER BY month
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    months = [row['month'] for row in rows]
    revenues = [row['revenue'] or 0 for row in rows]
    
    # Calculate totals for summary
    total_revenue = sum(revenues)
    highest_month = max(zip(months, revenues), key=lambda x: x[1]) if months else ('N/A', 0)
    
    return jsonify({
        'labels': months,
        'data': revenues,
        'total_revenue': total_revenue,
        'highest_month': highest_month[0] if highest_month else 'N/A',
        'highest_amount': highest_month[1] if highest_month else 0,
        'backgroundColor': '#FF9F40'
    })


@reports_bp.route('/analytics/api/summary')
def api_summary():
    """Return key summary statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total items
    cursor.execute('SELECT COUNT(*) as count FROM items')
    total_items = cursor.fetchone()['count']
    
    # Available items
    cursor.execute('SELECT COUNT(*) as count FROM items WHERE status = "available"')
    available_items = cursor.fetchone()['count']
    
    # Sold items
    cursor.execute('SELECT COUNT(*) as count FROM items WHERE status = "sold"')
    sold_items = cursor.fetchone()['count']
    
    # Total orders
    cursor.execute('SELECT COUNT(*) as count FROM orders')
    total_orders = cursor.fetchone()['count']
    
    # Total users
    cursor.execute('SELECT COUNT(*) as count FROM users')
    total_users = cursor.fetchone()['count']
    
    # Total revenue
    cursor.execute('SELECT SUM(total) as total FROM orders')
    result = cursor.fetchone()
    total_revenue = result['total'] or 0
    
    conn.close()
    
    return jsonify({
        'total_items': total_items,
        'available_items': available_items,
        'sold_items': sold_items,
        'total_orders': total_orders,
        'total_users': total_users,
        'total_revenue': total_revenue
    })

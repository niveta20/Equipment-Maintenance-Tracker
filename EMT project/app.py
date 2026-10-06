from flask import Flask, render_template, request, jsonify
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# Database Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Deva@2817',  
    'database': 'maintenance_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ==================== FRONTEND ROUTES ====================

@app.route('/')
def index():
    return render_template('index.html')

# ==================== REST API ENDPOINTS ====================

# 1. READ ALL (with Search & Filter)
@app.route('/api/equipment', methods=['GET'])
def get_all_equipment():
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM equipment WHERE (name LIKE %s OR category LIKE %s OR location LIKE %s)"
    params = [f"%{search}%", f"%{search}%", f"%{search}%"]

    if status_filter:
        query += " AND status = %s"
        params.append(status_filter)

    query += " ORDER BY id DESC"

    cursor.execute(query, params)
    equipment_list = cursor.fetchall()
    
    # Format date for JSON response
    for item in equipment_list:
        if item['last_serviced']:
            item['last_serviced'] = item['last_serviced'].strftime('%Y-%m-%d')

    cursor.close()
    conn.close()
    return jsonify({'success': True, 'data': equipment_list})


# 2. READ ONE
@app.route('/api/equipment/<int:item_id>', methods=['GET'])
def get_equipment_by_id(item_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM equipment WHERE id = %s", (item_id,))
    item = cursor.fetchone()
    cursor.close()
    conn.close()

    if item:
        if item['last_serviced']:
            item['last_serviced'] = item['last_serviced'].strftime('%Y-%m-%d')
        return jsonify({'success': True, 'data': item})
    return jsonify({'success': False, 'message': 'Equipment not found'}), 404


# 3. CREATE
@app.route('/api/equipment', methods=['POST'])
def add_equipment():
    data = request.json
    
    # Validation
    if not data.get('name') or not data.get('category') or not data.get('location') or not data.get('last_serviced'):
        return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO equipment (name, category, location, status, last_serviced)
        VALUES (%s, %s, %s, %s, %s)
    """
    values = (
        data['name'].strip(),
        data['category'].strip(),
        data['location'].strip(),
        data.get('status', 'Operational'),
        data['last_serviced']
    )
    cursor.execute(sql, values)
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()

    return jsonify({'success': True, 'message': 'Equipment added successfully', 'id': new_id}), 201


# 4. UPDATE
@app.route('/api/equipment/<int:item_id>', methods=['PUT'])
def update_equipment(item_id):
    data = request.json

    if not data.get('name') or not data.get('category') or not data.get('location') or not data.get('last_serviced'):
        return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE equipment 
        SET name = %s, category = %s, location = %s, status = %s, last_serviced = %s
        WHERE id = %s
    """
    values = (
        data['name'].strip(),
        data['category'].strip(),
        data['location'].strip(),
        data['status'],
        data['last_serviced'],
        item_id
    )
    cursor.execute(sql, values)
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({'success': False, 'message': 'Equipment not found'}), 404

    return jsonify({'success': True, 'message': 'Equipment updated successfully'})


# 5. DELETE
@app.route('/api/equipment/<int:item_id>', methods=['DELETE'])
def delete_equipment(item_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM equipment WHERE id = %s", (item_id,))
    conn.commit()
    affected = cursor.rowcount
    cursor.close()
    conn.close()

    if affected == 0:
        return jsonify({'success': False, 'message': 'Equipment not found'}), 404

    return jsonify({'success': True, 'message': 'Equipment deleted successfully'})


# 6. DASHBOARD METRICS
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) AS total FROM equipment")
    total = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS operational FROM equipment WHERE status = 'Operational'")
    operational = cursor.fetchone()['operational']

    cursor.execute("SELECT COUNT(*) AS needs_maint FROM equipment WHERE status = 'Needs Maintenance'")
    needs_maint = cursor.fetchone()['needs_maint']

    cursor.execute("SELECT COUNT(*) AS repair FROM equipment WHERE status = 'Under Repair'")
    repair = cursor.fetchone()['repair']

    cursor.close()
    conn.close()

    return jsonify({
        'success': True,
        'stats': {
            'total': total,
            'operational': operational,
            'needs_maint': needs_maint,
            'repair': repair
        }
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
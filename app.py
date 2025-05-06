from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
import sqlite3
from datetime import datetime
import os
import subprocess
import sys

def check_and_install_requirements():
    try:
        # Try to import required packages
        import flask
        import flask_wtf
        import werkzeug
        import jinja2
        import itsdangerous
        import click
        import markupsafe
    except ImportError:
        print("Installing required packages...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print("Requirements installed successfully!")
        except subprocess.CalledProcessError:
            print("Failed to install requirements. Please install them manually using: pip install -r requirements.txt")
            sys.exit(1)

# Check and install requirements before starting the app
check_and_install_requirements()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key'
csrf = CSRFProtect(app)

def get_db_connection():
    try:
        conn = sqlite3.connect('majikayobar.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        raise

def init_db():
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Create inventory table
        c.execute('''
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create tables table
        c.execute('''
            CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY,
                table_number INTEGER NOT NULL,
                is_available INTEGER DEFAULT 1,
                has_active_order INTEGER DEFAULT 0
            )
        ''')

        # Create menu_items table
        c.execute('''
            CREATE TABLE IF NOT EXISTS menu_items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL NOT NULL
            )
        ''')

        # Create promotions table
        c.execute('''
            CREATE TABLE IF NOT EXISTS promotions (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                food_name TEXT NOT NULL,
                discount_percentage INTEGER NOT NULL,
                FOREIGN KEY (food_name) REFERENCES menu_items (name)
            )
        ''')
        
        # Create orders table
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                table_id INTEGER NOT NULL,
                total_amount DECIMAL,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (table_id) REFERENCES tables (id)
            )
        ''')

        # Create order_items table
        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL,
                menu_item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                price DECIMAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
            )
        ''')

        # Create employees table
        c.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                position TEXT NOT NULL,
                salary DECIMAL NOT NULL,
                address TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                birth_date DATE NOT NULL,
                nationality TEXT NOT NULL,
                gender TEXT NOT NULL,
                military_status TEXT,
                education_level TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create store_goods table
        c.execute('''
            CREATE TABLE IF NOT EXISTS store_goods (
                id INTEGER PRIMARY KEY,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                deposit_date DATE NOT NULL,
                expiration_date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create item_sales_records table
        c.execute('''
            CREATE TABLE IF NOT EXISTS item_sales_records (
                id INTEGER PRIMARY KEY,
                menu_item_id INTEGER NOT NULL,
                quantity_sold INTEGER NOT NULL,
                total_revenue REAL NOT NULL,
                sale_date DATE NOT NULL,
                FOREIGN KEY (menu_item_id) REFERENCES menu_items (id)
            )
        ''')
        
        # Check if tables are already created
        c.execute('SELECT COUNT(*) FROM tables')
        count = c.fetchone()[0]
        
        # If no tables exist, create 9 tables
        if count == 0:
            for table_number in range(1, 10):
                c.execute('''
                    INSERT INTO tables (table_number, is_available, has_active_order)
                    VALUES (?, 1, 0)
                ''', (table_number,))
            print("Created 9 physical tables")
        
        conn.commit()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    finally:
        if 'conn' in locals():
            conn.close()

# Initialize database on startup
if not os.path.exists('majikayobar.db'):
    print("Creating new database...")
    init_db()
else:
    print("Database exists, checking structure...")
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if inventory table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventory'")
        if not c.fetchone():
            print("Inventory table not found, creating...")
            c.execute('''
                CREATE TABLE inventory (
                    id INTEGER PRIMARY KEY,
                    item_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("Inventory table created successfully")
        else:
            print("Inventory table exists")
            
        # Check if tables exist and create if missing
        tables = ['orders', 'order_items']
        for table in tables:
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not c.fetchone():
                print(f"{table} table not found, creating...")
                init_db()
                break
                
    except Exception as e:
        print(f"Error checking database structure: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

# Routes for each page
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/table-register')
def table_register():
    try:
        conn = get_db_connection()
        tables = conn.execute('SELECT * FROM tables ORDER BY table_number').fetchall()
        return render_template('table-register.html', tables=tables)
    except Exception as e:
        print(f"Error fetching tables: {str(e)}")
        return render_template('table-register.html', tables=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/food-list')
def food_list():
    return render_template('food-list.html')

@app.route('/receive-order')
def receive_order():
    return render_template('receive-order.html')

@app.route('/pay-service')
def pay_service():
    try:
        conn = get_db_connection()
        tables = conn.execute('SELECT * FROM tables WHERE is_available = 0 ORDER BY table_number').fetchall()
        return render_template('pay-service.html', tables=tables)
    except Exception as e:
        print(f"Error fetching tables: {str(e)}")
        return render_template('pay-service.html', tables=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/promotion-list')
def promotion_list():
    try:
        conn = get_db_connection()
        # Check if promotions table exists
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='promotions'")
        if not c.fetchone():
            print("Promotions table not found, creating...")
            c.execute('''
                CREATE TABLE promotions (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    menu_item_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    discount INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            print("Promotions table created successfully")
        
        # Get all promotions
        promotions = conn.execute('SELECT * FROM promotions').fetchall()
        print("Current promotions:", [dict(p) for p in promotions])
        return render_template('promotion-list.html', promotions=promotions)
    except Exception as e:
        print(f"Error in promotion_list: {str(e)}")
        return render_template('promotion-list.html', promotions=[])
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/performance-report')
def performance_report():
    return render_template('performance-report.html')

@app.route('/employee-register')
def employee_register():
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()
    conn.close()
    return render_template('employee-register.html', employees=employees)

@app.route('/store-goods')
def store_goods():
    conn = get_db_connection()
    goods = conn.execute('SELECT * FROM store_goods').fetchall()
    conn.close()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('store-goods.html', goods=goods, today=today)

@app.route('/inventory')
def inventory():
    try:
        conn = get_db_connection()
        items = conn.execute('SELECT * FROM inventory ORDER BY created_at DESC').fetchall()
        return render_template('inventory.html', items=items)
    except Exception as e:
        print(f"Error fetching inventory: {str(e)}")
        return render_template('inventory.html', items=[])
    finally:
        if 'conn' in locals():
            conn.close()

# API Routes for Table Management
@app.route('/api/tables', methods=['GET'])
def get_tables():
    conn = get_db_connection()
    tables = conn.execute('SELECT * FROM tables').fetchall()
    return jsonify([dict(table) for table in tables])

@app.route('/api/tables/<int:table_id>', methods=['GET', 'PUT'])
def update_table_status(table_id):
    if request.method == 'GET':
        conn = get_db_connection()
        table = conn.execute('SELECT * FROM tables WHERE id = ?', (table_id,)).fetchone()
        if not table:
            return jsonify({'error': 'Table not found'}), 404
        return jsonify(dict(table))
    
    try:
        conn = get_db_connection()
        data = request.get_json()
        
        if 'is_available' not in data:
            return jsonify({'message': 'Missing is_available parameter'}), 400
            
        conn.execute('''
            UPDATE tables 
            SET is_available = ?
            WHERE id = ?
        ''', (1 if data['is_available'] else 0, table_id))
        
        conn.commit()
        return jsonify({'message': 'Table status updated successfully'})
    except Exception as e:
        print(f"Error updating table status: {str(e)}")
        return jsonify({'message': f'Error updating table status: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/tables/<int:table_id>/toggle', methods=['PUT'])
def toggle_table_status(table_id):
    try:
        conn = get_db_connection()
        # Get current status
        table = conn.execute('SELECT is_available FROM tables WHERE id = ?', (table_id,)).fetchone()
        if table is None:
            return jsonify({'success': False, 'error': 'Table not found'}), 404
        
        # Toggle status
        new_status = 0 if table['is_available'] else 1
        conn.execute('UPDATE tables SET is_available = ? WHERE id = ?', (new_status, table_id))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error toggling table status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# API Routes for Menu Items
@app.route('/api/menu', methods=['GET', 'POST'])
def handle_menu():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('''
            INSERT INTO menu_items (name, price)
            VALUES (?, ?)
        ''', (data['name'], data['price']))
        conn.commit()
        return jsonify({'message': 'Menu item added successfully'})
    else:
        items = conn.execute('SELECT * FROM menu_items').fetchall()
        return jsonify([dict(item) for item in items])

@app.route('/api/menu/<int:item_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_menu_item(item_id):
    conn = get_db_connection()
    if request.method == 'GET':
        item = conn.execute('SELECT * FROM menu_items WHERE id = ?', (item_id,)).fetchone()
        if item is None:
            return jsonify({'message': 'Menu item not found'}), 404
        return jsonify(dict(item))
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
        conn.commit()
        return jsonify({'message': 'Menu item deleted successfully'})
    else:  # PUT
        data = request.get_json()
        conn.execute('''
            UPDATE menu_items 
            SET name = ?, price = ?
            WHERE id = ?
        ''', (data['name'], data['price'], item_id))
        conn.commit()
        return jsonify({'message': 'Menu item updated successfully'})

# API Routes for Promotions
@app.route('/api/promotions', methods=['GET', 'POST'])
def handle_promotions():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('''
            INSERT INTO promotions (name, food_name, discount_percentage)
            VALUES (?, ?, ?)
        ''', (data['name'], data['food_name'], data['discount_percentage']))
        conn.commit()
        return jsonify({'message': 'Promotion added successfully'})
    else:
        promotions = conn.execute('SELECT * FROM promotions ORDER BY id DESC').fetchall()
        return jsonify([dict(promotion) for promotion in promotions])

@app.route('/api/promotions/<int:promotion_id>', methods=['GET', 'PUT', 'DELETE'])
def handle_promotion(promotion_id):
    conn = get_db_connection()
    if request.method == 'GET':
        promotion = conn.execute('SELECT * FROM promotions WHERE id = ?', (promotion_id,)).fetchone()
        if promotion is None:
            return jsonify({'message': 'Promotion not found'}), 404
        return jsonify(dict(promotion))
    elif request.method == 'DELETE':
        conn.execute('DELETE FROM promotions WHERE id = ?', (promotion_id,))
        conn.commit()
        return jsonify({'message': 'Promotion deleted successfully'})
    else:  # PUT
        data = request.get_json()
        conn.execute('''
            UPDATE promotions 
            SET name = ?, food_name = ?, discount_percentage = ?
            WHERE id = ?
        ''', (data['name'], data['food_name'], data['discount_percentage'], promotion_id))
        conn.commit()
        return jsonify({'message': 'Promotion updated successfully'})

# API Routes for Employees
@app.route('/api/employees', methods=['GET', 'POST'])
def handle_employees():
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'message': 'No data provided'}), 400
                
                print("Received data:", data)  # Debug log
                
                # Validate required fields
                required_fields = ['first_name', 'last_name', 'position', 'salary', 'address', 
                                'phone', 'email', 'birth_date', 'nationality', 'gender', 
                                'education_level']
                
                for field in required_fields:
                    if not data.get(field):
                        return jsonify({'message': f'Missing required field: {field}'}), 400

                # Check for duplicate name
                existing_employee = conn.execute('''
                    SELECT * FROM employees 
                    WHERE first_name = ? AND last_name = ?
                ''', (data['first_name'], data['last_name'])).fetchone()
                
                if existing_employee:
                    return jsonify({'message': 'พนักงานที่มีชื่อและนามสกุลนี้มีอยู่ในระบบแล้ว'}), 400

                # Insert into database
                cursor = conn.execute('''
                    INSERT INTO employees (
                        first_name, last_name, position, salary, address,
                        phone, email, birth_date, nationality, gender,
                        military_status, education_level, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ''', (
                    data['first_name'], data['last_name'], data['position'],
                    data['salary'], data['address'], data['phone'], data['email'],
                    data['birth_date'], data['nationality'], data['gender'],
                    data.get('military_status', ''), data['education_level']
                ))
                
                conn.commit()
                print("Employee added successfully")  # Debug log
                return jsonify({'message': 'Employee added successfully', 'id': cursor.lastrowid})
                
            except Exception as e:
                print("Error adding employee:", str(e))  # Debug log
                conn.rollback()
                return jsonify({'message': f'Error adding employee: {str(e)}'}), 500
                
        else:
            employees = conn.execute('SELECT * FROM employees').fetchall()
            return jsonify([dict(employee) for employee in employees])
    except Exception as e:
        print("Database connection error:", str(e))  # Debug log
        return jsonify({'message': f'Database error: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/employees/<int:employee_id>', methods=['DELETE', 'PUT'])
def delete_employee(employee_id):
    try:
        conn = get_db_connection()
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'message': 'No data provided'}), 400

            # Validate required fields
            required_fields = ['first_name', 'last_name', 'position', 'salary', 'address', 
                            'phone', 'email', 'birth_date', 'nationality', 'gender', 
                            'education_level']
            
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'message': f'Missing required field: {field}'}), 400

            # Check if employee exists
            employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
            if not employee:
                return jsonify({'message': 'Employee not found'}), 404

            # Check for duplicate name (excluding current employee)
            existing_employee = conn.execute('''
                SELECT * FROM employees 
                WHERE first_name = ? AND last_name = ? AND id != ?
            ''', (data['first_name'], data['last_name'], employee_id)).fetchone()
            
            if existing_employee:
                return jsonify({'message': 'พนักงานที่มีชื่อและนามสกุลนี้มีอยู่ในระบบแล้ว'}), 400

            # Update employee
            conn.execute('''
                UPDATE employees SET
                    first_name = ?, last_name = ?, position = ?, salary = ?,
                    address = ?, phone = ?, email = ?, birth_date = ?,
                    nationality = ?, gender = ?, military_status = ?,
                    education_level = ?
                WHERE id = ?
            ''', (
                data['first_name'], data['last_name'], data['position'],
                data['salary'], data['address'], data['phone'], data['email'],
                data['birth_date'], data['nationality'], data['gender'],
                data.get('military_status', ''), data['education_level'],
                employee_id
            ))
            
            conn.commit()
            return jsonify({'message': 'Employee updated successfully'})

        else:  # DELETE method
            # Check if employee exists
            employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
            if not employee:
                return jsonify({'message': 'Employee not found'}), 404
                
            conn.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
            conn.commit()
            return jsonify({'message': 'Employee deleted successfully'})
    except Exception as e:
        print("Error handling employee:", str(e))  # Debug log
        return jsonify({'message': f'Error handling employee: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# API Routes for Store Goods
@app.route('/api/store-goods', methods=['GET', 'POST'])
def handle_store_goods():
    conn = get_db_connection()
    if request.method == 'POST':
        data = request.get_json()
        conn.execute('''
            INSERT INTO store_goods (
                customer_name, customer_phone, item_name,
                quantity, deposit_date, expiration_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['customer_name'], data['customer_phone'],
            data['item_name'], data['quantity'],
            data['deposit_date'], data['expiration_date'],
            data.get('notes')
        ))
        conn.commit()
        return jsonify({'message': 'เพิ่มข้อมูลการฝากสินค้าเรียบร้อยแล้ว'})
    else:
        goods = conn.execute('SELECT * FROM store_goods').fetchall()
        return jsonify([dict(item) for item in goods])

@app.route('/api/store-goods/<int:good_id>', methods=['PUT', 'DELETE'])
def handle_store_good(good_id):
    try:
        conn = get_db_connection()
        if request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'message': 'ไม่พบข้อมูลที่ส่งมา'}), 400

            # Validate required fields
            required_fields = ['customer_name', 'customer_phone', 'item_name', 
                             'quantity', 'deposit_date', 'expiration_date']
            
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'message': f'กรุณากรอกข้อมูล: {field}'}), 400

            # Check if store good exists
            good = conn.execute('SELECT * FROM store_goods WHERE id = ?', (good_id,)).fetchone()
            if not good:
                return jsonify({'message': 'ไม่พบข้อมูลการฝากสินค้า'}), 404

            # Update store good
            conn.execute('''
                UPDATE store_goods SET
                    customer_name = ?, customer_phone = ?, item_name = ?,
                    quantity = ?, deposit_date = ?, expiration_date = ?,
                    notes = ?
                WHERE id = ?
            ''', (
                data['customer_name'], data['customer_phone'],
                data['item_name'], data['quantity'],
                data['deposit_date'], data['expiration_date'],
                data.get('notes'), good_id
            ))
            
            conn.commit()
            return jsonify({'message': 'แก้ไขข้อมูลการฝากสินค้าเรียบร้อยแล้ว'})

        else:  # DELETE method
            # Check if store good exists
            good = conn.execute('SELECT * FROM store_goods WHERE id = ?', (good_id,)).fetchone()
            if not good:
                return jsonify({'message': 'ไม่พบข้อมูลการฝากสินค้า'}), 404
                
            conn.execute('DELETE FROM store_goods WHERE id = ?', (good_id,))
            conn.commit()
            return jsonify({'message': 'ลบข้อมูลการฝากสินค้าเรียบร้อยแล้ว'})
    except Exception as e:
        print("Error handling store good:", str(e))  # Debug log
        return jsonify({'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# API Routes for Inventory
@app.route('/api/inventory', methods=['GET', 'POST'])
def handle_inventory():
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            data = request.get_json()
            print("Received inventory data:", data)  # Debug log
            
            if not data or not all(k in data for k in ['item_name', 'quantity', 'unit']):
                return jsonify({'message': 'ข้อมูลไม่ครบถ้วน'}), 400
                
            try:
                conn.execute('''
                    INSERT INTO inventory (item_name, quantity, unit, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                ''', (data['item_name'], data['quantity'], data['unit']))
                conn.commit()
                print("Successfully added inventory item")  # Debug log
                return jsonify({'message': 'เพิ่มสินค้าเรียบร้อยแล้ว'})
            except Exception as e:
                print("Error adding inventory item:", str(e))  # Debug log
                conn.rollback()
                return jsonify({'message': f'เกิดข้อผิดพลาดในการเพิ่มสินค้า: {str(e)}'}), 500
        else:
            items = conn.execute('SELECT * FROM inventory ORDER BY created_at DESC').fetchall()
            return jsonify([dict(item) for item in items])
    except Exception as e:
        print("Database connection error:", str(e))  # Debug log
        return jsonify({'message': f'เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/inventory/<int:item_id>', methods=['PUT', 'DELETE'])
def handle_inventory_item(item_id):
    try:
        conn = get_db_connection()
        if request.method == 'PUT':
            data = request.get_json()
            print("Received update data:", data)  # Debug log
            
            if not data or not all(k in data for k in ['item_name', 'quantity', 'unit']):
                return jsonify({'message': 'ข้อมูลไม่ครบถ้วน'}), 400
                
            try:
                # Check if item exists
                item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
                if not item:
                    return jsonify({'message': 'ไม่พบสินค้า'}), 404
                    
                conn.execute('''
                    UPDATE inventory 
                    SET item_name = ?, quantity = ?, unit = ?
                    WHERE id = ?
                ''', (data['item_name'], data['quantity'], data['unit'], item_id))
                conn.commit()
                print("Successfully updated inventory item")  # Debug log
                return jsonify({'message': 'แก้ไขสินค้าเรียบร้อยแล้ว'})
            except Exception as e:
                print("Error updating inventory item:", str(e))  # Debug log
                conn.rollback()
                return jsonify({'message': f'เกิดข้อผิดพลาดในการแก้ไขสินค้า: {str(e)}'}), 500
        else:  # DELETE method
            try:
                # Check if item exists
                item = conn.execute('SELECT * FROM inventory WHERE id = ?', (item_id,)).fetchone()
                if not item:
                    return jsonify({'message': 'ไม่พบสินค้า'}), 404
                    
                conn.execute('DELETE FROM inventory WHERE id = ?', (item_id,))
                conn.commit()
                print("Successfully deleted inventory item")  # Debug log
                return jsonify({'message': 'ลบสินค้าเรียบร้อยแล้ว'})
            except Exception as e:
                print("Error deleting inventory item:", str(e))  # Debug log
                conn.rollback()
                return jsonify({'message': f'เกิดข้อผิดพลาดในการลบสินค้า: {str(e)}'}), 500
    except Exception as e:
        print("Database connection error:", str(e))  # Debug log
        return jsonify({'message': f'เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {str(e)}'}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# API Routes for Orders and Payments
@app.route('/api/orders', methods=['GET', 'POST'])
@csrf.exempt  # Exempt this route from CSRF protection
def handle_orders():
    conn = get_db_connection()
    try:
        if request.method == 'POST':
            print("Received request data:", request.data)  # Debug log
            data = request.get_json(force=True)  # Force JSON parsing
            print("Parsed JSON data:", data)  # Debug log
            
            if not data:
                return jsonify({'error': 'No data provided'}), 400

            if 'table_id' not in data or 'items' not in data:
                return jsonify({'error': 'Missing required fields'}), 400

            # Check if table already has a pending order
            existing_order = conn.execute('''
                SELECT id FROM orders 
                WHERE table_id = ? AND status = 'pending'
            ''', (data['table_id'],)).fetchone()

            if existing_order:
                order_id = existing_order['id']
            else:
                # Create new order
                cursor = conn.execute('''
                    INSERT INTO orders (table_id, status)
                    VALUES (?, 'pending')
                ''', (data['table_id'],))
                order_id = cursor.lastrowid

            # Add items to order
            total_amount = 0
            for item in data['items']:
                if 'menu_item_id' not in item or 'quantity' not in item:
                    return jsonify({'error': 'Invalid item data'}), 400

                menu_item = conn.execute('''
                    SELECT price FROM menu_items WHERE id = ?
                ''', (item['menu_item_id'],)).fetchone()
                
                if not menu_item:
                    return jsonify({'error': f'Menu item {item["menu_item_id"]} not found'}), 404
                
                item_total = menu_item['price'] * item['quantity']
                total_amount += item_total
                
                conn.execute('''
                    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['menu_item_id'], item['quantity'], menu_item['price']))

            # Update order total
            conn.execute('''
                UPDATE orders SET total_amount = ? WHERE id = ?
            ''', (total_amount, order_id))

            # Update table status
            conn.execute('''
                UPDATE tables SET is_available = 0, has_active_order = 1 WHERE id = ?
            ''', (data['table_id'],))

            conn.commit()
            return jsonify({
                'message': 'Order created/updated successfully',
                'order_id': order_id,
                'total_amount': total_amount
            })
        else:
            # GET method - get all pending orders
            orders = conn.execute('''
                SELECT o.*, t.table_number 
                FROM orders o
                JOIN tables t ON o.table_id = t.id
                WHERE o.status = 'pending'
            ''').fetchall()
            return jsonify([dict(order) for order in orders])
    except Exception as e:
        print("Error in handle_orders:", str(e))  # Debug log
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*, t.table_number 
        FROM orders o
        JOIN tables t ON o.table_id = t.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    items = conn.execute('''
        SELECT oi.*, mi.name as item_name
        FROM order_items oi
        JOIN menu_items mi ON oi.menu_item_id = mi.id
        WHERE oi.order_id = ?
    ''', (order_id,)).fetchall()
    
    return jsonify({
        'order': dict(order),
        'items': [dict(item) for item in items]
    })

@app.route('/api/orders/<int:order_id>/pay', methods=['POST'])
def process_payment(order_id):
    conn = get_db_connection()
    data = request.get_json()
    
    try:
        # Get order details
        order = conn.execute('''
            SELECT * FROM orders WHERE id = ?
        ''', (order_id,)).fetchone()
        
        if not order:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get all promotions
        promotions = conn.execute('''
            SELECT p.*, m.id as menu_item_id, m.name as menu_item_name 
            FROM promotions p
            JOIN menu_items m ON p.food_name = m.name
        ''').fetchall()
        
        # Create a lookup dictionary for promotions by menu item ID
        promotion_lookup = {p['menu_item_id']: p for p in promotions}
        
        # Record individual item sales with discounted prices
        order_items = conn.execute('''
            SELECT oi.*, mi.name as item_name 
            FROM order_items oi
            JOIN menu_items mi ON oi.menu_item_id = mi.id
            WHERE oi.order_id = ?
        ''', (order_id,)).fetchall()
        
        today = datetime.now().date()
        total_amount = 0
        
        for item in order_items:
            # Calculate price for this item
            item_price = float(item['price'])
            discounted_price = item_price
            
            # Apply discount if this item has a promotion
            if item['menu_item_id'] in promotion_lookup:
                promotion = promotion_lookup[item['menu_item_id']]
                discount_percentage = float(promotion['discount_percentage'])
                item_discount = item_price * (discount_percentage / 100)
                discounted_price = item_price - item_discount
            
            # Calculate total revenue for this item
            total_revenue = discounted_price * item['quantity']
            total_amount += total_revenue
            
            print(f"Item: {item['item_name']}, Original Price: {item_price}, Discounted Price: {discounted_price}, Quantity: {item['quantity']}, Total Revenue: {total_revenue}")  # Debug log
            
            conn.execute('''
                INSERT INTO item_sales_records 
                (menu_item_id, quantity_sold, total_revenue, sale_date)
                VALUES (?, ?, ?, ?)
            ''', (item['menu_item_id'], item['quantity'], total_revenue, today))
        
        # Update order status
        conn.execute('''
            UPDATE orders SET status = 'paid' WHERE id = ?
        ''', (order_id,))
        
        # Update table status
        conn.execute('''
            UPDATE tables SET is_available = 1 WHERE id = ?
        ''', (order['table_id'],))
        
        conn.commit()
        return jsonify({'message': 'Payment processed successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

# API Routes for Performance Reports
@app.route('/api/reports/sales', methods=['GET'])
def get_sales_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    print(f"Generating sales report for date range: {start_date} to {end_date}")  # Debug log
    
    conn = get_db_connection()
    
    try:
        # Get best selling items and total sales
        best_sellers = conn.execute('''
            SELECT 
                m.name,
                COALESCE(SUM(i.quantity_sold), 0) as total_quantity,
                COALESCE(SUM(i.total_revenue), 0) as total_revenue
            FROM item_sales_records i
            JOIN menu_items m ON m.id = i.menu_item_id
            WHERE i.sale_date BETWEEN ? AND ?
            GROUP BY i.menu_item_id
            ORDER BY total_quantity DESC
            LIMIT 10
        ''', (start_date, end_date)).fetchall()
        
        response_data = {
            'best_sellers': [dict(item) for item in best_sellers]
        }
        
        print(f"Response data: {response_data}")  # Debug log
        return jsonify(response_data)
    except Exception as e:
        print(f"Error generating sales report: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True)

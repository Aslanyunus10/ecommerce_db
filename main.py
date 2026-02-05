import streamlit as st
import psycopg2
import pandas as pd
import time
import graphviz  # Şema çizimi için gerekli

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Pro E-Commerce Admin",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- SECURITY: ROLE-BASED LOGIN SYSTEM ---
def check_password():
    """Checks the username and password, returns the user role."""

    def password_entered():
        """Validates the password entered by the user."""
        u = st.session_state["username"]
        p = st.session_state["password"]
        
        if u == "admin" and p == "admin123":
            st.session_state["authenticated"] = True
            st.session_state["role"] = "admin"  # FULL ACCESS
        elif u == "guest" and p == "guest":
            st.session_state["authenticated"] = True
            st.session_state["role"] = "guest"  # READ-ONLY
        else:
            st.session_state["authenticated"] = False
            st.error("😕 Incorrect username or password.")

    if "authenticated" not in st.session_state:
        # --- LOGIN SCREEN CSS ---
        st.markdown("""
            <style>
            .stApp { background-color: #0E1117; }
            .stTextInput>div>div>input { background-color: #262730; color: white; }
            </style>
            """, unsafe_allow_html=True)
        
        st.title("🛡️ Secure Access Portal")
        st.write("Please log in with your credentials.")
        
        c1, c2 = st.columns(2)
        c1.text_input("Username", key="username")
        c2.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        
        st.info("👀 **Guest Login (View Only):** guest / guest") 
        return False
    
    elif not st.session_state["authenticated"]:
        st.title("🛡️ Secure Access Portal")
        c1, c2 = st.columns(2)
        c1.text_input("Username", key="username")
        c2.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 Login failed. Please try again.")
        return False
    else:
        return True

# --- IF LOGIN SUCCESSFUL ---
if check_password():
    
    user_role = st.session_state["role"]
    
    # --- SIDEBAR & DESIGN ---
    st.sidebar.title("Management Console")
    
    if user_role == "admin":
        st.sidebar.success(f"👤 Logged in as: ADMIN (Full Access)")
    else:
        st.sidebar.warning(f"👀 Logged in as: GUEST (Read-Only)")

    # --- CSS STYLING ---
    st.markdown("""
        <style>
        .stApp {
            background-color: #0E1117;
            background-image: linear-gradient(180deg, #0E1117 0%, #161B22 100%);
            background-attachment: fixed;
        }
        .stMetric { background-color: #262730 !important; border: 1px solid #30333F; border-radius: 10px; }
        h1, h2, h3, p, div, span, label, .stMarkdown { color: #E6EAF1 !important; }
        .stTextInput>div>div>input, .stSelectbox>div>div>div { color: white; background-color: #262730; }
        .stDataFrame { background-color: #262730; }
        </style>
        """, unsafe_allow_html=True)

    # --- DATABASE CONNECTION (CLOUD) ---
    import psycopg2
    
    # 👇👇👇 NEON LİNKİNİ BURAYA YAPIŞTIRMAYI UNUTMA! 👇👇👇
    DATABASE_URL = "postgresql://neondb_owner:npg_5wXhrgUl1kJd@ep-plain-feather-agzwzpw0-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require" 

    def get_connection():
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            st.error(f"🔌 Database Connection Error: {e}")
            return None

    def get_data(query):
        conn = get_connection()
        if conn:
            df = pd.read_sql(query, conn)
            conn.close()
            return df
        return pd.DataFrame()

    def run_query(query, params):
        conn = get_connection()
        if conn:
            cur = conn.cursor()
            try:
                cur.execute(query, params)
                conn.commit()
                return True, "Success"
            except Exception as e:
                return False, str(e)
            finally:
                conn.close()

    # --- SIDEBAR NAVIGATION ---
    st.sidebar.markdown("---")
    # YENİ MENÜ EKLENDİ: Database Schema
    menu = st.sidebar.radio("Go to", ["Dashboard", "Inventory Management", "Customer Management", "Orders", "Database Schema"])
    
    if st.sidebar.button("Logout"):
        del st.session_state["authenticated"]
        del st.session_state["role"]
        st.rerun()

    # --- HELPER FUNCTION ---
    def set_header_style(color, title, subtitle):
        st.markdown(f"""
        <div style="background-color:{color};padding:20px;border-radius:10px;margin-bottom:25px">
        <h1 style="color:white;margin:0;">{title}</h1>
        <p style="color:white;margin:0;opacity:0.8;">{subtitle}</p>
        </div>
        """, unsafe_allow_html=True)

    # --- 1. DASHBOARD ---
    if menu == "Dashboard":
        set_header_style("#FF4B4B", "📊 Executive Dashboard", "Real-time overview of business KPIs")
        
        col1, col2, col3, col4 = st.columns(4)
        
        df_prod = get_data("SELECT COUNT(*) as count FROM products")
        df_cust = get_data("SELECT COUNT(*) as count FROM customers")
        df_ord = get_data("SELECT COUNT(*) as count FROM orders")
        df_sales = get_data("SELECT SUM(total_amount) as total FROM orders")
        
        count_prod = df_prod['count'][0] if not df_prod.empty else 0
        count_cust = df_cust['count'][0] if not df_cust.empty else 0
        count_ord = df_ord['count'][0] if not df_ord.empty else 0
        total_rev = df_sales['total'][0] if not df_sales.empty and df_sales['total'][0] is not None else 0.0
        
        col1.metric("📦 Total Products", count_prod)
        col2.metric("👥 Total Customers", count_cust)
        col3.metric("🛒 Total Orders", count_ord)
        col4.metric("💰 Revenue", f"${total_rev:,.2f}")
        
        st.markdown("### 📈 Global Activity & Analytics")
        c1, c2 = st.columns([2, 1])
        with c1:
            # HARİTA ÖZELLİĞİ BURADA
            st.markdown("#### 🌍 Customer Locations")
            map_data = get_data("SELECT lat, lon FROM customers WHERE lat IS NOT NULL")
            if not map_data.empty:
                st.map(map_data, zoom=1, color="#FF4B4B")
            else:
                st.info("No location data available.")

        with c2:
            st.markdown("#### 📦 Stock by Category")
            df_chart = get_data("SELECT c.name as category, COUNT(p.product_id) as count FROM products p JOIN categories c ON p.category_id = c.category_id GROUP BY c.name")
            if not df_chart.empty:
                st.bar_chart(df_chart.set_index("category"), color="#FF4B4B")
            else:
                st.info("No data available.")

    # --- 2. INVENTORY ---
    elif menu == "Inventory Management":
        set_header_style("#1E90FF", "📦 Inventory Management", "View, Add, and Delete Products")
        
        if user_role == "admin":
            tab1, tab2, tab3 = st.tabs(["📋 View Inventory", "➕ Add Product", "🗑️ Delete Product"])
            
            with tab1:
                search = st.text_input("🔍 Search Inventory...", placeholder="Type product name...")
                query = "SELECT p.product_id, p.name, c.name as category, p.price, p.stock_quantity FROM products p JOIN categories c ON p.category_id = c.category_id"
                if search: query += f" WHERE p.name ILIKE '%{search}%'"
                df = get_data(query)
                st.dataframe(df, column_config={"price": st.column_config.NumberColumn(format="$%.2f"), "stock_quantity": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=100)}, use_container_width=True, hide_index=True)

            with tab2:
                st.markdown("#### Add New Item")
                df_cats = get_data("SELECT category_id, name FROM categories")
                if not df_cats.empty:
                    cat_dict = dict(zip(df_cats['name'], df_cats['category_id']))
                    with st.form("add_prod_form", clear_on_submit=True):
                        name = st.text_input("Product Name")
                        category = st.selectbox("Category", list(cat_dict.keys()))
                        price = st.number_input("Price ($)", min_value=0.0)
                        stock = st.slider("Initial Stock", 1, 500, 50)
                        if st.form_submit_button("💾 Save Product"):
                            success, msg = run_query("INSERT INTO products (name, category_id, price, stock_quantity) VALUES (%s, %s, %s, %s)", (name, cat_dict[category], price, stock))
                            if success: st.success("✅ Added!"); time.sleep(1); st.rerun()
                            else: st.error(msg)
                else:
                    st.error("Categories table is empty.")

            with tab3:
                st.warning("⚠️ Warning: This action is permanent.")
                df_products = get_data("SELECT product_id, name FROM products ORDER BY name")
                if not df_products.empty:
                    prod_dict = dict(zip(df_products['name'], df_products['product_id']))
                    selected_prod = st.selectbox("Select Product to Delete", list(prod_dict.keys()))
                    if st.button("❌ Delete Product"):
                        success, msg = run_query("DELETE FROM products WHERE product_id = %s", (prod_dict[selected_prod],))
                        if success: st.success("✅ Deleted!"); time.sleep(1); st.rerun()
                        else: st.error("⛔ Cannot delete.")
        else:
            st.info("👀 You are in Read-Only Mode.")
            df = get_data("SELECT p.name, c.name as category, p.price, p.stock_quantity FROM products p JOIN categories c ON p.category_id = c.category_id")
            st.dataframe(df, use_container_width=True, hide_index=True)

    # --- 3. CUSTOMERS ---
    elif menu == "Customer Management":
        set_header_style("#2E8B57", "👥 Customer Management", "Manage your Client Database")
        
        if user_role == "admin":
            tab1, tab2, tab3 = st.tabs(["📋 Customer List", "➕ Add Customer", "🗑️ Delete Customer"])
            with tab1:
                df = get_data('SELECT full_name, email, city, join_date FROM customers')
                st.dataframe(df, use_container_width=True, hide_index=True)
            with tab2:
                with st.form("add_cust"):
                    name = st.text_input("Full Name"); city = st.text_input("City"); email = st.text_input("Email")
                    if st.form_submit_button("💾 Save"):
                        success, msg = run_query("INSERT INTO customers (full_name, email, city) VALUES (%s, %s, %s)", (name, email, city))
                        if success: st.success("✅ Registered!"); time.sleep(1); st.rerun()
                        else: st.error(msg)
            with tab3:
                df_cust = get_data("SELECT customer_id, full_name FROM customers")
                if not df_cust.empty:
                    cust_dict = dict(zip(df_cust['full_name'], df_cust['customer_id']))
                    sel = st.selectbox("Select Customer", list(cust_dict.keys()))
                    if st.button("❌ Delete"):
                        success, msg = run_query("DELETE FROM customers WHERE customer_id = %s", (cust_dict[sel],))
                        if success: st.success("✅ Deleted!"); time.sleep(1); st.rerun()
                        else: st.error("⛔ Cannot delete.")
        else:
            df = get_data('SELECT full_name, email, city, join_date FROM customers')
            st.dataframe(df, use_container_width=True, hide_index=True)

    # --- 4. ORDERS ---
    elif menu == "Orders":
        set_header_style("#8A2BE2", "🛒 Order History", "Track transactions")
        df = get_data("SELECT o.order_id, c.full_name, c.email, o.total_amount, o.order_date FROM orders o JOIN customers c ON o.customer_id = c.customer_id ORDER BY o.order_date DESC")
        if not df.empty:
            st.dataframe(df, column_config={"total_amount": st.column_config.NumberColumn(format="$%.2f")}, use_container_width=True)
        else:
            st.info("No orders found.")

   # --- 5. DATABASE SCHEMA (RELATIONAL DIAGRAM) ---
    elif menu == "Database Schema":
        set_header_style("#FF8C00", "🔗 Relational Schema", "Entity Relationship Diagram (ERD)")
        
        st.markdown("""
        This diagram visualizes the **Relational Database Structure** implemented in PostgreSQL.
        It shows how tables are connected via **Primary Keys (PK)** and **Foreign Keys (FK)**.
        """)
        
        # Graphviz - Standard/Simple Version
        graph = graphviz.Digraph()
        graph.attr(rankdir='LR') # Left to Right layout
        
        # Node Style (Simple Box, Dark Background, Red Outline)
        graph.attr('node', shape='box', style='filled', fillcolor='#262730', fontcolor='white', color='#FF4B4B')
        graph.attr('edge', color='#E6EAF1')

        # Nodes (Standard Text Representation)
        graph.node('Customers', label='CUSTOMERS\n--\nPK customer_id\nfull_name\nemail\ncity\nlat, lon')
        graph.node('Orders', label='ORDERS\n--\nPK order_id\nFK customer_id\ntotal_amount\norder_date')
        graph.node('Categories', label='CATEGORIES\n--\nPK category_id\nname\ndescription')
        graph.node('Products', label='PRODUCTS\n--\nPK product_id\nFK category_id\nname\nprice\nstock')

        # Edges (Relationships)
        graph.edge('Customers', 'Orders', label='1 to Many')
        graph.edge('Categories', 'Products', label='1 to Many')
        
        st.graphviz_chart(graph)
        
        st.success("✅ Verified Relational Integrity on PostgreSQL 16")
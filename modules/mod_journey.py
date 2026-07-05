import streamlit as st
import database as db
import pandas as pd

def render_page(can_access_journey, is_observer):
    if not can_access_journey:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2 style='text-align: center; color: #0077b6;'>🗺️ مسار حركة العميل</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>تتبع الرحلة المتكاملة للعميل من رفع المقاسات وحتى التركيب النهائي والتسليم</p><hr>", unsafe_allow_html=True)
    
    # Get all customers/field visits
    visits = db.get_all_field_visits()
    if not visits:
        st.info("ℹ️ لا يوجد عملاء مسجلين في النظام لتتبع حركتهم. يرجى إدخال العملاء ورفع المقاسات أولاً.")
        return
        
    customer_options = {f"MHM{v[0]:05d} | {v[1]} ({v[4]})": v[0] for v in visits}
    selected_cust = st.selectbox("اختر العميل / المشروع لاستعراض وتتبع مساره وحركته بالتفصيل:", list(customer_options.keys()))
    v_id = customer_options[selected_cust]
    
    # Find client details
    v_details = None
    for v in visits:
        if v[0] == v_id:
            v_details = v
            break
            
    is_canceled = v_details[20] if len(v_details) > 20 else 0
            
    # Check design info
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("SELECT designer_name, status, notes FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
    design_info = c.fetchone()
    
    # Check contract info
    # We match client name or search in contracts
    c.execute("SELECT contract_no, status, value, notes, odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (v_details[1], f"%MHM{v_id:05d}%"))
    contract_info = c.fetchone()
    
    # Check production info
    c.execute("SELECT assigned_factory, status, progress, notes FROM ProjectProduction WHERE visit_id = ?", (v_id,))
    prod_info = c.fetchone()
    
    # Check support tickets
    c.execute("SELECT title, status, created_at FROM tickets WHERE customer_id = ?", (v_id,))
    tickets_info = c.fetchall()
    conn.close()
    
    if is_canceled == 1:
        st.error("⚠️ هذا المشروع تم إلغاؤه/الاعتذار عنه من مسار رفع المقاسات.")

    # Render interactive vertical timeline
    st.markdown("### 📍 الخط الزمني لرحلة العميل")
    
    # 1. Size measurements stage
    m_icon = "❌ [تم الاعتذار]" if is_canceled == 1 else "🟢" if v_details[12] == "نعم" else "🟡"
    odoo_no = contract_info[4] if contract_info else ""
    odoo_tag = f" | <b>رقم أودو:</b> <span style='color:red;font-weight:bold;'>{odoo_no}</span>" if odoo_no else ""
    
    st.markdown(f"""
    <div style='background-color: #ffffff; border-right: 5px solid #4caf50; padding: 15px; border-radius: 8px; margin-bottom: 12px;'>
        <h4 style='color: #2e7d32; margin: 0;'>1. مسار رفع المقاسات والمعاينة الميدانية {m_icon}</h4>
        <p style='margin: 5px 0 0 0; font-size: 14px;'>
            <b>رقم مسارات:</b> MHM{v_id:05d} {odoo_tag}<br>
            <b>حالة رفع المقاسات:</b> {v_details[12]} | <b>تاريخ الزيارة:</b> {v_details[6]} {v_details[7]}<br>
            <b>نوع الأثاث المطلوبة:</b> {v_details[4]} | <b>حالة الموقع:</b> {v_details[5]}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Design stage
    if design_info:
        d_icon = "🟢" if "مكتمل" in design_info[1] else "🔵"
        st.markdown(f"""
        <div style='background-color: #ffffff; border-right: 5px solid #00b4d8; padding: 15px; border-radius: 8px; margin-bottom: 12px;'>
            <h4 style='color: #0077b6; margin: 0;'>2. مسار التصميم {d_icon}</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>
                <b>المصمم المسؤول:</b> {design_info[0]} | <b>حالة التصميم:</b> {design_info[1]}<br>
                <b>الملاحظات:</b> {design_info[2] or 'لا توجد'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #f5f5f5; border-right: 5px solid #9e9e9e; padding: 15px; border-radius: 8px; margin-bottom: 12px; opacity: 0.6;'>
            <h4 style='color: #616161; margin: 0;'>2. مسار التصميم ⏳</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>بانتظار تعيين مصمم وبدء العمل على التصاميم المقترحة للعميل.</p>
        </div>
        """, unsafe_allow_html=True)
        
    # 3. Contract stage
    if contract_info:
        c_odoo = contract_info[4]
        c_odoo_tag = f" | <b>رقم أودو:</b> {c_odoo}" if c_odoo else ""
        st.markdown(f"""
        <div style='background-color: #ffffff; border-right: 5px solid #ffb703; padding: 15px; border-radius: 8px; margin-bottom: 12px;'>
            <h4 style='color: #fb8500; margin: 0;'>3. مسار العقود 📝</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>
                <b>رقم العقد:</b> {contract_info[0]}{c_odoo_tag} | <b>قيمة العقد:</b> {contract_info[2]:,.2f} د.ل<br>
                <b>حالة العقد:</b> {contract_info[1]} | <b>الملاحظات:</b> {contract_info[3] or 'لا توجد'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #f5f5f5; border-right: 5px solid #9e9e9e; padding: 15px; border-radius: 8px; margin-bottom: 12px; opacity: 0.6;'>
            <h4 style='color: #616161; margin: 0;'>3. مسار العقود ⏳</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>بانتظار إبرام وتوقيع العقد الرسمي مع العميل وتحديد الدفعات المالية.</p>
        </div>
        """, unsafe_allow_html=True)
        
    # 4. Production stage
    if prod_info:
        p_icon = "🟢" if "تم التركيب" in prod_info[1] else "🔵"
        st.markdown(f"""
        <div style='background-color: #ffffff; border-right: 5px solid #7209b7; padding: 15px; border-radius: 8px; margin-bottom: 12px;'>
            <h4 style='color: #560bad; margin: 0;'>4. مسار الإنتاج والتصنيع {p_icon}</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>
                <b>المصنع/الورشة:</b> {prod_info[0]} | <b>حالة التصنيع:</b> {prod_info[1]}<br>
                <b>نسبة التقدم:</b> {prod_info[2]}% | <b>الملاحظات:</b> {prod_info[3] or 'لا توجد'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #f5f5f5; border-right: 5px solid #9e9e9e; padding: 15px; border-radius: 8px; margin-bottom: 12px; opacity: 0.6;'>
            <h4 style='color: #616161; margin: 0;'>4. مسار الإنتاج والتصنيع ⏳</h4>
            <p style='margin: 5px 0 0 0; font-size: 14px;'>بانتظار تحويل المشروع للمصنع لبدء عملية التصنيع والقص والتركيب بعد إمضاء العقد.</p>
        </div>
        """, unsafe_allow_html=True)
        
    # 5. Tickets stage
    if tickets_info:
        st.markdown("#### 🛠️ الدعم الفني وتذاكر الصيانة للعميل:")
        for t in tickets_info:
            t_status_color = "red" if t[1] == "جديدة" else "orange" if t[1] == "قيد المعالجة" else "green"
            st.markdown(f"- **{t[0]}** - حالة التذكرة: <span style='color: {t_status_color}; font-weight: bold;'>{t[1]}</span> ({t[2]})", unsafe_allow_html=True)

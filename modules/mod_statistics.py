import streamlit as st
import database as db
import pandas as pd

def render_page(can_access_statistics, is_observer):
    if not can_access_statistics:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2 style='text-align: center; color: #0077b6;'>📊 إحصائيات النظام العامة</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>تقارير إحصائية وتحليلية دقيقة لحركة وتدفق العملاء عبر المسارات</p><hr>", unsafe_allow_html=True)
    
    # Get all customers/field visits
    visits = db.get_all_field_visits()
    if not visits:
        st.info("ℹ️ لا توجد بيانات كافية لعرض الإحصائيات حالياً.")
        return
        
    conn = db.get_connection()
    c = conn.cursor()
    
    # Total Contracts count and value
    c.execute("SELECT COUNT(*), COALESCE(SUM(value), 0) FROM Contracts")
    contracts_count, contracts_val = c.fetchone()
    
    # Active Designs
    c.execute("SELECT COUNT(*) FROM ProjectDesigns WHERE status != 'مكتمل ومقبول'")
    active_designs = c.fetchone()[0]
    
    # Active Production
    c.execute("SELECT COUNT(*) FROM ProjectProduction WHERE status != 'تم التركيب والتسليم' AND status != 'بانتظار التعاقد'")
    active_prod = c.fetchone()[0]
    
    # Active Support Tickets
    c.execute("SELECT COUNT(*) FROM tickets WHERE status != 'مغلقة'")
    active_tickets = c.fetchone()[0]
    conn.close()
    
    # Metrics display
    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("👥 إجمالي طلبات الرفع", len(visits))
    mcol2.metric("📝 إجمالي العقود المبرمة", f"{contracts_count} عقود", f"{contracts_val:,.2f} د.ل")
    mcol3.metric("🏭 مشاريع قيد التصنيع", active_prod)
    mcol4.metric("🛠️ التذاكر المفتوحة", active_tickets)
    
    st.markdown("### 📈 إحصائيات وتقدم مسارات المشاريع")
    
    # Construct a dashboard dataframe
    dash_data = []
    for v in visits:
        v_id = v[0]
        c_name = v[1]
        
        # Design status
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT status FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
        ds = c.fetchone()
        d_status = ds[0] if ds else "لم يبدأ"
        
        # Contract status and odoo_no
        c.execute("SELECT contract_no, status, odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (c_name, f"%MHM{v_id:05d}%"))
        cs = c.fetchone()
        c_status = f"موقع ({cs[0]})" if cs else "غير موقع"
        odoo_no = cs[2] if cs else ""
        
        # Production status
        c.execute("SELECT status, progress FROM ProjectProduction WHERE visit_id = ?", (v_id,))
        ps = c.fetchone()
        p_status = f"{ps[0]} ({ps[1]}%)" if ps else "لم يبدأ"
        conn.close()
        
        is_canceled = v[20] if len(v) > 20 else 0
        m_status = "❌ تم الاعتذار/الملغي" if is_canceled == 1 else "مكتمل" if v[12] == "نعم" else "فشل/معلق"
        
        dash_data.append((
            f"MHM{v_id:05d}",
            odoo_no or "—",
            c_name,
            m_status,
            d_status if is_canceled == 0 else "—",
            c_status if is_canceled == 0 else "—",
            p_status if is_canceled == 0 else "—"
        ))
        
    df_dash = pd.DataFrame(dash_data, columns=["رقم مسارات", "رقم أودو", "اسم العميل", "حالة رفع المقاسات", "حالة التصميم", "حالة التعاقد", "حالة الإنتاج"])
    # Add sequence number #
    df_dash["#"] = range(1, len(df_dash) + 1)
    # Reverse columns for RTL visual order (right to left: #, رقم مسارات, رقم أودو, اسم العميل, حالة رفع المقاسات, حالة التصميم, حالة التعاقد, حالة الإنتاج)
    df_dash = df_dash[["حالة الإنتاج", "حالة التعاقد", "حالة التصميم", "حالة رفع المقاسات", "اسم العميل", "رقم أودو", "رقم مسارات", "#"]]
    st.dataframe(df_dash, use_container_width=True, hide_index=True)

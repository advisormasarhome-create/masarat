import streamlit as st
import database as db
import pandas as pd

def render_page(can_access_production, is_observer):
    if not can_access_production:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2 style='text-align: center; color: #0077b6;'>🏭 مسار الإنتاج</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>متابعة خط الإنتاج والتصنيع للمشاريع والعملاء</p><hr>", unsafe_allow_html=True)
    
    # Get all customers/field visits
    visits = db.get_all_field_visits()
    if not visits:
        st.info("ℹ️ لا يوجد عملاء مسجلين في النظام. يرجى إدخال العملاء ورفع المقاسات أولاً.")
        return
        
    # Check/Create table for production if not exists
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ProjectProduction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id INTEGER UNIQUE,
            assigned_factory TEXT DEFAULT "",
            status TEXT DEFAULT "بانتظار التعاقد",
            progress INTEGER DEFAULT 0,
            notes TEXT DEFAULT "",
            last_updated TEXT DEFAULT ""
        )
    ''')
    conn.commit()
    conn.close()
    
    tab1, tab2 = st.tabs(["📋 سجل خط الإنتاج", "⚙️ تحديث حالة التصنيع"])
    
    with tab1:
        # Load production join field visits and design links
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT f.id, f.customer_name, f.phone, f.furniture_type,
                   COALESCE(p.assigned_factory, 'غير محدد'),
                   COALESCE(p.status, 'بانتظار التعاقد'),
                   COALESCE(p.progress, 0),
                   COALESCE(p.notes, ''),
                   COALESCE(d.design_link, ''),
                   COALESCE(d.odoo_no, ''),
                   COALESCE(f.media_paths, ''),
                   COALESCE(d.design_docs, ''),
                   COALESCE(d.workshop_drawing, '')
            FROM FieldVisits f
            INNER JOIN ProjectDesigns d ON f.id = d.visit_id AND d.price_is_paid = 1
            LEFT JOIN ProjectProduction p ON f.id = p.visit_id
            WHERE f.is_canceled = 0
            ORDER BY f.id DESC
        ''')
        prod_records = c.fetchall()
        conn.close()
        
        # Render a custom styled table for better visual presentation of documents
        st.markdown("### 📋 جدول متابعة خطوط الإنتاج والملفات الفنية للتصنيع")
        for row in prod_records:
            v_id, c_name, phone, f_type, factory, status, progress, notes, design_link, odoo_no, media_paths, design_docs, workshop_drawing = row
            mhm_code = f"MHM{v_id:05d}"
            odoo_tag = f" | 🔢 Odoo: {odoo_no}" if odoo_no else ""
            
            with st.expander(f"🏭 {mhm_code}{odoo_tag} — {c_name} | {factory} | إنجاز: {progress}%"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**📞 الهاتف:** {phone}")
                    st.write(f"**🪑 الأثاث المطلوب:** {f_type}")
                    st.write(f"**📌 حالة التصنيع:** {status}")
                    st.write(f"**📝 ملاحظات الإنتاج:** {notes if notes else 'لا توجد'}")
                with col2:
                    st.markdown("**📂 المستندات والملفات الفنية المرفوعة للتصنيع:**")
                    
                    if workshop_drawing and os.path.exists(workshop_drawing):
                        fname = os.path.basename(workshop_drawing)
                        with open(workshop_drawing, "rb") as f_obj:
                            b64 = base64.b64encode(f_obj.read()).decode()
                        href = f'<a href="data:application/pdf;base64,{b64}" download="{fname}" style="display: inline-block; padding: 6px 12px; margin: 4px 0px; background-color: #ffebee; color: #c62828; text-decoration: none; border-radius: 4px; border: 1px solid #ef9a9a; font-size: 13px; font-weight: bold; width:100%; text-align:center;">🏭 الرسم الفني للمصنع (Workshop Drawing)</a>'
                        st.markdown(href, unsafe_allow_html=True)
                    
                    if design_link:
                        st.markdown(f'<a href="{design_link}" target="_blank" style="display:inline-block; background-color:#e0f7fa; color:#0077b6; padding:5px 10px; border-radius:4px; text-decoration:none; font-weight:bold; border:1px solid #00b4d8; font-size:12px; margin-bottom:5px; width:100%; text-align:center;">🔗 رابط التصميم (Drive/Dropbox)</a>', unsafe_allow_html=True)
                    
                    import os
                    import base64
                    
                    all_h_files = []
                    for p in (media_paths or "").split(","):
                        if p and os.path.exists(p):
                            all_h_files.append((p, "📐"))
                    for p in (design_docs or "").split(","):
                        if p and os.path.exists(p):
                            all_h_files.append((p, "🎨"))
                            
                    if all_h_files:
                        for p, icon in all_h_files:
                            fname = os.path.basename(p)
                            display_name = fname
                            if fname.startswith(f"design_{v_id}_"):
                                display_name = fname[len(f"design_{v_id}_"):]
                            with open(p, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 4px 8px; margin: 2px 0px; background-color: #f8f9fa; color: #212529; text-decoration: none; border-radius: 4px; border: 1px solid #ced4da; font-size: 12px; font-weight: bold; width:100%; text-align:center;">{icon} {display_name}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                    else:
                        if not workshop_drawing:
                            st.warning("⚠️ لا توجد مستندات مرفوعة لهذا العميل.")
                        
    with tab2:
        if is_observer:
            st.warning("🔒 وضع القراءة فقط: لا يمكنك تعديل حالة الإنتاج.")
        else:
            # Filter visits that are paid (first deposit paid)
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT visit_id FROM ProjectDesigns WHERE price_is_paid = 1")
            completed_visit_ids = {row[0] for row in c.fetchall()}
            conn.close()
            
            active_visits = [v for v in visits if (v[20] if len(v) > 20 else 0) == 0 and v[0] in completed_visit_ids]
            if not active_visits:
                st.warning("⚠️ لا توجد مشاريع نشطة بتصاميم معتمدة ودفعات مؤكدة للإنتاج حالياً.")
                st.stop()
                
            with st.form("update_production_form"):
                customer_options = {f"MHM{v[0]:05d} | {v[1]} ({v[4]})": v[0] for v in active_visits}
                selected_cust = st.selectbox("اختر العميل / المشروع لتحديث حالة إنتاجه وتصنيعه:", list(customer_options.keys()))
                v_id = customer_options[selected_cust]
                
                # Fetch existing production if exists
                conn = db.get_connection()
                c = conn.cursor()
                c.execute("SELECT assigned_factory, status, progress, notes FROM ProjectProduction WHERE visit_id = ?", (v_id,))
                existing = c.fetchone()
                
                # Also fetch design info to show the engineer the available documents right inside the form
                c.execute("SELECT design_link, COALESCE(design_docs, ''), COALESCE(workshop_drawing, ''), second_payment_paid FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
                d_link_row = c.fetchone()
                
                # Fetch field visits media paths
                c.execute("SELECT COALESCE(media_paths, '') FROM FieldVisits WHERE id = ?", (v_id,))
                fv_row = c.fetchone()
                conn.close()
                
                p_factory = existing[0] if existing else ""
                p_status = existing[1] if existing else "بانتظار التعاقد"
                p_progress = existing[2] if existing else 0
                p_notes = existing[3] if existing else ""
                
                d_link = d_link_row[0] if d_link_row else ""
                design_docs = d_link_row[1] if d_link_row else ""
                workshop_drawing = d_link_row[2] if d_link_row else ""
                media_paths = fv_row[0] if fv_row else ""
                
                if d_link:
                    st.markdown(f"🔗 **رابط التصميم (Drive / Dropbox):** [{d_link}]({d_link})")
                
                import os
                import base64
                
                if workshop_drawing and os.path.exists(workshop_drawing):
                    fname = os.path.basename(workshop_drawing)
                    with open(workshop_drawing, "rb") as f_obj:
                        b64 = base64.b64encode(f_obj.read()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="{fname}" style="display: inline-block; padding: 6px 12px; margin-bottom: 12px; background-color: #ffebee; color: #c62828; text-decoration: none; border-radius: 4px; border: 1px solid #ef9a9a; font-size: 13px; font-weight: bold;">🏭 الرسم الفني للمصنع (Workshop Drawing)</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                all_h_files = []
                for p in (media_paths or "").split(","):
                    if p and os.path.exists(p):
                        all_h_files.append((p, "📐"))
                for p in (design_docs or "").split(","):
                    if p and os.path.exists(p):
                        all_h_files.append((p, "🎨"))
                        
                if all_h_files:
                    st.markdown("**📎 مستندات المشروع التراكمية المتوفرة للإنتاج:**")
                    for p, icon in all_h_files:
                        fname = os.path.basename(p)
                        display_name = fname
                        if fname.startswith(f"design_{v_id}_"):
                            display_name = fname[len(f"design_{v_id}_"):]
                        with open(p, "rb") as f_obj:
                            b64 = base64.b64encode(f_obj.read()).decode()
                            href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 4px 8px; margin: 2px; background-color: #f8f9fa; color: #212529; text-decoration: none; border-radius: 4px; border: 1px solid #ced4da; font-size: 12px; font-weight: bold;">{icon} {display_name}</a>'
                            st.markdown(href, unsafe_allow_html=True)
                    st.markdown("---")
                
                factory = st.text_input("المصنع / الورشة المسؤولة", value=p_factory)
                status = st.selectbox("حالة الإنتاج", ["بانتظار التعاقد", "قص وتفصيل الأخشاب", "التجميع المبدئي", "الدهان والتشطيب", "التعبئة والتغليف", "جاهز للشحن والتركيب", "تم التركيب والتسليم"], index=["بانتظار التعاقد", "قص وتفصيل الأخشاب", "التجميع المبدئي", "الدهان والتشطيب", "التعبئة والتغليف", "جاهز للشحن والتركيب", "تم التركيب والتسليم"].index(p_status) if p_status in ["بانتظار التعاقد", "قص وتفصيل الأخشاب", "التجميع المبدئي", "الدهان والتشطيب", "التعبئة والتغليف", "جاهز للشحن والتركيب", "تم التركيب والتسليم"] else 0)
                progress = st.number_input("نسبة الإنجاز والتقدم (%)", min_value=0, max_value=100, value=int(p_progress), step=5)
                notes = st.text_area("ملاحظات التصنيع ومتابعة الجودة", value=p_notes)
                
                submit = st.form_submit_button("💾 حفظ حالة التصنيع")
                
                if submit:
                    second_paid = d_link_row[3] if (d_link_row and len(d_link_row) > 3) else 0
                    if (status == "تم التركيب والتسليم" or progress == 100) and not second_paid:
                        st.error("⚠️ عذراً: لا يمكن تغيير حالة الإنتاج إلى 'تم التركيب والتسليم' أو الوصول لنسبة إنجاز 100% لأن العميل لم يقم بتسديد الدفعة الثانية والأخيرة في الخزينة بعد.")
                    else:
                        import datetime
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn = db.get_connection()
                        c = conn.cursor()
                        c.execute('''
                            INSERT INTO ProjectProduction (visit_id, assigned_factory, status, progress, notes, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?)
                            ON CONFLICT(visit_id) DO UPDATE SET
                                assigned_factory=excluded.assigned_factory,
                                status=excluded.status,
                                progress=excluded.progress,
                                notes=excluded.notes,
                                last_updated=excluded.last_updated
                        ''', (v_id, factory.strip(), status, progress, notes.strip(), now_str))
                        conn.commit()
                        conn.close()
                        
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="تعديل إنتاج",
                            module="مسار الانتاج",
                            details=f"تم تحديث تصنيع العميل MHM{v_id:05d} إلى: {status} (الإنجاز: {progress}%)"
                        )
                        st.success("✅ تم حفظ حالة التصنيع والإنتاج بنجاح!")
                        st.rerun()

import streamlit as st
import database as db
import pandas as pd
import os
import datetime
import base64
import time

def render_page(can_access_design, is_observer):
    if not can_access_design:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2 style='text-align: center; color: #0077b6;'>🎨 مسار التصاميم</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>إدارة وتتبع تصاميم المشاريع المرتبطة بالعملاء</p><hr>", unsafe_allow_html=True)
    
    # Get all customers/field visits
    visits = db.get_all_field_visits()
    if not visits:
        st.info("ℹ️ لا يوجد عملاء مسجلين في النظام. يرجى إدخال العملاء ورفع المقاسات أولاً.")
        return
        

    
    tab1, tab2 = st.tabs(["📋 سجل المشاريع", "📜 تاريخ تعديلات التصميم"])
    
    with tab1:
        # Load designs join field visits and contracts (to pull odoo_no)
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT f.id, f.customer_name, f.phone, f.furniture_type,
                   COALESCE(d.designer_name, 'غير معين'),
                   COALESCE(d.status, 'مجدول'),
                   COALESCE(d.design_link, ''),
                   COALESCE(d.notes, ''),
                   COALESCE(con.odoo_no, ''),
                   f.is_canceled,
                   COALESCE(f.media_paths, ''),
                   COALESCE(d.design_docs, ''),
                   COALESCE(f.approved_at, '')
            FROM FieldVisits f
            LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
            LEFT JOIN Contracts con ON f.customer_name = con.client_name
            WHERE f.is_approved = 1
            ORDER BY f.id DESC
        ''')
        design_records = c.fetchall()
        conn.close()
        
        formatted_records = []
        for row in design_records:
            v_id, c_name, phone, fur_type, designer, status, link, notes, odoo, is_canceled, media_paths, design_docs, approved_at = row
            if is_canceled == 1:
                c_name = f"{c_name} ❌ [ملغي/اعتذار]"
                
            # Default status to 'مجدول'
            if not status or status.strip() == "":
                status = "مجدول"
                
            display_approved_date = approved_at
            
            formatted_records.append((v_id, c_name, status, display_approved_date, notes))
            
        df_designs = pd.DataFrame(formatted_records, columns=["المعرف", "اسم العميل", "الحالة", "تاريخ الاستلام", "ملاحظات"])
        # Add MHM format
        df_designs["رقم مسارات"] = df_designs["المعرف"].apply(lambda x: f"MHM{x:05d}")
        # Add sequence number
        df_designs["تسلسل"] = range(1, len(df_designs) + 1)
        # Reverse columns for RTL visual order
        df_designs = df_designs[["المعرف", "ملاحظات", "تاريخ الاستلام", "الحالة", "اسم العميل", "رقم مسارات", "تسلسل"]]
        
        st.markdown("##### 💡 انقر على أي صف في الجدول أدناه لعرض وتحديث بيانات التصميم الخاصة به:")
        selected_rows = st.dataframe(
            df_designs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "المعرف": None,  # Hide ID column
                "تاريخ الاستلام": st.column_config.TextColumn(
                    label="تاريخ الاستلام",
                    help="تاريخ التحويل من مسار المقاسات"
                )
            },
            on_select="rerun",
            selection_mode="single-row"
        )
        
        # Determine selection
        selected_visit_id = None
        if selected_rows and selected_rows.get("selection", {}).get("rows"):
            selected_idx = selected_rows["selection"]["rows"][0]
            selected_visit_id = int(df_designs.iloc[selected_idx]["المعرف"])
            st.session_state['selected_design_visit_id'] = selected_visit_id
        else:
            selected_visit_id = st.session_state.get('selected_design_visit_id', None)
            
        if selected_visit_id:
            st.markdown("---")
            st.markdown(f"### ⚙️ تعديل بيانات التصميم للمشروع: `MHM{selected_visit_id:05d}`")
            
            if is_observer:
                st.warning("🔒 وضع القراءة فقط: لا يمكنك تعديل التصاميم.")
            else:
                # Fetch existing design and measurement files
                conn = db.get_connection()
                c = conn.cursor()
                c.execute('''
                    SELECT d.designer_name, d.status, d.design_link, d.notes, d.odoo_no, 
                           COALESCE(d.design_docs, ''), COALESCE(f.media_paths, ''), 
                           f.customer_name, f.phone, f.furniture_type, f.address, 
                           COALESCE(d.is_sent_to_production, 0), COALESCE(d.workshop_drawing, '')
                    FROM FieldVisits f
                    LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
                    WHERE f.id = ?
                ''', (selected_visit_id,))
                existing_row = c.fetchone()
                
                # Check current number of edits
                c.execute("SELECT COUNT(*) FROM ProjectDesignHistory WHERE visit_id = ? AND status = 'قيد التعديل'", (selected_visit_id,))
                current_edit_count = c.fetchone()[0]
                conn.close()
                
                d_name = ""
                d_status = "مجدول"
                d_link = ""
                d_notes = ""
                d_odoo = ""
                d_docs = ""
                media_paths = ""
                c_name = ""
                c_phone = ""
                c_furniture = ""
                c_address = ""
                is_sent_prod = 0
                d_workshop = ""
                
                if existing_row:
                    d_name = existing_row[0] if existing_row[0] is not None else ""
                    if d_name == "غير معين":
                        d_name = ""
                    d_status = existing_row[1] if existing_row[1] is not None else "مجدول"
                    d_link = existing_row[2] if existing_row[2] is not None else ""
                    d_notes = existing_row[3] if existing_row[3] is not None else ""
                    d_odoo = existing_row[4] if existing_row[4] is not None else ""
                    d_docs = existing_row[5] if existing_row[5] is not None else ""
                    media_paths = existing_row[6] if existing_row[6] is not None else ""
                    c_name = existing_row[7]
                    c_phone = existing_row[8]
                    c_furniture = existing_row[9]
                    c_address = existing_row[10]
                    is_sent_prod = existing_row[11] if existing_row[11] is not None else 0
                    d_workshop = existing_row[12] if existing_row[12] is not None else ""
                
                # Display files
                # 1. Measurement files
                meas_paths = [p for p in media_paths.split(",") if p]
                if meas_paths:
                    st.markdown("**📐 مستندات رفع المقاسات المستلمة للعميل:**")
                    for p in meas_paths:
                        if os.path.exists(p):
                            fname = os.path.basename(p)
                            with open(p, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 5px 10px; margin: 2px 2px 8px 2px; background-color: #f1f8e9; color: #33691e; text-decoration: none; border-radius: 4px; border: 1px solid #81c784; font-size: 13px; font-weight: bold;">⬇️ {fname}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                    st.markdown("---")

                # 2. Design files
                des_paths = [p for p in d_docs.split(",") if p]
                if des_paths:
                    st.markdown("**🎨 مستندات التصميم المرفوعة حالياً:**")
                    for p in des_paths:
                        if os.path.exists(p):
                            fname = os.path.basename(p)
                            display_name = fname
                            if fname.startswith(f"design_{selected_visit_id}_"):
                                display_name = fname[len(f"design_{selected_visit_id}_"):]
                            with open(p, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 5px 10px; margin: 2px 2px 8px 2px; background-color: #e0f7fa; color: #0077b6; text-decoration: none; border-radius: 4px; border: 1px solid #00b4d8; font-size: 13px; font-weight: bold;">⬇️ {display_name}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                    st.markdown("---")
                
                with st.form(f"update_design_form_{selected_visit_id}"):
                    st.markdown("##### 📋 بيانات المشروع والعميل (قابلة للتعديل والتحديث)")
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        c_name_input = st.text_input("اسم العميل", value=c_name, key=f"c_name_ds_{selected_visit_id}")
                        c_furniture_input = st.text_input("نوع الأثاث المطلوب", value=c_furniture, key=f"c_furniture_ds_{selected_visit_id}")
                    with col_info2:
                        c_phone_input = st.text_input("رقم الهاتف", value=c_phone, key=f"c_phone_ds_{selected_visit_id}")
                        c_address_input = st.text_input("العنوان بالتفصيل", value=c_address, key=f"c_address_ds_{selected_visit_id}")
                    
                    st.markdown("---")
                    
                    col_mhm, col_odoo = st.columns(2)
                    with col_mhm:
                        st.text_input("رقم منظومة مسارات", value=f"MHM{selected_visit_id:05d}", disabled=True)
                    with col_odoo:
                        odoo_val = st.text_input("رقم منظومة أودو المكافئ له", value=d_odoo)
                        
                    designer_options = [
                        "اختر المصمم المسؤول...",
                        "م. شهد الطاهر هويدي",
                        "م. عبد الرؤوف محمد عريبي",
                        "اكتب اسم المصمم / ــة"
                    ]
                    default_sel_idx = 0
                    manual_designer_val = ""
                    if d_name and d_name != "غير معين":
                        if d_name in ["م. شهد الطاهر هويدي", "م. عبد الرؤوف محمد عريبي"]:
                            default_sel_idx = designer_options.index(d_name)
                        else:
                            default_sel_idx = designer_options.index("اكتب اسم المصمم / ــة")
                            manual_designer_val = d_name
                            
                    selected_opt = st.selectbox("المصمم المسؤول * (إلزامي)", designer_options, index=default_sel_idx)
                    if selected_opt == "اكتب اسم المصمم / ــة":
                        designer = st.text_input("اسم المصمم / ــة (كتابة يدوية) *", value=manual_designer_val)
                    else:
                        designer = selected_opt
                    status_options = ["مجدول", "قيد التنفيذ", "بانتظار موافقة العميل", "قيد التعديل", "مكتمل نهائي"]
                    status = st.selectbox("حالة التصميم", status_options, index=status_options.index(d_status) if d_status in status_options else 0)
                    design_link = st.text_input("رابط التصميم (Drive / Dropbox)", value=d_link)
                    
                    uploaded_files = st.file_uploader("📎 تحميل مستندات التصميم (PDF / صور / ملفات)", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "docx", "zip", "rar"])
                    
                    # Display current workshop drawing if it exists
                    if d_workshop and os.path.exists(d_workshop):
                        st.markdown("**🏭 الرسم الفني الحالي للمصنع (Workshop Drawing):**")
                        w_name = os.path.basename(d_workshop)
                        with open(d_workshop, "rb") as w_file:
                            w_b64 = base64.b64encode(w_file.read()).decode()
                        w_href = f'<a href="data:application/pdf;base64,{w_b64}" download="{w_name}" style="display: inline-block; padding: 5px 10px; margin: 2px 2px 8px 2px; background-color: #ffebee; color: #c62828; text-decoration: none; border-radius: 4px; border: 1px solid #ef9a9a; font-size: 13px; font-weight: bold;">⬇️ {w_name}</a>'
                        st.markdown(w_href, unsafe_allow_html=True)
                    
                    uploaded_workshop_file = st.file_uploader("🏭 تحميل الرسم الفني للمصنع (Workshop Drawing) - صيغة PDF فقط:", type=["pdf"], key=f"workshop_drawing_{selected_visit_id}")
                    
                    notes = st.text_area("ملاحظات التصميم والتعديلات", value=d_notes)
                    
                    approved_by_manager = False
                    if current_edit_count >= 2:
                        st.warning(f"⚠️ هذا التصميم تم تعديله مسبقاً ({current_edit_count}) مرات. لا يسمح بإجراء تعديل إضافي إلا بعد اعتماد مدير الصالة كحالة استثنائية.")
                        if st.session_state.get('role', '') == 'Admin':
                            approved_by_manager = st.checkbox("✅ تم اعتماد هذا التعديل الاستثنائي من قبل مدير الصالة (صلاحية الإدارة)")
                        else:
                            st.error("🔒 يتطلب هذا الإجراء تسجيل الدخول بحساب الإدارة.")
                    
                    # Check if design record exists in database
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute("SELECT 1 FROM ProjectDesigns WHERE visit_id = ?", (selected_visit_id,))
                    has_existing_db = c.fetchone()
                    conn.close()
                    
                    is_admin_user = (st.session_state.get('username') == 'Admin' or st.session_state.get('role') == 'Admin')
                    
                    if has_existing_db:
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        with col_btn1:
                            submit = st.form_submit_button("💾 حفظ السجل", use_container_width=True)
                        with col_btn2:
                            submit_approve = st.form_submit_button("💾 حفظ واعتماد السجل", use_container_width=True)
                        with col_btn3:
                            delete_submit = st.form_submit_button("🗑️ حذف سجل التصميم", type="secondary", use_container_width=True, help="اتصل بمدير النظام للموافقة على تطبيق الاجراء")
                    else:
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            submit = st.form_submit_button("💾 حفظ السجل", use_container_width=True)
                        with col_btn2:
                            submit_approve = st.form_submit_button("💾 حفظ واعتماد السجل", use_container_width=True)
                        delete_submit = False
                
                if submit or submit_approve:
                    if designer == "اختر المصمم المسؤول..." or designer == "اكتب اسم المصمم / ــة" or designer.strip() == "" or designer.strip() == "غير معين":
                        st.error("⚠️ يرجى اختيار اسم المصمم المسؤول أو كتابته يدوياً!")
                        st.stop()
                    if status == "قيد التعديل" and current_edit_count >= 2 and not approved_by_manager:
                        st.error("⚠️ لا يمكن حفظ التعديل الثالث دون تفعيل خيار الاعتماد من مدير الصالة!")
                        st.stop()
                        
                    now = datetime.datetime.now()
                    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Process uploaded files
                    upload_dir = "desdata"
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    saved_paths = []
                    if d_docs:
                        saved_paths = [p for p in d_docs.split(",") if p]
                        
                    if uploaded_files:
                        for f in uploaded_files:
                            safe_name = "".join(c for c in f.name if c.isalnum() or c in " ._-")
                            file_name = f"design_{selected_visit_id}_{safe_name}"
                            file_path = os.path.join(upload_dir, file_name)
                            with open(file_path, "wb") as file_out:
                                file_out.write(f.read())
                            if file_path not in saved_paths:
                                saved_paths.append(file_path)
                                
                    new_docs_str = ",".join(saved_paths)
                    
                    # Process uploaded workshop drawing
                    new_workshop_path = d_workshop
                    if uploaded_workshop_file:
                        workshop_dir = "desdata"
                        os.makedirs(workshop_dir, exist_ok=True)
                        safe_w_name = "".join(c for c in uploaded_workshop_file.name if c.isalnum() or c in " ._-")
                        w_file_name = f"workshop_{selected_visit_id}_{safe_w_name}"
                        w_file_path = os.path.join(workshop_dir, w_file_name)
                        with open(w_file_path, "wb") as w_out:
                            w_out.write(uploaded_workshop_file.read())
                        new_workshop_path = w_file_path
                        
                    new_is_sent_prod = 0 # No longer sent directly to production from here
                    
                    conn = db.get_connection()
                    c = conn.cursor()
                    
                    # Update basic client and project details in FieldVisits
                    c.execute('''
                        UPDATE FieldVisits
                        SET customer_name = ?, phone = ?, furniture_type = ?, address = ?
                        WHERE id = ?
                    ''', (c_name_input.strip(), c_phone_input.strip(), c_furniture_input.strip(), c_address_input.strip(), selected_visit_id))
                    
                    c.execute('''
                        INSERT INTO ProjectDesigns (visit_id, designer_name, status, design_link, notes, last_updated, odoo_no, design_docs, is_sent_to_production, workshop_drawing)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(visit_id) DO UPDATE SET
                            designer_name=excluded.designer_name,
                            status=excluded.status,
                            design_link=excluded.design_link,
                            notes=excluded.notes,
                            last_updated=excluded.last_updated,
                            odoo_no=excluded.odoo_no,
                            design_docs=excluded.design_docs,
                            is_sent_to_production=excluded.is_sent_to_production,
                            workshop_drawing=excluded.workshop_drawing
                    ''', (selected_visit_id, designer.strip(), status, design_link.strip(), notes.strip(), now_str, odoo_val.strip(), new_docs_str, new_is_sent_prod, new_workshop_path))
                    
                    # Insert history record
                    days_ar = {0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
                    day_name = days_ar[now.weekday()]
                    time_str = now.strftime("%I:%M %p")
                    date_str = now.strftime("%Y-%m-%d")
                    timestamp_full = f"{day_name} | {date_str} | {time_str}"
                    
                    username = st.session_state.get('username', 'Unknown')
                    employee_name = st.session_state.get('employee_name', 'Unknown')
                    
                    c.execute('''
                        INSERT INTO ProjectDesignHistory (visit_id, designer_name, status, notes, username, employee_name, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (selected_visit_id, designer.strip(), status, notes.strip(), username, employee_name, timestamp_full))
                    
                    conn.commit()
                    conn.close()
                    
                    db.log_activity(
                        username=username,
                        employee_name=employee_name,
                        action_type="أرشفة المواصفات واعتماد التصميم" if submit_approve else "تعديل تصميم",
                        module="مسار التصاميم",
                        details=f"تم اعتماد وأرشفة تصميم العميل MHM{selected_visit_id:05d} لانتظار التعاقد" if submit_approve else f"تم تحديث تصميم العميل MHM{selected_visit_id:05d} إلى: {status}"
                    )
                    if submit_approve:
                        st.success("✅ تم حفظ تصميم المشروع وأرشفة المواصفات الفنية للانتقال لمسار التسعير والتعاقد بنجاح!")
                    else:
                        st.success("✅ تم حفظ بيانات التصميم بنجاح!")
                    time.sleep(2)
                    st.rerun()
                    
                if delete_submit:
                    if st.session_state.get('username') != 'Admin' and st.session_state.get('role') != 'Admin':
                        st.error("🔒 اتصل بمدير النظام للموافقة على تطبيق الاجراء")
                    else:
                        conn = db.get_connection()
                        c = conn.cursor()
                        
                        # Delete files from disk
                        c.execute("SELECT design_docs, workshop_drawing FROM ProjectDesigns WHERE visit_id = ?", (selected_visit_id,))
                        row_docs = c.fetchone()
                        if row_docs:
                            if row_docs[0]:
                                for p in row_docs[0].split(","):
                                    if p and os.path.exists(p):
                                        try:
                                            os.remove(p)
                                        except:
                                            pass
                            if row_docs[1] and os.path.exists(row_docs[1]):
                                try:
                                    os.remove(row_docs[1])
                                except:
                                    pass
                                        
                        c.execute("DELETE FROM ProjectDesigns WHERE visit_id = ?", (selected_visit_id,))
                        c.execute("DELETE FROM ProjectDesignHistory WHERE visit_id = ?", (selected_visit_id,))
                        conn.commit()
                        conn.close()
                        
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="حذف تصميم",
                            module="مسار التصاميم",
                            details=f"تم حذف سجل تصميم العميل MHM{selected_visit_id:05d}"
                        )
                        st.success("🗑️ تم حذف سجل التصميم بنجاح!")
                        st.session_state['selected_design_visit_id'] = None
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("💡 انقر على أي صف في الجدول أعلاه لعرض وتحديث بيانات التصميم الخاصة به.")
 
    with tab2:
        # Filter visits to only approved ones
        active_visits = [v for v in visits if (v[20] if len(v) > 20 else 0) == 0 and (v[21] if len(v) > 21 else 0) == 1]
        if not active_visits:
            st.warning("⚠️ لا توجد مشاريع نشطة حالياً.")
        else:
            customer_options_hist = {f"MHM{v[0]:05d} | {v[1]} ({v[4]})": v[0] for v in active_visits}
            selected_cust_hist = st.selectbox("اختر العميل / المشروع لاستعراض سجل وتاريخ التعديلات:", list(customer_options_hist.keys()), key="hist_select")
            v_id_hist = customer_options_hist[selected_cust_hist]
            
            # Fetch design status and notes
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT designer_name, status, odoo_no FROM ProjectDesigns WHERE visit_id = ?", (v_id_hist,))
            ds_info = c.fetchone()
            
            # Fetch edit count (number of times it went to "قيد التعديل")
            c.execute("SELECT COUNT(*) FROM ProjectDesignHistory WHERE visit_id = ? AND status = 'قيد التعديل'", (v_id_hist,))
            edit_count = c.fetchone()[0]
            
            # Fetch full history
            c.execute("SELECT timestamp, status, designer_name, username, employee_name, notes FROM ProjectDesignHistory WHERE visit_id = ? ORDER BY id DESC", (v_id_hist,))
            history_records = c.fetchall()
            conn.close()
            
            if ds_info:
                st.markdown(f"**المرحلة الحالية للتصميم:** `{ds_info[1]}`")
                st.markdown(f"**اسم المصمم المسؤول:** `{ds_info[0]}`")
                st.markdown(f"**عدد التعديلات التي تمت:** `{edit_count}`")
                
                # Fetch design and measurement files for cumulative display
                conn = db.get_connection()
                c = conn.cursor()
                c.execute("SELECT COALESCE(d.design_docs, ''), COALESCE(f.media_paths, '') FROM FieldVisits f LEFT JOIN ProjectDesigns d ON f.id = d.visit_id WHERE f.id = ?", (v_id_hist,))
                files_row = c.fetchone()
                conn.close()
                if files_row:
                    d_docs_h, media_paths_h = files_row
                    all_h_files = []
                    for p in (media_paths_h or "").split(","):
                        if p and os.path.exists(p):
                            all_h_files.append((p, "📐"))
                    for p in (d_docs_h or "").split(","):
                        if p and os.path.exists(p):
                            all_h_files.append((p, "🎨"))
                    if all_h_files:
                        st.markdown("**📎 ملفات ومستندات المشروع المتوفرة:**")
                        for p, icon in all_h_files:
                            fname = os.path.basename(p)
                            display_name = fname
                            if fname.startswith(f"design_{v_id_hist}_"):
                                display_name = fname[len(f"design_{v_id_hist}_"):]
                            with open(p, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 4px 8px; margin: 2px; background-color: #f8f9fa; color: #212529; text-decoration: none; border-radius: 4px; border: 1px solid #ced4da; font-size: 12px; font-weight: bold;">{icon} {display_name}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                        st.markdown("---")
            else:
                st.info("ℹ️ لم يتم إدخال بيانات تصميم بعد لهذا العميل.")
                
            st.markdown("#### 📜 سجل المراحل والتعديلات التفصيلي")
            if not history_records:
                st.info("📭 لا توجد حركات مسجلة لتاريخ هذا التصميم بعد.")
            else:
                df_hist = pd.DataFrame(
                    history_records,
                    columns=["التوقيت (اليوم | التاريخ | الوقت)", "حالة التصميم", "اسم المصمم", "اسم المستخدم", "اسم الموظف", "ملاحظات التعديل"]
                )
                # Reverse columns for RTL visual order
                df_hist = df_hist[["ملاحظات التعديل", "اسم الموظف", "اسم المستخدم", "اسم المصمم", "حالة التصميم", "التوقيت (اليوم | التاريخ | الوقت)"]]
                st.dataframe(df_hist, use_container_width=True, hide_index=True)

import streamlit as st
# Design module: supports contract printing, termination, and satisfaction surveys
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
        
    st.markdown("<h2 style='text-align: center; color: #0077b6;'>🎨 مسار التصميم</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>إدارة وتتبع تصاميم المشاريع المرتبطة بالعملاء</p><hr>", unsafe_allow_html=True)
    
    # Get all customers/field visits
    visits = db.get_all_field_visits()
    
    tab0, tab1, tab2 = st.tabs(["➕ إضافة مشروع جديد", "📋 سجل المشاريع", "📜 تاريخ تعديلات التصميم"])
    
    with tab0:
        st.markdown("### ➕ إضافة مشروع جديد")
        st.markdown("قم بتعبئة البيانات أدناه لإنشاء مشروع جديد مباشرة في مسار التصميم:")
        
        with st.form("add_new_project_form"):
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                new_customer_name = st.text_input("اسم العميل / المشروع * (مطلوب)")
                new_address = st.text_input("العنوان بالتفصيل")
            with col_add2:
                new_phone = st.text_input("رقم الهاتف * (مطلوب)")
                furniture_options = ["بيت كامل", "مطبخ", "غرفة نوم", "غرفة ملابس", "ديكور شاشة", "مدخل", "جلسة", "صيدلية", "محل تجاري", "مطعم", "مقهى", "مكتب اداري", "ستائر", "استراحة", "منتجات اخرى"]
                new_furniture_sel = st.multiselect("نوع الأثاث المطلوب", furniture_options)
                
            new_furniture_type = "، ".join(new_furniture_sel) if new_furniture_sel else "لم يتم التحديد"
            
            st.markdown("---")
            col_add3, col_add4 = st.columns(2)
            with col_add3:
                new_odoo_val = st.text_input("رقم منظومة أودو (اختياري)")
            with col_add4:
                designer_options = [
                    "اختر المصمم المنفذ...",
                    "م. شهد الطاهر هويدي",
                    "م. عبد الرؤوف محمد عريبي",
                    "اكتب اسم المصمم / ــة"
                ]
                new_selected_opt = st.selectbox("المصمم المنفذ * (إلزامي)", designer_options, key="new_designer_select")
                if new_selected_opt == "اكتب اسم المصمم / ــة":
                    new_designer = st.text_input("اسم المصمم / ــة (كتابة يدوية) *", key="new_designer_manual")
                else:
                    new_designer = new_selected_opt
            
            new_status_options = ["مجدول", "قيد التنفيذ", "بانتظار موافقة العميل", "قيد التعديل", "مكتمل نهائي"]
            new_status = st.selectbox("حالة التصميم", new_status_options, index=0)
            new_design_link = st.text_input("رابط التصميم (Drive / Dropbox)")
            new_notes = st.text_area("ملاحظات التصميم")
            
            submit_add = st.form_submit_button("➕ إضافة المشروع")
            
            if submit_add:
                if not new_customer_name or not new_phone:
                    st.error("⚠️ يرجى إدخال اسم العميل ورقم الهاتف على الأقل.")
                elif new_selected_opt == "اختر المصمم المنفذ...":
                    st.error("⚠️ يرجى اختيار المصمم المنفذ.")
                elif new_selected_opt == "اكتب اسم المصمم / ــة" and not new_designer.strip():
                    st.error("⚠️ يرجى كتابة اسم المصمم.")
                else:
                    now = datetime.datetime.now()
                    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
                    
                    conn = db.get_connection()
                    c = conn.cursor()
                    
                    # Insert into FieldVisits
                    c.execute('''
                        INSERT INTO FieldVisits (
                            customer_name, phone, address, furniture_type, 
                            site_status, visit_date, visit_time, visit_value, 
                            design_value, payment_status, measurement_completed, 
                            document_revision_completed, media_paths, map_link, 
                            site_status_note, is_approved, approved_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_customer_name.strip(), new_phone.strip(), new_address.strip(), new_furniture_type,
                        "جاهز", now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), 0.0,
                        0.0, "تم الدفع", "تمت",
                        "تمت", "", "",
                        "", 1, now_str
                    ))
                    
                    new_visit_id = c.lastrowid
                    
                    # Insert into ProjectDesigns
                    c.execute('''
                        INSERT INTO ProjectDesigns (
                            visit_id, designer_name, status, design_link, notes, 
                            last_updated, odoo_no, design_docs, is_sent_to_production, 
                            workshop_drawing
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        new_visit_id, new_designer.strip(), new_status, new_design_link.strip(), new_notes.strip(),
                        now_str, new_odoo_val.strip(), "", 0, ""
                    ))
                    
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
                    ''', (new_visit_id, new_designer.strip(), new_status, "تم إنشاء المشروع وتعيينه للمرة الأولى".strip(), username, employee_name, timestamp_full))
                    
                    conn.commit()
                    conn.close()
                    
                    db.log_activity(
                        username=username,
                        employee_name=employee_name,
                        action_type="إضافة مشروع جديد",
                        module="مسار التصميم",
                        details=f"تم إضافة مشروع جديد للعميل MHM{new_visit_id:05d}: {new_customer_name}"
                    )
                    
                    st.success(f"🎉 تم إضافة المشروع بنجاح برقم مسارات: MHM{new_visit_id:05d}")
                    time.sleep(2)
                    st.rerun()
                    
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
                   COALESCE(f.approved_at, ''),
                   f.visit_date
            FROM FieldVisits f
            LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
            LEFT JOIN Contracts con ON f.customer_name = con.client_name
            WHERE f.is_approved = 1
            ORDER BY f.id DESC
        ''')
        design_records = c.fetchall()
        conn.close()
        
        # Search Block in Tab 1
        with st.expander("🔍 البحث المتقدم في أرشيف المشاريع", expanded=False):
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                search_name = st.text_input("اسم العميل / المشروع", key="s_name_design")
            with col_s2:
                search_masar = st.text_input("رقم مسارات (مثال: MHM00045)", key="s_masar_design")
            with col_s3:
                search_odoo = st.text_input("رقم أودو", key="s_odoo_design")
            with col_s4:
                search_dates = st.date_input("الفترة الزمنية (من - إلى)", value=(), key="s_dates_design")

        is_search_active = bool(search_name or search_masar or search_odoo or (len(search_dates) == 2))
        
        formatted_records = []
        for row in design_records:
            v_id, c_name, phone, fur_type, designer, status, link, notes, odoo, is_canceled, media_paths, design_docs, approved_at, v_date = row
            
            # Apply filters
            if search_name and search_name.strip().lower() not in c_name.lower():
                continue
            if search_masar:
                clean_m = search_masar.strip().upper()
                if clean_m not in f"MHM{v_id:05d}":
                    continue
            if search_odoo and search_odoo.strip().lower() not in odoo.lower():
                continue
            if len(search_dates) == 2:
                start_d, end_d = search_dates
                try:
                    v_date_parsed = datetime.datetime.strptime(v_date, "%Y-%m-%d").date()
                    if not (start_d <= v_date_parsed <= end_d):
                        continue
                except:
                    continue
                    
            if is_canceled == 1:
                c_name = f"{c_name} ❌ [ملغي/اعتذار]"
                
            # Default status to 'مجدول'
            if not status or status.strip() == "":
                status = "مجدول"
                
            display_approved_date = approved_at
            formatted_records.append((v_id, c_name, status, display_approved_date, notes))
            
        # Limit to 10 if search is not active
        if not is_search_active:
            formatted_records = formatted_records[:10]
            st.info("💡 يعرض الجدول أدناه آخر 10 مشاريع نشطة افتراضياً. للبحث عن مشاريع أقدم، استخدم لوحة البحث المتقدم بالرأس.")
        else:
            st.success(f"🔍 تم العثور على {len(formatted_records)} مشروع مطابق لمعايير البحث.")
            
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
            
            # Fetch project details (for both editors and observers)
            conn = db.get_connection()
            c = conn.cursor()
            c.execute('''
                SELECT d.designer_name, d.status, d.design_link, d.notes, d.odoo_no, 
                       COALESCE(d.design_docs, ''), COALESCE(f.media_paths, ''), 
                       f.customer_name, f.phone, f.furniture_type, f.address, 
                       COALESCE(d.is_sent_to_production, 0), COALESCE(d.workshop_drawing, ''),
                       f.map_link
                FROM FieldVisits f
                LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
                WHERE f.id = ?
            ''', (selected_visit_id,))
            existing_row = c.fetchone()
            
            # Check current number of edits
            c.execute("SELECT COUNT(*) FROM ProjectDesignHistory WHERE visit_id = ? AND status = 'قيد التعديل'", (selected_visit_id,))
            current_edit_count = c.fetchone()[0]
            
            # Fetch all customer projects/visits for history
            c_name = existing_row[7] if existing_row else ""
            c.execute('''
                SELECT f.id, f.visit_date, f.furniture_type, 
                       COALESCE(d.status, 'مجدول'), f.is_canceled, f.is_approved
                FROM FieldVisits f
                LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
                WHERE f.customer_name = ?
                ORDER BY f.id DESC
            ''', (c_name,))
            all_customer_projects = c.fetchall()
            conn.close()
            
            d_name = ""
            d_status = "مجدول"
            d_link = ""
            d_notes = ""
            d_odoo = ""
            d_docs = ""
            media_paths = ""
            c_phone = ""
            c_furniture = ""
            c_address = ""
            is_sent_prod = 0
            d_workshop = ""
            map_link = ""
            
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
                c_phone = existing_row[8]
                c_furniture = existing_row[9]
                c_address = existing_row[10]
                is_sent_prod = existing_row[11] if existing_row[11] is not None else 0
                d_workshop = existing_row[12] if existing_row[12] is not None else ""
                map_link = existing_row[13] if len(existing_row) > 13 and existing_row[13] is not None else ""

            # Expander for Customer Profile Details (Brings Customer Record directly to Design Page!)
            with st.expander(f"👤 ملف وسجل العميل التفصيلي: {c_name} (معلومات التواصل والأرشيف)", expanded=True):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"**📞 رقم الهاتف:** `{c_phone or 'غير محدد'}`")
                    st.markdown(f"**📍 العنوان بالتفصيل:** `{c_address or 'غير محدد'}`")
                    if map_link:
                        st.markdown(f"🗺️ **موقع العميل على الخريطة:** [🗺️ اضغط لفتح الموقع]({map_link})")
                with col_c2:
                    st.markdown(f"**🛋️ نوع الأثاث المطلوب:** `{c_furniture or 'غير محدد'}`")
                    
                    # Show measurement files/drawings if available
                    meas_paths = [p for p in media_paths.split(",") if p]
                    if meas_paths:
                        st.markdown("**📐 مستندات رفع المقاسات المستلمة للعميل:**")
                        for p in meas_paths:
                            if os.path.exists(p):
                                fname = os.path.basename(p)
                                with open(p, "rb") as f_obj:
                                    b64 = base64.b64encode(f_obj.read()).decode()
                                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}" style="display: inline-block; padding: 4px 8px; margin: 2px; background-color: #f1f8e9; color: #33691e; text-decoration: none; border-radius: 4px; border: 1px solid #81c784; font-size: 12px; font-weight: bold;">⬇️ {fname}</a>'
                                    st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.write("ℹ️ لا توجد مستندات مقاسات مرفوعة للعميل.")
                
                # Show all customer projects table
                if len(all_customer_projects) > 1:
                    st.markdown("---")
                    st.markdown("**📋 كافة مشاريع هذا العميل المسجلة في المنظومة:**")
                    proj_rows = []
                    for p_id, p_date, p_furniture, p_status, p_canceled, p_approved in all_customer_projects:
                        p_no = f"MHM{p_id:05d}"
                        
                        if p_canceled == 1:
                            status_str = "❌ ملغي/اعتذار"
                        elif p_approved == 1:
                            status_str = f"🎨 تصميم ({p_status})"
                        else:
                            status_str = "⏳ بانتظار اعتماد المقاسات"
                            
                        highlight = "⭐ (المشروع الحالي)" if p_id == selected_visit_id else ""
                        
                        proj_rows.append({
                            "رقم مسارات": p_no,
                            "التاريخ": p_date or "غير محدد",
                            "الأثاث المطلوب": p_furniture or "غير محدد",
                            "الحالة": status_str,
                            "ملاحظة": highlight
                        })
                    st.dataframe(pd.DataFrame(proj_rows), use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            if is_observer:
                st.warning("🔒 وضع القراءة فقط: لا يمكنك تعديل التصاميم.")
            else:

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
                
                is_admin_user = (st.session_state.get('username') == 'Admin' or st.session_state.get('role') == 'Admin')
                is_read_only_design = (is_sent_prod == 1 and not is_admin_user)
                
                if is_read_only_design:
                    st.warning("🔒 هذا التصميم تم حفظه واعتماده للإنتاج. التعديل متاح فقط لمدير النظام (الأدمن).")
                
                with st.form(f"update_design_form_{selected_visit_id}"):
                    st.markdown("##### 📋 بيانات المشروع والعميل")
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        c_name_input = st.text_input("اسم العميل", value=c_name, key=f"c_name_ds_{selected_visit_id}", disabled=is_read_only_design)
                        
                        # Requirement 2: Multiselect dropdown for requested furniture in edit mode
                        default_selections = []
                        furniture_options = ["بيت كامل", "مطبخ", "غرفة نوم", "غرفة ملابس", "ديكور شاشة", "مدخل", "جلسة", "صيدلية", "محل تجاري", "مطعم", "مقهى", "مكتب اداري", "ستائر", "استراحة", "منتجات اخرى"]
                        if c_furniture:
                            raw_selections = [x.strip() for x in c_furniture.split("،") if x.strip()]
                            if not raw_selections:
                                raw_selections = [x.strip() for x in c_furniture.split(",") if x.strip()]
                            for item in raw_selections:
                                if item in furniture_options:
                                    default_selections.append(item)
                                elif item.startswith("أخرى (") and item.endswith(")"):
                                    if "منتجات اخرى" not in default_selections:
                                        default_selections.append("منتجات اخرى")
                                else:
                                    if "منتجات اخرى" not in default_selections:
                                        default_selections.append("منتجات اخرى")
                        
                        new_furniture_sel = st.multiselect("نوع الأثاث المطلوب:", furniture_options, default=default_selections, key=f"c_fur_sel_{selected_visit_id}", disabled=is_read_only_design)
                        
                        new_other_fur = ""
                        if "منتجات اخرى" in new_furniture_sel:
                            old_custom_val = ""
                            if c_furniture:
                                raw_selections = [x.strip() for x in c_furniture.split("،") if x.strip()]
                                for item in raw_selections:
                                    if item not in furniture_options:
                                        old_custom_val = item
                                    elif item.startswith("أخرى (") and item.endswith(")"):
                                        old_custom_val = item[6:-1]
                            new_other_fur = st.text_input("يرجى تحديد نوع المنتج الآخر:", value=old_custom_val, key=f"c_other_fur_{selected_visit_id}", disabled=is_read_only_design)
                        
                        final_selections = [f"أخرى ({new_other_fur})" if item == "منتجات اخرى" and new_other_fur else item for item in new_furniture_sel]
                        c_furniture_input = "، ".join(final_selections) if final_selections else "لم يتم التحديد"
                        
                    with col_info2:
                        c_phone_input = st.text_input("رقم الهاتف", value=c_phone, key=f"c_phone_ds_{selected_visit_id}", disabled=is_read_only_design)
                        c_address_input = st.text_input("العنوان بالتفصيل", value=c_address, key=f"c_address_ds_{selected_visit_id}", disabled=is_read_only_design)
                    
                    st.markdown("---")
                    
                    col_mhm, col_odoo = st.columns(2)
                    with col_mhm:
                        st.text_input("رقم منظومة مسارات", value=f"MHM{selected_visit_id:05d}", disabled=True)
                    with col_odoo:
                        odoo_val = st.text_input("رقم منظومة أودو المكافئ له", value=d_odoo, disabled=is_read_only_design)
                        
                    designer_options = [
                        "اختر المصمم المنفذ...",
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
                            
                    selected_opt = st.selectbox("المصمم المنفذ * (إلزامي)", designer_options, index=default_sel_idx, disabled=is_read_only_design)
                    if selected_opt == "اكتب اسم المصمم / ــة":
                        designer = st.text_input("اسم المصمم / ــة (كتابة يدوية) *", value=manual_designer_val, disabled=is_read_only_design)
                    else:
                        designer = selected_opt
                    status_options = ["مجدول", "قيد التنفيذ", "بانتظار موافقة العميل", "قيد التعديل", "مكتمل نهائي"]
                    status = st.selectbox("حالة التصميم", status_options, index=status_options.index(d_status) if d_status in status_options else 0, disabled=is_read_only_design)
                    design_link = st.text_input("رابط التصميم (Drive / Dropbox)", value=d_link, disabled=is_read_only_design)
                    
                    uploaded_files = st.file_uploader("📎 تحميل مستندات التصميم (PDF / صور / ملفات)", accept_multiple_files=True, type=["pdf", "png", "jpg", "jpeg", "docx", "zip", "rar"], disabled=is_read_only_design)
                    
                    # Display current workshop drawing if it exists
                    if d_workshop and os.path.exists(d_workshop):
                        st.markdown("**🏭 الرسم الفني الحالي للمصنع (Workshop Drawing):**")
                        w_name = os.path.basename(d_workshop)
                        with open(d_workshop, "rb") as w_file:
                            w_b64 = base64.b64encode(w_file.read()).decode()
                        w_href = f'<a href="data:application/pdf;base64,{w_b64}" download="{w_name}" style="display: inline-block; padding: 5px 10px; margin: 2px 2px 8px 2px; background-color: #ffebee; color: #c62828; text-decoration: none; border-radius: 4px; border: 1px solid #ef9a9a; font-size: 13px; font-weight: bold;">⬇️ {w_name}</a>'
                        st.markdown(w_href, unsafe_allow_html=True)
                    
                    uploaded_workshop_file = st.file_uploader("🏭 تحميل الرسم الفني للمصنع (Workshop Drawing) - صيغة PDF فقط:", type=["pdf"], key=f"workshop_drawing_{selected_visit_id}", disabled=is_read_only_design)
                    
                    notes = st.text_area("ملاحظات التصميم والتعديلات", value=d_notes, disabled=is_read_only_design)
                    
                    approved_by_manager = False
                    if current_edit_count >= 2:
                        st.warning(f"⚠️ هذا التصميم تم تعديله مسبقاً ({current_edit_count}) مرات. لا يسمح بإجراء تعديل إضافي إلا بعد اعتماد مدير الصالة كحالة استثنائية.")
                        approved_by_manager = st.checkbox("✅ تم اعتماد هذا التعديل الاستثنائي من قبل مدير الصالة", disabled=is_read_only_design)
                    
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
                    if designer == "اختر المصمم المنفذ..." or designer == "اكتب اسم المصمم / ــة" or designer.strip() == "" or designer.strip() == "غير معين":
                        st.error("⚠️ يرجى اختيار اسم المصمم المنفذ أو كتابته يدوياً!")
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
                        
                    new_is_sent_prod = 1 if submit_approve else is_sent_prod
                    
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
                        action_type="اعتماد تصميم للإنتاج" if submit_approve else "تعديل تصميم",
                        module="مسار التصميم",
                        details=f"تم اعتماد وتصدير تصميم العميل MHM{selected_visit_id:05d} للإنتاج" if submit_approve else f"تم تحديث تصميم العميل MHM{selected_visit_id:05d} إلى: {status}"
                    )
                    if submit_approve:
                        st.success("✅ تم حفظ تصميم المشروع واعتماده ونقله لمسار الإنتاج بنجاح!")
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
                            module="مسار التصميم",
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
            # Search Block in Tab 2
            with st.expander("🔍 البحث المتقدم في تاريخ التعديلات", expanded=False):
                col_s1_h, col_s2_h, col_s3_h, col_s4_h = st.columns(4)
                with col_s1_h:
                    search_name_h = st.text_input("اسم العميل / المشروع", key="s_name_hist")
                with col_s2_h:
                    search_masar_h = st.text_input("رقم مسارات (مثال: MHM00045)", key="s_masar_hist")
                with col_s3_h:
                    search_odoo_h = st.text_input("رقم أودو", key="s_odoo_hist")
                with col_s4_h:
                    search_dates_h = st.date_input("الفترة الزمنية (من - إلى)", value=(), key="s_dates_hist")
            
            # Fetch Odoo mapping
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT visit_id, odoo_no FROM ProjectDesigns")
            designs_odoo = {row[0]: row[1].strip() for row in c.fetchall() if row[1] and row[1].strip()}
            c.execute("SELECT client_name, odoo_no, notes FROM Contracts")
            contracts_odoo = c.fetchall()
            conn.close()
            
            def get_visit_odoo(v_id, client_n):
                if v_id in designs_odoo:
                    return designs_odoo[v_id]
                for client_name, odoo_no, notes in contracts_odoo:
                    if odoo_no and odoo_no.strip():
                        if client_name == client_n:
                            return odoo_no.strip()
                        if notes and f"MHM{v_id:05d}" in notes:
                            return odoo_no.strip()
                return ""
            
            is_search_active_h = bool(search_name_h or search_masar_h or search_odoo_h or (len(search_dates_h) == 2))
            
            filtered_visits_h = []
            for v in active_visits:
                v_id = v[0]
                v_name = v[1]
                v_date = v[6]
                v_odoo = get_visit_odoo(v_id, v_name)
                
                # Apply filters
                if search_name_h and search_name_h.strip().lower() not in v_name.lower():
                    continue
                if search_masar_h:
                    clean_m = search_masar_h.strip().upper()
                    if clean_m not in f"MHM{v_id:05d}":
                        continue
                if search_odoo_h and search_odoo_h.strip().lower() not in v_odoo.lower():
                    continue
                if len(search_dates_h) == 2:
                    start_d, end_d = search_dates_h
                    try:
                        v_date_parsed = datetime.datetime.strptime(v_date, "%Y-%m-%d").date()
                        if not (start_d <= v_date_parsed <= end_d):
                            continue
                    except:
                        continue
                
                filtered_visits_h.append(v)
                
            # Limit to 10 if search is not active
            if not is_search_active_h:
                filtered_visits_h = filtered_visits_h[:10]
                st.info("💡 تعرض القائمة أدناه آخر 10 مشاريع نشطة افتراضياً. للبحث عن مشاريع أقدم، استخدم لوحة البحث المتقدم بالرأس.")
            else:
                st.success(f"🔍 تم العثور على {len(filtered_visits_h)} مشروع مطابق لمعايير البحث.")
                
            if not filtered_visits_h:
                st.warning("⚠️ لا توجد مشاريع مطابقة لمعايير البحث.")
            else:
                customer_options_hist = {f"MHM{v[0]:05d} | {v[1]} ({v[4]})": v[0] for v in filtered_visits_h}
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
                st.markdown(f"<p style='font-size: 19px; font-family: \"Readex Pro\", sans-serif; margin: 8px 0;'><b>حالة التصميم:</b> <span style='color: #2b9348; font-weight: bold;'>{ds_info[1]}</span></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 19px; font-family: \"Readex Pro\", sans-serif; margin: 8px 0;'><b>اسم المصمم المنفذ:</b> <span style='color: #0077b6; font-weight: bold;'>{ds_info[0]}</span></p>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 19px; font-family: \"Readex Pro\", sans-serif; margin: 8px 0;'><b>عدد التعديلات التي تمت:</b> <span style='color: #d90429; font-weight: bold;'>{edit_count}</span></p>", unsafe_allow_html=True)
                
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

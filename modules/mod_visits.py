import streamlit as st
import time
import database as db

def render_page(can_access_visits, is_observer):
    st.markdown("""
        <style>
            [data-testid='stFileUploader'] section > button {
                font-size: 0 !important;
            }
            [data-testid='stFileUploader'] section > button::after {
                content: 'استعراض';
                font-size: 14px;
                display: block;
                visibility: visible;
            }
        </style>
    """, unsafe_allow_html=True)
    if not can_access_visits:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("""
        <style>
            .force-center, .force-center * {
                text-align: center !important;
            }
            .header-box {
                display: inline-block !important;
                border: 2px solid #0d8a95 !important;
                border-radius: 12px !important;
                padding: 8px 24px !important;
                background-color: #f4fbfb !important;
            }
        </style>
    """, unsafe_allow_html=True)
    st.markdown("<div class='force-center'><h2 style='color: #0d47a1; font-family: \"Readex Pro\", sans-serif; font-weight: 700; font-size: 34px; margin-bottom: 5px;'>سجل رفع المقاسات والمعاينة الميدانية</h2></div>", unsafe_allow_html=True)
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0d8a95; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 15px; margin-bottom: 20px; font-size: 28px;'>مسار التسجيل</h3></div>", unsafe_allow_html=True)
    
    st.markdown("<h3 style='background-color: #e0e0e0; padding: 10px; border-radius: 5px; text-align: center;'>ادخال بيانات العميل</h3>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        customer_name = st.text_input("1. أسم العميل/ المشروع")
        address = st.text_input("3. عنوان العميل")
        map_link = st.text_input("رابط موقع العميل على خرائط جوجل (اختياري)", placeholder="الصق الرابط هنا...")
        site_status = st.radio("5. حالة الموقع", ["جاهز", "تحت التشطيب"], horizontal=True)
        site_status_note = ""
        if site_status == "تحت التشطيب":
            site_status_note = st.text_area("ملاحظات عن حالة الموقع:", placeholder="اكتب ملاحظات توضيحية عن وضع الموقع...")
    with col2:
        phone = st.text_input("2. رقم هاتف العميل")
        furniture_options = ["بيت كامل", "مطبخ", "غرفة نوم", "غرفة ملابس", "ديكور شاشة", "مدخل", "جلسة", "صيدلية", "محل تجاري", "مطعم", "مقهى", "مكتب اداري", "منتجات اخرى"]
        selected_furniture = st.multiselect("4. نوع الأثاث المطلوب", furniture_options)
        if "منتجات اخرى" in selected_furniture:
            other_furniture = st.text_input("يرجى تحديد نوع المنتج:")
            final_selections = [f"أخرى ({other_furniture})" if item == "منتجات اخرى" and other_furniture else item for item in selected_furniture]
        else:
            final_selections = selected_furniture
            
        furniture_type = "، ".join(final_selections) if final_selections else "لم يتم التحديد"
        
        next_visit_id = db.get_next_visit_id()
        col_mhm, col_odoo = st.columns(2)
        with col_mhm:
            st.text_input("6. رقم مسارات", value=f"MHM{next_visit_id:05d}", disabled=True)
        with col_odoo:
            st.text_input("7. رقم أودو", value="لم يتم الاتفاق مع العميل بعد", disabled=True)

    st.markdown("<div style='background-color: #3b5323; color: white; padding: 15px; border-radius: 5px; text-align: center; margin: 20px 0px; font-weight: bold;'>ملاحظة: يتم التواصل مع العميل بخصوص موعد الزيارة الميدانية قبل الموعد بـ 24 ساعة لتأكيد الحجز او تغييره ان تطلب الأمر</div>", unsafe_allow_html=True)

    st.markdown("<h3 style='background-color: #e0e0e0; padding: 10px; border-radius: 5px; text-align: center;'>موعد رفع المقاسات</h3>", unsafe_allow_html=True)
    col_d, col_t = st.columns(2)
    with col_d:
        visit_date = st.date_input("التاريخ")
        # Format day in Arabic
        days_ar = {0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"}
        st.info(f"اليوم: {days_ar[visit_date.weekday()]}")
    with col_t:
        time_options = []
        for h in range(8, 22):
            for m in ["00", "30"]:
                period = "صباحاً" if h < 12 else "مساءً"
                h12 = h if h <= 12 else h - 12
                if h12 == 0: h12 = 12
                time_options.append(f"{h12:02d}:{m} {period}")
        visit_time = st.selectbox("الساعة", time_options)

    st.markdown("<h3 style='background-color: #e0e0e0; padding: 10px; border-radius: 5px; text-align: center;'>القيم المالية<br><span style='font-size: 16px; font-weight: normal;'>(تعتمد على موقع العميل ويتم خصمها لاحقاً من قيمة المشروع اذا انجز العميل المشروع مع الشركة)</span></h3>", unsafe_allow_html=True)
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        visit_value = st.number_input("قيمة رفع المقاسات (دينار ليبي)", min_value=0.0, step=25.0, value=50.0)
    with col_v2:
        design_value = st.number_input("قيمة التصميم (دينار ليبي)", min_value=0.0, step=50.0, value=150.0)
    
    payment_status = st.radio("حالة الدفع", ["تم الدفع", "لم يتم بعد"], horizontal=True)
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0d8a95; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 25px; margin-bottom: 20px; font-size: 28px;'>مسار الزيارة الميدانية</h3></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='background-color: #e0e0e0; padding: 10px; border-radius: 5px; text-align: center;'>حالة رفع المقاسات</h3>", unsafe_allow_html=True)
    measurement_completed = st.radio("هل تمت عملية رفع المقاسات بنجاح؟", ["نعم", "لا"], horizontal=True)
    
    measurement_reason = ""
    if measurement_completed == "لا":
        measurement_reason = st.text_area("سبب عدم اتمام عملية رفع المقاسات:", placeholder="اكتب السبب هنا...")

    document_revision_completed = ""
    document_revision_reason = ""
    st.markdown("<div style='color: #d62828; font-weight: bold; margin-bottom: 5px;'>ملاحظة: يجب أن تكون الملفات والمستندات المرفوعة بصيغة PDF حصراً.</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("رفع المستندات والصور والفيديوهات الخاصة بالمشروع", accept_multiple_files=True, type=["pdf"])

    st.markdown("---")
    if is_observer:
        st.info("وضع القراءة فقط: لا يمكنك إضافة سجلات.")
    else:
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            save_btn = st.button("💾 حفظ السجل", use_container_width=True)
        with col_save2:
            save_approve_btn = st.button("💾 حفظ واعتماد السجل", use_container_width=True)
            
        if save_btn or save_approve_btn:
            try:
                if customer_name and phone:
                    import os
                    saved_paths = []
                    if uploaded_files:
                        upload_dir = "dimdata"
                        os.makedirs(upload_dir, exist_ok=True)
                        for f in uploaded_files:
                            # Clean filename
                            safe_name = "".join(c for c in f.name if c.isalnum() or c in " ._-")
                            file_path = os.path.join(upload_dir, safe_name)
                            with open(file_path, "wb") as file_out:
                                file_out.write(f.read())
                            saved_paths.append(file_path)
                    
                    media_paths_str = ",".join(saved_paths)
                    import importlib
                    importlib.reload(db)
                    db.save_field_visit(customer_name, phone, address, furniture_type, site_status, str(visit_date), str(visit_time), visit_value, payment_status, measurement_completed, measurement_reason, document_revision_completed, document_revision_reason, media_paths_str, design_value, map_link, site_status_note)
                    
                    if save_approve_btn:
                        import datetime
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        conn = db.get_connection()
                        c = conn.cursor()
                        c.execute("UPDATE FieldVisits SET is_approved = 1, approved_at = ? WHERE id = (SELECT MAX(id) FROM FieldVisits)", (now_str,))
                        conn.commit()
                        conn.close()
                        
                    db.log_activity(
                        username=st.session_state.get('username', 'Unknown'),
                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                        action_type="إضافة ومعاينة" if save_approve_btn else "إضافة",
                        module="مسار رفع المقاسات",
                        details=f"تم إضافة سجل زيارة ميدانية للعميل مع الاعتماد للتصميم: {customer_name}" if save_approve_btn else f"تم إضافة سجل زيارة ميدانية للعميل: {customer_name}"
                    )
                    if save_approve_btn:
                        st.success("تم حفظ السجل واعتماده ونقله لمسار التصاميم بنجاح!")
                    else:
                        st.success("تم حفظ السجل بنجاح مع المرفقات!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("يرجى إدخال اسم العميل ورقم الهاتف على الأقل.")
            except Exception as e:
                st.error(f"حدث خطأ أثناء حفظ البيانات: {e}")

    # --- استعراض سجل العملاء ---
    st.markdown("---")
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0d8a95; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 30px; margin-bottom: 20px; font-size: 28px;'>استعراض سجل العملاء</h3></div>", unsafe_allow_html=True)
    
    saved_visits = db.get_all_field_visits()
    if not saved_visits:
        st.info("لا توجد سجلات محفوظة حتى الآن.")
    else:
        for v in saved_visits:
            v_id = v[0]
            c_name = v[1]
            phone = v[2]
            address = v[3]
            f_type = v[4]
            s_status = v[5]
            v_date = v[6]
            v_time = v[7]
            v_val = v[8]
            p_status = v[9]
            d_val = v[23] if len(v) > 23 else 0.0
            m_link = v[24] if len(v) > 24 else ""
            s_note = v[25] if len(v) > 25 else ""
            m_comp = v[12] if len(v) > 12 else "غير محدد"
            m_rsn = v[13] if len(v) > 13 else ""
            d_comp = v[14] if len(v) > 14 else "غير محدد"
            d_rsn = v[15] if len(v) > 15 else ""
            media = v[16] if len(v) > 16 else ""
            
            last_mod_by = v[17] if len(v) > 17 else ""
            last_mod_at = v[18] if len(v) > 18 else ""
            contact_reason = v[19] if len(v) > 19 else ""
            
            is_canceled = v[20] if len(v) > 20 else 0
            
            # Label color and status icon
            is_approved = v[21] if len(v) > 21 else 0
            status_tag = ""
            if is_canceled == 1:
                status_tag = "❌ [ملغي/اعتذار]"
            elif is_approved == 1:
                status_tag = "✅ [معتمد للتصاميم]"
            else:
                status_tag = "⏳ [بانتظار الاعتماد]"
            
            with st.expander(f"📁 [{f'MHM{v_id:05d}'}] {status_tag} العميل: {c_name} | التاريخ: {v_date}"):
                edit_key = f"edit_{v_id}"
                is_editing = st.session_state.get(edit_key, False)
                
                if is_editing:
                    st.markdown("#### وضع التعديل")
                    col_mhm_edit, col_odoo_edit = st.columns(2)
                    with col_mhm_edit:
                        st.text_input("رقم مسارات:", value=f"MHM{v_id:05d}", disabled=True, key=f"ref_num_{v_id}")
                    with col_odoo_edit:
                        conn = db.get_connection()
                        c = conn.cursor()
                        c.execute("SELECT odoo_no FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
                        row = c.fetchone()
                        odoo_val = row[0].strip() if (row and row[0] and row[0].strip()) else ""
                        if not odoo_val:
                            c.execute("SELECT odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (c_name, f"%MHM{v_id:05d}%"))
                            row = c.fetchone()
                            odoo_val = row[0].strip() if (row and row[0] and row[0].strip()) else "لم يتم الاتفاق مع العميل بعد"
                        conn.close()
                        st.text_input("رقم أودو:", value=odoo_val, disabled=True, key=f"odoo_num_{v_id}")
                    new_cname = st.text_input("اسم العميل:", value=c_name, key=f"cname_{v_id}")
                    new_phone = st.text_input("رقم هاتف العميل:", value=phone, key=f"phone_{v_id}")
                    new_address = st.text_area("العنوان بالتفصيل:", value=address, key=f"address_{v_id}")
                    new_map_link = st.text_input("رابط موقع العميل على خرائط جوجل (اختياري)", value=m_link, key=f"mlink_{v_id}")
                    new_furniture = st.text_input("نوع الأثاث المطلوب:", value=f_type, key=f"fur_{v_id}")
                    new_site_status = st.selectbox("حالة الموقع:", ["جاهز", "تحت التشطيب"], index=0 if s_status=="جاهز" else 1, key=f"site_{v_id}")
                    new_site_status_note = s_note
                    if new_site_status == "تحت التشطيب":
                        new_site_status_note = st.text_area("ملاحظات عن حالة الموقع:", value=s_note, key=f"snote_{v_id}")
                    else:
                        new_site_status_note = ""
                    import datetime
                    try:
                        existing_date = datetime.datetime.strptime(v_date, "%Y-%m-%d").date()
                    except:
                        existing_date = datetime.date.today()
                    new_visit_date = st.date_input("تاريخ الزيارة:", value=existing_date, key=f"vdate_{v_id}")
                    
                    time_options = []
                    for h in range(8, 22):
                        for m in ["00", "30"]:
                            period = "صباحاً" if h < 12 else "مساءً"
                            h12 = h if h <= 12 else h - 12
                            if h12 == 0: h12 = 12
                            time_options.append(f"{h12:02d}:{m} {period}")
                    time_idx = time_options.index(v_time) if v_time in time_options else 0
                    new_visit_time = st.selectbox("وقت الزيارة:", time_options, index=time_idx, key=f"vtime_{v_id}")
                    
                    col_edit_val1, col_edit_val2 = st.columns(2)
                    with col_edit_val1:
                        new_visit_value = st.number_input("قيمة رفع المقاسات (دينار ليبي):", value=float(v_val) if v_val else 0.0, step=25.0, key=f"vval_{v_id}")
                    with col_edit_val2:
                        new_design_value = st.number_input("قيمة التصميم (دينار ليبي):", value=float(d_val) if d_val else 0.0, step=50.0, key=f"dval_{v_id}")
                    
                    new_payment_status = st.radio("حالة الدفع:", ["تم الدفع", "لم يتم بعد"], index=0 if p_status in ["تم الدفع في الصالة", "تم الدفع"] else 1, key=f"pstat_{v_id}")
                    new_m_comp = st.radio("حالة رفع المقاسات:", ["نعم", "لا"], index=0 if m_comp=="نعم" else 1, key=f"mcomp_{v_id}")
                    new_m_rsn = st.text_area("سبب عدم اتمام عملية رفع المقاسات:", value=m_rsn, key=f"mrsn_{v_id}")
                    new_d_comp = ""
                    new_d_rsn = ""
                    st.markdown("**إضافة ملفات جديدة (ستضاف للملفات السابقة):**")
                    new_files = st.file_uploader("إضافة ملفات:", accept_multiple_files=True, type=["pdf"], key=f"files_{v_id}")
                    
                    col_s, col_c = st.columns(2)
                    with col_s:
                        if st.button("💾 حفظ التعديلات", use_container_width=True, key=f"save_edit_{v_id}"):
                            import os
                            import datetime
                            saved_paths = []
                            if media:
                                saved_paths = media.split(",")
                            if new_files:
                                upload_dir = "dimdata"
                                os.makedirs(upload_dir, exist_ok=True)
                                for f in new_files:
                                    safe_name = "".join(c for c in f.name if c.isalnum() or c in " ._-")
                                    file_path = os.path.join(upload_dir, safe_name)
                                    with open(file_path, "wb") as file_out:
                                        file_out.write(f.read())
                                    if file_path not in saved_paths:
                                        saved_paths.append(file_path)
                            
                            new_media_str = ",".join(saved_paths)
                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
                            
                            new_modifier = st.session_state.get('username', 'Unknown')
                            
                            # Preserve is_canceled on update
                            import importlib
                            importlib.reload(db)
                            db.update_field_visit(v_id, new_cname, new_phone, new_address, new_furniture, new_site_status, new_visit_date, new_visit_time, new_visit_value, new_payment_status, new_m_comp, new_m_rsn, new_d_comp, new_d_rsn, new_media_str, new_modifier, now_str, new_design_value, new_map_link, new_site_status_note)
                            
                            db.log_activity(
                                username=st.session_state.get('username', 'Unknown'),
                                employee_name=st.session_state.get('employee_name', 'Unknown'),
                                action_type="تعديل",
                                module="مسار رفع المقاسات",
                                details=f"تم تعديل بيانات سجل العميل: {new_cname}"
                            )
                            st.session_state[edit_key] = False
                            st.rerun()
                    with col_c:
                        if st.button("❌ إلغاء", use_container_width=True, key=f"cancel_edit_{v_id}"):
                            st.session_state[edit_key] = False
                            st.rerun()
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        # Fetch Odoo number
                        conn = db.get_connection()
                        c = conn.cursor()
                        c.execute("SELECT odoo_no FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
                        row = c.fetchone()
                        odoo_val = row[0].strip() if (row and row[0] and row[0].strip()) else ""
                        if not odoo_val:
                            c.execute("SELECT odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (c_name, f"%MHM{v_id:05d}%"))
                            row = c.fetchone()
                            odoo_val = row[0].strip() if (row and row[0] and row[0].strip()) else "لم يتم الاتفاق مع العميل بعد"
                        conn.close()
                        
                        st.markdown(f"**رقم مسارات:** MHM{v_id:05d}")
                        st.markdown(f"**رقم أودو:** {odoo_val}")
                        st.markdown(f"**الهاتف:** {phone}")
                        st.markdown(f"**العنوان:** {address}")
                        if m_link:
                            st.markdown(f"**خرائط جوجل:** [📍 عرض الموقع على الخريطة]({m_link})")
                        st.markdown(f"**نوع الأثاث:** {f_type}")
                    with c2:
                        st.markdown(f"**حالة الموقع:** {s_status}")
                        if s_note:
                            st.markdown(f"**ملاحظات حالة الموقع:** {s_note}")
                        st.markdown(f"**الوقت:** {v_time}")
                        st.markdown(f"**قيمة المقاسات:** {v_val} دينار ({p_status})")
                        st.markdown(f"**قيمة التصميم:** {d_val} دينار")
                    
                    st.markdown("---")
                    st.markdown(f"**حالة رفع المقاسات:** {m_comp}")
                    if m_comp == 'لا':
                        st.warning(f"📝 **ملاحظة/السبب:** {m_rsn if m_rsn else 'لم يتم إدخال سبب'}")
                        
                    
                    if contact_reason:
                        st.error(f"📞 **سبب عدم التواصل (من الإشعارات):** {contact_reason}")
                        
                    if media:
                        st.markdown("**الملفات المرفقة بالمشروع:**")
                        import os
                        import base64
                        paths = media.split(",")
                        for p in paths:
                            if os.path.exists(p):
                                file_name = os.path.basename(p)
                                with open(p, "rb") as file:
                                    b64 = base64.b64encode(file.read()).decode()
                                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}" style="display: inline-block; padding: 0.5em 1em; margin-bottom: 5px; background-color: #f9f9f9; color: #000; text-decoration: none; border-radius: 5px; border: 1px solid #ccc; font-size: 14px;">📄 تحميل {file_name}</a><br>'
                                    st.markdown(href, unsafe_allow_html=True)
                    
                    if last_mod_by:
                        st.markdown(f"<small style='color: gray;'>آخر تعديل بواسطة: {last_mod_by} في {last_mod_at}</small>", unsafe_allow_html=True)
                    
                    is_admin_user = (st.session_state.get('username') == 'Admin' or st.session_state.get('role') == 'Admin')
                    
                    if not is_observer:
                        ecol1, ecol2, ecol3 = st.columns(3)
                        with ecol1:
                            if st.button("✏️ تعديل سجل المشروع", use_container_width=True, key=f"btn_edit_{v_id}"):
                                st.session_state[edit_key] = True
                                st.rerun()
                        with ecol2:
                            if is_canceled == 0:
                                if st.button("❌ إلغاء/اعتذار العميل", use_container_width=True, key=f"btn_cancel_proj_{v_id}"):
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE FieldVisits SET is_canceled = 1 WHERE id = ?", (v_id,))
                                    conn.commit()
                                    conn.close()
                                    db.log_activity(
                                        username=st.session_state.get('username', 'Unknown'),
                                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                                        action_type="إلغاء مشروع",
                                        module="مسار رفع المقاسات",
                                        details=f"تم وضع مشروع العميل MHM{v_id:05d} في حالة اعتذار/إلغاء"
                                    )
                                    st.success("تم إلغاء المشروع.")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                if st.button("🔄 استعادة تفعيل المشروع", use_container_width=True, key=f"btn_activate_proj_{v_id}"):
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    c.execute("UPDATE FieldVisits SET is_canceled = 0 WHERE id = ?", (v_id,))
                                    conn.commit()
                                    conn.close()
                                    db.log_activity(
                                        username=st.session_state.get('username', 'Unknown'),
                                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                                        action_type="تفعيل مشروع",
                                        module="مسار رفع المقاسات",
                                        details=f"تمت إعادة تفعيل مشروع العميل MHM{v_id:05d}"
                                    )
                                    st.success("تمت إعادة تفعيل المشروع.")
                                    time.sleep(1)
                                    st.rerun()
                        with ecol3:
                            if st.session_state.get('username') == 'Admin' or st.session_state.get('role') == 'Admin':
                                if st.button("🗑️ حذف سجل المشروع", type="secondary", use_container_width=True, key=f"btn_delete_proj_{v_id}", help="خاص بمدير النظام فقط"):
                                    import os
                                    conn = db.get_connection()
                                    c = conn.cursor()
                                    
                                    # Clean up files from disk
                                    c.execute("SELECT design_docs FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
                                    row_docs = c.fetchone()
                                    if row_docs and row_docs[0]:
                                        for p in row_docs[0].split(","):
                                            if p and os.path.exists(p):
                                                try:
                                                    os.remove(p)
                                                except:
                                                    pass
                                                    
                                    c.execute("SELECT media_paths FROM FieldVisits WHERE id = ?", (v_id,))
                                    row_media = c.fetchone()
                                    if row_media and row_media[0]:
                                        for p in row_media[0].split(","):
                                            if p and os.path.exists(p):
                                                try:
                                                    os.remove(p)
                                                except:
                                                    pass
                                    
                                    c.execute("DELETE FROM FieldVisits WHERE id = ?", (v_id,))
                                    c.execute("DELETE FROM ProjectDesigns WHERE visit_id = ?", (v_id,))
                                    c.execute("DELETE FROM ProjectDesignHistory WHERE visit_id = ?", (v_id,))
                                    c.execute("DELETE FROM ProjectProduction WHERE visit_id = ?", (v_id,))
                                    c.execute("DELETE FROM Tickets WHERE customer_id = ?", (v_id,))
                                    conn.commit()
                                    conn.close()
                                    
                                    db.log_activity(
                                        username=st.session_state.get('username', 'Unknown'),
                                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                                        action_type="حذف مشروع",
                                        module="مسار رفع المقاسات",
                                        details=f"تم حذف سجل العميل والمشروع MHM{v_id:05d} بالكامل من المنظومة"
                                    )
                                    st.success("🗑️ تم حذف سجل المشروع وكافة ملحقاته بنجاح!")
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.button("🗑️ حذف السجل (خاص بالمدير)", type="secondary", disabled=True, use_container_width=True, key=f"btn_delete_proj_disabled_{v_id}")

                    if is_approved == 0 and is_canceled == 0:
                        st.markdown("---")
                        if st.button("✅ اعتماد وإرسال لمسار التصاميم", use_container_width=True, key=f"btn_approve_{v_id}"):
                            import datetime
                            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            conn = db.get_connection()
                            c = conn.cursor()
                            c.execute("UPDATE FieldVisits SET is_approved = 1, approved_at = ? WHERE id = ?", (now_str, v_id))
                            conn.commit()
                            conn.close()
                            db.log_activity(
                                username=st.session_state.get('username', 'Unknown'),
                                employee_name=st.session_state.get('employee_name', 'Unknown'),
                                action_type="اعتماد مشروع",
                                module="مسار رفع المقاسات",
                                details=f"تم اعتماد مشروع العميل MHM{v_id:05d} ونقله لمسار التصاميم"
                            )
                            st.success("تم اعتماد المشروع وإرساله لمسار التصاميم بنجاح!")
                            time.sleep(1)
                            st.rerun()

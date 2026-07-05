import streamlit as st
import database as db
import os
import base64
import time

def render_page(can_access_finance, is_observer):
    if not can_access_finance:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("""
        <style>
            .force-center, .force-center * {
                text-align: center !important;
            }
            .header-box {
                display: inline-block !important;
                border: 2px solid #0077b6 !important;
                border-radius: 12px !important;
                padding: 8px 24px !important;
                background-color: #e0fbfc !important;
            }
            .payment-card {
                background: linear-gradient(135deg, #f0fdfa 0%, #ccfbf1 100%);
                border: 1px solid #99f6e4;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
                margin-bottom: 15px;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='force-center'><h2 style='color: #03045e; font-family: \"Readex Pro\", sans-serif; font-weight: 700; font-size: 34px; margin-bottom: 5px;'>💰 مسار الخزينة والإدارة المالية</h2></div>", unsafe_allow_html=True)
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 15px; margin-bottom: 20px; font-size: 28px;'>مسار الخزينة</h3></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⏳ الدفعة الأولى (بانتظار التأكيد)", "⏳ الدفعة الثانية والأخيرة", "✅ أرشيف الدفعات المستلمة"])
    
    # ---------------------------------------------------------
    # TAB 1: PENDING DEPOSITS
    # ---------------------------------------------------------
    with tab1:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT f.id, f.customer_name, f.phone, f.address, f.furniture_type,
                   d.price_final, d.workshop_drawing, d.design_link, d.design_docs, d.odoo_no
            FROM FieldVisits f
            INNER JOIN ProjectDesigns d ON f.id = d.visit_id
            WHERE f.is_canceled = 0 AND d.contract_is_approved = 1 AND d.price_is_paid = 0
            ORDER BY f.id DESC
        ''')
        pending_payments = c.fetchall()
        conn.close()
        
        if not pending_payments:
            st.info("ℹ️ لا توجد دفعات أولى معلقة بانتظار التأكيد حالياً.")
        else:
            st.markdown("<p style='text-align: center; color: gray;'>المشاريع المدرجة أدناه تم اعتماد تسعيرتها وبانتظار تأكيد استلام الدفعة الأولى وإدخال رقم أودو</p>", unsafe_allow_html=True)
            for row in pending_payments:
                v_id, c_name, phone, address, f_type, price_final, workshop_drawing, design_link, design_docs, existing_odoo = row
                mhm_code = f"MHM{v_id:05d}"
                
                with st.expander(f"📁 [{mhm_code}] العميل: {c_name} | القيمة المعتمدة: {price_final:,.2f} د.ل"):
                    st.markdown(f"**👤 اسم العميل:** {c_name} | **📞 الهاتف:** {phone or '—'}")
                    st.markdown(f"**📍 العنوان:** {address or '—'} | **🪑 نوع الأثاث:** {f_type or '—'}")
                    st.markdown(f"**💰 السعر النهائي المعتمد للمشروع:** <span style='font-size: 18px; color: #166534; font-weight: bold;'>{price_final:,.2f} دينار ليبي</span>", unsafe_allow_html=True)
                    
                    st.markdown("---")
                    
                    c_files1, c_files2 = st.columns(2)
                    with c_files1:
                        st.markdown("**🎨 المستندات والتصاميم المبدئية:**")
                        if design_link:
                            st.markdown(f"[🔗 رابط التصميم (Drive/Dropbox)]({design_link})")
                        if design_docs:
                            paths = design_docs.split(",")
                            for p in paths:
                                if os.path.exists(p):
                                    fname = os.path.basename(p)
                                    with open(p, "rb") as f_obj:
                                        b64 = base64.b64encode(f_obj.read()).decode()
                                    st.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="{fname}">📥 تحميل تصميم: {fname}</a>', unsafe_allow_html=True)
                        else:
                            st.info("لا توجد مستندات تصميم مرفقة.")
                            
                    with c_files2:
                        st.markdown("**🏭 الرسم الفني للمصنع (Workshop Drawing):**")
                        if workshop_drawing and os.path.exists(workshop_drawing):
                            fname = os.path.basename(workshop_drawing)
                            with open(workshop_drawing, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{fname}" style="display: inline-block; padding: 5px 10px; background-color: #ffebee; color: #c62828; text-decoration: none; border-radius: 4px; border: 1px solid #ef9a9a; font-size: 13px; font-weight: bold;">📥 تحميل الرسم الفني (Workshop Drawing)</a>', unsafe_allow_html=True)
                        else:
                            st.warning("⚠️ لم يتم إرفاق الرسم الفني للمصنع بعد.")
                    
                    st.markdown("---")
                    
                    if is_observer:
                        st.warning("🔒 وضع القراءة فقط: لا يمكنك تأكيد استلام الدفعة.")
                    else:
                        st.markdown("##### ⚙️ تأكيد المعاملة المالية وإدخال رقم أودو:")
                        col_mhm, col_odoo = st.columns(2)
                        with col_mhm:
                            st.text_input("رقم منظومة مسارات (للعرض فقط):", value=mhm_code, disabled=True, key=f"mhm_fin_{v_id}")
                        with col_odoo:
                            odoo_input = st.text_input("رقم منظومة أودو المرجعي * (إلزامي):", value=existing_odoo, placeholder="أدخل رقم أودو هنا...", key=f"odoo_fin_{v_id}")
                        
                        btn_confirm = st.button("✅ تأكيد استلام الدفعة الأولى والتحويل للإنتاج", key=f"confirm_pay_{v_id}", use_container_width=True)
                        
                        if btn_confirm:
                            if not odoo_input.strip():
                                st.error("⚠️ خطأ: يرجى إدخال رقم منظومة أودو المرجعي لتأكيد المعاملة!")
                            else:
                                conn = db.get_connection()
                                c = conn.cursor()
                                c.execute('''
                                    UPDATE ProjectDesigns
                                    SET price_is_paid = 1,
                                        is_sent_to_production = 1,
                                        odoo_no = ?
                                    WHERE visit_id = ?
                                ''', (odoo_input.strip(), v_id))
                                conn.commit()
                                conn.close()
                                
                                # Log Activity
                                db.log_activity(
                                    username=st.session_state.get('username', 'Unknown'),
                                    employee_name=st.session_state.get('employee_name', 'Unknown'),
                                    action_type="تأكيد الدفعة الأولى",
                                    module="مسار الخزينة",
                                    details=f"تم تأكيد استلام الدفعة الأولى وإدخال رقم أودو: {odoo_input.strip()} للمشروع {mhm_code} بقيمة {price_final:,.2f} د.ل"
                                )
                                
                                st.success(f"✅ تم تأكيد الدفعة الأولى للمشروع {mhm_code} ونقله لمسار الإنتاج بنجاح!")
                                time.sleep(1.5)
                                st.rerun()

    # ---------------------------------------------------------
    # TAB 2: PENDING SECOND DEPOSIT
    # ---------------------------------------------------------
    with tab2:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT f.id, f.customer_name, f.phone, f.address, f.furniture_type,
                   d.price_final, d.odoo_no, p.status
            FROM FieldVisits f
            INNER JOIN ProjectDesigns d ON f.id = d.visit_id
            LEFT JOIN ProjectProduction p ON f.id = p.visit_id
            WHERE f.is_canceled = 0 AND d.price_is_paid = 1 AND d.second_payment_paid = 0
            ORDER BY f.id DESC
        ''')
        pending_second = c.fetchall()
        conn.close()
        
        if not pending_second:
            st.info("ℹ️ لا توجد مشاريع بانتظار تأكيد الدفعة الثانية حالياً.")
        else:
            st.markdown("<p style='text-align: center; color: gray;'>المشاريع أدناه تم دفع الدفعة الأولى لها وهي في مسار الإنتاج، بانتظار تحصيل الدفعة الثانية لتسليمها.</p>", unsafe_allow_html=True)
            for row in pending_second:
                v_id, c_name, phone, address, f_type, price_final, existing_odoo, prod_status = row
                mhm_code = f"MHM{v_id:05d}"
                
                with st.expander(f"💰 [{mhm_code}] العميل: {c_name} | حالة الإنتاج: {prod_status or 'غير محدد'}"):
                    st.markdown(f"**👤 العميل:** {c_name} | **📞 الهاتف:** {phone or '—'}")
                    st.markdown(f"**🏭 حالة التصنيع الآن:** {prod_status or 'غير محدد'}")
                    
                    st.markdown("---")
                    
                    if is_observer:
                        st.warning("🔒 وضع القراءة فقط.")
                    else:
                        btn_confirm_2 = st.button("✅ تأكيد استلام الدفعة الثانية والأخيرة", key=f"confirm_pay2_{v_id}", use_container_width=True)
                        if btn_confirm_2:
                            conn = db.get_connection()
                            c = conn.cursor()
                            c.execute('UPDATE ProjectDesigns SET second_payment_paid = 1 WHERE visit_id = ?', (v_id,))
                            conn.commit()
                            conn.close()
                            
                            db.log_activity(
                                username=st.session_state.get('username', 'Unknown'),
                                employee_name=st.session_state.get('employee_name', 'Unknown'),
                                action_type="تأكيد الدفعة الثانية",
                                module="مسار الخزينة",
                                details=f"تم تأكيد استلام الدفعة الثانية والأخيرة للمشروع {mhm_code}"
                            )
                            
                            st.success(f"✅ تم تأكيد الدفعة الثانية والأخيرة للمشروع {mhm_code} بنجاح! الآن يمكن تسليمه للعميل.")
                            time.sleep(1.5)
                            st.rerun()

    # ---------------------------------------------------------
    # TAB 3: CONFIRMED PAYMENTS
    # ---------------------------------------------------------
    with tab3:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT f.id, f.customer_name, f.phone, f.furniture_type,
                   d.price_final, d.odoo_no, d.workshop_drawing, d.second_payment_paid
            FROM FieldVisits f
            INNER JOIN ProjectDesigns d ON f.id = d.visit_id
            WHERE f.is_canceled = 0 AND d.price_is_paid = 1
            ORDER BY f.id DESC
        ''')
        confirmed_payments = c.fetchall()
        conn.close()
        
        if not confirmed_payments:
            st.info("ℹ️ لا توجد دفعات مستلمة ومؤكدة حالياً.")
        else:
            st.markdown("<p style='text-align: center; color: gray;'>قائمة المشاريع التي تم استلام دفعتها الأولى (وربما الثانية) وتأكيدها في النظام</p>", unsafe_allow_html=True)
            for row in confirmed_payments:
                v_id, c_name, phone, f_type, price_final, odoo_no, workshop_drawing, second_paid = row
                mhm_code = f"MHM{v_id:05d}"
                sec_icon = "🟢 (تم استلام الدفعة الثانية)" if second_paid else "⏳ (بانتظار الدفعة الثانية)"
                
                with st.expander(f"✅ [{mhm_code}] 🔢 Odoo: {odoo_no} | العميل: {c_name} | {sec_icon}"):
                    c_col1, c_col2 = st.columns(2)
                    with c_col1:
                        st.markdown(f"**اسم العميل:** {c_name}")
                        st.markdown(f"**رقم الهاتف:** {phone or '—'}")
                        st.markdown(f"**نوع الأثاث:** {f_type or '—'}")
                    with c_col2:
                        st.markdown(f"**القيمة المدفوعة (الدفعة الأولى):** {price_final:,.2f} د.ل")
                        st.markdown(f"**حالة الدفعة الثانية:** {sec_icon}")
                        st.markdown(f"**رقم أودو المسجل:** {odoo_no}")
                        if workshop_drawing and os.path.exists(workshop_drawing):
                            fname = os.path.basename(workshop_drawing)
                            with open(workshop_drawing, "rb") as f_obj:
                                b64 = base64.b64encode(f_obj.read()).decode()
                            st.markdown(f'<a href="data:application/pdf;base64,{b64}" download="{fname}" style="display: inline-block; padding: 4px 8px; background-color: #f1f8e9; color: #33691e; text-decoration: none; border-radius: 4px; border: 1px solid #81c784; font-size: 12px; font-weight: bold;">📥 تحميل الرسم الفني (Workshop Drawing)</a>', unsafe_allow_html=True)
                        else:
                            st.info("لا يوجد رسم فني مرفق.")

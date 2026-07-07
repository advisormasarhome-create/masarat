"""
mod_contracts.py  —  مسار العقود
إدارة عقود العملاء والمشاريع: سجل العملاء، إضافة عقد، استعراض وعمليات العقود.
"""

import streamlit as st
import datetime
import os
import database as db
import base64

STATUS_OPTIONS = ["جاري", "مكتمل", "معلق", "ملغي", "تحت المراجعة"]

STATUS_COLORS = {
    "جاري":          ("#e0f7fa", "#0077b6", "🔵"),
    "مكتمل":         ("#e8f5e9", "#2e7d32", "✅"),
    "معلق":          ("#fff8e1", "#f57f17", "⏸️"),
    "ملغي":          ("#fce4ec", "#c62828", "❌"),
    "تحت المراجعة": ("#f3e5f5", "#6a1b9a", "🔍"),
}

CONTRACTS_UPLOADS_DIR = "uploads/contracts"

def _ensure_uploads_dir():
    os.makedirs(CONTRACTS_UPLOADS_DIR, exist_ok=True)

def _save_uploaded_file(uploaded_file, contract_no):
    _ensure_uploads_dir()
    safe_name = uploaded_file.name.replace(" ", "_")
    file_path = os.path.join(CONTRACTS_UPLOADS_DIR, f"{contract_no}_{safe_name}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def _status_badge(status):
    bg, fg, icon = STATUS_COLORS.get(status, ("#eeeeee", "#333", "📄"))
    return (
        f"<span style='background:{bg}; color:{fg}; padding:3px 10px; "
        f"border-radius:12px; font-size:13px; font-weight:600;'>{icon} {status}</span>"
    )

# ────────────────────────────────────────────────
# 1. سجل العملاء
# ────────────────────────────────────────────────
def _render_clients_tab():
    st.markdown(
        "<h3 style='color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>👥 سجل العملاء (العملاء المعتمد تسعيرتهم بانتظار توقيع العقد)</h3>",
        unsafe_allow_html=True,
    )

    if st.session_state.get('selected_client_visit_id'):
        st.success(f"✅ تم اختيار العميل **{st.session_state.get('selected_client_name')}** بنجاح!")
        st.info("👆 **يرجى النقر على تبويب '➕ إضافة عقد جديد' في أعلى الصفحة لتعبئة وتوقيع العقد.**")
        st.markdown("<br>", unsafe_allow_html=True)
        
    # Only load clients whose price is approved but contract is not yet approved
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT f.id, f.customer_name, f.phone, f.address, f.furniture_type, f.site_status, f.visit_date,
               COALESCE(d.price_final, 0.0), COALESCE(d.odoo_no, '')
        FROM FieldVisits f
        INNER JOIN ProjectDesigns d ON f.id = d.visit_id AND d.price_is_approved = 1 AND d.contract_is_approved = 0
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    clients = c.fetchall()
    conn.close()

    if not clients:
        st.info("ℹ️ لا يوجد عملاء بانتظار التعاقد حالياً (العملاء يظهرون هنا تلقائياً بعد اعتماد التسعيرة في مسار التصميم).")
        return

    # بحث وتصفية
    search_q = st.text_input("🔍 ابحث عن عميل (الاسم، رقم الهاتف، أو رقم مسارات MHM):", placeholder="اكتب للبحث...")
    
    filtered_clients = []
    for row in clients:
        c_id, c_name, phone, address, furniture_type, site_status, visit_date, price_final, odoo_no = row
        mhm_code = f"MHM{c_id:05d}"
        
        # تصفية البحث
        if search_q.strip():
            q = search_q.strip().lower()
            if q not in mhm_code.lower() and q not in (c_name or "").lower() and q not in (phone or "").lower():
                continue
                
        filtered_clients.append((c_id, mhm_code, c_name, phone, address, furniture_type, site_status, visit_date, price_final, odoo_no))

    st.markdown(f"**عدد العملاء:** {len(filtered_clients)}")
    st.markdown("---")

    for cl in filtered_clients:
        c_id, mhm_code, c_name, phone, address, furniture_type, site_status, visit_date, price_final, odoo_no = cl
        
        with st.container():
            st.markdown(
                f"""
                <div style='background-color:#f0f8ff; border-right:5px solid #0077b6; border-radius:8px; padding:12px; margin-bottom:12px;'>
                    <table style='width:100%; font-size:14px;'>
                        <tr>
                            <td><b>🆔 رقم مسارات:</b></td><td style='color:#0077b6; font-weight:bold;'>{mhm_code}</td>
                            <td><b>👤 اسم العميل:</b></td><td>{c_name}</td>
                        </tr>
                        <tr>
                            <td><b>📞 الهاتف:</b></td><td>{phone or '—'}</td>
                            <td><b>📍 العنوان:</b></td><td>{address or '—'}</td>
                        </tr>
                        <tr>
                            <td><b>🪑 نوع الأثاث:</b></td><td>{furniture_type or '—'}</td>
                            <td><b>💰 قيمة التسعيرة:</b></td><td style='color:#166534; font-weight:bold;'>{price_final:,.2f} د.ل</td>
                        </tr>
                        <tr>
                            <td><b>🔢 رقم أودو:</b></td><td style='color:#d62828; font-weight:bold;'>{odoo_no or '—'}</td>
                            <td><b>📅 تاريخ الزيارة:</b></td><td>{visit_date or '—'}</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True
            )
            
            if st.button(f"📝 إنشاء عقد جديد للعميل: {c_name}", key=f"select_client_{c_id}"):
                st.session_state['selected_client_visit_id'] = c_id
                st.session_state['selected_client_name'] = c_name
                st.session_state['selected_client_phone'] = phone
                st.session_state['selected_client_value'] = price_final
                st.session_state['selected_client_odoo_no'] = odoo_no
                st.rerun()

# ────────────────────────────────────────────────
# 2. إضافة عقد جديد
# ────────────────────────────────────────────────
def _render_add_tab(emp_name: str):
    st.markdown(
        "<h3 style='color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>➕ إضافة عقد جديد</h3>",
        unsafe_allow_html=True,
    )
    
    default_visit_id = st.session_state.get('selected_client_visit_id', None)
    default_name = st.session_state.get('selected_client_name', "")
    default_phone = st.session_state.get('selected_client_phone', "")
    default_value = st.session_state.get('selected_client_value', 0.0)
    default_odoo = st.session_state.get('selected_client_odoo_no', "")
    
    if default_name:
        st.info(f"💡 تم تعبئة البيانات تلقائياً للعميل المختار: **{default_name}**")
        if st.button("❌ إلغاء تحديد العميل"):
            st.session_state.pop('selected_client_visit_id', None)
            st.session_state.pop('selected_client_name', None)
            st.session_state.pop('selected_client_phone', None)
            st.session_state.pop('selected_client_value', None)
            st.session_state.pop('selected_client_odoo_no', None)
            st.rerun()

    with st.form("add_contract_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            title       = st.text_input("📝 موضوع / عنوان العقد *")
            client_name = st.text_input("👤 اسم العميل *", value=default_name)
            client_phone= st.text_input("📞 رقم الهاتف", value=default_phone)
            value       = st.number_input("💰 قيمة العقد (د.ل)", min_value=0.0, value=float(default_value), step=100.0, format="%.2f")
        with c2:
            contract_date = st.date_input("📅 تاريخ إبرام العقد", value=datetime.date.today())
            start_date    = st.date_input("🚀 تاريخ بدء التنفيذ",  value=datetime.date.today())
            end_date      = st.date_input("🏁 تاريخ الانتهاء المتوقع",
                                          value=datetime.date.today() + datetime.timedelta(days=30))
            status        = st.selectbox("📌 حالة العقد", STATUS_OPTIONS)
            odoo_no       = st.text_input("🔢 رقم اودو المرجعي (Odoo Number)", value=default_odoo)

        manager_name = st.text_input("👤 اسم ممثل الطرف الأول (مدير الصالة) *", value="م. علي بن عيسى")
        notes = st.text_area("📋 ملاحظات", height=80)
        attachments = st.file_uploader(
            "📎 مرفقات العقد (PDF / صور)",
            accept_multiple_files=True,
            type=["pdf", "png", "jpg", "jpeg", "docx"],
        )

        c_btn1, c_btn2, c_btn3 = st.columns(3)
        with c_btn1:
            btn_save = st.form_submit_button("💾 حفظ العقد", type="secondary", use_container_width=True)
        with c_btn2:
            btn_approve = st.form_submit_button("💾 حفظ واعتماد العقد (للخزينة)", type="primary", use_container_width=True)
        with c_btn3:
            btn_preview = st.form_submit_button("👁️ معاينة وطباعة العقد", use_container_width=True)

        if btn_preview:
            st.session_state['preview_contract_data'] = {
                'title': title.strip(),
                'client_name': client_name.strip(),
                'client_phone': client_phone.strip(),
                'value': value,
                'contract_date': str(contract_date),
                'start_date': str(start_date),
                'end_date': str(end_date),
                'notes': notes.strip(),
                'odoo_no': odoo_no.strip(),
                'manager_name': manager_name.strip()
            }
            st.rerun()

        if btn_save or btn_approve:
            if not title.strip() or not client_name.strip():
                st.error("⚠️ يرجى تعبئة موضوع العقد واسم العميل على الأقل.")
                return

            new_id, contract_no = db.add_contract(
                title=title.strip(),
                client_name=client_name.strip(),
                client_phone=client_phone.strip(),
                contract_date=str(contract_date),
                start_date=str(start_date),
                end_date=str(end_date),
                value=value,
                status=status,
                notes=notes.strip(),
                created_by=emp_name,
                odoo_no=odoo_no.strip()
            )

            # حفظ المرفقات
            saved_paths = []
            if attachments:
                for f in attachments:
                    p = _save_uploaded_file(f, contract_no)
                    saved_paths.append(p)
                if saved_paths:
                    db.update_contract_files(new_id, "|".join(saved_paths), emp_name)

            if btn_approve and default_visit_id:
                conn = db.get_connection()
                c = conn.cursor()
                c.execute("UPDATE ProjectDesigns SET contract_is_approved = 1 WHERE visit_id = ?", (default_visit_id,))
                conn.commit()
                conn.close()

            # إزالة العميل المحدد من الجلسة بعد الحفظ الناجح
            st.session_state.pop('selected_client_visit_id', None)
            st.session_state.pop('selected_client_name', None)
            st.session_state.pop('selected_client_phone', None)
            st.session_state.pop('selected_client_value', None)
            st.session_state.pop('selected_client_odoo_no', None)
            
            if btn_approve:
                st.session_state["contracts_success"] = f"✅ تم حفظ واعتماد العقد [{contract_no}] بنجاح ونقله للخزينة!"
            else:
                st.session_state["contracts_success"] = f"✅ تم حفظ سجل العقد [{contract_no}] بنجاح!"
            st.rerun()

    # عرض معاينة الطباعة إذا كانت موجودة في الجلسة
    preview_data = st.session_state.get('preview_contract_data', None)
    if preview_data:
        st.markdown("---")
        st.markdown("<h4 style='color:#0077b6; font-family:\"Readex Pro\";'>📄 معاينة الطباعة الاحترافية للعقد</h4>", unsafe_allow_html=True)
        st.info("💡 للطباعة المباشرة، اضغط على زر Ctrl + P (أو Cmd + P على نظام الماك) لطباعة الصفحة المنسقة للعقد.")
        
        logo_base64 = ""
        if os.path.exists("logo.jpg"):
            with open("logo.jpg", "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
        
        logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" style="max-height:85px;"/>' if logo_base64 else '<span style="font-size:24px; font-weight:bold; color:#0077b6;">MASAR HOME</span>'
        
        contract_html = f"""
        <div class="print-container" style="background-color: white; color: black; padding: 40px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: 'Readex Pro', sans-serif; direction: rtl; text-align: right;">
            <!-- Header -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                <tr>
                    <td style="text-align: right; vertical-align: middle; width: 50%;">
                        <h2 style="margin: 0; color: #1e3d59; font-size: 20px;">شركة مساهوم للتصميم والديكور</h2>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">مسار العقود والمشاريع</p>
                    </td>
                    <td style="text-align: left; vertical-align: middle; width: 50%;">
                        {logo_html}
                    </td>
                </tr>
            </table>
            <hr style="border: 1px solid #1e3d59; margin-bottom: 25px;"/>
            
            <!-- Title -->
            <h3 style="text-align: center; color: #1e3d59; margin-bottom: 35px; font-size: 22px; border-bottom: 2px solid #1e3d59; padding-bottom: 8px;">عقد تقديم خدمات تصميم وتنفيذ</h3>
            
            <!-- Content -->
            <p style="font-size: 15px; line-height: 1.8; margin-bottom: 15px;">
                إنه في تاريخ <b>{preview_data['contract_date']}</b>، تم الاتفاق والتعاقد بين كل من:
            </p>
            
            <ol style="font-size: 15px; line-height: 1.8; margin-bottom: 25px; padding-right: 20px;">
                <li style="margin-bottom: 8px;">
                    <b>الطرف الأول (الشركة):</b> شركة مساهوم للتصميم والديكور، ويمثلها في التوقيع: <b>{preview_data['manager_name']}</b>.
                </li>
                <li style="margin-bottom: 8px;">
                    <b>الطرف الثاني (العميل):</b> السيد/ة <b>{preview_data['client_name']}</b>، رقم الهاتف: <b>{preview_data['client_phone'] or 'غير محدد'}</b>.
                </li>
            </ol>
            
            <p style="font-size: 15px; line-height: 1.8; margin-bottom: 15px;">
                وقد اتفق الطرفان على البنود والمواصفات التالية:
            </p>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px;">
                <tr style="background-color: #f7f9fa;">
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right; width: 25%;">عنوان / موضوع العقد</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_data['title']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">قيمة العقد الإجمالية</th>
                    <td style="border: 1px solid #ccc; padding: 10px; font-weight: bold; color: #1b4d3e;">{float(preview_data['value']):,.2f} د.ل (دينار ليبي)</td>
                </tr>
                <tr style="background-color: #f7f9fa;">
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">تاريخ بدء التنفيذ</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_data['start_date']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">تاريخ الانتهاء المتوقع</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_data['end_date']}</td>
                </tr>
                {f'''<tr style="background-color: #f7f9fa;">
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">رقم Odoo المرجعي</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_data['odoo_no']}</td>
                </tr>''' if preview_data['odoo_no'] else ''}
            </table>
            
            <h4 style="color: #1e3d59; margin-top: 25px; margin-bottom: 8px;">📝 الشروط والتفاصيل الإضافية:</h4>
            <div style="border: 1px solid #ccc; padding: 15px; border-radius: 4px; background-color: #fafafa; font-size: 14px; min-height: 80px; white-space: pre-wrap; line-height: 1.6; margin-bottom: 35px;">{preview_data['notes'] or 'لا توجد ملاحظات إضافية.'}</div>
            
            <!-- Signatures -->
            <table style="width: 100%; border-collapse: collapse; margin-top: 40px; font-size: 14px;">
                <tr>
                    <td style="width: 50%; text-align: center; vertical-align: top; padding-bottom: 30px;">
                        <b>الطرف الأول (الشركة)</b><br/><br/>
                        الاسم ممثلاً: {preview_data['manager_name']}<br/><br/>
                        التوقيع: ....................................
                    </td>
                    <td style="width: 50%; text-align: center; vertical-align: top; padding-bottom: 30px;">
                        <b>الطرف الثاني (العميل)</b><br/><br/>
                        الاسم: {preview_data['client_name']}<br/><br/>
                        التوقيع: ....................................
                    </td>
                </tr>
            </table>
        </div>
        """
        
        st.markdown("""
        <style>
        @media print {
            body * {
                visibility: hidden;
            }
            .print-container, .print-container * {
                visibility: visible;
            }
            .print-container {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(contract_html, unsafe_allow_html=True)
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.button("🖨️ طباعة العقد مباشرة", key="print_contract_btn_sub", use_container_width=True)
        with col_c2:
            if st.button("❌ إغلاق المعاينة", key="close_contract_btn_sub", use_container_width=True):
                st.session_state.pop('preview_contract_data', None)
                st.rerun()

# ────────────────────────────────────────────────
# 3. استعراض سجل العقود
# ────────────────────────────────────────────────
def _render_contract_card(row, can_edit: bool, is_admin: bool, emp_name: str):
    (cid, contract_no, title, client_name, client_phone,
     contract_date, start_date, end_date, value, status,
     notes, file_paths, created_by, created_at,
     last_mod_by, last_mod_at, odoo_no) = row

    bg, fg, icon = STATUS_COLORS.get(status, ("#eeeeee", "#333", "📄"))

    odoo_tag = f" | 🔢 Odoo: {odoo_no}" if odoo_no else ""
    with st.expander(
        f"{icon} **{contract_no}** — {title}  |  👤 {client_name}{odoo_tag}  |  💰 {value:,.2f} د.ل  |  {status}",
        expanded=False,
    ):
        info_col, action_col = st.columns([3, 1])
        with info_col:
            st.markdown(f"""
            <div style='background:{bg}; border-radius:10px; padding:12px 18px;
                        border-right:4px solid {fg}; margin-bottom:8px;'>
                <table style='width:100%; font-size:14px;'>
                  <tr>
                    <td><b>📋 رقم العقد:</b></td><td>{contract_no}</td>
                    <td><b>📞 الهاتف:</b></td><td>{client_phone or '—'}</td>
                  </tr>
                  <tr>
                    <td><b>📅 تاريخ الإبرام:</b></td><td>{contract_date or '—'}</td>
                    <td><b>🚀 بداية التنفيذ:</b></td><td>{start_date or '—'}</td>
                  </tr>
                  <tr>
                    <td><b>🏁 نهاية التنفيذ:</b></td><td>{end_date or '—'}</td>
                    <td><b>💰 القيمة:</b></td><td>{value:,.2f} د.ل</td>
                  </tr>
                  <tr>
                    <td><b>📌 الحالة:</b></td>
                    <td>{_status_badge(status)}</td>
                    <td><b>🔢 رقم أودو:</b></td>
                    <td style='color:#d62828; font-weight:bold;'>{odoo_no or '—'}</td>
                  </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

            if notes:
                st.markdown(f"<div style='font-size:13px; color:#555; padding:4px 8px;'>📝 {notes}</div>",
                            unsafe_allow_html=True)

            st.caption(f"👤 أُنشئ بواسطة: {created_by}  |  آخر تعديل: {last_mod_by} ({last_mod_at[:16] if last_mod_at else '—'})")

        # Check if this contract is approved in ProjectDesigns
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("""
            SELECT contract_is_approved 
            FROM ProjectDesigns d
            JOIN FieldVisits f ON d.visit_id = f.id
            WHERE f.customer_name = ? OR (d.odoo_no = ? AND d.odoo_no != '')
        """, (client_name, odoo_no))
        row_approved = c.fetchone()
        conn.close()
        
        contract_is_approved = row_approved[0] if row_approved else 0
        is_admin_user = is_admin
        can_modify_contract = (contract_is_approved == 0) or is_admin_user

        with action_col:
            if can_edit:
                if not can_modify_contract:
                    st.caption("🔒 معتمد للخزينة")
                if st.button("✏️ تعديل سجل", key=f"edit_btn_{cid}", use_container_width=True, disabled=not can_modify_contract):
                    st.session_state[f"edit_contract_{cid}"] = True
                if is_admin:
                    if st.button("🗑️ حذف سجل", key=f"del_btn_{cid}", use_container_width=True, disabled=not can_modify_contract):
                        st.session_state[f"confirm_del_{cid}"] = True

        # ── تأكيد الحذف ──
        if st.session_state.get(f"confirm_del_{cid}"):
            st.warning(f"⚠️ هل أنت متأكد من حذف هذا السجل [{contract_no}]؟ لا يمكن التراجع!")
            dconf1, dconf2 = st.columns(2)
            with dconf1:
                if st.button("✅ نعم، احذف", key=f"conf_del_yes_{cid}", use_container_width=True):
                    db.delete_contract(cid)
                    st.session_state[f"confirm_del_{cid}"] = False
                    st.session_state["contracts_success"] = f"🗑️ تم حذف السجل بنجاح [{contract_no}]."
                    st.rerun()
            with dconf2:
                if st.button("❌ إلغاء", key=f"conf_del_no_{cid}", use_container_width=True):
                    st.session_state[f"confirm_del_{cid}"] = False
                    st.rerun()

        # ── نموذج التعديل ──
        if st.session_state.get(f"edit_contract_{cid}") and can_edit and can_modify_contract:
            st.markdown("---")
            st.markdown("**✏️ تعديل بيانات العقد:**")
            with st.form(f"edit_form_{cid}"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_title  = st.text_input("موضوع العقد", value=title)
                    e_client = st.text_input("اسم العميل",  value=client_name)
                    e_phone  = st.text_input("الهاتف",       value=client_phone or "")
                    e_value  = st.number_input("القيمة (د.ل)", value=float(value), min_value=0.0, step=100.0, format="%.2f")
                with ec2:
                    e_cdate = st.date_input("تاريخ الإبرام",
                                            value=datetime.date.fromisoformat(contract_date) if contract_date else datetime.date.today())
                    e_sdate = st.date_input("بداية التنفيذ",
                                            value=datetime.date.fromisoformat(start_date) if start_date else datetime.date.today())
                    e_edate = st.date_input("نهاية التنفيذ",
                                            value=datetime.date.fromisoformat(end_date) if end_date else datetime.date.today())
                    e_status = st.selectbox("الحالة", STATUS_OPTIONS,
                                            index=STATUS_OPTIONS.index(status) if status in STATUS_OPTIONS else 0)
                    e_odoo = st.text_input("رقم اودو المرجعي (Odoo Number)", value=odoo_no)

                e_notes = st.text_area("ملاحظات", value=notes or "", height=80)

                # مرفقات إضافية
                new_attachments = st.file_uploader(
                    "إضافة مرفقات جديدة", accept_multiple_files=True,
                    type=["pdf", "png", "jpg", "jpeg", "docx"],
                    key=f"edit_files_{cid}",
                )

                save_col, cancel_col = st.columns(2)
                with save_col:
                    save_btn = st.form_submit_button("💾 حفظ سجل", type="primary", use_container_width=True)
                with cancel_col:
                    cancel_btn = st.form_submit_button("❌ إلغاء", use_container_width=True)

                if save_btn:
                    db.update_contract(
                        contract_id=cid,
                        title=e_title.strip(),
                        client_name=e_client.strip(),
                        client_phone=e_phone.strip(),
                        contract_date=str(e_cdate),
                        start_date=str(e_sdate),
                        end_date=str(e_edate),
                        value=e_value,
                        status=e_status,
                        notes=e_notes.strip(),
                        modified_by=emp_name,
                        odoo_no=e_odoo.strip()
                    )
                    # مرفقات جديدة
                    existing_paths = [p for p in (file_paths or "").split("|") if p]
                    for nf in new_attachments:
                        np_ = _save_uploaded_file(nf, contract_no)
                        existing_paths.append(np_)
                    if existing_paths:
                        db.update_contract_files(cid, "|".join(existing_paths), emp_name)

                    st.session_state[f"edit_contract_{cid}"] = False
                    st.session_state["contracts_success"] = f"✅ تم حفظ سجل العقد [{contract_no}] بنجاح."
                    st.rerun()

                if cancel_btn:
                    st.session_state[f"edit_contract_{cid}"] = False
                    st.rerun()

        # ── عرض المرفقات الموجودة ──
        if file_paths:
            paths = [p for p in file_paths.split("|") if p and os.path.exists(p)]
            if paths:
                st.markdown("**📎 المرفقات:**")
                for p in paths:
                    fname = os.path.basename(p)
                    with open(p, "rb") as fp:
                        st.download_button(
                            label=f"⬇️ {fname}",
                            data=fp.read(),
                            file_name=fname,
                            key=f"dl_{cid}_{fname}",
                        )

def _render_stats(contracts):
    if not contracts:
        return
    total_value = sum(r[8] for r in contracts)
    status_counts = {}
    for r in contracts:
        status_counts[r[9]] = status_counts.get(r[9], 0) + 1

    st.markdown("### 📊 إحصائيات سريعة")
    scols = st.columns(len(STATUS_OPTIONS) + 1)
    with scols[0]:
        st.markdown(
            f"<div style='background:#e0fbfc;border-radius:10px;padding:14px;text-align:center;"
            f"border-top:4px solid #00b4d8;'>"
            f"<div style='font-size:12px;color:#457b9d;font-weight:600;'>إجمالي القيمة</div>"
            f"<div style='font-size:20px;font-weight:700;color:#03045e;'>{total_value:,.0f}<br>"
            f"<small>د.ل</small></div></div>",
            unsafe_allow_html=True,
        )
    for i, s in enumerate(STATUS_OPTIONS):
        cnt = status_counts.get(s, 0)
        bg, fg, icon = STATUS_COLORS.get(s, ("#eee", "#333", "📄"))
        with scols[i + 1]:
            st.markdown(
                f"<div style='background:{bg};border-radius:10px;padding:14px;text-align:center;"
                f"border-top:4px solid {fg};'>"
                f"<div style='font-size:12px;color:{fg};font-weight:600;'>{icon} {s}</div>"
                f"<div style='font-size:26px;font-weight:700;color:{fg};'>{cnt}</div></div>",
                unsafe_allow_html=True,
            )
    st.markdown("<br>", unsafe_allow_html=True)

def _render_contracts_list_tab(can_edit: bool, is_admin: bool, emp_name: str):
    st.markdown(
        "<h3 style='color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>📋 استعراض سجل العقود</h3>",
        unsafe_allow_html=True,
    )
    
    contracts = db.get_all_contracts()
    if not contracts:
        st.info("📭 لا توجد عقود مسجلة بعد. ابدأ بإضافة عقد جديد.")
        return

    # الإحصائيات
    _render_stats(contracts)

    # ── أدوات التصفية ──
    st.markdown("#### 🔍 تصفية العقود")
    fcol1, fcol2, fcol3 = st.columns([2, 1, 1])
    with fcol1:
        search_q = st.text_input("🔎 بحث (بالاسم أو رقم العقد أو الموضوع)", label_visibility="collapsed",
                                 placeholder="ابحث عن عقد...")
    with fcol2:
        filter_status = st.selectbox("الحالة", ["الكل"] + STATUS_OPTIONS, label_visibility="collapsed")
    with fcol3:
        sort_by = st.selectbox("الترتيب", ["الأحدث أولاً", "الأقدم أولاً", "القيمة تنازلياً"],
                               label_visibility="collapsed")

    # تطبيق التصفية
    filtered = list(contracts)
    if search_q.strip():
        q = search_q.strip().lower()
        filtered = [r for r in filtered if
                    q in (r[1] or "").lower() or   # contract_no
                    q in (r[2] or "").lower() or   # client_name
                    q in (r[3] or "").lower()]      # client_name and phone
    if filter_status != "الكل":
        filtered = [r for r in filtered if r[9] == filter_status]

    if sort_by == "الأقدم أولاً":
        filtered = list(reversed(filtered))
    elif sort_by == "القيمة تنازلياً":
        filtered = sorted(filtered, key=lambda r: r[8], reverse=True)

    st.markdown(f"**{len(filtered)} عقد** مطابق للبحث.")
    st.markdown("---")

    if not filtered:
        st.warning("لا توجد عقود تطابق معايير البحث.")
    else:
        for row in filtered:
            _render_contract_card(row, can_edit=can_edit, is_admin=is_admin, emp_name=emp_name)

# ────────────────────────────────────────────────
# الدالة الرئيسية
# ────────────────────────────────────────────────
def _render_termination_tab(emp_name: str):
    st.markdown(
        "<h3 style='color:#c62828; font-family:\"Readex Pro\",sans-serif;'>📜 إشعار إنهاء التعاقد واستلام الأعمال</h3>",
        unsafe_allow_html=True,
    )
    
    contracts = db.get_all_contracts()
    if not contracts:
        st.info("📭 لا توجد عقود مسجلة لإصدار إشعار إنهاء تعاقد لها.")
        return

    # Search Block in Tab 4
    with st.expander("🔍 البحث المتقدم عن العقد المطلوب إنهاؤه", expanded=False):
        col_s1_t, col_s2_t, col_s3_t, col_s4_t = st.columns(4)
        with col_s1_t:
            search_name_t = st.text_input("اسم العميل", key="s_name_term")
        with col_s2_t:
            search_masar_t = st.text_input("رقم مسارات (مثال: MHM00045)", key="s_masar_term")
        with col_s3_t:
            search_odoo_t = st.text_input("رقم أودو", key="s_odoo_term")
        with col_s4_t:
            search_dates_t = st.date_input("الفترة الزمنية للعقد (من - إلى)", value=(), key="s_dates_term")

    is_search_active_t = bool(search_name_t or search_masar_t or search_odoo_t or (len(search_dates_t) == 2))

    filtered_contracts_t = []
    for r in contracts:
        c_no = r[1]
        c_name = r[3]
        c_odoo = r[16]
        c_date = r[5]
        
        # Match filters
        if search_name_t and search_name_t.strip().lower() not in c_name.lower():
            continue
        if search_masar_t:
            clean_m = search_masar_t.strip().upper()
            c_notes = r[10] or ""
            if clean_m not in c_no and clean_m not in c_notes:
                continue
        if search_odoo_t:
            clean_o = search_odoo_t.strip().lower()
            if not c_odoo or clean_o not in c_odoo.lower():
                continue
        if len(search_dates_t) == 2:
            start_d, end_d = search_dates_t
            try:
                c_date_parsed = datetime.datetime.strptime(c_date, "%Y-%m-%d").date()
                if not (start_d <= c_date_parsed <= end_d):
                    continue
            except:
                continue
        filtered_contracts_t.append(r)

    # Limit to 10 if search is not active
    if not is_search_active_t:
        filtered_contracts_t = filtered_contracts_t[:10]
        st.info("💡 تعرض القائمة أدناه آخر 10 عقود نشطة افتراضياً. للبحث عن عقود أقدم، استخدم لوحة البحث المتقدم بالرأس.")
    else:
        st.success(f"🔍 تم العثور على {len(filtered_contracts_t)} عقد مطابق لمعايير البحث.")

    # Create options list
    contract_opts = ["اختر عقداً..."] + [f"{r[1]} — {r[3]} ({r[2]})" for r in filtered_contracts_t]
    selected_contract_opt = st.selectbox("📋 اختر العقد المعني *", contract_opts, key="termination_contract_select")
    
    if selected_contract_opt == "اختر عقداً...":
        return
        
    # Get selected contract row
    contract_idx = contract_opts.index(selected_contract_opt) - 1
    selected_row = filtered_contracts_t[contract_idx]
    cid, contract_no, title, client_name, client_phone, contract_date, start_date, end_date, value, status, notes, file_paths, created_by, created_at, last_mod_by, last_mod_at, odoo_no = selected_row
    
    # Check if there is an existing termination
    existing_term = db.get_contract_termination(contract_no)
    
    default_end_date = datetime.date.today()
    default_rep = "م. علي بن عيسى"
    default_notes = "يقر الطرف الثاني (العميل) بأنه قد عاين واستلم كافة الأعمال والخدمات المتفق عليها بموجب هذا العقد على الوجه الصحيح ووفقاً للمواصفات الفنية المطلوبة، ويعتبر هذا الإشعار بمثابة مخالصة نهائية وإقرار تام بانتهاء كافة الالتزامات والتعاقد بين الطرفين دون وجود أي التزامات مستقبلية."
    
    if existing_term:
        st.success(f"ℹ️ يوجد إشعار إنهاء تعاقد مسجل لهذا العقد مسبقاً (بتاريخ {str(existing_term[6])[:10] if existing_term[6] else ''})")
        default_end_date = datetime.date.fromisoformat(existing_term[3]) if existing_term[3] else datetime.date.today()
        default_rep = existing_term[4]
        default_notes = existing_term[5]
        
    with st.form("termination_form"):
        term_date = st.date_input("📅 تاريخ إنهاء التعاقد", value=default_end_date)
        rep_name = st.text_input("👤 ممثل الطرف الأول (الشركة)", value=default_rep)
        st.text_input("👤 اسم الطرف الثاني (العميل)", value=client_name, disabled=True)
        term_notes = st.text_area("📄 صيغة إشعار إنهاء التعاقد والإقرار", value=default_notes, height=120)
        
        col1, col2 = st.columns(2)
        with col1:
            btn_save_term = st.form_submit_button("💾 حفظ وإصدار الإشعار", type="primary", use_container_width=True)
        with col2:
            btn_preview_term = st.form_submit_button("👁️ معاينة وطباعة الإشعار", type="secondary", use_container_width=True)
            
    if btn_save_term:
        db.save_contract_termination(contract_no, client_name, str(term_date), rep_name.strip(), term_notes.strip())
        st.session_state["contracts_success"] = f"✅ تم حفظ وإصدار إشعار إنهاء التعاقد للعقد [{contract_no}] بنجاح!"
        db.log_activity(st.session_state.get('username', 'Unknown'), f"إصدار إشعار إنهاء تعاقد للعقد {contract_no}")
        st.rerun()
        
    # Preview logic
    if btn_preview_term:
        st.session_state['preview_term_data'] = {
            'contract_no': contract_no,
            'client_name': client_name,
            'end_date': str(term_date),
            'representative': rep_name.strip(),
            'notes': term_notes.strip()
        }
        st.rerun()
        
    preview_term = st.session_state.get('preview_term_data', None)
    if preview_term and preview_term['contract_no'] == contract_no:
        st.markdown("---")
        st.markdown("<h4 style='color:#c62828;'>📄 معاينة إشعار إنهاء التعاقد للطباعة</h4>", unsafe_allow_html=True)
        st.info("💡 للطباعة المباشرة، اضغط على زر Ctrl + P (أو Cmd + P على نظام الماك) لطباعة الصفحة المنسقة للإقرار.")
        
        logo_base64 = ""
        if os.path.exists("logo.jpg"):
            with open("logo.jpg", "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
        
        logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" style="max-height:85px;"/>' if logo_base64 else '<span style="font-size:24px; font-weight:bold; color:#0077b6;">MASAR HOME</span>'
        
        term_html = f"""
        <div class="print-container" style="background-color: white; color: black; padding: 40px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: 'Readex Pro', sans-serif; direction: rtl; text-align: right;">
            <!-- Header -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                <tr>
                    <td style="text-align: right; vertical-align: middle; width: 50%;">
                        <h2 style="margin: 0; color: #c62828; font-size: 20px;">شركة مساهوم للتصميم والديكور</h2>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">مسار العقود والمشاريع - إقرار مخالصة</p>
                    </td>
                    <td style="text-align: left; vertical-align: middle; width: 50%;">
                        {logo_html}
                    </td>
                </tr>
            </table>
            <hr style="border: 1px solid #c62828; margin-bottom: 25px;"/>
            
            <!-- Title -->
            <h3 style="text-align: center; color: #c62828; margin-bottom: 35px; font-size: 22px; border-bottom: 2px solid #c62828; padding-bottom: 8px;">إشعار إنهاء تعاقد وإقرار استلام أعمال</h3>
            
            <!-- Details Table -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 14px;">
                <tr style="background-color: #fcf8f8;">
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right; width: 25%;">رقم العقد المرجعي</th>
                    <td style="border: 1px solid #ccc; padding: 10px; font-weight: bold;">{preview_term['contract_no']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">اسم العميل (الطرف الثاني)</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_term['client_name']}</td>
                </tr>
                <tr style="background-color: #fcf8f8;">
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">تاريخ إنهاء التعاقد</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_term['end_date']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ccc; padding: 10px; text-align: right;">ممثل الشركة (الطرف الأول)</th>
                    <td style="border: 1px solid #ccc; padding: 10px;">{preview_term['representative']}</td>
                </tr>
            </table>
            
            <!-- Statement -->
            <h4 style="color: #c62828; margin-top: 25px; margin-bottom: 8px;">📜 نص الإقرار والاستلام:</h4>
            <div style="border: 1px solid #ccc; padding: 15px; border-radius: 4px; background-color: #fafafa; font-size: 14px; line-height: 1.8; white-space: pre-wrap; margin-bottom: 40px;">
                {preview_term['notes']}
            </div>
            
            <!-- Signatures -->
            <table style="width: 100%; border-collapse: collapse; margin-top: 40px; font-size: 14px;">
                <tr>
                    <td style="width: 50%; text-align: center; vertical-align: top; padding-bottom: 30px;">
                        <b>الطرف الأول (الشركة)</b><br/><br/>
                        الاسم: {preview_term['representative']}<br/><br/>
                        التوقيع: ....................................
                    </td>
                    <td style="width: 50%; text-align: center; vertical-align: top; padding-bottom: 30px;">
                        <b>الطرف الثاني (العميل)</b><br/><br/>
                        الاسم: {preview_term['client_name']}<br/><br/>
                        التوقيع: ....................................
                    </td>
                </tr>
            </table>
        </div>
        """
        st.markdown("""
        <style>
        @media print {
            body * {
                visibility: hidden;
            }
            .print-container, .print-container * {
                visibility: visible;
            }
            .print-container {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(term_html, unsafe_allow_html=True)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.button("🖨️ طباعة الإشعار مباشرة", key="print_term_btn_sub", use_container_width=True)
        with col_act2:
            if st.button("❌ إغلاق المعاينة", key="close_term_btn_sub", use_container_width=True):
                st.session_state.pop('preview_term_data', None)
                st.rerun()

def _render_survey_tab(emp_name: str):
    st.markdown(
        "<h3 style='color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>📊 استبيان رضا العميل عن الخدمات</h3>",
        unsafe_allow_html=True,
    )
    
    contracts = db.get_all_contracts()
    if not contracts:
        st.info("📭 لا توجد عقود مسجلة لإجراء استبيان رضا العميل لها.")
        return

    # Search Block in Tab 5
    with st.expander("🔍 البحث المتقدم عن العميل المطلوب استبيان رضاه", expanded=False):
        col_s1_s, col_s2_s, col_s3_s, col_s4_s = st.columns(4)
        with col_s1_s:
            search_name_s = st.text_input("اسم العميل", key="s_name_survey")
        with col_s2_s:
            search_masar_s = st.text_input("رقم مسارات (مثال: MHM00045)", key="s_masar_survey")
        with col_s3_s:
            search_odoo_s = st.text_input("رقم أودو", key="s_odoo_survey")
        with col_s4_s:
            search_dates_s = st.date_input("الفترة الزمنية للعقد (من - إلى)", value=(), key="s_dates_survey")

    is_search_active_s = bool(search_name_s or search_masar_s or search_odoo_s or (len(search_dates_s) == 2))

    filtered_contracts_s = []
    for r in contracts:
        c_no = r[1]
        c_name = r[3]
        c_odoo = r[16]
        c_date = r[5]
        
        # Match filters
        if search_name_s and search_name_s.strip().lower() not in c_name.lower():
            continue
        if search_masar_s:
            clean_m = search_masar_s.strip().upper()
            c_notes = r[10] or ""
            if clean_m not in c_no and clean_m not in c_notes:
                continue
        if search_odoo_s:
            clean_o = search_odoo_s.strip().lower()
            if not c_odoo or clean_o not in c_odoo.lower():
                continue
        if len(search_dates_s) == 2:
            start_d, end_d = search_dates_s
            try:
                c_date_parsed = datetime.datetime.strptime(c_date, "%Y-%m-%d").date()
                if not (start_d <= c_date_parsed <= end_d):
                    continue
            except:
                continue
        filtered_contracts_s.append(r)

    # Limit to 10 if search is not active
    if not is_search_active_s:
        filtered_contracts_s = filtered_contracts_s[:10]
        st.info("💡 تعرض القائمة أدناه آخر 10 عقود نشطة افتراضياً. للبحث عن عقود أقدم، استخدم لوحة البحث المتقدم بالرأس.")
    else:
        st.success(f"🔍 تم العثور على {len(filtered_contracts_s)} عقد مطابق لمعايير البحث.")

    # Create options list
    contract_opts = ["اختر عقداً..."] + [f"{r[1]} — {r[3]} ({r[2]})" for r in filtered_contracts_s]
    selected_contract_opt = st.selectbox("📋 اختر العقد المعني بالاستبيان *", contract_opts, key="survey_contract_select")
    
    if selected_contract_opt == "اختر عقداً...":
        return
        
    # Get selected contract row
    contract_idx = contract_opts.index(selected_contract_opt) - 1
    selected_row = filtered_contracts_s[contract_idx]
    cid, contract_no, title, client_name, client_phone, contract_date, start_date, end_date, value, status, notes, file_paths, created_by, created_at, last_mod_by, last_mod_at, odoo_no = selected_row
    
    # Check if there is an existing survey
    existing_survey = db.get_customer_survey(contract_no)
    
    default_d = 5
    default_t = 5
    default_r = 5
    default_s = 5
    default_o = 5
    default_fb = ""
    
    if existing_survey:
        st.success(f"ℹ️ تم تقديم هذا الاستبيان مسبقاً (بتاريخ {str(existing_survey[9])[:10] if existing_survey[9] else ''})")
        default_d = existing_survey[3]
        default_t = existing_survey[4]
        default_r = existing_survey[5]
        default_s = existing_survey[6]
        default_o = existing_survey[7]
        default_fb = existing_survey[8]
        
    with st.form("survey_form"):
        st.markdown("##### ⭐️ يرجى تحديد التقييم من 1 (ضعيف جداً) إلى 5 (ممتاز):")
        d_rating = st.slider("📐 جودة وتفاصيل التصاميم المقدمة", 1, 5, value=default_d)
        t_rating = st.slider("⏱️ الالتزام بالوقت والجدول الزمني للتنفيذ", 1, 5, value=default_t)
        r_rating = st.slider("📞 سرعة الاستجابة والتواصل الفعال من طاقم العمل", 1, 5, value=default_r)
        s_rating = st.slider("🛠️ مدى مطابقة الأعمال المنفذة للمواصفات المتفق عليها", 1, 5, value=default_s)
        o_rating = st.slider("🌟 التقييم العام لتجربتك مع شركة مساهوم", 1, 5, value=default_o)
        feedback = st.text_area("💬 ملاحظات ومقترحات إضافية لتحسين خدماتنا", value=default_fb, height=100)
        
        col1, col2 = st.columns(2)
        with col1:
            btn_save_survey = st.form_submit_button("💾 حفظ الاستبيان رقمياً", type="primary", use_container_width=True)
        with col2:
            btn_preview_survey = st.form_submit_button("👁️ معاينة وطباعة الاستبيان الورقي", type="secondary", use_container_width=True)
            
    if btn_save_survey:
        db.save_customer_survey(contract_no, client_name, d_rating, t_rating, r_rating, s_rating, o_rating, feedback.strip())
        st.session_state["contracts_success"] = f"✅ تم حفظ استبيان رضا العميل للعقد [{contract_no}] بنجاح!"
        db.log_activity(st.session_state.get('username', 'Unknown'), f"حفظ استبيان رضا العميل للعقد {contract_no}")
        st.rerun()
        
    # Preview logic
    if btn_preview_survey:
        st.session_state['preview_survey_data'] = {
            'contract_no': contract_no,
            'client_name': client_name,
            'design_rating': d_rating,
            'timeline_rating': t_rating,
            'response_rating': r_rating,
            'spec_rating': s_rating,
            'overall_rating': o_rating,
            'feedback': feedback.strip()
        }
        st.rerun()
        
    preview_survey = st.session_state.get('preview_survey_data', None)
    if preview_survey and preview_survey['contract_no'] == contract_no:
        st.markdown("---")
        st.markdown("<h4 style='color:#0077b6;'>📄 معاينة نموذج استبيان الرضا للطباعة</h4>", unsafe_allow_html=True)
        st.info("💡 للطباعة المباشرة، اضغط على زر Ctrl + P (أو Cmd + P على نظام الماك) لطباعة الاستبيان.")
        
        logo_base64 = ""
        if os.path.exists("logo.jpg"):
            with open("logo.jpg", "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
        
        logo_html = f'<img src="data:image/jpeg;base64,{logo_base64}" style="max-height:85px;"/>' if logo_base64 else '<span style="font-size:24px; font-weight:bold; color:#0077b6;">MASAR HOME</span>'
        
        def make_stars_html(rating):
            stars = ""
            for i in range(1, 6):
                if i <= rating:
                    stars += "★ "
                else:
                    stars += "☆ "
            return stars
            
        survey_html = f"""
        <div class="print-container" style="background-color: white; color: black; padding: 40px; border: 1px solid #ddd; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); font-family: 'Readex Pro', sans-serif; direction: rtl; text-align: right;">
            <!-- Header -->
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px;">
                <tr>
                    <td style="text-align: right; vertical-align: middle; width: 50%;">
                        <h2 style="margin: 0; color: #0077b6; font-size: 20px;">شركة مساهوم للتصميم والديكور</h2>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 13px;">استبيان وقياس رضا العملاء عن الخدمة</p>
                    </td>
                    <td style="text-align: left; vertical-align: middle; width: 50%;">
                        {logo_html}
                    </td>
                </tr>
            </table>
            <hr style="border: 1px solid #0077b6; margin-bottom: 25px;"/>
            
            <h3 style="text-align: center; color: #0077b6; margin-bottom: 30px; font-size: 20px;">نموذج استبيان رضا العميل</h3>
            
            <p style="font-size: 14px; line-height: 1.8; margin-bottom: 20px;">
                عزيزنا العميل <b>{preview_survey['client_name']}</b> (عقد رقم: <b>{preview_survey['contract_no']}</b>)،<br/>
                حرصاً منا على تحسين جودة خدماتنا وتقديم الأفضل لكم دائماً، يرجى ملء الاستبيان التالي لتقييم تجربتكم معنا:
            </p>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px; font-size: 14px; text-align: right;">
                <thead>
                    <tr style="background-color: #f0f7ff; color: #0077b6;">
                        <th style="border: 1px solid #ccc; padding: 10px; text-align: right; width: 60%;">معيار التقييم</th>
                        <th style="border: 1px solid #ccc; padding: 10px; text-align: center; width: 40%;">التقييم (1 إلى 5 نجوم)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;"><b>📐 جودة وتفاصيل التصاميم المقدمة:</b></td>
                        <td style="border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 16px; color: #f39c12;">{make_stars_html(preview_survey['design_rating'])}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;"><b>⏱️ الالتزام بالوقت والجدول الزمني للتنفيذ:</b></td>
                        <td style="border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 16px; color: #f39c12;">{make_stars_html(preview_survey['timeline_rating'])}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;"><b>📞 سرعة الاستجابة والتواصل الفعال من طاقم العمل:</b></td>
                        <td style="border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 16px; color: #f39c12;">{make_stars_html(preview_survey['response_rating'])}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;"><b>🛠️ مدى مطابقة الأعمال المنفذة للمواصفات المتفق عليها:</b></td>
                        <td style="border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 16px; color: #f39c12;">{make_stars_html(preview_survey['spec_rating'])}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ccc; padding: 10px;"><b>🌟 التقييم العام لتجربتك مع شركة مساهوم:</b></td>
                        <td style="border: 1px solid #ccc; padding: 10px; text-align: center; font-size: 16px; color: #f39c12;">{make_stars_html(preview_survey['overall_rating'])}</td>
                    </tr>
                </tbody>
            </table>
            
            <h4 style="color: #0077b6; margin-top: 20px; margin-bottom: 8px;">💬 ملاحظات ومقترحات إضافية:</h4>
            <div style="border: 1px solid #ccc; padding: 15px; border-radius: 4px; background-color: #fafafa; font-size: 13px; min-height: 80px; white-space: pre-wrap; line-height: 1.6; margin-bottom: 35px;">
                {preview_survey['feedback'] or '................................................................................................................................................................'}
            </div>
            
            <table style="width: 100%; border-collapse: collapse; margin-top: 35px; font-size: 13px;">
                <tr>
                    <td style="width: 50%; text-align: right;">
                        <b>اسم وتوقيع العميل:</b> ...................................................
                    </td>
                    <td style="width: 50%; text-align: left;">
                        <b>تاريخ ملء الاستبيان:</b> ....................................
                    </td>
                </tr>
            </table>
        </div>
        """
        st.markdown("""
        <style>
        @media print {
            body * {
                visibility: hidden;
            }
            .print-container, .print-container * {
                visibility: visible;
            }
            .print-container {
                position: absolute;
                left: 0;
                top: 0;
                width: 100%;
                border: none !important;
                box-shadow: none !important;
                padding: 0 !important;
                margin: 0 !important;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown(survey_html, unsafe_allow_html=True)
        
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            st.button("🖨️ طباعة الاستبيان مباشرة", key="print_survey_btn_sub", use_container_width=True)
        with col_act2:
            if st.button("❌ إغلاق المعاينة", key="close_survey_btn_sub", use_container_width=True):
                st.session_state.pop('preview_survey_data', None)
                st.rerun()

def render_page(can_access: bool, is_observer: bool, user_role: str = "", emp_name: str = ""):
    st.markdown(
        "<h2 style='text-align:center; color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>"
        "📋 مسار العقود</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>إدارة ومتابعة عقود العملاء والمشاريع.</p>"
        "<hr style='border-top:1px solid #caf0f8;'>",
        unsafe_allow_html=True,
    )

    if not can_access:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()

    is_admin = (user_role == "Admin")
    can_edit = not is_observer

    # عرض رسائل النجاح المخزنة في الجلسة
    if "contracts_success" in st.session_state:
        st.success(st.session_state.pop("contracts_success"))

    # ── إنشاء التبويبات الخمسة ──
    tab_clients, tab_add, tab_list, tab_termination, tab_survey = st.tabs([
        "👥 سجل العملاء",
        "➕ إضافة عقد جديد",
        "📋 استعراض سجل العقود",
        "📜 إشعار إنهاء التعاقد",
        "📊 استبيان رضا العميل"
    ])

    with tab_clients:
        _render_clients_tab()

    with tab_add:
        if can_edit:
            _render_add_tab(emp_name)
        else:
            st.warning("🔒 وضع القراءة فقط: لا يمكنك إضافة عقود جديدة.")

    with tab_list:
        _render_contracts_list_tab(can_edit=can_edit, is_admin=is_admin, emp_name=emp_name)

    with tab_termination:
        if can_edit:
            _render_termination_tab(emp_name)
        else:
            st.warning("🔒 وضع القراءة فقط: لا يمكنك إجراء إنهاء تعاقد.")

    with tab_survey:
        if can_edit:
            _render_survey_tab(emp_name)
        else:
            st.warning("🔒 وضع القراءة فقط: لا يمكنك تعبئة استبيان الرضا.")

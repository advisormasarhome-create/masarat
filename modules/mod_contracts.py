"""
mod_contracts.py  —  مسار العقود
إدارة عقود العملاء والمشاريع: سجل العملاء، إضافة عقد، استعراض وعمليات العقود.
"""

import streamlit as st
import datetime
import os
import database as db

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
               COALESCE(d.price_final, 0.0), COALESCE(d.odoo_no, ''), COALESCE(d.design_docs, ''), COALESCE(d.workshop_drawing, ''), COALESCE(d.notes, '')
        FROM FieldVisits f
        INNER JOIN ProjectDesigns d ON f.id = d.visit_id AND d.price_is_paid = 1 AND d.contract_is_approved = 0
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    clients = c.fetchall()
    conn.close()

    if not clients:
        st.info("ℹ️ لا يوجد عملاء بانتظار التعاقد حالياً (العملاء يظهرون هنا تلقائياً بعد اعتماد التسعيرة في مسار التصاميم).")
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
                st.session_state['selected_client_design_docs'] = design_docs
                st.session_state['selected_client_workshop'] = workshop
                st.session_state['selected_client_design_notes'] = design_notes
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
    default_design_docs = st.session_state.get('selected_client_design_docs', "")
    default_workshop = st.session_state.get('selected_client_workshop', "")
    default_design_notes = st.session_state.get('selected_client_design_notes', "")
    
    if default_name:
        st.info(f"💡 تم تعبئة البيانات تلقائياً للعميل المختار: **{default_name}**")
        if st.button("❌ إلغاء تحديد العميل"):
            st.session_state.pop('selected_client_visit_id', None)
            st.session_state.pop('selected_client_name', None)
            st.session_state.pop('selected_client_phone', None)
            st.session_state.pop('selected_client_value', None)
            st.session_state.pop('selected_client_odoo_no', None)
            st.session_state.pop('selected_client_design_docs', None)
            st.session_state.pop('selected_client_workshop', None)
            st.session_state.pop('selected_client_design_notes', None)
            st.rerun()

    with st.form("add_contract_form", clear_on_submit=True):
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

        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("#### استدعاء المواصفات الفنية المؤرشفة")
        if default_design_notes:
            st.info(f"**ملاحظات التصميم:** {default_design_notes}")
        if default_design_docs:
            st.markdown(f"📄 **المخطط الرئيسي:** [عرض الملف]({default_design_docs})")
        if default_workshop:
            st.markdown(f"🏭 **مخطط الورشة:** [عرض الملف]({default_workshop})")
        if not default_design_docs and not default_workshop and not default_design_notes:
            st.warning("لا توجد مواصفات فنية مرفقة من قسم التصميم.")
        st.markdown("<hr>", unsafe_allow_html=True)

        notes = st.text_area("📋 ملاحظات إضافية للعقد", height=80)
        attachments = st.file_uploader(
            "📎 مرفقات العقد (PDF / صور)",
            accept_multiple_files=True,
            type=["pdf", "png", "jpg", "jpeg", "docx"],
        )

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            btn_save = st.form_submit_button("💾 حفظ العقد", type="secondary", use_container_width=True)
        with c_btn2:
            btn_approve = st.form_submit_button("💾 حفظ واعتماد العقد (للخزينة)", type="primary", use_container_width=True)

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
                c.execute("UPDATE ProjectDesigns SET contract_is_approved = 1, is_sent_to_production = 1 WHERE visit_id = ?", (default_visit_id,))
                conn.commit()
                conn.close()

            # إزالة العميل المحدد من الجلسة بعد الحفظ الناجح
            st.session_state.pop('selected_client_visit_id', None)
            st.session_state.pop('selected_client_name', None)
            st.session_state.pop('selected_client_phone', None)
            st.session_state.pop('selected_client_value', None)
            st.session_state.pop('selected_client_odoo_no', None)
            st.session_state.pop('selected_client_design_docs', None)
            st.session_state.pop('selected_client_workshop', None)
            st.session_state.pop('selected_client_design_notes', None)
            if btn_approve:
                st.session_state["contracts_success"] = f"✅ تم حفظ واعتماد العقد [{contract_no}] بنجاح ونقله للخزينة!"
            else:
                st.session_state["contracts_success"] = f"✅ تم حفظ سجل العقد [{contract_no}] بنجاح!"
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

        with action_col:
            if can_edit:
                if st.button("✏️ تعديل سجل", key=f"edit_btn_{cid}", use_container_width=True):
                    st.session_state[f"edit_contract_{cid}"] = True
                if is_admin:
                    if st.button("🗑️ حذف سجل", key=f"del_btn_{cid}", use_container_width=True):
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
        if st.session_state.get(f"edit_contract_{cid}") and can_edit:
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

    # ── إنشاء التبويبات الثلاثة ──
    # 1. سجل العملاء
    # 2. إضافة عقد جديد
    # 3. استعراض سجل العقود
    tab_clients, tab_add, tab_list = st.tabs([
        "👥 سجل العملاء",
        "➕ إضافة عقد جديد",
        "📋 استعراض سجل العقود"
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

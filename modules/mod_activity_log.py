import streamlit as st
import pandas as pd
import datetime
import database as db


def render_page(user_role):
    if user_role != "Admin":
        st.error("🔒 هذا القسم مخصص للمدير فقط.")
        st.stop()

    # ── Header ──────────────────────────────────────────────────────
    st.markdown("""
    <div style='background: linear-gradient(135deg, #0077b6 0%, #023e8a 100%);
                padding: 16px 28px; border-radius: 12px; margin-bottom: 25px;
                display: flex; align-items: center; gap: 14px;'>
        <span style='font-size: 30px;'>🔍</span>
        <div>
            <div style='font-family:"Readex Pro",sans-serif; font-weight:700;
                        color:white; font-size:22px;'>
                مسار حركة المستخدم
            </div>
            <div style='font-family:"Readex Pro",sans-serif; font-weight:300;
                        color:#caf0f8; font-size:13px; margin-top:3px;'>
                سجل كامل لجميع حركات المستخدمين — للمدير فقط
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load user mapping ─────────────────────────────────────────────
    import sys, os, importlib
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import database as _db
    importlib.reload(_db)

    u_to_e, e_to_u = _db.get_users_map()
    all_usernames  = ["الكل"] + list(u_to_e.keys())
    all_employees  = ["الكل"] + list(e_to_u.keys())

    # ── Callbacks for Dropdown Sync ──────────────────────────────────
    def sync_user():
        u_val = st.session_state.log_user_sel
        if u_val == "الكل":
            st.session_state.log_emp_sel = "الكل"
        elif u_val in u_to_e:
            st.session_state.log_emp_sel = u_to_e[u_val]

    def sync_emp():
        e_val = st.session_state.log_emp_sel
        if e_val == "الكل":
            st.session_state.log_user_sel = "الكل"
        elif e_val in e_to_u:
            st.session_state.log_user_sel = e_to_u[e_val]

    # ── Filters ──────────────────────────────────────────────────────
    st.markdown("### 🔽 خيارات الفرز والتصفية")
    col1, col2 = st.columns(2)

    with col1:
        today = datetime.date.today()
        date_from = st.date_input("📅 من تاريخ", value=today - datetime.timedelta(days=30))
    with col2:
        date_to = st.date_input("📅 إلى تاريخ", value=today)

    col3, col4 = st.columns(2)

    with col3:
        user_sel = st.selectbox("👤 اسم المستخدم (في النظام)", all_usernames,
                                key="log_user_sel", on_change=sync_user)

    with col4:
        emp_sel = st.selectbox("📛 اسم الموظف (الحقيقي)", all_employees,
                               key="log_emp_sel", on_change=sync_emp)

    resolved_username = user_sel if user_sel != "الكل" else "الكل"

    col5, col6 = st.columns(2)
    with col5:
        action_types = [
            "الكل", "تسجيل دخول", "تسجيل خروج",
            "إضافة", "تعديل", "حذف", "حفظ",
            "رفع مستند", "تغيير كلمة المرور",
            "تم التواصل", "لم يتم التواصل", "إنشاء تذكرة", "تحديث حالة تذكرة",
        ]
        action_filter = st.selectbox("⚡ نوع الحركة", action_types)

    with col6:
        modules_list = [
            "الكل", "تسجيل الدخول", "تنبيهات المواعيد",
            "مسار الفحص اليومي", "مسار رفع المقاسات",
            "مسار التصاميم", "مسار الانتاج", "مسار الخزينة",
            "مسار العملاء", "مسار الدعم الفني",
            "مسار حركة العميل", "إحصائيات", "إدارة الحسابات",
        ]
        module_filter = st.selectbox("📂 القسم", modules_list)

    st.button("🔄 تحديث النتائج", use_container_width=False)
    st.markdown("---")

    # ── Fetch & Display ───────────────────────────────────────────────
    logs = db.get_activity_logs(
        date_from=date_from,
        date_to=date_to,
        username_filter=resolved_username,
        action_type_filter=action_filter,
        module_filter=module_filter,
    )

    if not logs:
        st.info("📭 لا توجد حركات مسجلة تطابق معايير البحث.")
    else:
        total = len(logs)
        st.markdown(
            f"<div style='background:#e0fbfc; border-right:4px solid #0077b6; "
            f"padding:10px 16px; border-radius:8px; margin-bottom:16px; "
            f"font-family:\"Readex Pro\",sans-serif; font-weight:400; color:#023e8a;'>"
            f"📊 إجمالي النتائج: <b>{total}</b> حركة</div>",
            unsafe_allow_html=True,
        )

        df = pd.DataFrame(
            logs,
            columns=["#", "المستخدم", "الموظف", "نوع الحركة", "القسم", "التفاصيل", "التوقيت"],
        )
        # Overwrite # column with a clean sequence
        df["#"] = range(1, len(df) + 1)
        # Reverse columns for RTL visual order (right to left: #, المستخدم, الموظف, نوع الحركة, القسم, التفاصيل, التوقيت)
        df = df[["التوقيت", "التفاصيل", "القسم", "نوع الحركة", "الموظف", "المستخدم", "#"]]

        # Colour-code action type column via pandas styler
        ACTION_COLORS = {
            "تسجيل دخول":          "#d4edda",
            "تسجيل خروج":          "#fff3cd",
            "إضافة":               "#cce5ff",
            "حفظ":                 "#cce5ff",
            "رفع مستند":           "#cce5ff",
            "إنشاء تذكرة":         "#cce5ff",
            "تعديل":               "#ffeeba",
            "تحديث حالة تذكرة":    "#ffeeba",
            "تم التواصل":          "#ffeeba",
            "حذف":                 "#f8d7da",
            "تغيير كلمة المرور":   "#e2d9f3",
        }

        def highlight_action(row):
            color = ACTION_COLORS.get(row["نوع الحركة"], "#ffffff")
            return [f"background-color: {color}" if col == "نوع الحركة" else "" for col in row.index]

        styled_df = df.style.apply(highlight_action, axis=1)

        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
        )

        # ── Export CSV ──────────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        csv_data = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="⬇️ تصدير السجل كملف Excel / CSV",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"activity_log_{date_from}_to_{date_to}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ── Admin Clear Logs ──────────────────────────────────────────────
    st.markdown("---")
    with st.expander("🗑️ حذف السجلات القديمة (للمدير فقط)"):
        st.warning("⚠️ هذا الإجراء لا يمكن التراجع عنه.")
        c1, c2 = st.columns(2)
        with c1:
            days_old = st.number_input("احذف السجلات الأقدم من (يوم):", min_value=1, value=90, step=1)
            if st.button("🗑️ حذف السجلات القديمة", use_container_width=True):
                deleted = db.clear_activity_logs(days_older_than=int(days_old))
                st.success(f"تم حذف {deleted} سجل قديم.")
                st.rerun()
        with c2:
            if st.button("🚨 حذف جميع السجلات نهائياً", use_container_width=True, type="primary"):
                deleted = db.clear_activity_logs()
                st.success(f"تم مسح {deleted} سجل من قاعدة البيانات.")
                st.rerun()

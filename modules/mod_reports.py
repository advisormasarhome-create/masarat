import streamlit as st
import pandas as pd
import database as db
import datetime
import io

def render_page(can_access: bool, is_observer: bool):
    if not can_access:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()

    st.markdown(
        "<h2 style='text-align:center; color:#0077b6; font-family:\"Readex Pro\",sans-serif;'>"
        "📊 مسار التقارير والتحليلات</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='text-align:center; color:gray;'>استخراج ومتابعة التقارير المالية والتشغيلية والتاريخية لمنظومة مسارات.</p>"
        "<hr style='border-top:1px solid #caf0f8;'>",
        unsafe_allow_html=True,
    )

    tab_financial, tab_technical, tab_logs, tab_surveys = st.tabs([
        "💰 التقارير المالية والتعاقدية",
        "📐 تقارير الفحص والزيارات الفنية",
        "📋 تقارير الالتزام ونشاط النظام",
        "📈 تقارير رضا العملاء والاستبيانات"
    ])

    # ────────────────────────────────────────────────
    # 1. التقارير المالية والتعاقدية
    # ────────────────────────────────────────────────
    with tab_financial:
        st.markdown("### 💰 تقرير العقود والمبيعات")
        
        # Fetch all contracts
        contracts = db.get_all_contracts()
        if not contracts:
            st.info("📭 لا توجد عقود مسجلة لاستخراج التقارير المالية حالياً.")
        else:
            # Convert to DataFrame
            # (id, contract_no, title, client_name, client_phone, contract_date, start_date, end_date, value, status, notes, file_paths, created_by, created_at, last_mod_by, last_mod_at, odoo_no)
            columns = [
                "معرف", "رقم العقد", "موضوع العقد", "اسم العميل", "رقم الهاتف",
                "تاريخ الإبرام", "تاريخ البدء", "تاريخ الانتهاء", "القيمة (د.ل)",
                "الحالة", "ملاحظات", "الملفات", "أنشئ بواسطة", "تاريخ الإنشاء",
                "عُدل بواسطة", "تاريخ التعديل", "رقم أودو"
            ]
            df_contracts = pd.DataFrame(contracts, columns=columns)
            
            # Filters
            st.markdown("#### 🔍 فلاتر البحث والترشيح")
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                search_q = st.text_input("🔎 بحث باسم العميل أو رقم العقد/أودو:", placeholder="ابحث هنا...", key="search_fin")
            with f_col2:
                # Range date selector
                min_date = datetime.date(2025, 1, 1)
                max_date = datetime.date.today() + datetime.timedelta(days=365)
                date_range = st.date_input("📅 نطاق تاريخ العقد (من - إلى):", value=(min_date, max_date), key="date_fin")
            with f_col3:
                status_opts = ["الكل"] + sorted(list(df_contracts["الحالة"].unique()))
                filter_status = st.selectbox("📌 حالة العقد:", status_opts, key="status_fin")

            # Apply filters
            df_filtered = df_contracts.copy()
            if search_q.strip():
                q = search_q.strip().lower()
                df_filtered = df_filtered[
                    df_filtered["اسم العميل"].str.lower().str.contains(q) |
                    df_filtered["رقم العقد"].str.lower().str.contains(q) |
                    df_filtered["رقم أودو"].str.lower().str.contains(q)
                ]
            
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_f, end_f = date_range
                df_filtered["ParsedDate"] = pd.to_datetime(df_filtered["تاريخ الإبرام"], errors='coerce').dt.date
                df_filtered = df_filtered[
                    (df_filtered["ParsedDate"] >= start_f) & 
                    (df_filtered["ParsedDate"] <= end_f)
                ]
                df_filtered = df_filtered.drop(columns=["ParsedDate"])
                
            if filter_status != "الكل":
                df_filtered = df_filtered[df_filtered["الحالة"] == filter_status]

            # Financial Metrics
            total_val = df_filtered["القيمة (د.ل)"].sum()
            avg_val = df_filtered["القيمة (د.ل)"].mean() if len(df_filtered) > 0 else 0
            total_contracts = len(df_filtered)
            
            m_col1, m_col2, m_col3 = st.columns(3)
            m_col1.metric("💰 إجمالي المبيعات المتعاقد عليها", f"{total_val:,.2f} د.ل")
            m_col2.metric("📊 متوسط قيمة العقد الواحد", f"{avg_val:,.2f} د.ل")
            m_col3.metric("📝 عدد العقود المطابقة للفلتر", f"{total_contracts} عقد")

            # Table view
            st.markdown("#### 📋 السجلات المطابقة")
            # Re-order columns for RTL friendly UI representation
            display_cols = ["رقم أودو", "أنشئ بواسطة", "الحالة", "القيمة (د.ل)", "تاريخ الإبرام", "اسم العميل", "موضوع العقد", "رقم العقد"]
            st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)
            
            # Export Report
            csv_data = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تصدير التقرير المالي كـ Excel/CSV",
                data=csv_data,
                file_name=f"financial_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )

            # Analytics / Visuals
            st.markdown("#### 📈 التحليل البياني للعقود")
            ch_col1, ch_col2 = st.columns(2)
            with ch_col1:
                st.markdown("<p style='text-align: center; font-weight: bold;'>توزيع قيم العقود حسب الحالة</p>", unsafe_allow_html=True)
                val_by_status = df_filtered.groupby("الحالة")["القيمة (د.ل)"].sum()
                st.bar_chart(val_by_status)
            with ch_col2:
                st.markdown("<p style='text-align: center; font-weight: bold;'>عدد العقود المبرمة حسب الموظف</p>", unsafe_allow_html=True)
                cnt_by_employee = df_filtered["أنشئ بواسطة"].value_counts()
                st.bar_chart(cnt_by_employee)

    # ────────────────────────────────────────────────
    # 2. تقارير الفحص والزيارات الفنية
    # ────────────────────────────────────────────────
    with tab_technical:
        st.markdown("### 📐 تقرير رفع المقاسات وتصميم المشاريع")
        
        # Query joined visits & designs
        conn = db.get_connection()
        query = """
            SELECT 
                f.id, f.customer_name, f.phone, f.address, f.furniture_type, 
                f.visit_date, f.measurement_completed, f.measurement_reason,
                d.designer_name, d.status, d.design_value, d.price_final, d.edit_count
            FROM FieldVisits f
            LEFT JOIN ProjectDesigns d ON f.id = d.visit_id
        """
        df_tech = pd.read_sql_query(query, conn)
        conn.close()
        
        if df_tech.empty:
            st.info("ℹ️ لا توجد بيانات زيارات أو مشاريع كافية لعرضها.")
        else:
            # Rename columns to Arabic for presentation
            df_tech.columns = [
                "رقم مسارات", "اسم العميل", "رقم الهاتف", "العنوان", "نوع الأثاث",
                "تاريخ الزيارة", "رفع المقاسات", "سبب عدم الاتمام",
                "المصمم المسؤول", "حالة التصميم", "قيمة التصميم (د.ل)", "السعر النهائي المعتمد (د.ل)", "مرات التعديل"
            ]
            
            # Default values filling
            df_tech["المصمم المسؤول"] = df_tech["المصمم المسؤول"].fillna("غير معين")
            df_tech["حالة التصميم"] = df_tech["حالة التصميم"].fillna("لم يبدأ")
            df_tech["قيمة التصميم (د.ل)"] = df_tech["قيمة التصميم (د.ل)"].fillna(0.0)
            df_tech["السعر النهائي المعتمد (د.ل)"] = df_tech["السعر النهائي المعتمد (د.ل)"].fillna(0.0)
            df_tech["مرات التعديل"] = df_tech["مرات التعديل"].fillna(0).astype(int)
            
            st.markdown("#### 🔍 فلاتر البحث والترشيح")
            t_col1, t_col2, t_col3 = st.columns(3)
            with t_col1:
                search_t = st.text_input("🔎 بحث باسم العميل أو نوع الأثاث:", placeholder="ابحث هنا...", key="search_tech")
            with t_col2:
                designers = ["الكل"] + sorted(list(df_tech["المصمم المسؤول"].unique()))
                filter_des = st.selectbox("🎨 المصمم المسؤول:", designers, key="des_tech")
            with t_col3:
                m_statuses = ["الكل", "نعم", "لا", "ليس بعد"]
                filter_meas = st.selectbox("📐 حالة رفع المقاسات:", m_statuses, key="meas_tech")
                
            # Apply filters
            df_tech_filtered = df_tech.copy()
            if search_t.strip():
                qt = search_t.strip().lower()
                df_tech_filtered = df_tech_filtered[
                    df_tech_filtered["اسم العميل"].str.lower().str.contains(qt) |
                    df_tech_filtered["نوع الأثاث"].str.lower().str.contains(qt)
                ]
            if filter_des != "الكل":
                df_tech_filtered = df_tech_filtered[df_tech_filtered["المصمم المسؤول"] == filter_des]
            if filter_meas != "الكل":
                df_tech_filtered = df_tech_filtered[df_tech_filtered["رفع المقاسات"] == filter_meas]
                
            # Tech Metrics
            total_designs = len(df_tech_filtered)
            success_meas = len(df_tech_filtered[df_tech_filtered["رفع المقاسات"] == "نعم"])
            avg_edits = df_tech_filtered["مرات التعديل"].mean() if total_designs > 0 else 0
            
            tm_col1, tm_col2, tm_col3 = st.columns(3)
            tm_col1.metric("📂 إجمالي المشاريع الفنية", f"{total_designs} مشروع")
            tm_col2.metric("📐 مقاسات تم رفعها بنجاح", f"{success_meas} مشروع")
            tm_col3.metric("🔄 متوسط عدد مرات التعديل", f"{avg_edits:.1f} تعديل")
            
            # Show Table
            st.markdown("#### 📋 المشاريع والزيارات المطابقة")
            disp_tech_cols = [
                "السعر النهائي المعتمد (د.ل)", "مرات التعديل", "حالة التصميم", 
                "المصمم المسؤول", "رفع المقاسات", "نوع الأثاث", "اسم العميل", "رقم مسارات"
            ]
            st.dataframe(df_tech_filtered[disp_tech_cols], use_container_width=True, hide_index=True)
            
            # Export Button
            csv_tech_data = df_tech_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تصدير التقرير الفني كـ Excel/CSV",
                data=csv_tech_data,
                file_name=f"technical_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
            # Visuals
            st.markdown("#### 📈 التحليل الفني للمشاريع")
            tch1, tch2 = st.columns(2)
            with tch1:
                st.markdown("<p style='text-align: center; font-weight: bold;'>عبء العمل (عدد المشاريع لكل مصمم)</p>", unsafe_allow_html=True)
                workload = df_tech_filtered["المصمم المسؤول"].value_counts()
                st.bar_chart(workload)
            with tch2:
                st.markdown("<p style='text-align: center; font-weight: bold;'>توزيع مشاريع التصاميم حسب الحالة</p>", unsafe_allow_html=True)
                design_stat_cnt = df_tech_filtered["حالة التصميم"].value_counts()
                st.bar_chart(design_stat_cnt)

    # ────────────────────────────────────────────────
    # 3. تقارير الالتزام ونشاط النظام
    # ────────────────────────────────────────────────
    with tab_logs:
        st.markdown("### 📋 سجلات نشاط النظام والفحص اليومي")
        
        log_type = st.radio("اختر التقرير المطلوب:", ["سجلات حركة المستخدمين", "سجلات الفحص والالتزام اليومي"], horizontal=True)
        
        conn = db.get_connection()
        
        if log_type == "سجلات حركة المستخدمين":
            # Fetch ActivityLog
            query_log = "SELECT username, employee_name, action_type, module, details, timestamp FROM ActivityLog ORDER BY timestamp DESC"
            df_logs = pd.read_sql_query(query_log, conn)
            conn.close()
            
            if df_logs.empty:
                st.info("ℹ️ لا توجد حركات مسجلة للمستخدمين حتى الآن.")
            else:
                df_logs.columns = ["اسم المستخدم", "اسم الموظف", "نوع الإجراء", "القسم / المسار", "التفاصيل", "تاريخ ووقت الحركة"]
                
                st.markdown("#### 🔍 تصفية الحركات")
                l_col1, l_col2 = st.columns(2)
                with l_col1:
                    emp_opt = ["الكل"] + sorted(list(df_logs["اسم الموظف"].unique()))
                    filter_emp = st.selectbox("👤 اسم الموظف:", emp_opt, key="emp_log")
                with l_col2:
                    action_opt = ["الكل"] + sorted(list(df_logs["نوع الإجراء"].unique()))
                    filter_act = st.selectbox("⚡ نوع الإجراء:", action_opt, key="act_log")
                
                # Apply filter
                df_logs_filtered = df_logs.copy()
                if filter_emp != "الكل":
                    df_logs_filtered = df_logs_filtered[df_logs_filtered["اسم الموظف"] == filter_emp]
                if filter_act != "الكل":
                    df_logs_filtered = df_logs_filtered[df_logs_filtered["نوع الإجراء"] == filter_act]
                    
                st.dataframe(df_logs_filtered, use_container_width=True, hide_index=True)
                
                # Export
                csv_log_data = df_logs_filtered.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تصدير سجلات حركة الموظفين كـ Excel/CSV",
                    data=csv_log_data,
                    file_name=f"user_activity_log_{datetime.date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                
        else: # Daily Checklist
            query_chk = "SELECT date, employee_name, clean_showroom, showroom_display, notes, created_at FROM DailyChecklist ORDER BY date DESC"
            df_chk = pd.read_sql_query(query_chk, conn)
            conn.close()
            
            if df_chk.empty:
                st.info("ℹ️ لا توجد سجلات فحص يومي مسجلة بعد.")
            else:
                df_chk.columns = ["التاريخ", "اسم الموظف", "نظافة الصالة", "وضعية المعروضات", "ملاحظات الفحص", "سجل في"]
                
                st.markdown("#### 🔍 تصفية سجلات الفحص")
                c_col1 = st.columns(1)[0]
                with c_col1:
                    chk_emp_opt = ["الكل"] + sorted(list(df_chk["اسم الموظف"].unique()))
                    filter_chk_emp = st.selectbox("👤 اسم الموظف المسؤول:", chk_emp_opt, key="emp_chk")
                
                df_chk_filtered = df_chk.copy()
                if filter_chk_emp != "الكل":
                    df_chk_filtered = df_chk_filtered[df_chk_filtered["اسم الموظف"] == filter_chk_emp]
                    
                st.dataframe(df_chk_filtered, use_container_width=True, hide_index=True)
                
                # Export
                csv_chk_data = df_chk_filtered.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تصدير سجلات الفحص اليومي كـ Excel/CSV",
                    data=csv_chk_data,
                    file_name=f"daily_checklist_report_{datetime.date.today().isoformat()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # ────────────────────────────────────────────────
    # 4. تقارير رضا العملاء والاستبيانات
    # ────────────────────────────────────────────────
    with tab_surveys:
        st.markdown("### 📈 تقارير استبيانات رضا العملاء")
        surveys = db.get_all_surveys()
        if not surveys:
            st.info("📭 لا توجد استبيانات رضا عملاء مسجلة حتى الآن.")
        else:
            survey_cols = [
                "معرف", "رقم العقد", "اسم العميل", "تقييم التصميم", "تقييم الالتزام بالوقت", 
                "تقييم سرعة الاستجابة", "تقييم مطابقة المواصفات", "التقييم العام", "الملاحظات والمقترحات", "تاريخ المشاركة"
            ]
            df_surveys = pd.DataFrame(surveys, columns=survey_cols)
            
            avg_design = df_surveys["تقييم التصميم"].mean()
            avg_time = df_surveys["تقييم الالتزام بالوقت"].mean()
            avg_resp = df_surveys["تقييم سرعة الاستجابة"].mean()
            avg_spec = df_surveys["تقييم مطابقة المواصفات"].mean()
            avg_overall = df_surveys["التقييم العام"].mean()
            total_surveys = len(df_surveys)
            
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("📐 تقييم التصاميم", f"{avg_design:.2f} / 5")
            m_col2.metric("⏱️ تقييم الالتزام", f"{avg_time:.2f} / 5")
            m_col3.metric("📞 تقييم الاستجابة", f"{avg_resp:.2f} / 5")
            m_col4.metric("🛠️ مطابقة المواصفات", f"{avg_spec:.2f} / 5")
            m_col5.metric("🌟 التقييم العام", f"{avg_overall:.2f} / 5")
            
            st.markdown(f"**عدد الاستبيانات المستلمة:** {total_surveys} استبيان")
            
            avg_series = pd.Series({
                "جودة التصميم": avg_design,
                "الالتزام بالوقت": avg_time,
                "سرعة الاستجابة": avg_resp,
                "مطابقة المواصفات": avg_spec,
                "التقييم العام": avg_overall
            })
            st.markdown("##### 📊 متوسط التقييمات لكل معيار")
            st.bar_chart(avg_series)
            
            st.markdown("##### 📋 تفاصيل الاستبيانات والملاحظات")
            st.dataframe(df_surveys[["تاريخ المشاركة", "اسم العميل", "رقم العقد", "التقييم العام", "الملاحظات والمقترحات"]], use_container_width=True, hide_index=True)
            
            csv_survey_data = df_surveys.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 تصدير استبيانات رضا العملاء كـ Excel/CSV",
                data=csv_survey_data,
                file_name=f"customer_surveys_report_{datetime.date.today().isoformat()}.csv",
                mime="text/csv",
                use_container_width=True
            )

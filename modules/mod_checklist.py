import streamlit as st
import datetime
import database as db

def render_page(can_access_checklist, is_observer):
    if not can_access_checklist:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    col_title, col_date = st.columns([2, 1])
    with col_title:
        st.markdown("<h2>✅ قائمة التحقق اليومية (Daily Checklist)</h2>", unsafe_allow_html=True)
    with col_date:
        all_dates = db.get_all_checklist_dates()
        options = ["اليوم (قائمة جديدة/حالية)"] + all_dates
        choice_date = st.selectbox("📅 استعراض أو إنشاء قائمة:", options)
        
        if choice_date == "اليوم (قائمة جديدة/حالية)":
            selected_date = st.date_input("أو اختر تاريخاً يدوياً:", value=datetime.date.today())
            date_str = selected_date.strftime("%Y-%m-%d")
        else:
            date_str = choice_date
            st.info(f"📌 عرض قائمة يوم: {date_str}")

    # Load existing checklist for the selected date
    cl_data = db.get_checklist(date_str)
    if cl_data:
        _, vm1, vm2, vm3, vm4, vmn, vd1, vd2, vd3, vd4, vdn, ve1, ve2, ve3, ve4, ven = cl_data
    else:
        vm1 = vm2 = vm3 = vm4 = vd1 = vd2 = vd3 = vd4 = ve1 = ve2 = ve3 = ve4 = 0
        vmn = vdn = ven = ""
        
    def render_check_row(text, val, key_prefix):
        col_desc, col_yes, col_no = st.columns([6, 1, 1])
        col_desc.write(text)
        with col_yes:
            y_check = st.checkbox(" ", value=(val == 1), key=f"{key_prefix}_y", label_visibility="collapsed")
        with col_no:
            n_check = st.checkbox(" ", value=(val == 2), key=f"{key_prefix}_n", label_visibility="collapsed")
        if y_check: return 1
        if n_check: return 2
        return 0

    def render_header():
        col_desc, col_yes, col_no = st.columns([6, 1, 1])
        col_desc.write("")
        col_yes.markdown("<div style='text-align: right; color:#0077b6; font-weight:bold; margin-bottom:10px;'>نعم</div>", unsafe_allow_html=True)
        col_no.markdown("<div style='text-align: right; color:#0077b6; font-weight:bold; margin-bottom:10px;'>لا</div>", unsafe_allow_html=True)

    st.markdown("<h3>🌅 فترة الصباح (الافتتاح)</h3>", unsafe_allow_html=True)
    render_header()
    m1 = render_check_row("1. مراجعة بصمة الحضور والانصراف والتأكد من تواجد جميع الموظفين في مواقعهم.", vm1, "m1")
    m2 = render_check_row("2. جولة تفتيشية على نظافة الصالة، الإضاءة، التكييف، وترتيب المعروضات.", vm2, "m2")
    m3 = render_check_row("3. فحص حالة المنتجات المعروضة والتأكد من عدم وجود أي خدوش أو تلفيات تتطلب صيانة فنية.", vm3, "m3")
    m4 = render_check_row("4. عقد اجتماع صباحي سريع (5 دقائق) لاستعراض هدف المبيعات اليومي.", vm4, "m4")
    m_notes = st.text_area("ملاحظات فترة الصباح (من قبل مدير النظام)", value=vmn if vmn else "", height=80)
    
    st.markdown("---")
    st.markdown("<h3>☀️ خلال اليوم (التشغيل)</h3>", unsafe_allow_html=True)
    render_header()
    d1 = render_check_row("1. الإشراف على إعداد العقود الجديدة وتدقيق بياناتها الفنية والمالية.", vd1, "d1")
    d2 = render_check_row("2. متابعة حركة الزوار وتحليل التفاعل مع فريق المبيعات.", vd2, "d2")
    d3 = render_check_row("3. معالجة أي شكوى عميل تظهر بشكل فوري.", vd3, "d3")
    d4 = render_check_row("4. التنسيق مع المصنع بشأن طلبيات اليوم أو تحديثات التوريد.", vd4, "d4")
    d_notes = st.text_area("ملاحظات خلال اليوم (من قبل مدير النظام)", value=vdn if vdn else "", height=80)
    
    st.markdown("---")
    st.markdown("<h3>🌙 فترة المساء (الإغلاق)</h3>", unsafe_allow_html=True)
    render_header()
    e1 = render_check_row("1. مطابقة المبالغ النقدية (الكاش) المحصلة مع فواتير وعقود اليوم.", ve1, "e1")
    e2 = render_check_row("2. التأكد من أرشفة النسخ الورقية من العقود في ملفاتها المخصصة.", ve2, "e2")
    e3 = render_check_row("3. إرسال التقرير اليومي عبر البريد الإلكتروني للإدارة العليا.", ve3, "e3")
    e4 = render_check_row("4. التأكد من إطفاء الأنظمة غير الضرورية وتأمين الصالة.", ve4, "e4")
    e_notes = st.text_area("ملاحظات فترة المساء (من قبل مدير النظام)", value=ven if ven else "", height=80)

    st.markdown("---")
    if is_observer:
        st.info("وضع القراءة فقط: لا يمكنك حفظ بيانات الفحص.")
    elif st.button("💾 حفظ القائمة لهذا اليوم", use_container_width=True):
        db.save_checklist(date_str, int(m1), int(m2), int(m3), int(m4), m_notes,
                                    int(d1), int(d2), int(d3), int(d4), d_notes,
                                    int(e1), int(e2), int(e3), int(e4), e_notes)
        db.log_activity(
            username=st.session_state.get('username', 'Unknown'),
            employee_name=st.session_state.get('employee_name', 'Unknown'),
            action_type="إضافة",
            module="مسار الفحص اليومي",
            details=f"تم حفظ القائمة الخاصة بيوم: {date_str}"
        )
        st.session_state.success_msg = f"تم حفظ قائمة الفحص بنجاح ليوم {date_str}!"
        st.rerun()

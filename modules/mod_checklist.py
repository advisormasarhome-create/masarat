import streamlit as st
# Checklist version 1.2.0: Added references to contract completion tasks
import datetime
import database as db
import textwrap

def render_page(can_access_checklist, is_observer):
    if not can_access_checklist:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    tab_checklist, tab_maintenance, tab_ration = st.tabs([
        "📋 قائمة التحقق اليومية", 
        "🛠️ استمارة طلب صيانة", 
        "☕ طلب الراشن الشهري"
    ])
    
    with tab_checklist:
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

    with tab_maintenance:
        st.markdown("<h3 style='color: #023e8a; font-family: \"Readex Pro\", sans-serif; font-weight:700;'>🛠️ استمارة طلب صيانة صالة العرض</h3>", unsafe_allow_html=True)
        st.markdown("يرجى تعبئة النموذج أدناه لوصف المشكلة وتقديم طلب صيانة فني للمدير العام:")
        
        # Reset state button if already submitted
        if st.session_state.get('maint_form_submitted'):
            if st.button("🆕 إنشاء طلب صيانة جديد", type="primary"):
                st.session_state.pop('maint_form_submitted', None)
                st.session_state.pop('maint_prob', None)
                st.session_state.pop('maint_type', None)
                st.session_state.pop('maint_correction', None)
                st.rerun()
        
        if not st.session_state.get('maint_form_submitted'):
            with st.form("maintenance_form"):
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    maint_prob = st.text_input("المشكلة التي تحتاج إلى صيانة *", placeholder="مثال: تعطل مكيف الهواء في الصالة")
                with col_m2:
                    maint_type = st.selectbox("نوع المشكلة *", ["أعمال كهربائية", "أجهزة تكييف وصحي", "أثاث ومعروضات وتلفيات", "نظافة وصحة عامة", "شبكات وحاسوب وإنترنت", "أخرى"])
                    
                maint_correction = st.text_area("التصحيح المقترح / المطلوب (إن أمكن)", placeholder="مثال: استبدال مفتاح الكهرباء أو استدعاء فني التبريد")
                submit_maint = st.form_submit_button("💾 حفظ وتوليد الاستمارة الرسمية للطباعة والنسخ")
                
            if submit_maint:
                if not maint_prob:
                    st.error("يرجى كتابة تفاصيل المشكلة أولاً.")
                else:
                    cur_date = datetime.date.today().strftime("%Y-%m-%d")
                    username = st.session_state.get('username', 'user')
                    
                    db.save_maintenance_request(cur_date, maint_prob, maint_type, maint_correction, username)
                    db.log_activity(
                        username=username,
                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                        action_type="إضافة",
                        module="طلب صيانة",
                        details=f"تم إنشاء طلب صيانة جديد بنوع: {maint_type}"
                    )
                    
                    st.session_state['maint_form_submitted'] = True
                    st.session_state['maint_prob'] = maint_prob
                    st.session_state['maint_type'] = maint_type
                    st.session_state['maint_correction'] = maint_correction
                    st.success("💾 تم حفظ طلب الصيانة في السجلات بنجاح!")
                    st.rerun()
                
        if st.session_state.get('maint_form_submitted'):
            prob = st.session_state['maint_prob']
            mtype = st.session_state['maint_type']
            corr = st.session_state['maint_correction'] or "لا يوجد تصحيح مقترح"
            
            import base64
            logo_b64 = ""
            import os
            if os.path.exists("logo.jpg"):
                with open("logo.jpg", "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode()
                    
            logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="height:60px; max-width:150px; object-fit:contain;">' if logo_b64 else ""
            
            cur_date = datetime.date.today().strftime("%Y-%m-%d")
            emp_name = st.session_state.get('employee_name', 'موظف الصالة')
            username = st.session_state.get('username', 'user')
            
            # HTML code MUST NOT contain leading indentation spaces in Python to prevent Markdown codeblock rendering
            letter_html = f"""<div class="printable-card-area" style="background-color: white; color: black; padding: 30px; border: 2px solid #0077b6; border-radius: 8px; direction: rtl; text-align: right; font-family: 'Readex Pro', sans-serif; max-width: 800px; margin: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0077b6; padding-bottom: 10px; margin-bottom: 20px;">
<div style="text-align: right; flex-grow:1;">
<h2 style="color: #023e8a; margin: 0; font-family:'Readex Pro',sans-serif; font-weight:700; text-align:right;">شركة مسار هوم</h2>
<p style="color: gray; margin: 5px 0 0 0; font-size: 14px; font-family:'Readex Pro',sans-serif; text-align:right;">منظومة مسارات Masarat</p>
</div>
<div style="flex-shrink:0; text-align:left;">
{logo_tag}
</div>
</div>
<div style="text-align: left; font-size: 14px; margin-bottom: 20px; color: #333; font-family:'Readex Pro',sans-serif;">
<b>التاريخ:</b> {cur_date}
</div>
<div style="margin-bottom: 35px; text-align:right;">
<p style="font-size: 16px; font-weight: bold; margin: 0 0 10px 0; font-family:'Readex Pro',sans-serif; text-align:right;">السيد/ المدير العام المحترم،</p>
<p style="margin: 0 20px; font-size: 15px; line-height: 1.6; font-family:'Readex Pro',sans-serif; text-align:right;">السلام عليكم ورحمة الله وبركاته،،</p>
</div>
<div style="margin-bottom: 35px; min-height: 150px; text-align:right;">
<h4 style="text-align: center; color: #023e8a; border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-bottom: 20px; font-weight: bold; font-family:'Readex Pro',sans-serif;">الموضوع: طلب صيانة عاجل لصالة العرض</h4>
<p style="font-size: 15px; line-height: 1.8; text-indent: 30px; font-family:'Readex Pro',sans-serif; text-align:right;">
نود إحاطتكم علماً بأنه يوجد عطل/مشكلة تتطلب الصيانة الفنية الفورية في صالة العرض، وفيما يلي تفاصيل الطلب:
</p>
<table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 15px; text-align:right; font-family:'Readex Pro',sans-serif;">
<tr style="border-bottom: 1px solid #eee;">
<td style="padding: 10px; font-weight: bold; width: 25%; text-align:right;">نوع المشكلة:</td>
<td style="padding: 10px; text-align:right;">{mtype}</td>
</tr>
<tr style="border-bottom: 1px solid #eee;">
<td style="padding: 10px; font-weight: bold; vertical-align: top; text-align:right;">تفاصيل المشكلة:</td>
<td style="padding: 10px; line-height: 1.6; text-align:right;">{prob}</td>
</tr>
<tr style="border-bottom: 1px solid #eee;">
<td style="padding: 10px; font-weight: bold; vertical-align: top; text-align:right;">التصحيح المقترح:</td>
<td style="padding: 10px; line-height: 1.6; text-align:right;">{corr}</td>
</tr>
</table>
</div>
<div style="text-align: left; margin-top: 50px;">
<p style="margin: 0; font-weight: bold; text-align:left; font-family:'Readex Pro',sans-serif;">مقدم الطلب:</p>
<p style="margin: 5px 0 0 0; color: gray; text-align:left; font-family:'Readex Pro',sans-serif;">{emp_name} (@{username})</p>
</div>
</div>"""
            st.markdown("### 📄 معاينة الاستمارة الرسمية:")
            st.markdown(letter_html, unsafe_allow_html=True)
            
            st.info("💡 **جاهز للطباعة والنسخ:** لطباعة هذه الاستمارة الرسمية فقط، يرجى استخدام اختصار لوحة المفاتيح **(Ctrl + P)** أو **(Cmd + P)** في المتصفح، أو النقر على الثلاث نقاط أعلى المتصفح واختيار **طباعة (Print)**. كود التنسيق الذكي سيتكفل بطباعة ورقة الاستمارة فقط وإخفاء واجهة المنظومة بالكامل.")
            
            copy_text = f"""المرسل: {emp_name}
التاريخ: {cur_date}
إلى: السيد/ المدير العام المحترم
الموضوع: طلب صيانة عاجل لصالة العرض

السلام عليكم ورحمة الله وبركاته،،

نود إحاطتكم علماً بأنه يوجد عطل/مشكلة تتطلب الصيانة الفنية الفورية في صالة العرض، وفيما يلي تفاصيل الطلب:

- نوع المشكلة: {mtype}
- تفاصيل المشكلة: {prob}
- التصحيح المقترح: {corr}

ولكم منا فائق الاحترام والتقدير،،
مقدم الطلب: {emp_name} (@{username})"""
            st.markdown("### 📋 نسخ محتوى الرسالة (لتوجيهها عبر الإيميل أو الواتساب):")
            st.code(copy_text, language="text")

        # Maintenance History Log Table
        st.markdown("---")
        st.markdown("<h4 style='color: #0077b6;'>📋 سجل طلبات الصيانة السابقة</h4>", unsafe_allow_html=True)
        maint_records = db.get_all_maintenance_requests()
        if maint_records:
            maint_list = []
            for idx, r in enumerate(maint_records):
                maint_list.append({
                    "#": idx + 1,
                    "رقم الطلب": f"MNT-{r[0]:04d}",
                    "التاريخ": r[1],
                    "نوع المشكلة": r[3],
                    "المشكلة": r[2],
                    "التصحيح المقترح": r[4],
                    "بواسطة": r[5]
                })
            df_maint = pd = db.pd.DataFrame(maint_list) if hasattr(db, 'pd') else __import__('pandas').DataFrame(maint_list)
            st.dataframe(df_maint, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد طلبات صيانة مسجلة حالياً في قاعدة البيانات.")

    with tab_ration:
        is_first_day = (datetime.date.today().day == 1) or (datetime.datetime.strptime(date_str, "%Y-%m-%d").day == 1)
        test_mode = st.checkbox("🧪 تفعيل وضع التجربة (لإظهار استمارة طلب الكونة في غير يوم 1 من الشهر)", value=False)
        
        if not is_first_day and not test_mode:
            st.info("ℹ️ استمارة طلب الراشن الشهري تظهر تلقائياً في يوم 1 من كل شهر لتوجيه طلب الصرف المخصص للموظفين للمدير العام.")
        else:
            st.markdown("<h3 style='color: #023e8a; font-family: \"Readex Pro\", sans-serif; font-weight:700;'>☕ طلب الكونة والراشن الشهري لصالة العرض</h3>", unsafe_allow_html=True)
            st.markdown("يرجى إدخال وتحديد الكميات المطلوبة لصالح موظفي صالة العرض من مياه الشرب، القهوة، والشاي:")
            
            months_ar = {
                1: "يناير", 2: "فبراير", 3: "مارس", 4: "أبريل", 5: "مايو", 6: "يونيو",
                7: "يوليو", 8: "أغسطس", 9: "سبتمبر", 10: "أكتوبر", 11: "نوفمبر", 12: "ديسمبر"
            }
            cur_month_name = months_ar[datetime.date.today().month]
            cur_year = datetime.date.today().year
            
            # Reset state button if already submitted
            if st.session_state.get('ration_form_submitted'):
                if st.button("🆕 إنشاء طلب راشن جديد", type="primary"):
                    st.session_state.pop('ration_form_submitted', None)
                    st.session_state.pop('water_qty', None)
                    st.session_state.pop('water_notes', None)
                    st.session_state.pop('coffee_qty', None)
                    st.session_state.pop('coffee_notes', None)
                    st.session_state.pop('tea_qty', None)
                    st.session_state.pop('tea_notes', None)
                    st.session_state.pop('other_item_use', None)
                    st.session_state.pop('other_name', None)
                    st.session_state.pop('other_qty', None)
                    st.session_state.pop('other_notes', None)
                    st.rerun()

            if not st.session_state.get('ration_form_submitted'):
                with st.form("ration_form"):
                    col_r1, col_r2, col_r3 = st.columns(3)
                    with col_r1:
                        water_qty = st.text_input("كمية مياه الشرب *", value="5 صناديق")
                        water_notes = st.text_input("ملاحظات المياه", value="عبوات صغيرة 250 مل")
                    with col_r2:
                        coffee_qty = st.text_input("كمية القهوة *", value="3 علب")
                        coffee_notes = st.text_input("ملاحظات القهوة", value="سريعة التحضير (نسكافيه)")
                    with col_r3:
                        tea_qty = st.text_input("كمية الشاي *", value="4 علب")
                        tea_notes = st.text_input("ملاحظات الشاي", value="شاي أحمر خيط (ليبتون)")
                        
                    other_item_use = st.checkbox("إضافة بند آخر إضافي للطلب")
                    other_name = ""
                    other_qty = ""
                    other_notes = ""
                    if other_item_use:
                        col_ro1, col_ro2, col_ro3 = st.columns(3)
                        with col_ro1:
                            other_name = st.text_input("اسم البند الإضافي (مثال: سكر)")
                        with col_ro2:
                            other_qty = st.text_input("الكمية المطلوبة (مثال: 5 كجم)")
                        with col_ro3:
                            other_notes = st.text_input("ملاحظات البند الإضافي")
                            
                    submit_ration = st.form_submit_button("💾 حفظ وتوليد استمارة طلب الراشن الرسمية")
                    
                if submit_ration:
                    cur_date = datetime.date.today().strftime("%Y-%m-%d")
                    username = st.session_state.get('username', 'user')
                    
                    db.save_ration_request(
                        cur_date, water_qty, water_notes, coffee_qty, coffee_notes,
                        tea_qty, tea_notes, other_name, other_qty, other_notes, username
                    )
                    db.log_activity(
                        username=username,
                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                        action_type="إضافة",
                        module="طلب راشن",
                        details=f"تم تقديم طلب الراشن لشهر: {cur_month_name}"
                    )
                    
                    st.session_state['ration_form_submitted'] = True
                    st.session_state['water_qty'] = water_qty
                    st.session_state['water_notes'] = water_notes
                    st.session_state['coffee_qty'] = coffee_qty
                    st.session_state['coffee_notes'] = coffee_notes
                    st.session_state['tea_qty'] = tea_qty
                    st.session_state['tea_notes'] = tea_notes
                    st.session_state['other_item_use'] = other_item_use
                    st.session_state['other_name'] = other_name
                    st.session_state['other_qty'] = other_qty
                    st.session_state['other_notes'] = other_notes
                    st.success("💾 تم حفظ طلب الراشن في السجلات بنجاح!")
                    st.rerun()
                
            if st.session_state.get('ration_form_submitted'):
                w_qty = st.session_state['water_qty']
                w_notes = st.session_state['water_notes']
                c_qty = st.session_state['coffee_qty']
                c_notes = st.session_state['coffee_notes']
                t_qty = st.session_state['tea_qty']
                t_notes = st.session_state['tea_notes']
                
                other_row_html = ""
                other_text = ""
                if st.session_state.get('other_item_use') and st.session_state.get('other_name'):
                    o_name = st.session_state['other_name']
                    o_qty = st.session_state['other_qty']
                    o_notes = st.session_state['other_notes']
                    other_row_html = f"""
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center;">4</td>
                        <td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; text-align: right;">{o_name}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{o_qty}</td>
                        <td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{o_notes}</td>
                    </tr>
                    """
                    other_text = f"\n4. {o_name}: {o_qty} ({o_notes})"
                
                import base64
                logo_b64 = ""
                import os
                if os.path.exists("logo.jpg"):
                    with open("logo.jpg", "rb") as f:
                        logo_b64 = base64.b64encode(f.read()).decode()
                        
                logo_tag = f'<img src="data:image/jpeg;base64,{logo_b64}" style="height:60px; max-width:150px; object-fit:contain;">' if logo_b64 else ""
                
                cur_date = datetime.date.today().strftime("%Y-%m-%d")
                emp_name = st.session_state.get('employee_name', 'موظف الصالة')
                username = st.session_state.get('username', 'user')
                
                # HTML code MUST NOT contain leading indentation spaces in Python to prevent Markdown codeblock rendering
                ration_html = f"""<div class="printable-card-area" style="background-color: white; color: black; padding: 30px; border: 2px solid #0077b6; border-radius: 8px; direction: rtl; text-align: right; font-family: 'Readex Pro', sans-serif; max-width: 800px; margin: auto; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #0077b6; padding-bottom: 10px; margin-bottom: 20px;">
<div style="text-align: right; flex-grow:1;">
<h2 style="color: #023e8a; margin: 0; font-family:'Readex Pro',sans-serif; font-weight:700; text-align:right;">شركة مسار هوم</h2>
<p style="color: gray; margin: 5px 0 0 0; font-size: 14px; font-family:'Readex Pro',sans-serif; text-align:right;">منظومة مسارات Masarat</p>
</div>
<div style="flex-shrink:0; text-align:left;">
{logo_tag}
</div>
</div>
<div style="text-align: left; font-size: 14px; margin-bottom: 20px; color: #333; font-family:'Readex Pro',sans-serif;">
<b>التاريخ:</b> {cur_date}
</div>
<div style="margin-bottom: 35px; text-align:right;">
<p style="font-size: 16px; font-weight: bold; margin: 0 0 10px 0; font-family:'Readex Pro',sans-serif; text-align:right;">السيد/ المدير العام المحترم،</p>
<p style="margin: 0 20px; font-size: 15px; line-height: 1.6; font-family:'Readex Pro',sans-serif; text-align:right;">السلام عليكم ورحمة الله وبركاته،،</p>
</div>
<div style="margin-bottom: 35px; min-height: 150px; text-align:right;">
<h4 style="text-align: center; color: #023e8a; border-bottom: 1px solid #ddd; padding-bottom: 8px; margin-bottom: 20px; font-weight: bold; font-family:'Readex Pro',sans-serif;">الموضوع: طلب الكونة الشهرية (الراشن المخصص لموظفي صالة العرض)</h4>
<p style="font-size: 15px; line-height: 1.8; text-indent: 30px; font-family:'Readex Pro',sans-serif; text-align:right;">
يرجى التكرم بالموافقة على صرف الكونة الشهرية والراشن المخصص لصالح موظفي صالة العرض عن شهر **{cur_month_name} {cur_year}**، وفيما يلي تفاصيل المواد والكميات المطلوبة:
</p>
<table style="width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 15px; text-align:right; font-family:'Readex Pro',sans-serif; border: 1px solid #ddd;">
<tr style="background-color: #f2f2f2; border-bottom: 1px solid #ddd;">
<th style="padding: 10px; border: 1px solid #ddd; text-align: center; width: 10%;">#</th>
<th style="padding: 10px; border: 1px solid #ddd; text-align: right;">البند المطلوب</th>
<th style="padding: 10px; border: 1px solid #ddd; text-align: center; width: 25%;">الكمية المطلوبة</th>
<th style="padding: 10px; border: 1px solid #ddd; text-align: right; width: 35%;">ملاحظات</th>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">1</td>
<td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; text-align: right;">مياه شرب (عبوات صغيرة / صناديق)</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{w_qty}</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{w_notes}</td>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">2</td>
<td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; text-align: right;">قهوة (علب / مغلفات)</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{c_qty}</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{c_notes}</td>
</tr>
<tr>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center;">3</td>
<td style="padding: 10px; border: 1px solid #ddd; font-weight: bold; text-align: right;">شاي (علب مغلفات / خيط)</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: center; font-weight: bold;">{t_qty}</td>
<td style="padding: 10px; border: 1px solid #ddd; text-align: right;">{t_notes}</td>
</tr>
{other_row_html}
</table>
</div>
<div style="text-align: left; margin-top: 50px;">
<p style="margin: 0; font-weight: bold; text-align:left; font-family:'Readex Pro',sans-serif;">مقدم الطلب:</p>
<p style="margin: 5px 0 0 0; color: gray; text-align:left; font-family:'Readex Pro',sans-serif;">{emp_name} (@{username})</p>
</div>
</div>"""
                st.markdown("### 📄 معاينة الاستمارة الرسمية للراشن:")
                st.markdown(textwrap.dedent(ration_html), unsafe_allow_html=True)
                
                st.info("💡 **جاهز للطباعة والنسخ:** لطباعة هذه الاستمارة الرسمية فقط، يرجى استخدام اختصار لوحة المفاتيح **(Ctrl + P)** أو **(Cmd + P)** في المتصفح، أو النقر على الثلاث نقاط أعلى المتصفح واختيار **طباعة (Print)**. كود التنسيق الذكي سيتكفل بطباعة ورقة الاستمارة فقط وإخفاء واجهة المنظومة بالكامل.")
                
                copy_ration_text = f"""المرسل: {emp_name}
التاريخ: {cur_date}
إلى: السيد/ المدير العام المحترم
الموضوع: طلب صرف الكونة والراشن الشهري لموظفي صالة العرض

السلام عليكم ورحمة الله وبركاته،،

يرجى التكرم بالموافقة على صرف الكونة الشهرية (الراشن المخصص) لصالح موظفي صالة العرض عن شهر {cur_month_name} {cur_year}، وتفاصيل الطلب هي:

1. مياه شرب: {w_qty} ({w_notes})
2. قهوة: {c_qty} ({c_notes})
3. شاي: {t_qty} ({t_notes}){other_text}

ولكم منا فائق الاحترام والتقدير،،
مقدم الطلب: {emp_name} (@{username})"""
                st.markdown("### 📋 نسخ محتوى الرسالة (لتوجيهها عبر الإيميل أو الواتساب):")
                st.code(copy_ration_text, language="text")

        # Ration History Log Table
        st.markdown("---")
        st.markdown("<h4 style='color: #0077b6;'>📋 سجل طلبات الكونة والراشن السابقة</h4>", unsafe_allow_html=True)
        ration_records = db.get_all_ration_requests()
        if ration_records:
            ration_list = []
            for idx, r in enumerate(ration_records):
                other_str = f"{r[8]}: {r[9]}" if r[8] else "لا يوجد"
                ration_list.append({
                    "#": idx + 1,
                    "رقم الطلب": f"RAT-{r[0]:04d}",
                    "التاريخ": r[1],
                    "المياه": f"{r[2]} ({r[3]})",
                    "القهوة": f"{r[4]} ({r[5]})",
                    "الشاي": f"{r[6]} ({r[7]})",
                    "إضافات": other_str,
                    "بواسطة": r[11]
                })
            df_ration = pd = db.pd.DataFrame(ration_list) if hasattr(db, 'pd') else __import__('pandas').DataFrame(ration_list)
            st.dataframe(df_ration, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد طلبات راشن مسجلة حالياً في قاعدة البيانات.")

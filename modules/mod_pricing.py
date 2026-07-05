import streamlit as st
import database as db

def render_page(can_access_pricing, is_observer):
    if not can_access_pricing:
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
            /* Styling for final breakdown card */
            .breakdown-card {
                background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                border: 1px solid #bbf7d0;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 10px rgba(0, 180, 216, 0.05);
                margin-top: 20px;
                color: #14532d;
            }
            .breakdown-row {
                display: flex;
                justify-content: space-between;
                border-bottom: 1px dashed #bbf7d0;
                padding: 8px 0;
            }
            .breakdown-row:last-child {
                border-bottom: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='force-center'><h2 style='color: #0d47a1; font-family: \"Readex Pro\", sans-serif; font-weight: 700; font-size: 34px; margin-bottom: 5px;'>سجل حساب وتسعير المشاريع</h2></div>", unsafe_allow_html=True)
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0d8a95; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 15px; margin-bottom: 20px; font-size: 28px;'>مسار التسعير</h3></div>", unsafe_allow_html=True)
    
    # Load all active designs for dropdown selection
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT f.id, f.customer_name, f.furniture_type
        FROM FieldVisits f
        INNER JOIN ProjectDesigns d ON f.id = d.visit_id
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    active_projects = c.fetchall()
    conn.close()
    
    project_options = {"-- اختر عميلاً/مشروعاً للتسعير --": None}
    for row in active_projects:
        project_options[f"MHM{row[0]:05d} | {row[1]} ({row[2]})"] = row[0]
        
    selected_visit_id = st.session_state.get('selected_pricing_visit_id', None)
    
    default_idx = 0
    if selected_visit_id:
        for idx, val in enumerate(project_options.values()):
            if val == selected_visit_id:
                default_idx = idx
                break
                
    selected_project_key = st.selectbox(
        "🗂️ اختر العميل أو المشروع المستهدف لتسعيره وحفظه:", 
        options=list(project_options.keys()), 
        index=default_idx,
        key="pricing_project_select"
    )
    new_visit_id = project_options[selected_project_key]
    
    if new_visit_id != selected_visit_id:
        st.session_state['selected_pricing_visit_id'] = new_visit_id
        if new_visit_id:
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT customer_name, furniture_type FROM FieldVisits WHERE id = ?", (new_visit_id,))
            fv_row = c.fetchone()
            conn.close()
            if fv_row:
                st.session_state['selected_pricing_cname'] = fv_row[0]
                st.session_state['selected_pricing_furniture'] = fv_row[1]
        else:
            st.session_state['selected_pricing_cname'] = ''
            st.session_state['selected_pricing_furniture'] = ''
        st.rerun()

    # Load saved details if selected
    saved_pricing_details = {}
    saved_workshop_drawing = ""
    is_price_approved = 0
    is_price_paid = 0
    is_read_only_pricing = False
    if selected_visit_id:
        conn = db.get_connection()
        c = conn.cursor()
        c.execute("SELECT price_details, workshop_drawing, price_is_approved, price_is_paid FROM ProjectDesigns WHERE visit_id = ?", (selected_visit_id,))
        p_row = c.fetchone()
        conn.close()
        if p_row:
            import json
            price_details_str, saved_workshop_drawing, is_price_approved, is_price_paid = p_row
            is_admin_user = (st.session_state.get('username') == 'Admin' or st.session_state.get('role') == 'Admin')
            is_read_only_pricing = (is_price_approved == 1 and not is_admin_user)
            if price_details_str:
                try:
                    saved_pricing_details = json.loads(price_details_str)
                except:
                    pass

    cname_val = st.session_state.get('selected_pricing_cname', '')
    furniture_val = st.session_state.get('selected_pricing_furniture', '')
    
    # Side-by-side columns: Worksheet on the Right (wider), Calculator on the Left (fixed/narrower)
    col_sheet, col_calc = st.columns([1.8, 1.2])
    
    with col_sheet:
        st.markdown("<h4 style='color: #0d47a1; font-family: \"Readex Pro\", sans-serif; border-bottom: 2px solid #90e0ef; padding-bottom: 5px; margin-bottom: 15px;'>📋 مسودة حساب وتفصيل التسعيرة</h4>", unsafe_allow_html=True)
        
        # Product details
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            customer_name = st.text_input("اسم العميل / المشروع المرجعي:", value=cname_val, disabled=True if selected_visit_id else False)
            
            # Helper to map the furniture type text to the closest selectbox option
            def map_furniture_to_category(f_type):
                f_type_lower = f_type.lower() if f_type else ""
                categories = ["مطبخ", "غرفة نوم", "غرفة ملابس", "ديكور شاشة", "أبواب داخلية", "جلسة"]
                for cat in categories:
                    if cat in f_type_lower or (cat == "جلسة" and ("جلسة" in f_type_lower or "أثاث" in f_type_lower)):
                        return "جلسة/أثاث صالة" if cat == "جلسة" else cat
                return "منتجات أخرى"
            
            mapped_cat = map_furniture_to_category(furniture_val)
            cat_options = ["مطبخ", "غرفة نوم", "غرفة ملابس", "ديكور شاشة", "أبواب داخلية", "جلسة/أثاث صالة", "منتجات أخرى"]
            cat_idx = cat_options.index(mapped_cat) if mapped_cat in cat_options else 6
            
            # Override if saved
            saved_cat = saved_pricing_details.get("category", "")
            if saved_cat in cat_options:
                cat_idx = cat_options.index(saved_cat)
                
            category = st.selectbox("تصنيف المنتج/الأثاث:", cat_options, index=cat_idx, disabled=is_read_only_pricing)
        with col_p2:
            saved_calc_method = saved_pricing_details.get("calc_method", "بالمتر الطولي (Running Meter)")
            calc_options = ["بالمتر الطولي (Running Meter)", "بالمتر المربع (Square Meter)", "سعر مقطوع (Lump Sum)"]
            calc_idx = calc_options.index(saved_calc_method) if saved_calc_method in calc_options else 0
            calc_method = st.radio("طريقة حساب التسعير:", calc_options, index=calc_idx, horizontal=False, disabled=is_read_only_pricing)
            
            saved_material = saved_pricing_details.get("material", "MDF ميلامين تركي")
            material_options = ["MDF ميلامين تركي", "MDF ميلامين أسباني", "لاتيه (Blockboard) قشرة طبيعي", "خشب زان طبيعي", "خشب صنوبر/سويدي", "أكريليك مجوف", "خامات أخرى"]
            mat_idx = material_options.index(saved_material) if saved_material in material_options else 0
            material = st.selectbox("نوع الخامات الرئيسية (المادة):", material_options, index=mat_idx, disabled=is_read_only_pricing)
            
            # Auto-assign smart default pricing per unit based on material
            material_defaults = {
                "MDF ميلامين تركي": 450.0,
                "MDF ميلامين أسباني": 550.0,
                "لاتيه (Blockboard) قشرة طبيعي": 750.0,
                "خشب زان طبيعي": 1200.0,
                "خشب صنوبر/سويدي": 850.0,
                "أكريليك مجوف": 650.0,
                "خامات أخرى": 300.0
            }
            default_price = material_defaults.get(material, 450.0)
            saved_unit_price = saved_pricing_details.get("unit_price", default_price)
            unit_price = st.number_input("سعر الوحدة/المتر المعتمد (د.ل):", min_value=0.0, value=float(saved_unit_price), step=50.0, disabled=is_read_only_pricing)

        # Dimensions & quantities
        st.markdown("<h5 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; margin-top: 15px;'>📏 الأبعاد والكميات</h5>", unsafe_allow_html=True)
        col_d1, col_d2, col_d3 = st.columns(3)
        
        saved_length = saved_pricing_details.get("length", 1.0)
        saved_width = saved_pricing_details.get("width", 1.0)
        saved_qty = saved_pricing_details.get("qty", 1)
        
        length = 1.0
        width = 1.0
        qty = 1
        
        if calc_method == "سعر مقطوع (Lump Sum)":
            with col_d1:
                qty = st.number_input("الكمية (عدد القطع):", min_value=1, value=int(saved_qty), step=1, disabled=is_read_only_pricing)
            with col_d2:
                st.text_input("الطول (متر):", value="غير مطبق", disabled=True)
            with col_d3:
                st.text_input("الارتفاع/العرض (متر):", value="غير مطبق", disabled=True)
        elif calc_method == "بالمتر المربع (Square Meter)":
            with col_d1:
                length = st.number_input("الطول الإجمالي (متر):", min_value=0.0, value=float(saved_length), step=0.1, disabled=is_read_only_pricing)
            with col_d2:
                width = st.number_input("العرض أو الارتفاع (متر):", min_value=0.0, value=float(saved_width), step=0.1, disabled=is_read_only_pricing)
            with col_d3:
                qty = st.number_input("الكمية (عدد القطع):", min_value=1, value=int(saved_qty), step=1, disabled=is_read_only_pricing)
        else: # running meter
            with col_d1:
                length = st.number_input("الطول الإجمالي (متر):", min_value=0.0, value=float(saved_length), step=0.1, disabled=is_read_only_pricing)
            with col_d2:
                st.text_input("الارتفاع/العرض (متر):", value="غير مطبق", disabled=True)
            with col_d3:
                qty = st.number_input("الكمية (عدد القطع):", min_value=1, value=int(saved_qty), step=1, disabled=is_read_only_pricing)

        # Additional Expenses
        st.markdown("<h5 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; margin-top: 15px;'>➕ الإكسسوارات والمصاريف الإضافية</h5>", unsafe_allow_html=True)
        col_e1, col_e2, col_e3 = st.columns(3)
        saved_acc_cost = saved_pricing_details.get("accessories_cost", 0.0)
        saved_trans_cost = saved_pricing_details.get("transport_install", 0.0)
        saved_other_cost = saved_pricing_details.get("other_extra", 0.0)
        with col_e1:
            accessories_cost = st.number_input("تكلفة المقابض والإكسسوارات (د.ل):", min_value=0.0, value=float(saved_acc_cost), step=25.0, disabled=is_read_only_pricing)
        with col_e2:
            transport_install = st.number_input("تكلفة النقل والتركيب (د.ل):", min_value=0.0, value=float(saved_trans_cost), step=25.0, disabled=is_read_only_pricing)
        with col_e3:
            other_extra = st.number_input("مصاريف إضافية أخرى (د.ل):", min_value=0.0, value=float(saved_other_cost), step=25.0, disabled=is_read_only_pricing)

        # Markups & Discounts
        st.markdown("<h5 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; margin-top: 15px;'>📈 نسب هامش الربح والخصومات</h5>", unsafe_allow_html=True)
        col_md1, col_md2 = st.columns(2)
        saved_markup = saved_pricing_details.get("markup_pct", 0.0)
        saved_discount = saved_pricing_details.get("discount_pct", 0.0)
        with col_md1:
            markup_pct = st.number_input("هامش الربح الإضافي (%) - اختياري:", min_value=0.0, value=float(saved_markup), step=1.0, disabled=is_read_only_pricing)
        with col_md2:
            discount_pct = st.number_input("نسبة الخصم الممنوحة (%) - اختياري:", min_value=0.0, value=float(saved_discount), step=1.0, disabled=is_read_only_pricing)

        # Logic computations
        if calc_method == "سعر مقطوع (Lump Sum)":
            base_cost = unit_price * qty
            dimensions_desc = f"{qty} قطع (سعر مقطوع)"
        elif calc_method == "بالمتر المربع (Square Meter)":
            base_cost = length * width * unit_price * qty
            dimensions_desc = f"{length:.2f}م طولي × {width:.2f}م عرض × {qty} قطع ({length*width*qty:.2f} م²)"
        else: # running meter
            base_cost = length * unit_price * qty
            dimensions_desc = f"{length:.2f}م طولي × {qty} قطع ({length*qty:.2f}م)"

        total_additions = accessories_cost + transport_install + other_extra
        subtotal = base_cost + total_additions
        profit_val = subtotal * (markup_pct / 100.0)
        total_before_discount = subtotal + profit_val
        discount_val = total_before_discount * (discount_pct / 100.0)
        final_price = total_before_discount - discount_val

        # Display breakdown card
        st.markdown(f"""
            <div class='breakdown-card'>
                <h4 style='margin-top:0; color:#14532d; font-family:"Readex Pro", sans-serif; border-bottom: 2px solid #bbf7d0; padding-bottom:5px;'>📊 تفاصيل الفاتورة النهائية</h4>
                <div class='breakdown-row'>
                    <span><b>اسم العميل المرجعي:</b> {customer_name if customer_name else 'عام/غير محدد'}</span>
                    <span><b>آلية الحساب:</b> {dimensions_desc}</span>
                </div>
                <div class='breakdown-row'>
                    <span>التكلفة الأساسية للأعمال الخشبية ({category} - {material})</span>
                    <span><b>{base_cost:,.2f} د.ل</b></span>
                </div>
                <div class='breakdown-row'>
                    <span>تكاليف إضافية (إكسسوارات + تركيب ونقل + أخرى)</span>
                    <span><b>{total_additions:,.2f} د.ل</b></span>
                </div>
                <div class='breakdown-row'>
                    <span>هامش الربح الإضافي المطبق ({markup_pct}%)</span>
                    <span><b>{profit_val:,.2f} د.ل</b></span>
                </div>
                <div class='breakdown-row'>
                    <span>المجموع قبل الخصم المالي</span>
                    <span><b>{total_before_discount:,.2f} د.ل</b></span>
                </div>
                <div class='breakdown-row'>
                    <span>قيمة الخصم التجاري الممنوح ({discount_pct}%)</span>
                    <span style='color: #b91c1c;'><b>- {discount_val:,.2f} د.ل</b></span>
                </div>
                <div class='breakdown-row' style='border-top: 2px solid #86efac; margin-top:10px; padding-top:12px; font-size:22px; font-weight:bold; color: #166534;'>
                    <span>السعر النهائي المعتمد للمشروع</span>
                    <span>{final_price:,.2f} دينار ليبي</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Save Actions
        st.markdown("<br>", unsafe_allow_html=True)
        if not selected_visit_id:
            st.warning("⚠️ يرجى تحديد عميل من قائمة الاختيار في الأعلى ليتم ربط وحفظ السجل باسمه.")
        else:
            if is_read_only_pricing:
                st.warning("🔒 هذه التسعيرة تم حفظها واعتمادها. التعديل متاح فقط لمدير النظام (الأدمن).")
                btn_save = False
                btn_approve = False
            else:
                col_act1, col_act2 = st.columns(2)
                with col_act1:
                    btn_save = st.button("💾 حفظ السجل", use_container_width=True)
                with col_act2:
                    btn_approve = st.button("💾 حفظ واعتماد السجل", use_container_width=True)
                
            if btn_save or btn_approve:
                if is_read_only_pricing:
                    st.error("🔒 عذراً، لا تمتلك الصلاحية لتعديل هذا السجل المعتمد.")
                    st.stop()
                
                # Serialized details
                import json
                price_details_dict = {
                    "calc_method": calc_method,
                    "category": category,
                    "material": material,
                    "unit_price": unit_price,
                    "length": length,
                    "width": width,
                    "qty": qty,
                    "accessories_cost": accessories_cost,
                    "transport_install": transport_install,
                    "other_extra": other_extra,
                    "markup_pct": markup_pct,
                    "discount_pct": discount_pct
                }
                price_details_str = json.dumps(price_details_dict, ensure_ascii=False)
                
                new_price_is_approved = 1 if btn_approve else is_price_approved
                
                conn = db.get_connection()
                c = conn.cursor()
                c.execute('''
                    UPDATE ProjectDesigns
                    SET price_final = ?,
                        price_is_approved = ?,
                        price_details = ?
                    WHERE visit_id = ?
                ''', (final_price, new_price_is_approved, price_details_str, selected_visit_id))
                conn.commit()
                conn.close()
                
                db.log_activity(
                    username=st.session_state.get('username', 'Unknown'),
                    employee_name=st.session_state.get('employee_name', 'Unknown'),
                    action_type="اعتماد التسعيرة" if btn_approve else "حفظ مسودة التسعير",
                    module="مسار التسعير",
                    details=f"تم {'حفظ واعتماد' if btn_approve else 'حفظ'} تسعيرة العميل MHM{selected_visit_id:05d} بقيمة {final_price:,.2f} د.ل"
                )
                
                if btn_approve:
                    st.success(f"✅ تم حفظ واعتماد التسعيرة للمشروع MHM{selected_visit_id:05d}! السجل متوفر الآن في مسار العقود لإبرام وتوقيع العقد.")
                else:
                    st.success(f"✅ تم حفظ مسودة التسعيرة للمشروع MHM{selected_visit_id:05d}!")
                
                import time
                time.sleep(1.5)
                st.rerun()

        # WhatsApp Share Summary Template
        whatsapp_msg = f"""السلام عليكم عميلنا الكريم 🌸
يسر شركة مسار هوم تقديم عرض السعر المبدئي لمشروعكم الكريم:

🔹 العميل المرجعي: {customer_name if customer_name else 'مشروع عام'}
🔹 تصنيف المشروع: {category}
🔹 الخامة المستخدمة: {material}
🔹 إجمالي الكمية/الأبعاد: {dimensions_desc}
----------------------------------------
🔸 التكلفة الأساسية: {base_cost:,.2f} د.ل
🔸 الإضافات والملحقات: {total_additions:,.2f} د.ل
🔸 الخصم التجاري الممنوح: {discount_val:,.2f} د.ل
----------------------------------------
✅ القيمة النهائية الإجمالية للمشروع: {final_price:,.2f} دينار ليبي

يسعدنا تواصلكم لاعتماد التصميم وبدء العمل! ✨"""

        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("💬 توليد ملخص مشاركة واتساب (WhatsApp Share Summary)"):
            import base64
            msg_b64 = base64.b64encode(whatsapp_msg.encode('utf-8')).decode('utf-8')
            
            whatsapp_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <link href="https://fonts.googleapis.com/css2?family=Readex+Pro:wght@400;500;600&display=swap" rel="stylesheet">
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        background-color: transparent;
                        font-family: 'Readex Pro', sans-serif;
                        direction: rtl;
                    }}
                    .container {{
                        display: flex;
                        flex-direction: column;
                        gap: 10px;
                    }}
                    textarea {{
                        width: 100%;
                        height: 200px;
                        padding: 12px;
                        border: 1px solid #cbd5e1;
                        border-radius: 8px;
                        font-size: 14px;
                        font-family: 'Readex Pro', sans-serif;
                        resize: none;
                        box-sizing: border-box;
                        background-color: #ffffff;
                        color: #334155;
                        line-height: 1.6;
                    }}
                    textarea:focus {{
                        outline: none;
                        border-color: #25d366;
                        box-shadow: 0 0 0 2px rgba(37, 211, 102, 0.2);
                    }}
                    .copy-btn {{
                        background-color: #25d366;
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 12px 0;
                        font-size: 15px;
                        font-weight: 500;
                        cursor: pointer;
                        transition: all 0.2s ease;
                        font-family: 'Readex Pro', sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        gap: 8px;
                        box-shadow: 0 2px 4px rgba(37, 211, 102, 0.2);
                    }}
                    .copy-btn:hover {{
                        background-color: #20ba5a;
                        transform: translateY(-2px);
                        box-shadow: 0 4px 8px rgba(37, 211, 102, 0.3);
                    }}
                    .copy-btn:active {{
                        transform: translateY(0);
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <textarea id="msgText" readonly></textarea>
                    <button class="copy-btn" onclick="copyText()">📋 نسخ الرسالة للمشاركة عبر واتساب</button>
                </div>

                <script>
                    const b64Str = "{msg_b64}";
                    document.getElementById('msgText').value = decodeURIComponent(atob(b64Str).split('').map(function(c) {{
                        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                    }}).join(''));

                    function copyText() {{
                        let val = document.getElementById('msgText').value;
                        try {{
                            navigator.clipboard.writeText(val);
                            alert("✅ تم نسخ رسالة الواتساب بنجاح!");
                        }} catch (err) {{
                            const temp = document.createElement('textarea');
                            temp.value = val;
                            document.body.appendChild(temp);
                            temp.select();
                            document.execCommand('copy');
                            document.body.removeChild(temp);
                            alert("✅ تم نسخ رسالة الواتساب بنجاح!");
                        }}
                    }}
                </script>
            </body>
            </html>
            """
            st.components.v1.html(whatsapp_html, height=270)
            st.info("💡 يمكنك الضغط على الزر الأخضر أعلاه لنسخ رسالة عرض السعر بالكامل ومشاركتها مع العميل مباشرة.")

    with col_calc:
        st.markdown("<h4 style='color: #0d47a1; font-family: \"Readex Pro\", sans-serif; border-bottom: 2px solid #90e0ef; padding-bottom: 5px; margin-bottom: 15px;'>🧮 آلة حاسبة تفاعلية سريعة</h4>", unsafe_allow_html=True)
        
        # Embedded zero-lag premium HTML/JS Apple-style Calculator (Modern Light Design)
        calculator_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <link href="https://fonts.googleapis.com/css2?family=Readex+Pro:wght@400;500;600&display=swap" rel="stylesheet">
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    background-color: transparent;
                    font-family: 'Readex Pro', sans-serif;
                    direction: ltr;
                }
                .calc-body {
                    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
                    border-radius: 20px;
                    padding: 20px;
                    box-shadow: 0 10px 25px rgba(148, 163, 184, 0.25);
                    width: 280px;
                    color: #1e293b;
                    border: 1px solid #e2e8f0;
                }
                .calc-screen {
                    background-color: #ffffff;
                    border-radius: 12px;
                    padding: 15px;
                    text-align: right;
                    margin-bottom: 15px;
                    border: 1px solid #cbd5e1;
                    box-shadow: inset 0 2px 4px rgba(148, 163, 184, 0.05);
                }
                .calc-formula {
                    font-size: 13px;
                    color: #64748b;
                    min-height: 20px;
                    word-break: break-all;
                    margin-bottom: 5px;
                }
                .calc-display {
                    font-size: 30px;
                    font-weight: 600;
                    color: #0284c7;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                }
                .calc-grid {
                    display: grid;
                    grid-template-columns: repeat(4, 1fr);
                    gap: 10px;
                }
                .calc-btn {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    color: #334155;
                    font-size: 18px;
                    font-weight: 500;
                    padding: 12px 0;
                    cursor: pointer;
                    transition: all 0.15s ease;
                    font-family: 'Readex Pro', sans-serif;
                    outline: none;
                    box-shadow: 0 2px 4px rgba(148, 163, 184, 0.05);
                }
                .calc-btn:hover {
                    background-color: #f8fafc;
                    border-color: #cbd5e1;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(148, 163, 184, 0.1);
                }
                .calc-btn:active {
                    transform: translateY(0);
                }
                .calc-btn.op {
                    background-color: #e0f2fe;
                    color: #0369a1;
                    border-color: #bae6fd;
                }
                .calc-btn.op:hover {
                    background-color: #bae6fd;
                }
                .calc-btn.zero {
                    grid-column: span 2;
                }
                .calc-btn.equal {
                    background-color: #0d9488;
                    color: white;
                    border: none;
                    grid-column: span 2;
                }
                .calc-btn.equal:hover {
                    background-color: #0f766e;
                }
                .calc-btn.copy {
                    background-color: #f0fdf4;
                    color: #166534;
                    border: 1px solid #bbf7d0;
                    grid-column: span 2;
                    font-size: 14px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 5px;
                }
                .calc-btn.copy:hover {
                    background-color: #dcfce7;
                    color: #14532d;
                    border-color: #86efac;
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(148, 163, 184, 0.1);
                }
                .calc-btn.clear {
                    background-color: #fee2e2;
                    color: #b91c1c;
                    border-color: #fecaca;
                }
                .calc-btn.clear:hover {
                    background-color: #fecaca;
                }
            </style>
        </head>
        <body>
            <div class="calc-body">
                <div class="calc-screen">
                    <div class="calc-formula" id="formula"></div>
                    <div class="calc-display" id="display">0</div>
                </div>
                <div class="calc-grid">
                    <button class="calc-btn clear" onclick="clearAll()">C</button>
                    <button class="calc-btn op" onclick="press('(')">(</button>
                    <button class="calc-btn op" onclick="press(')')">)</button>
                    <button class="calc-btn op" onclick="press('/')">÷</button>
                    
                    <button class="calc-btn" onclick="press('7')">7</button>
                    <button class="calc-btn" onclick="press('8')">8</button>
                    <button class="calc-btn" onclick="press('9')">9</button>
                    <button class="calc-btn op" onclick="press('*')">×</button>
                    
                    <button class="calc-btn" onclick="press('4')">4</button>
                    <button class="calc-btn" onclick="press('5')">5</button>
                    <button class="calc-btn" onclick="press('6')">6</button>
                    <button class="calc-btn op" onclick="press('-')">-</button>
                    
                    <button class="calc-btn" onclick="press('1')">1</button>
                    <button class="calc-btn" onclick="press('2')">2</button>
                    <button class="calc-btn" onclick="press('3')">3</button>
                    <button class="calc-btn op" onclick="press('+')">+</button>
                    
                    <button class="calc-btn zero" onclick="press('0')">0</button>
                    <button class="calc-btn" onclick="press('.')">.</button>
                    <button class="calc-btn" onclick="backspace()">⌫</button>
                    
                    <button class="calc-btn equal" onclick="solve()">=</button>
                    <button class="calc-btn copy" onclick="copyResult()">📋 نسخ النتيجة</button>
                </div>
            </div>

            <script>
                let currentInput = "0";
                let formulaStr = "";
                let isDone = false;

                function updateScreen() {
                    document.getElementById('display').innerText = currentInput;
                    document.getElementById('formula').innerText = formulaStr;
                }

                function press(val) {
                    if (isDone) {
                        if ("+-*/".includes(val)) {
                            formulaStr = currentInput;
                            isDone = false;
                        } else {
                            currentInput = "0";
                            formulaStr = "";
                            isDone = false;
                        }
                    }

                    if (currentInput === "0" && !"+-*/.)".includes(val)) {
                        currentInput = val;
                    } else {
                        currentInput += val;
                    }
                    updateScreen();
                }

                function clearAll() {
                    currentInput = "0";
                    formulaStr = "";
                    isDone = false;
                    updateScreen();
                }

                function backspace() {
                    if (isDone) {
                        clearAll();
                        return;
                    }
                    if (currentInput.length > 1) {
                        currentInput = currentInput.slice(0, -1);
                    } else {
                        currentInput = "0";
                    }
                    updateScreen();
                }

                function solve() {
                    if (currentInput === "0" && formulaStr === "") return;
                    try {
                        let expr = currentInput;
                        formulaStr = currentInput + " =";
                        let result = eval(expr);
                        
                        if (result % 1 !== 0) {
                            result = parseFloat(result.toFixed(4));
                        }
                        currentInput = result.toString();
                        isDone = true;
                    } catch (err) {
                        currentInput = "خطأ";
                        isDone = true;
                    }
                    updateScreen();
                }

                function copyResult() {
                    let val = currentInput;
                    if (val === "خطأ") return;
                    try {
                        navigator.clipboard.writeText(val);
                        alert("تم نسخ النتيجة: " + val);
                    } catch (err) {
                        const temp = document.createElement('input');
                        temp.value = val;
                        document.body.appendChild(temp);
                        temp.select();
                        document.execCommand('copy');
                        document.body.removeChild(temp);
                        alert("تم نسخ النتيجة: " + val);
                    }
                }
            </script>
        </body>
        </html>
        """
        
        st.components.v1.html(calculator_html, height=530)

    # --- استعراض سجل العملاء ---
    st.markdown("---")
    st.markdown("<div class='force-center'><h3 class='header-box' style='color: #0d8a95; font-family: \"Readex Pro\", sans-serif; font-weight: 600; margin-top: 20px; margin-bottom: 20px; font-size: 28px;'>استعراض سجل العملاء</h3></div>", unsafe_allow_html=True)
    
    conn = db.get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT f.id, f.customer_name, f.phone, f.address, f.furniture_type, f.site_status,
               COALESCE(d.designer_name, 'غير معين'),
               COALESCE(d.status, 'تحت الدراسة'),
               COALESCE(d.design_link, ''),
               COALESCE(d.notes, ''),
               COALESCE(d.design_docs, ''),
               COALESCE(f.media_paths, '')
        FROM FieldVisits f
        INNER JOIN ProjectDesigns d ON f.id = d.visit_id
        WHERE f.is_canceled = 0
        ORDER BY f.id DESC
    ''')
    saved_designs = c.fetchall()
    conn.close()
    
    if not saved_designs:
        st.info("لا توجد سجلات تصاميم محفوظة حالياً في النظام.")
    else:
        st.markdown("<p style='text-align: center; color: gray;'>اضغط على العميل لمشاهدة تفاصيل ومستندات ورسومات التصميم المبدئي واستيراد بياناته للتسعير المباشر</p>", unsafe_allow_html=True)
        
        for row in saved_designs:
            v_id, c_name, phone, address, f_type, s_status, designer, design_status, design_link, design_notes, design_docs, visit_media = row
            
            # Fetch Odoo number if existing
            conn = db.get_connection()
            c = conn.cursor()
            c.execute("SELECT odoo_no FROM Contracts WHERE client_name = ? OR notes LIKE ?", (c_name, f"%MHM{v_id:05d}%"))
            con_row = c.fetchone()
            conn.close()
            odoo_no = con_row[0].strip() if (con_row and con_row[0] and con_row[0].strip()) else ""
            
            odoo_tag = f" | 🔢 أودو: {odoo_no}" if odoo_no else ""
            
            with st.expander(f"📁 [{f'MHM{v_id:05d}'}]{odoo_tag} العميل: {c_name} | المصمم: {designer} | حالة التصميم: {design_status}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**اسم العميل:** {c_name}")
                    st.markdown(f"**رقم الهاتف:** {phone}")
                    st.markdown(f"**العنوان بالتفصيل:** {address}")
                    st.markdown(f"**نوع الأثاث المخطط:** {f_type}")
                with c2:
                    st.markdown(f"**المصمم المسؤول:** {designer}")
                    st.markdown(f"**حالة التصميم المبدئي:** {design_status}")
                    if design_link:
                        st.markdown(f"**🔗 رابط التصميم:** [افتح الرابط في نافذة جديدة]({design_link})")
                    else:
                        st.markdown("**🔗 رابط التصميم:** لا يوجد رابط متاح")
                    st.markdown(f"**حالة الموقع الفعلي:** {s_status}")
                    
                if design_notes:
                    st.info(f"📝 **ملاحظات المصمم:** {design_notes}")
                    
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    if design_docs:
                        st.markdown("##### 🎨 مستندات ورسومات التصميم المبدئي المرفقة:")
                        import os
                        import base64
                        paths = design_docs.split(",")
                        for p in paths:
                            if os.path.exists(p):
                                file_name = os.path.basename(p)
                                with open(p, "rb") as f:
                                    data = f.read()
                                b64 = base64.b64encode(data).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📥 تحميل تصميم: {file_name}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.info("⚠️ لم يتم إرفاق رسومات/ملفات تصميم لهذا العميل بعد.")
                        
                with col_f2:
                    if visit_media:
                        st.markdown("##### 📏 ملفات المقاسات الأصلية المرفقة:")
                        import os
                        import base64
                        paths = visit_media.split(",")
                        for p in paths:
                            if os.path.exists(p):
                                file_name = os.path.basename(p)
                                with open(p, "rb") as f:
                                    data = f.read()
                                b64 = base64.b64encode(data).decode()
                                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">📥 تحميل مقاسات: {file_name}</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("📋 استيراد بيانات التصميم للتسعير الفوري", key=f"load_d_{v_id}", use_container_width=True):
                    st.session_state['selected_pricing_visit_id'] = v_id
                    st.session_state['selected_pricing_cname'] = c_name
                    st.session_state['selected_pricing_furniture'] = f_type
                    st.success(f"تم تحميل بيانات التصميم للعميل {c_name} للتسعير في الأعلى!")
                    import time
                    time.sleep(1)
                    st.rerun()

    # Log Activity
    db.log_activity(
        username=st.session_state.get('username', 'Unknown'),
        employee_name=st.session_state.get('employee_name', 'Unknown'),
        action_type="استعراض",
        module="مسار التسعير",
        details="تم فتح مسار التسعير وحساب تكلفة مشروع"
    )

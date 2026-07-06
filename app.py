import streamlit as st
import pandas as pd
import database as db
import time
import os

# Initialize database ONCE per server session (not on every rerun)
if 'db_initialized' not in st.session_state:
    db.init_db()
    st.session_state['db_initialized'] = True


# Page Config
st.set_page_config(page_title="مسار هوم - منظومة إدارة المشاريع", page_icon="🪑", layout="wide", initial_sidebar_state="expanded")

# Custom CSS for FULL RTL and aesthetics (Light Cyan Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Readex+Pro:wght@300;400;500;600;700&family=El+Messiri:wght@400;500;600;700&family=Almarai:wght@300;400;700&display=swap');

    /* Hide Deploy Menu and Footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    /* Increase Sidebar Width */
    [data-testid="stSidebar"] {
        min-width: 330px !important;
    }

    /* Global RTL, Typography, and Background Color to match icons */
    .stApp, body, main {
        direction: rtl !important;
        font-family: 'Readex Pro', 'Almarai', 'Segoe UI', sans-serif !important;
        font-weight: 300 !important;
        background-color: #F8F9F9 !important;
    }
    
    /* Apply Readex Pro to user-visible text elements only */
    p, .stMarkdown, .stText, .stAlert, .stInfo,
    [class*="stTextInput"] input,
    [class*="stTextArea"] textarea,
    [class*="stSelectbox"] *,
    [class*="stRadio"] label,
    [class*="stCheckbox"] label,
    [class*="stNumberInput"] input,
    .stDataFrame, [data-testid="stTable"],
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
        font-family: 'Readex Pro', 'Almarai', sans-serif !important;
    }
    
    /* Hide Streamlit internal keyboard/accessibility artifacts that bleed through */
    [data-baseweb="input"] ~ div[role="none"],
    [class*="keyboard"],
    [aria-label*="keyboard"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* Readex Pro for display headings — elegant, bold presence for major titles */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Readex Pro', 'Almarai', sans-serif !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em;
    }
    
    /* Sidebar Navigation Font - Readex Pro, elegant and clean */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div {
        font-family: 'Readex Pro', 'Almarai', sans-serif !important;
        font-weight: 300 !important;
    }
    /* Sidebar headings keep Readex Pro */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        font-family: 'Readex Pro', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Text elements align to the right in RTL mode */
    p, div, h1, h2, h3, h4, h5, h6, span, label, .stMarkdown, .stText {
        text-align: right !important;
    }
    
    /* Exception for center aligned metric texts and specific headers */
    .metric-card h2, .metric-card h3, h1, div[data-testid="stMetricValue"] {
        text-align: center !important;
    }
    
    /* Center align headers in the sidebar (Company name, App name, Main Menu) */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4 {
        text-align: center !important;
        width: 100%;
    }
    
    /* Metric Cards Styling */
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0, 180, 216, 0.15);
        text-align: center;
        border-top: 5px solid #00b4d8;
        margin-bottom: 20px;
    }
    .metric-card h3 {
        margin-top: 0;
        font-size: 1.2rem;
        color: #0077b6;
    }
    .metric-card h2 {
        margin-bottom: 0;
        font-size: 2.8rem;
        color: #03045e;
        font-weight: bold;
    }
    
    /* Buttons Customization */
    .stButton>button, .stFormSubmitButton>button {
        background-color: #00b4d8 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover {
        background-color: #0096c7 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }

    /* Hide Header, Deploy Button, Main Menu, and Sidebar Toggle Icon across all Streamlit versions */
    header, 
    [data-testid="stHeader"], 
    .stAppHeader, 
    div[data-testid="stToolbar"], 
    div[data-testid="stAppToolbar"],
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
    }
    
    #MainMenu {
        display: none !important;
    }
    
    /* Hide the sidebar collapse/expand button which is showing the broken text */
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="stSidebarCollapseButton"],
    button[title="Collapse sidebar"],
    button[title="Expand sidebar"],
    button[aria-label="Collapse sidebar"],
    button[aria-label="Expand sidebar"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        font-size: 0 !important;
    }
    
    div[data-testid="stTooltipContent"] {
        display: none !important;
    }
    
    /* Add space between checkbox and text */
    [data-testid="stCheckbox"] div[data-testid="stMarkdownContainer"] {
        margin-right: 20px !important;
    }
    
    /* Form Inputs styling */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background-color: #ffffff;
        border: 1px solid #90e0ef;
        border-radius: 8px;
        text-align: right !important;
        direction: rtl !important;
    }
    
    /* Fix tab direction */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        direction: rtl;
        justify-content: flex-start;
    }
    
    /* Fix Sidebar Radio Buttons alignment */
    .stRadio label {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
    }
    .stRadio div[data-testid="stMarkdownContainer"] {
        flex-grow: 0 !important;
        margin-right: 10px !important;
    }
    
    /* Dataframes RTL */
    [data-testid="stDataFrame"], [data-testid="stTable"] {
        direction: rtl !important;
    }
    
    /* Table Headers & Cells */
    th, td {
        text-align: right !important;
    }
    div[data-testid="stCheckbox"] p {
        margin-right: 35px !important;
    }

    /* File Uploader Translation CSS Hack */
    div[data-testid="stFileUploadDropzone"] div div::before {
        content: "اسحب وأفلت الملفات هنا";
        display: block;
        text-align: center;
        color: #457b9d;
        font-weight: bold;
        margin-bottom: 5px;
    }
    div[data-testid="stFileUploadDropzone"] div div span {
        display: none !important;
    }
    div[data-testid="stFileUploadDropzone"] div div small {
        display: none !important;
    }
    div[data-testid="stFileUploadDropzone"] button::before {
        content: "استعراض الملفات ...";
        visibility: visible;
        display: block;
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        color: #0077b6;
        font-weight: bold;
        white-space: nowrap;
    }
    div[data-testid="stFileUploadDropzone"] button {
        color: transparent !important;
        position: relative;
    }
    div[data-testid="stFileUploadDropzone"] button svg {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Notification System Setup (Using Session State for persistence across reruns)
if 'success_msg' in st.session_state:
    st.toast(st.session_state.success_msg, icon='✅')
    st.success(st.session_state.success_msg)
    del st.session_state.success_msg

if 'error_msg' in st.session_state:
    st.toast(st.session_state.error_msg, icon='⚠️')
    st.error(st.session_state.error_msg)
    del st.session_state.error_msg

# --- AUTHENTICATION ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['role'] = None
    st.session_state['employee_name'] = None

if not st.session_state['logged_in']:
    # Inject background decorative shapes
    st.markdown("""
    <div style="position: fixed; top: -100px; right: 10%; width: 250px; height: 250px; background: linear-gradient(135deg, #a4b4e5 0%, #4bd1ce 100%); border-radius: 40px; transform: rotate(45deg); z-index: 0; opacity: 0.6;"></div>
    <div style="position: fixed; top: 15%; right: 5%; width: 80px; height: 80px; background: linear-gradient(135deg, #a4b4e5 0%, #4bd1ce 100%); border-radius: 20px; transform: rotate(20deg); z-index: 0; opacity: 0.7;"></div>
    <div style="position: fixed; bottom: -150px; left: -50px; width: 450px; height: 450px; background: linear-gradient(135deg, #0d8a95 0%, #4bd1ce 100%); border-radius: 80px; transform: rotate(35deg); z-index: 0; opacity: 0.9;"></div>
    <div style="position: fixed; bottom: 20%; left: 5%; width: 120px; height: 120px; background: linear-gradient(135deg, #4bd1ce 0%, #0d8a95 100%); border-radius: 30px; transform: rotate(15deg); z-index: 0; opacity: 0.5;"></div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
        /* Hide sidebar completely on login page */
        [data-testid="stSidebar"] {display: none !important;}
        header {display: none !important;}
        
        /* Make background light gray */
        .stApp, body, main {
            background-color: #f3f7f9 !important;
            overflow: hidden !important;
        }
        
        /* Center everything */
        .block-container {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 0 !important;
            max-width: 100% !important;
            z-index: 1;
        }
        
        /* Style the login card */
        [data-testid="stForm"] {
            background-color: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(10px);
            padding: 50px 40px !important;
            border-radius: 24px !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.05), 0 5px 15px rgba(0,0,0,0.03) !important;
            width: 100%;
            max-width: 420px;
            border: 1px solid rgba(255,255,255,0.5) !important;
            margin: 0 auto;
            position: relative;
            overflow: hidden;
        }
        
        /* Inner decorative blob for the form card */
        [data-testid="stForm"]::before {
            content: "";
            position: absolute;
            top: -50px;
            right: -50px;
            width: 150px;
            height: 150px;
            background: linear-gradient(135deg, #a4b4e5 0%, #4bd1ce 100%);
            border-radius: 40px;
            transform: rotate(45deg);
            opacity: 0.7;
            z-index: 0;
        }
        
        /* Typography overrides for form elements to be above the blob */
        [data-testid="stForm"] > div {
            position: relative;
            z-index: 1;
        }
        
        /* Style the inputs to have underline only */
        [data-testid="stForm"] .stTextInput>div>div>input {
            background-color: transparent !important;
            border: none !important;
            border-bottom: 2px solid #0d8a95 !important;
            border-radius: 0 !important;
            color: #2b2b2b !important;
            padding-right: 5px !important;
            box-shadow: none !important;
            transition: border-color 0.3s ease;
        }
        [data-testid="stForm"] .stTextInput>div>div>input:focus {
            border-bottom: 2px solid #4bd1ce !important;
        }
        
        /* Remove background from input wrapper */
        [data-testid="stForm"] .stTextInput>div>div {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* Style labels */
        [data-testid="stForm"] .stTextInput label p {
            color: #2b2b2b !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }
        
        /* Style the submit button */
        [data-testid="stForm"] button {
            background: linear-gradient(90deg, #4bd1ce 0%, #a4b4e5 100%) !important;
            color: white !important;
            border-radius: 30px !important;
            border: none !important;
            width: 100% !important;
            margin-top: 25px !important;
            padding: 12px !important;
            font-weight: bold !important;
            font-size: 16px !important;
            box-shadow: 0 4px 15px rgba(75, 209, 206, 0.4) !important;
            transition: transform 0.2s, box-shadow 0.2s !important;
        }
        [data-testid="stForm"] button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(75, 209, 206, 0.6) !important;
        }
        
        /* Add icons using CSS for inputs (Assuming first input is user, second is pass based on order) */
        [data-testid="stForm"] div.stTextInput:nth-of-type(1) > div > div::before {
            content: "📧";
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.5;
        }
        [data-testid="stForm"] div.stTextInput:nth-of-type(1) > div > div > input {
            padding-right: 30px !important;
        }
        
        [data-testid="stForm"] div.stTextInput:nth-of-type(2) > div > div::before {
            content: "🔒";
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
            opacity: 0.5;
        }
        [data-testid="stForm"] div.stTextInput:nth-of-type(2) > div > div > input {
            padding-right: 30px !important;
        }
        
        /* Fix the password eye icon position */
        [data-testid="stForm"] div[data-testid="stTextInput"] button[aria-label="Toggle password visibility"] {
            margin-top: -10px !important;
        }
        
        /* Style secondary button as a link for forgot password */
        [data-testid="stForm"] button[kind="secondaryFormSubmit"] {
            background: none !important;
            border: none !important;
            color: #0d8a95 !important;
            box-shadow: none !important;
            padding: 0 !important;
            font-size: 13px !important;
            font-weight: normal !important;
            margin-top: 10px !important;
            width: auto !important;
            display: flex !important;
            justify-content: flex-start !important;
        }
        [data-testid="stForm"] button[kind="secondaryFormSubmit"] p {
            font-size: 13px !important;
            color: #0d8a95 !important;
        }
        [data-testid="stForm"] button[kind="secondaryFormSubmit"]:hover {
            text-decoration: underline !important;
            transform: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    if st.session_state.get('show_forgot'):
        with st.form("forgot_password_form"):
            st.markdown("<h2 style='text-align: center !important; color: #0d5e65; font-family: \"Readex Pro\", sans-serif;'>إعادة تعيين كلمة المرور</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #6c757d; font-size: 13px; margin-bottom: 20px;'>سيتم إرسال طلب لمدير النظام لإعادة تعيين كلمة المرور الخاصة بك إلى الكلمة الافتراضية أو تزويدك بكلمة مرور جديدة.</p>", unsafe_allow_html=True)
            
            f_username = st.text_input("اسم المستخدم أو البريد الإلكتروني")
            
            col_b1, col_b2 = st.columns([1, 1])
            with col_b1:
                send_req = st.form_submit_button("إرسال الطلب", type="primary", use_container_width=True)
            with col_b2:
                cancel_req = st.form_submit_button("إلغاء", type="secondary", use_container_width=True)
                
            if send_req:
                if f_username:
                    # في بيئة حقيقية يتم إرسال رسالة أو بريد إلكتروني لمدير النظام هنا
                    st.success("تم إرسال طلب إعادة التعيين لمدير النظام بنجاح.")
                    st.session_state['show_forgot'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.warning("يرجى إدخال اسم المستخدم.")
            
            if cancel_req:
                st.session_state['show_forgot'] = False
                st.rerun()
    else:
        with st.form("login_form"):
            # Header text inside the card
            st.markdown("<h1 style='text-align: center !important; color: #0d5e65; font-family: \"Readex Pro\", sans-serif; font-weight: bold; font-size: 36px; margin-bottom: 5px; margin-top: 0;'>مسارات Masarat</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center !important; color: #2b2b2b; font-family: \"Readex Pro\", sans-serif; font-weight: 600; font-size: 20px; margin-bottom: 5px; margin-top: 0;'>دخول النظام</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #6c757d; font-size: 13px; margin-bottom: 30px;'>يرجى تسجيل الدخول للمتابعة</p>", unsafe_allow_html=True)
            
            username = st.text_input("اسم المستخدم", placeholder="username")
            password = st.text_input("كلمة المرور", type="password")
            
            forgot_pwd = st.form_submit_button("هل نسيت كلمة المرور؟", type="secondary")
            
            submitted = st.form_submit_button("دخول  ←", type="primary", use_container_width=True)
            
            if forgot_pwd:
                st.session_state['show_forgot'] = True
                st.rerun()
            
            if submitted:
                if username and password:
                    res = db.verify_user(username, password)
                    if res["success"]:
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['role'] = res["role"]
                        st.session_state['employee_name'] = res.get("employee_name", username)
                        db.log_activity(
                            username=username,
                            employee_name=res.get("employee_name", username),
                            action_type="تسجيل دخول",
                            module="تسجيل الدخول",
                            details=f"تم تسجيل الدخول بنجاح"
                        )
                        st.rerun()
                    else:
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة.")
                else:
                    st.warning("يرجى إدخال اسم المستخدم وكلمة المرور.")
                    
    # --- LOGIN PAGE FOOTER ---
    st.markdown("""
    <div style='position: fixed; bottom: 20px; left: 50%; transform: translateX(-50%); width: calc(100% - 40px); max-width: 800px; background-color: #e0fbfc; padding: 10px; border-radius: 8px; text-align: center; font-family: "Readex Pro", "Almarai", sans-serif; color: #0077b6; font-size: 14px; border: 1px solid #caf0f8; z-index: 100; display: flex; justify-content: center; align-items: center; gap: 5px; flex-wrap: wrap;'>
        <span dir="rtl">جميع الحقوق الفكرية للمنظومة مملوكة لشركة مسارات MASARAT (م. علي بن عيسى) © 2026</span> 
        <span>|</span> 
        <span dir="ltr">ALL RIGHTS RESERVED</span>
    </div>
    """, unsafe_allow_html=True)

    st.stop() # Stop execution here if not logged in

# --- ONLY RENDER SIDEBAR AND DASHBOARD HEADER IF LOGGED IN ---

# Title Header
st.markdown("""
<div style='background: linear-gradient(135deg, rgba(255,255,255,0.8) 0%, rgba(240,248,255,0.6) 100%); backdrop-filter: blur(10px); padding: 20px 30px; border-radius: 16px; box-shadow: 0 8px 32px rgba(0, 119, 182, 0.08); margin-top: 10px; margin-bottom: 30px; display: flex; align-items: center; justify-content: center; gap: 20px; flex-wrap: wrap; border: 1px solid rgba(255, 255, 255, 0.4); position: relative; overflow: hidden;'>
    <div style='position: absolute; top: -50px; right: -50px; width: 100px; height: 100px; background: rgba(0, 119, 182, 0.1); border-radius: 50%; blur: 20px;'></div>
    <div style='position: absolute; bottom: -30px; left: -30px; width: 80px; height: 80px; background: rgba(72, 202, 228, 0.15); border-radius: 50%; blur: 15px;'></div>
    <span style='font-family: "Readex Pro", sans-serif; font-weight: 400; color: #0077b6; font-size: 28px; z-index: 1;'>لوحة المعلومات</span>
    <span style='color: #0077b6; font-weight: 300; font-size: 30px; opacity: 0.3; z-index: 1;'>|</span>
    <span style='font-family: "Readex Pro", sans-serif; font-weight: 500; letter-spacing: 8px; color: #0096c7; font-size: 20px; opacity: 0.9; z-index: 1;'>DASHBOARD</span>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("<div style='text-align: center !important; width: 100%; color: #6c757d; font-size: 15px; margin-bottom: 25px; font-family: \"Readex Pro\", sans-serif; line-height: 1.6;'>تم ترخيص استخدام هذه النسخة من<br><span style='color: #023e8a; font-weight: bold;'>منظومة مسارات</span> لصالح...</div>", unsafe_allow_html=True)

col1, col2, col3 = st.sidebar.columns([1, 2, 1])
with col2:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    elif os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.markdown("<h2 style='text-align: center !important;'>🪑</h2>", unsafe_allow_html=True)

st.sidebar.markdown("<div style='text-align: center; width: 100%; margin-top: 15px;'><h2 style='color: #0077b6; margin: 0; font-family: \"Readex Pro\", sans-serif; font-weight: 700; font-size: 26px;'>شركة مسار هوم</h2></div>", unsafe_allow_html=True)

st.sidebar.markdown("<hr style='border: 1px solid #caf0f8; margin: 10px 0px;'>", unsafe_allow_html=True)

# --- ROLE PERMISSIONS ---
user_role = st.session_state['role']
emp_name = st.session_state.get('employee_name', st.session_state['username'])

# Determine if user has view-only access
is_observer = user_role == "Observer"
has_full_access = user_role == "Admin" or "الجميع" in user_role or is_observer

# Determine section access
can_access_visits = has_full_access or "الزيارة الميدانية" in user_role or user_role == "Surveyor"
can_access_crm = has_full_access or "إدارة العملاء" in user_role
can_access_helpdesk = has_full_access or "الدعم الفني" in user_role
can_access_checklist = has_full_access or "قائمة الفحص اليومي" in user_role
can_access_design = has_full_access or "إدارة التصاميم" in user_role or user_role == "Designer"
can_access_pricing = has_full_access or "إدارة التسعير" in user_role or user_role == "Admin" or user_role == "Financial"
can_access_contracts = has_full_access or "إدارة العقود" in user_role
can_access_production = has_full_access or "إدارة الإنتاج" in user_role or user_role == "Production"
can_access_finance = has_full_access or "الإدارة المالية" in user_role or user_role == "Financial"
can_access_journey = has_full_access or "تتبع رحلة العميل" in user_role or "تتبع مسار مشروع / عميل" in user_role or "مسار حركة العميل" in user_role
can_access_statistics = has_full_access or "إحصائيات" in user_role
can_delete = user_role == "Admin"

# Sidebar Auth Info
import datetime
current_hour = datetime.datetime.now().hour
greeting_time = "صباح الخير ☀️" if current_hour < 12 else "مساء الخير 🌙"

st.sidebar.markdown(f"""
<div style='display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center !important; background-color: #f8f9fa; padding: 15px; border-radius: 12px; border: 2px solid #0077b6; margin-bottom: 15px; font-family: "Readex Pro", "Almarai", sans-serif; box-shadow: 0 4px 8px rgba(0, 119, 182, 0.1);'>
    <div style='font-size: 18px; color: #023e8a; font-weight: 800; margin-bottom: 3px; text-align: center;'>السلام عليكم 👋</div>
    <div style='font-size: 14px; color: #0096c7; font-weight: 600; margin-bottom: 10px; text-align: center;'>{greeting_time}</div>
    <div style='font-size: 15px; color: #333; text-align: center;'>يـــــا <span style='background: linear-gradient(120deg, #d4fc79 0%, #96e6a1 100%); color: #1b4332; padding: 3px 10px; border-radius: 20px; font-weight: bold; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>{emp_name}</span></div>
    <div style='width: 100%; margin-top: 10px; border-top: 1px dashed #caf0f8; padding-top: 6px; display: flex; justify-content: flex-end;'><span style='font-size: 14px; color: #111111; font-weight: 900; font-family: monospace; direction: ltr;'>@{st.session_state['username']}</span></div>
</div>
""", unsafe_allow_html=True)

# Init session state for menu
if 'menu_choice' not in st.session_state:
    st.session_state['menu_choice'] = "📊 لوحة القيادة (Dashboard)"

if st.sidebar.button("🏠 القائمة الرئيسية", use_container_width=True):
    st.session_state['menu_choice'] = "📊 لوحة القيادة (Dashboard)"
    st.session_state['override_page'] = None
    st.rerun()

menu = [
    "📊 لوحة القيادة (Dashboard)",
    "💬 مسار التواصل",
    "✅ مسار الفحص اليومي",
    "📏 مسار رفع المقاسات",
    "🎨 مسار التصاميم",
    "🏷️ مسار التسعير",
    "📋 مسار العقود",
    "💰 مسار الخزينة",
    "🏭 مسار الانتاج",
    "👥 مسار العملاء",
    "🛠️ مسار الدعم الفني",
    "🗺️ مسار حركة العميل",
    "🔍 مسار حركة المستخدم",
    "📈 إحصائيات",
    "ℹ️ حول مسارات"
]

def on_menu_change():
    st.session_state['override_page'] = None


# Get unread counts with a 5-second cache to reduce DB hits on every rerun
_now = time.time()
_cache_key = f"unread_cache_{st.session_state['username']}"
_cache_time_key = f"unread_cache_time_{st.session_state['username']}"
if _cache_key not in st.session_state or (_now - st.session_state.get(_cache_time_key, 0)) > 5:
    st.session_state[_cache_key] = db.get_unread_counts(st.session_state['username'])
    st.session_state[_cache_time_key] = _now
unread_counts = st.session_state[_cache_key]
total_unread = sum(unread_counts.values())


def menu_format(option):
    if option == "💬 مسار التواصل" and total_unread > 0:
        return f"{option} 🔴({total_unread})"
    return option

choice_radio = st.sidebar.radio("اختر القسم:", menu, key="menu_choice", label_visibility="collapsed", on_change=on_menu_change, format_func=menu_format)

st.sidebar.markdown("<hr style='border: 1px solid #caf0f8; margin: 10px 0px;'>", unsafe_allow_html=True)

if st.sidebar.button("🔑 تغيير كلمة المرور", use_container_width=True):
    st.session_state['override_page'] = "🔑 تغيير كلمة المرور"
    st.rerun()

if user_role == "Admin":
    if st.sidebar.button("⚙️ إدارة الحسابات", use_container_width=True):
        st.session_state['override_page'] = "⚙️ إدارة الحسابات"
        st.rerun()

if st.sidebar.button("🚩 تسجيل الخروج", use_container_width=True):
    # سجّل الخروج قبل مسح الجلسة
    db.log_activity(
        username=st.session_state.get('username', ''),
        employee_name=st.session_state.get('employee_name', ''),
        action_type="تسجيل خروج",
        module="تسجيل الدخول",
        details="تسجيل الخروج من المنظومة"
    )
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['role'] = None
    st.session_state['employee_name'] = None
    # Clear menu
    for key in ['menu_choice', 'override_page', 'selected_client_name', 'selected_client_phone']:
        st.session_state.pop(key, None)
    st.rerun()

if st.session_state.get('override_page'):
    choice = st.session_state['override_page']
else:
    choice = choice_radio
@st.cache_data(ttl=3600)
def fetch_weather_data(latitude, longitude):
    import urllib.request, json
    url_main = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current=temperature_2m,relative_humidity_2m,surface_pressure,weather_code&hourly=temperature_2m&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
    url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={latitude}&longitude={longitude}&current=wave_height"
    
    result = {}
    try:
        req_main = urllib.request.Request(url_main, headers={'User-Agent': 'MasarHomeApp/1.0'})
        with urllib.request.urlopen(req_main, timeout=5) as r:
            result['main'] = json.loads(r.read().decode())
    except:
        return None
        
    try:
        req_marine = urllib.request.Request(url_marine, headers={'User-Agent': 'MasarHomeApp/1.0'})
        with urllib.request.urlopen(req_marine, timeout=3) as r:
            result['marine'] = json.loads(r.read().decode())
    except:
        result['marine'] = None
        
    return result

if choice == "💬 مسار التواصل":
    st.markdown("<h2 style='text-align: center; color: #0077b6; font-family: \"Readex Pro\", sans-serif;'>💬 مسار التواصل (صندوق البريد والمحادثات)</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray;'>تواصل بشكل مباشر مع فريق العمل.</p><hr style='border-top: 1px solid #caf0f8;'>", unsafe_allow_html=True)

    # Cache user list for 30 seconds (rarely changes)
    _u_now = time.time()
    if 'all_users_cache' not in st.session_state or (_u_now - st.session_state.get('all_users_cache_time', 0)) > 30:
        st.session_state['all_users_cache'] = db.get_all_users()
        st.session_state['all_users_cache_time'] = _u_now
    raw_users = st.session_state['all_users_cache']
    # Format raw_users into list of dicts for chat logic compatibility
    users = [{"id": u[0], "username": u[1], "role": u[2], "employee_name": u[3] if len(u)>3 and u[3] else u[1]} for u in raw_users]
    
    current_user = st.session_state['username']
    
    # Exclude current user
    chat_users = [u for u in users if u['username'] != current_user]
    chat_users_dict = {u['username']: u for u in chat_users}
    
    # Get unread counts (reuse the sidebar cache – already fetched above)
    unread_counts = st.session_state.get(f"unread_cache_{current_user}", {})
    
    def chat_format(username):
        u = chat_users_dict[username]
        label = f"{u['employee_name']} ({u['username']})"
        if unread_counts.get(username, 0) > 0:
            label += f" 🔴({unread_counts[username]})"
        return label
        
    if user_role == "Admin":
        tab_users, tab_groups, tab_admin = st.tabs(["👤 الأفراد (مباشر ومسار تعميم)", "👥 المجموعات (غرف الدردشة)", "🕵️‍♂️ سجل المراسلات (مراقبة)"])
    else:
        tab_users, tab_groups = st.tabs(["👤 الأفراد (مباشر ومسار تعميم)", "👥 المجموعات (غرف الدردشة)"])
    
    with tab_users:
        col1, col2 = st.columns([1, 2.5])
        with col1:
            with st.container(border=True):
                st.markdown("<h4 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; margin-top:0;'>قائمة الموظفين</h4>", unsafe_allow_html=True)
                # Use multiselect instead of radio
                selected_usernames = st.multiselect("اختر موظفاً (أو أكثر):", list(chat_users_dict.keys()), format_func=chat_format)
            
        with col2:
            if not selected_usernames:
                st.info("يرجى تحديد موظف واحد على الأقل من القائمة لبدء المحادثة أو إرسال تعميم.")
            elif len(selected_usernames) == 1:
                selected_username = selected_usernames[0]
                target_user = chat_users_dict[selected_username]
                st.markdown(f"<h4 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; background-color: #e0fbfc; padding: 10px; border-radius: 8px;'>المحادثة مع: {target_user['employee_name']}</h4>", unsafe_allow_html=True)
                
                # Mark messages as read if there are unread ones
                if unread_counts.get(selected_username, 0) > 0:
                    db.mark_messages_read(selected_username, current_user)
                    unread_counts[selected_username] = 0 # locally update
                    st.rerun() # Force a rerun so the sidebar menu badge disappears instantly
                
                # Display chat history
                history = db.get_chat_history(current_user, selected_username)
                
                chat_container = st.container(height=400)
                with chat_container:
                    if not history:
                        st.info("لا توجد رسائل سابقة. ابدأ المحادثة الآن!")
                    else:
                        for msg in history:
                            msg_id, sender, receiver, content, timestamp, is_read, group_id = msg
                            if group_id is not None: continue # Skip group messages just in case
                            
                            is_me = (sender == current_user)
                            time_str = timestamp[:16] # Remove seconds
                            
                            if is_me:
                                st.chat_message("user", avatar="👤").markdown(f"**أنا:** {content}\n\n<div style='text-align: left; font-size: 10px; color: gray;'>{time_str}</div>", unsafe_allow_html=True)
                            else:
                                st.chat_message("assistant", avatar="💬").markdown(f"**{target_user['employee_name']}:** {content}\n\n<div style='text-align: left; font-size: 10px; color: gray;'>{time_str}</div>", unsafe_allow_html=True)
                
                # Input field
                new_msg = st.chat_input("اكتب رسالتك هنا...", key="single_chat_input")
                if new_msg:
                    db.send_message(current_user, selected_username, new_msg)
                    st.rerun()
                
                # Add a manual refresh and download buttons
                st.markdown("<br>", unsafe_allow_html=True)
                col_ref, col_save = st.columns(2)
                with col_ref:
                    if st.button("🔄 تحديث المحادثة", use_container_width=True):
                        st.rerun()
                with col_save:
                    chat_text = ""
                    for msg in history:
                        msg_id, sender, receiver, content, timestamp, is_read, group_id = msg
                        s_name = "أنا" if sender == current_user else target_user['employee_name']
                        r_name = "أنا" if receiver == current_user else target_user['employee_name']
                        chat_text += f"[{timestamp}] {s_name} -> {r_name}: {content}\n"
                    st.download_button(
                        label="💾 حفظ/تحميل المحادثة",
                        data=chat_text,
                        file_name=f"chat_{current_user}_{selected_username}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
            else:
                # BROADCAST MODE
                st.markdown(f"<h4 style='color: #d62828; font-family: \"Readex Pro\", sans-serif; background-color: #ffe5d9; padding: 10px; border-radius: 8px;'>إرسال تعميم إلى ({len(selected_usernames)}) موظفين</h4>", unsafe_allow_html=True)
                st.info("أنت الآن تقوم بإرسال رسالة جماعية. ستصل الرسالة لكل موظف في محادثته الخاصة معك بشكل فردي ولن يرى ردود الآخرين.")
                
                new_broadcast = st.chat_input("اكتب رسالة التعميم هنا...", key="broadcast_chat_input")
                if new_broadcast:
                    for u in selected_usernames:
                        db.send_message(current_user, u, new_broadcast)
                    st.success("تم إرسال التعميم لجميع الموظفين المحددين بنجاح!")
 
    with tab_groups:
        st.markdown("<h4 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif;'>إدارة المجموعات (غرف الدردشة)</h4>", unsafe_allow_html=True)
        
        # Top section: Create new group (restricted to Admin)
        if user_role == "Admin":
            with st.expander("➕ إنشاء مجموعة جديدة"):
                with st.form("create_group_form"):
                    new_group_name = st.text_input("اسم المجموعة:")
                    new_group_members = st.multiselect("اختر أعضاء المجموعة:", list(chat_users_dict.keys()), format_func=lambda x: f"{chat_users_dict[x]['employee_name']} ({x})")
                    submit_group = st.form_submit_button("إنشاء المجموعة")
                    if submit_group:
                        if not new_group_name:
                            st.error("يرجى كتابة اسم المجموعة.")
                        elif not new_group_members:
                            st.error("يرجى اختيار عضو واحد على الأقل للمجموعة.")
                        else:
                            db.create_chat_group(new_group_name, current_user, new_group_members)
                            st.success(f"تم إنشاء مجموعة '{new_group_name}' بنجاح!")
                            st.rerun()
        
        st.markdown("<hr style='border-top: 1px solid #caf0f8;'>", unsafe_allow_html=True)
        
        # Bottom section: Select and chat in a group
        user_groups = db.get_user_groups(current_user)
        if not user_groups:
            if user_role == "Admin":
                st.info("أنت لست عضواً في أي مجموعة حالياً. يمكنك إنشاء واحدة من الأعلى.")
            else:
                st.info("أنت لست عضواً في أي مجموعة حالياً.")
        else:
            group_options = {g[0]: f"{g[1]} (أنشئت بواسطة {g[2]})" for g in user_groups}
            selected_group_id = st.selectbox("اختر المجموعة للدخول إليها:", list(group_options.keys()), format_func=lambda x: group_options[x])
            
            if selected_group_id:
                group_name = [g[1] for g in user_groups if g[0] == selected_group_id][0]
                members = db.get_group_members(selected_group_id)
                member_names = ", ".join([m['employee_name'] for m in members])
                
                st.markdown(f"<h4 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif; background-color: #e0fbfc; padding: 10px; border-radius: 8px;'>👥 غرفة: {group_name}</h4>", unsafe_allow_html=True)
                st.caption(f"الأعضاء: {member_names}")
                
                history = db.get_group_messages(selected_group_id)
                
                group_chat_container = st.container(height=400)
                with group_chat_container:
                    if not history:
                        st.info("لا توجد رسائل في هذه المجموعة. كن أول من يبدأ بالحديث!")
                    else:
                        for msg in history:
                            msg_id, sender, content, timestamp = msg
                            is_me = (sender == current_user)
                            time_str = timestamp[:16]
                            
                            # Get sender display name
                            if is_me:
                                sender_display = "أنا"
                            else:
                                sender_user_obj = next((u for u in users if u['username'] == sender), None)
                                sender_display = sender_user_obj['employee_name'] if sender_user_obj else sender
                                
                            if is_me:
                                st.chat_message("user", avatar="👤").markdown(f"**أنا:** {content}\n\n<div style='text-align: left; font-size: 10px; color: gray;'>{time_str}</div>", unsafe_allow_html=True)
                            else:
                                st.chat_message("assistant", avatar="💬").markdown(f"**{sender_display}:** {content}\n\n<div style='text-align: left; font-size: 10px; color: gray;'>{time_str}</div>", unsafe_allow_html=True)
                
                # Input field
                new_group_msg = st.chat_input("اكتب رسالتك في المجموعة...", key=f"group_input_{selected_group_id}")
                if new_group_msg:
                    db.send_group_message(current_user, selected_group_id, new_group_msg)
                    st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                col_btn_refresh, col_btn_save, col_btn_del = st.columns(3)
                with col_btn_refresh:
                    if st.button("🔄 تحديث رسائل المجموعة", key=f"refresh_group_{selected_group_id}", use_container_width=True):
                        st.rerun()
                
                with col_btn_save:
                    group_text = ""
                    for msg in history:
                        msg_id, sender, content, timestamp = msg
                        s_name = "أنا" if sender == current_user else (next((u['employee_name'] for u in users if u['username'] == sender), None) or sender)
                        group_text += f"[{timestamp}] {s_name}: {content}\n"
                    st.download_button(
                        label="💾 حفظ المحادثة",
                        data=group_text,
                        file_name=f"group_{group_name}.txt",
                        mime="text/plain",
                        key=f"save_group_{selected_group_id}",
                        use_container_width=True
                    )
                
                with col_btn_del:
                    if user_role == "Admin":
                        if st.button("❌ إلغاء المجموعة", key=f"delete_group_{selected_group_id}", use_container_width=True):
                            db.delete_chat_group(selected_group_id)
                            st.success("تم إلغاء المجموعة بنجاح!")
                            import time
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.write("") # empty placeholder

    if user_role == "Admin":
        with tab_admin:
            st.markdown("<h4 style='color: #0077b6; font-family: \"Readex Pro\", sans-serif;'>🕵️‍♂️ سجل المراسلات (مراقبة)</h4>", unsafe_allow_html=True)
            st.info("هذا القسم متاح للمدير العام فقط ويتيح لك الاطلاع على المحادثات الفردية بين أي موظفين.")
            
            c1, c2 = st.columns(2)
            with c1:
                admin_user1 = st.selectbox(
                    "الطرف الأول:", 
                    ["الكل"] + list(chat_users_dict.keys()), 
                    format_func=lambda x: "الكل (جميع المحادثات)" if x == "الكل" else f"{chat_users_dict[x]['employee_name']} ({x})", 
                    key="admin_u1"
                )
            with c2:
                admin_user2 = st.selectbox(
                    "الطرف الثاني:", 
                    ["الكل"] + list(chat_users_dict.keys()), 
                    format_func=lambda x: "الكل (جميع المحادثات)" if x == "الكل" else f"{chat_users_dict[x]['employee_name']} ({x})", 
                    key="admin_u2"
                )
            
            if admin_user1 and admin_user2:
                if admin_user1 != "الكل" and admin_user2 != "الكل" and admin_user1 == admin_user2:
                    st.warning("الرجاء اختيار موظفين مختلفين.")
                else:
                    if admin_user1 == "الكل" and admin_user2 == "الكل":
                        admin_history = db.get_all_private_messages()
                        title_text = "**جميع المراسلات الخاصة بين جميع الموظفين**"
                    elif admin_user1 == "الكل":
                        admin_history = db.get_all_user_chat_history(admin_user2)
                        title_text = f"**جميع المراسلات الخاصة بالموظف: {chat_users_dict[admin_user2]['employee_name']}**"
                    elif admin_user2 == "الكل":
                        admin_history = db.get_all_user_chat_history(admin_user1)
                        title_text = f"**جميع المراسلات الخاصة بالموظف: {chat_users_dict[admin_user1]['employee_name']}**"
                    else:
                        admin_history = db.get_chat_history(admin_user1, admin_user2)
                        title_text = f"**سجل المحادثة بين: {chat_users_dict[admin_user1]['employee_name']} ↔️ {chat_users_dict[admin_user2]['employee_name']}**"
                        
                    if not admin_history:
                        st.info("لا توجد مراسلات.")
                    else:
                        st.markdown(title_text)
                        admin_chat_container = st.container(height=400)
                        with admin_chat_container:
                            for msg in admin_history:
                                msg_id, sender, receiver, content, timestamp, is_read, group_id = msg
                                sender_name = chat_users_dict[sender]['employee_name'] if sender in chat_users_dict else (st.session_state.get('employee_name', sender) if sender == current_user else sender)
                                receiver_name = chat_users_dict[receiver]['employee_name'] if receiver in chat_users_dict else (st.session_state.get('employee_name', receiver) if receiver == current_user else receiver)
                                
                                if admin_user1 != "الكل":
                                    align = "right" if sender == admin_user1 else "left"
                                    bg_color = "#e0fbfc" if sender == admin_user1 else "#f8f9fa"
                                elif admin_user2 != "الكل":
                                    align = "right" if sender == admin_user2 else "left"
                                    bg_color = "#e0fbfc" if sender == admin_user2 else "#f8f9fa"
                                else:
                                    align = "right"
                                    bg_color = "#e0fbfc"
                                
                                if admin_user1 == "الكل" or admin_user2 == "الكل":
                                    label_text = f"<b>{sender_name} ➡️ {receiver_name}:</b>"
                                else:
                                    label_text = f"<b>{sender_name}:</b>"
                                    
                                st.markdown(f"<div style='text-align:{align}; background-color:{bg_color}; padding:10px; border-radius:8px; margin-bottom:5px; border: 1px solid #caf0f8;'>{label_text} {content} <br><small style='color:gray;'>{timestamp[:16]}</small></div>", unsafe_allow_html=True)
                                
                        st.markdown("<br>", unsafe_allow_html=True)
                        admin_chat_text = ""
                        for msg in admin_history:
                            msg_id, sender, receiver, content, timestamp, is_read, group_id = msg
                            s_name = chat_users_dict[sender]['employee_name'] if sender in chat_users_dict else (st.session_state.get('employee_name', sender) if sender == current_user else sender)
                            r_name = chat_users_dict[receiver]['employee_name'] if receiver in chat_users_dict else (st.session_state.get('employee_name', receiver) if receiver == current_user else receiver)
                            admin_chat_text += f"[{timestamp}] {s_name} -> {r_name}: {content}\n"
                        st.download_button(
                            label="💾 حفظ/تحميل سجل هذه المحادثة كملف نصي",
                            data=admin_chat_text,
                            file_name=f"monitored_chat_{admin_user1}_{admin_user2}.txt",
                            mime="text/plain",
                            key=f"save_admin_chat_{admin_user1}_{admin_user2}",
                            use_container_width=True
                        )


elif choice == "📊 لوحة القيادة (Dashboard)":

    
    # === NEW DASHBOARD WIDGETS ===
    import datetime
    import streamlit.components.v1 as components
    
    today_date = datetime.date.today()
    st.markdown("""
    <style>
        .premium-card {
            background: linear-gradient(145deg, #ffffff, #f6f8fb);
            border: 1px solid rgba(255, 255, 255, 0.9);
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
            box-shadow: 0 4px 15px rgba(0, 119, 182, 0.04);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
            direction: rtl;
        }
        .premium-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0, 119, 182, 0.12);
        }
        .premium-card::before {
            content: '';
            position: absolute;
            top: 0;
            right: 0;
            height: 100%;
            width: 4px;
            background: linear-gradient(to bottom, #0077b6, #48cae4);
            border-radius: 0 14px 14px 0;
        }
        .dash-header {
            text-align: center;
            font-family: "Readex Pro", sans-serif;
            font-weight: 800;
            color: #03045e;
            background: linear-gradient(90deg, transparent, rgba(0,119,182,0.05), transparent);
            padding: 12px;
            border-radius: 10px;
            margin-bottom: 20px;
            font-size: 18px;
        }
        [data-testid="column"]:has(#col2-header) {
            border-right: 1px dashed rgba(0,119,182,0.15);
            border-left: 1px dashed rgba(0,119,182,0.15);
            padding: 0 20px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    dash_col1, dash_col2, dash_col3 = st.columns(3)
    
    with dash_col1:
        st.markdown("<div class='dash-header'>📅 مواعيد اليوم</div>", unsafe_allow_html=True)
        all_visits = db.get_all_field_visits()
        if all_visits:
            # Deduplicate by customer name (keep the one with the highest ID/latest)
            all_visits = sorted(all_visits, key=lambda x: x[0], reverse=True)
            seen_customers = set()
            dedup_visits = []
            for v in all_visits:
                if v[1] not in seen_customers:
                    seen_customers.add(v[1])
                    dedup_visits.append(v)

            today_visits = [v for v in dedup_visits if str(v[6]) == str(today_date)]
            if today_visits:
                for v in today_visits:
                    st.markdown(f"""
                    <div class='premium-card'>
                        <div style='color: #023e8a; font-weight: bold; font-size: 15px; margin-bottom: 5px;'>{v[1]}</div>
                        <div style='color: #6c757d; font-size: 13px;'>⏰ {v[7]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("لا توجد مواعيد مجدولة لهذا اليوم.")
                
            st.markdown("<div class='dash-header' style='margin-top: 30px; font-size: 16px; color: #0077b6;'>🔜 مواعيد قادمة (5 أيام)</div>", unsafe_allow_html=True)
            upcoming_visits = []
            for v in dedup_visits:
                try:
                    v_dt = datetime.datetime.strptime(str(v[6]), "%Y-%m-%d").date()
                    delta = (v_dt - today_date).days
                    if 1 <= delta <= 5:
                        upcoming_visits.append((v_dt, v))
                except:
                    pass
            
            if upcoming_visits:
                upcoming_visits.sort(key=lambda x: x[0])
                for v_dt, v in upcoming_visits:
                    st.markdown(f"""
                    <div class='premium-card' style='border-right: 4px solid #48cae4;'>
                        <div style='color: #023e8a; font-weight: bold; font-size: 14px; margin-bottom: 4px;'>{v[1]}</div>
                        <div style='color: #6c757d; font-size: 12px; display: flex; gap: 10px;'>
                            <span>📅 {v[6]}</span>
                            <span>⏰ {v[7]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='text-align: center; font-size: 14px; color: #adb5bd;'>لا توجد مواعيد قادمة قريباً.</p>", unsafe_allow_html=True)
        else:
            st.success("لا توجد مواعيد مجدولة لهذا اليوم.")
            
    with dash_col2:
        st.markdown("<div id='col2-header' class='dash-header'>👥 أحدث العملاء</div>", unsafe_allow_html=True)
        all_custs = db.get_all_customers()
        if all_custs:
            conn = db.get_connection()
            c_db = conn.cursor()
            latest_custs = sorted(all_custs, key=lambda x: x[0], reverse=True)[:4]
            for c in latest_custs:
                c_id, c_name, phone, address, notes = c
                
                # Find date from FieldVisits
                c_db.execute("SELECT visit_date FROM FieldVisits WHERE customer_name = ? OR phone = ? ORDER BY id DESC LIMIT 1", (c_name, phone))
                row_date = c_db.fetchone()
                if row_date and row_date[0]:
                    date_str = row_date[0]
                else:
                    fallback_dates = {
                        "ياسر قدور": "2026-06-25",
                        "معتز البخاري": "2026-06-23",
                        "شهد هويدي": "2026-06-21",
                        "علي بن عيسى": "2026-06-19"
                    }
                    date_str = fallback_dates.get(c_name, "2026-06-20")
                    
                st.markdown(f"""
                <div class='premium-card'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'>
                        <span style='color: #023e8a; font-weight: bold; font-size: 15px;'>{c_name}</span>
                        <span style='color: #48cae4; font-size: 12px; font-weight: 600; background: rgba(72,202,228,0.1); padding: 2px 8px; border-radius: 10px;'>{date_str}</span>
                    </div>
                    <div style='color: #6c757d; font-size: 13px;'>📞 <span style='font-family: monospace;'>{phone}</span></div>
                </div>
                """, unsafe_allow_html=True)
            conn.close()
        else:
            st.info("لم يتم تسجيل عملاء بعد.")
            
    with dash_col3:
        st.markdown("<div class='dash-header'>⛅ حالة الطقس</div>", unsafe_allow_html=True)
        
        cities_coords = {
            "طرابلس": (32.8892, 13.1906),
            "بنغازي": (32.1167, 20.0667),
            "مصراتة": (32.3754, 15.0925),
            "الزاوية": (32.7522, 12.7278),
            "صبراتة": (32.7933, 12.4886),
            "العجيلات": (32.7500, 12.3750),
            "زوارة": (32.9333, 12.0833),
            "سبها": (27.0377, 14.4283)
        }
        
        selected_city = st.selectbox("اختر المدينة:", list(cities_coords.keys()), label_visibility="collapsed")
        lat, lon = cities_coords[selected_city]
        
        w_data = fetch_weather_data(lat, lon)
        if w_data and 'main' in w_data:
            main_data = w_data['main']
            current = main_data.get('current', {})
            daily = main_data.get('daily', {})
            hourly = main_data.get('hourly', {})
            
            temp_now = current.get('temperature_2m', '--')
            code = current.get('weather_code', -1)
            humidity = current.get('relative_humidity_2m', '--')
            pressure_hpa = current.get('surface_pressure', '--')
            pressure = f"{pressure_hpa / 1013.25:.3f}" if pressure_hpa != '--' else '--'
            
            t_max = daily.get('temperature_2m_max', ['--'])[0] if daily.get('temperature_2m_max') else '--'
            t_min = daily.get('temperature_2m_min', ['--'])[0] if daily.get('temperature_2m_min') else '--'
            
            wave_height = '--'
            sea_state = 'غير متوفر'
            if w_data.get('marine') and 'current' in w_data['marine']:
                wh = w_data['marine']['current'].get('wave_height')
                if wh is not None:
                    wave_height = f"{wh}m"
                    if wh < 0.5: sea_state = "هادئ 🌊"
                    elif wh < 1.25: sea_state = "خفيف الموج 🌊"
                    elif wh < 2.5: sea_state = "معتدل 🌊"
                    elif wh < 4.0: sea_state = "مضطرب ⚠️"
                    else: sea_state = "هائج ⛔"
            
            emojis = {0:"☀️", 1:"🌤️", 2:"⛅", 3:"☁️", 45:"🌫️", 48:"🌫️", 51:"🌧️", 53:"🌧️", 55:"🌧️", 61:"🌧️", 63:"🌧️", 65:"🌧️", 71:"❄️", 73:"❄️", 75:"❄️", 95:"⛈️", 96:"⛈️", 99:"⛈️"}
            emoji = emojis.get(code, "🌡️")
            
            st.markdown(f"""
            <div style='background-color: #f1f8ff; padding: 10px; border-radius: 10px; border-right: 4px solid #0077b6;'>
                <h2 style='margin:0; color:#0077b6; text-align:center;'>{emoji} {temp_now}°C</h2>
                <div style='color: gray; font-size: 13px; margin-top: 5px; text-align:center;'>
                    <b>العظمى:</b> <span style='color:#d62828;'>{t_max}°C</span> | 
                    <b>الصغرى:</b> <span style='color:#023e8a;'>{t_min}°C</span>
                </div>
                <hr style='margin: 8px 0; border: 0.5px solid #d0e8f2;'>
                <div style='color: #457b9d; font-size: 12px; display: flex; justify-content: space-between;'>
                    <span>💧 الرطوبة: <b>{humidity}%</b></span>
                    <span>🧭 الضغط: <b>{pressure} atm</b></span>
                </div>
                <div style='color: #457b9d; font-size: 12px; text-align:center; margin-top: 5px;'>
                    حالة البحر: <b>{sea_state}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            try:
                import datetime, pandas as pd
                times = hourly.get('time', [])
                temps = hourly.get('temperature_2m', [])
                now_str = datetime.datetime.now().strftime("%Y-%m-%dT%H:00")
                idx = times.index(now_str) if now_str in times else datetime.datetime.now().hour
                
                next_12_temps = temps[idx:idx+12]
                next_12_times = [t.split("T")[1] for t in times[idx:idx+12]]
                
                df_temps = pd.DataFrame({"الحرارة (°C)": next_12_temps}, index=next_12_times)
                st.markdown("<p style='font-size:12px; color:gray; margin-top:10px; margin-bottom:5px; text-align:center;'>التوقعات (12 ساعة القادمة)</p>", unsafe_allow_html=True)
                st.line_chart(df_temps, height=130)
            except Exception:
                pass
        else:
            st.error("تعذر جلب بيانات الطقس حالياً.")

    st.markdown("---")
    
    # 🔔 Automated Reminders System
    raw_visits = db.get_all_field_visits()
    if raw_visits:
        # Deduplicate visits by customer_name (keep highest ID/latest)
        raw_visits = sorted(raw_visits, key=lambda x: x[0], reverse=True)
        seen_reminders = set()
        visits = []
        for v in raw_visits:
            if v[1] not in seen_reminders:
                seen_reminders.add(v[1])
                visits.append(v)
                
        import datetime
        now = datetime.datetime.now()
        urgent_visits = []
        warning_visits = []
        future_visits = []
        
        for v in visits:
            v_id, c_name, phone = v[0], v[1], v[2]
            v_date, v_time = v[6], v[7]
            is_contacted = v[11] if len(v) > 11 else 0
            
            if is_contacted in (0, 2, '0', '2') or is_contacted is None:
                # Parse v_time properly for old format "14:30:00" and new format "02:30 مساءً"
                time_parts = str(v_time).split(" ")
                time_str = time_parts[0]
                period = time_parts[1] if len(time_parts) > 1 else ""
                try:
                    t_comps = time_str.split(':')
                    h = int(t_comps[0])
                    m = int(t_comps[1])
                    if period == 'مساءً' and h != 12: h += 12
                    elif period == 'صباحاً' and h == 12: h = 0
                    
                    visit_dt = datetime.datetime.strptime(str(v_date), "%Y-%m-%d").replace(hour=h, minute=m)
                    time_diff = visit_dt - now
                    hours_diff = time_diff.total_seconds() / 3600
                    
                    if hours_diff <= 24:
                        urgent_visits.append((v_id, c_name, phone, visit_dt, hours_diff))
                    elif 24 < hours_diff <= 48:
                        warning_visits.append((v_id, c_name, phone, visit_dt, hours_diff))
                    else:
                        future_visits.append((v_id, c_name, phone, visit_dt, hours_diff))
                except Exception as e:
                    # Ignore parsing errors for malformed legacy data
                    pass
        
        if urgent_visits or warning_visits or future_visits:
            st.markdown("<h3 style='color: #d62828; text-align: center; margin-top: 20px;'>🔔 تنبيهات وتذكير المواعيد الميدانية</h3>", unsafe_allow_html=True)
            
            def render_reminder_item(v_id, c_name, phone, visit_dt, hours_diff, urgency):
                col_text, col_btn1, col_btn2 = st.columns([4, 1, 1])
                with col_text:
                    if urgency == "urgent":
                        if hours_diff < 0:
                            st.error(f"🔴 **تنبيه فائت!** موعد العميل **{c_name}** ({phone}) كان منذ **{abs(int(hours_diff))} ساعة**. يرجى التواصل فوراً!")
                        else:
                            st.error(f"🔴 **عاجل (أقل من 24 ساعة):** موعد العميل **{c_name}** ({phone}) متبقي له **{int(hours_diff)} ساعة**. يرجى التواصل لتأكيد الحجز فوراً!")
                    elif urgency == "warning":
                        st.warning(f"🟡 **تذكير (بين 24 و 48 ساعة):** موعد العميل **{c_name}** ({phone}) متبقي له **{int(hours_diff)} ساعة**. يفضل التواصل معه اليوم للتأكيد.")
                    else:
                        st.info(f"🔵 **موعد قادم:** العميل **{c_name}** ({phone}) متبقي له أكثر من يومين (الموعد يوم {visit_dt.strftime('%Y-%m-%d')}).")
                        
                with col_btn1:
                    st.write("") # Add a little top padding
                    if st.button("✅ تم التواصل", key=f"btn_{v_id}", use_container_width=True):
                        db.mark_visit_contacted(v_id)
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="تم التواصل",
                            module="تنبيهات المواعيد",
                            details=f"تم التواصل مع العميل: {c_name} بشأن الموعد الميداني."
                        )
                        st.rerun()
                with col_btn2:
                    st.write("") # Add a little top padding
                    if st.button("❌ لم يتم", key=f"btn_not_{v_id}", use_container_width=True):
                        st.session_state[f"show_reason_{v_id}"] = not st.session_state.get(f"show_reason_{v_id}", False)
                        st.rerun()
                            
                if st.session_state.get(f"show_reason_{v_id}", False):
                    st.markdown(f"<div style='background-color:#ffe5d9; padding:10px; border-radius:5px; margin-bottom:10px;'>", unsafe_allow_html=True)
                    reason = st.text_area(f"سبب عدم التواصل مع العميل {c_name}:", key=f"reason_text_{v_id}")
                    if st.button("💾 حفظ السجل", key=f"save_reason_{v_id}", use_container_width=False):
                        db.mark_visit_not_contacted(v_id, reason)
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="لم يتم التواصل",
                            module="تنبيهات المواعيد",
                            details=f"العميل: {c_name} | السبب: {reason}"
                        )
                        st.session_state[f"show_reason_{v_id}"] = False
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

            for v_id, c_name, phone, visit_dt, hours_diff in urgent_visits:
                render_reminder_item(v_id, c_name, phone, visit_dt, hours_diff, "urgent")
                    
            for v_id, c_name, phone, visit_dt, hours_diff in warning_visits:
                render_reminder_item(v_id, c_name, phone, visit_dt, hours_diff, "warning")

            for v_id, c_name, phone, visit_dt, hours_diff in future_visits:
                render_reminder_item(v_id, c_name, phone, visit_dt, hours_diff, "future")
                
            st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #e0fbfc 0%, #caf0f8 100%); padding: 10px 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(144, 224, 239, 0.2); margin-top: 20px; margin-bottom: 25px; display: flex; align-items: center; justify-content: center; gap: 15px; flex-wrap: wrap; border: 1px solid #ade8f4;'>
        <span style='font-family: "Readex Pro", sans-serif; font-weight: 400; color: #0077b6; font-size: 24px;'>تطبيقات مسارات</span>
        <span style='color: #0077b6; font-weight: 300; font-size: 24px; opacity: 0.5;'>|</span>
        <span style='font-family: "Segoe UI", "Helvetica Neue", sans-serif; font-weight: 400; letter-spacing: 5px; color: #0077b6; font-size: 20px;'>MASARAT apps</span>
    </div>
    """, unsafe_allow_html=True)
    
    import base64
    import os
    
    def get_b64(filename):
        if os.path.exists(filename):
            with open(filename, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None

    # Map target page to (access, image_filename, module_key, emoji, short_title, target_page)
    modules_config = [
        (can_access_checklist, "مسار الفحص اليومي.png", "chk", "✅", "مسار الفحص اليومي", "✅ مسار الفحص اليومي"),
        (can_access_visits, "مسار رفع مقاسات.png", "vis", "📏", "مسار رفع المقاسات", "📏 مسار رفع المقاسات"),
        (can_access_design, "مسار التصاميم.png", "des", "🎨", "مسار التصاميم", "🎨 مسار التصاميم"),
        (can_access_pricing, "تسعير.png", "price", "🏷️", "مسار التسعير", "🏷️ مسار التسعير"),
        (can_access_contracts, "عقود.png", "contr", "📋", "مسار العقود", "📋 مسار العقود"),
        (can_access_finance, "مسار الخزينة.png", "fin", "💰", "مسار الخزينة", "💰 مسار الخزينة"),
        (can_access_production, "مسار الانتاج.png", "prod", "🏭", "مسار الانتاج", "🏭 مسار الانتاج"),
        (can_access_crm, "مسار العملاء.png", "crm", "👥", "مسار العملاء", "👥 مسار العملاء"),
        (can_access_helpdesk, "مسار الدعم الفني.png", "help", "🛠️", "مسار الدعم الفني", "🛠️ مسار الدعم الفني"),
        (can_access_journey, "مسار حركة مشروع - عميل.png", "jour", "🗺️", "مسار حركة العميل", "🗺️ مسار حركة العميل"),
        (user_role == "Admin", r"C:\Users\PC\Desktop\512\حركات.png", "activity", "🔍", "مسار حركة المستخدم", "🔍 مسار حركة المستخدم"),
        (can_access_statistics, "احصائيات.png", "stat", "📈", "إحصائيات", "📈 إحصائيات"),
        (True, r"C:\Users\PC\Desktop\Masarat\512\مسار التواصل.png", "chat", "💬", "مسار التواصل", "💬 مسار التواصل"),
        (True, "حول.png", "about", "ℹ️", "حول مسارات", "ℹ️ حول مسارات"),
    ]
        
    available_modules = [m for m in modules_config if m[0]]
    
    css_rules = []
    for m in available_modules:
        _, img_file, mod_key, emoji, title, target = m
        if img_file and os.path.exists(img_file):
            b64 = get_b64(img_file)
            css_rules.append(f"""
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button {{
                background-image: url("data:image/jpeg;base64,{b64}") !important;
                background-size: 50% !important;
                background-position: center 20px !important;
                background-repeat: no-repeat !important;
                background-color: #ffffff !important;
                height: 180px !important;
                border: 2px solid transparent !important;
                color: #0077b6 !important;
                border-radius: 15px !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
                transition: all 0.3s ease !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: flex-end !important;
                padding-bottom: 15px !important;
                align-items: center !important;
            }}
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button:hover {{
                transform: translateY(-5px) !important;
                box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
                border-color: #0077b6 !important;
            }}
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button p {{
                display: block !important;
                font-family: "Readex Pro", sans-serif !important;
                font-size: 15px !important;
                font-weight: 300 !important;
                margin: 0 !important;
                text-align: center !important;
                color: #0077b6 !important;
            }}
            """)
        else:
            # Fallback style for text/emoji buttons
            css_rules.append(f"""
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button {{
                height: 180px !important;
                border-radius: 15px !important;
                border: 2px solid transparent !important;
                background-color: white !important;
                color: #0077b6 !important;
                font-weight: bold !important;
                font-size: 1.1rem !important;
                box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
                transition: all 0.3s ease !important;
            }}
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button:hover {{
                transform: translateY(-5px) !important;
                box-shadow: 0 8px 20px rgba(0,0,0,0.2) !important;
                border-color: #0077b6 !important;
            }}
            .element-container:has(.icon-{mod_key}) + .element-container .stButton button p {{
                font-family: "Readex Pro", sans-serif !important;
                font-size: 15px !important;
                font-weight: 300 !important;
                color: #0077b6 !important;
                margin-top: 10px !important;
            }}
            """)
            
    st.markdown(f"""
        <style>
        {''.join(css_rules)}
        </style>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    for i, m in enumerate(available_modules):
        _, img_file, mod_key, emoji, title, target = m
        col = cols[i % 4]
        with col:
            st.markdown(f'<div class="icon-{mod_key}"></div>', unsafe_allow_html=True)
            
            # If we have an image, we still pass the title so it renders in the HTML
            if img_file and os.path.exists(img_file):
                btn_label = f" {title}"
            else:
                btn_label = f"{emoji}\n\n{title}"
                
            if st.button(btn_label, key=f"btn_mod_{mod_key}", use_container_width=True):
                st.session_state['override_page'] = target
                st.rerun()

elif choice == "✅ مسار الفحص اليومي":
    from modules import mod_checklist
    import importlib
    importlib.reload(mod_checklist)
    mod_checklist.render_page(can_access_checklist, is_observer)

elif choice == "📏 مسار رفع المقاسات":
    from modules import mod_visits
    import importlib
    importlib.reload(mod_visits)
    mod_visits.render_page(can_access_visits, is_observer)

elif choice == "👥 مسار العملاء":
    if not can_access_crm:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2>👥 إدارة العملاء</h2>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ إضافة عميل جديد", "📋 قائمة العملاء", "✏️ تعديل / حذف عميل"])
    
    with tab1:
        st.info("💡 يتم تسجيل العملاء وإضافتهم تلقائياً عبر قسم **(مسار رفع المقاسات)**. يرجى إدخال العملاء الجدد من هناك لضمان تسجيلهم وتوليد رقم مسارات الخاص بهم تلقائياً.")
        
    with tab2:
        visits = db.get_all_field_visits()
        if visits:
            formatted_visits = []
            for v in visits:
                c_name = v[1]
                is_canceled = v[20] if len(v) > 20 else 0
                if is_canceled == 1:
                    c_name = f"{c_name} ❌ [ملغي/اعتذار]"
                formatted_visits.append((v[0], f"MHM{v[0]:05d}", c_name, v[2], v[3], v[4]))
                
            df_customers = pd.DataFrame(
                formatted_visits,
                columns=["المعرف", "رقم مسارات", "الاسم", "الهاتف", "العنوان", "الأثاث المطلوب"]
            )
            # Add sequence number #
            df_customers["#"] = range(1, len(df_customers) + 1)
            # Reverse columns for RTL visual order (right to left: #, رقم مسارات, الاسم, الهاتف, العنوان, الأثاث المطلوب)
            df_customers = df_customers[["الأثاث المطلوب", "العنوان", "الهاتف", "الاسم", "رقم مسارات", "#"]]
            st.dataframe(df_customers, use_container_width=True, hide_index=True)
        else:
            st.info("لا يوجد عملاء مسجلين حالياً.")
            
    with tab3:
        visits = db.get_all_field_visits()
        if not visits:
            st.info("لا يوجد عملاء مسجلين حالياً للتعديل أو الحذف.")
        else:
            st.markdown("<h3>تعديل بيانات العميل أو حذفه</h3>", unsafe_allow_html=True)
            customer_dict = {f"MHM{v[0]:05d} | الاسم: {v[1]}": v for v in visits}
            
            selected_customer_str = st.selectbox("اختر العميل للتعديل أو الحذف:", list(customer_dict.keys()))
            selected_v = customer_dict[selected_customer_str]
            
            v_id = selected_v[0]
            c_name = selected_v[1]
            c_phone = selected_v[2]
            c_address = selected_v[3]
            c_furniture = selected_v[4]
            c_status = selected_v[5]
            
            with st.form("edit_customer_form"):
                new_name = st.text_input("اسم العميل *", value=c_name)
                new_phone = st.text_input("رقم الهاتف", value=c_phone if c_phone else "")
                new_address = st.text_area("العنوان", value=c_address if c_address else "")
                new_furniture = st.text_input("نوع الأثاث المطلوب", value=c_furniture if c_furniture else "")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if is_observer:
                        update_btn = False
                    else:
                        update_btn = st.form_submit_button("💾 حفظ التعديلات")
                with col_btn2:
                    if not can_delete:
                        delete_btn = False
                    else:
                        delete_btn = st.form_submit_button("🗑️ حذف العميل نهائياً")
                
                if update_btn:
                    if new_name:
                        # Update field visit record to keep database in sync
                        # Get full record first
                        import datetime
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
                        new_modifier = st.session_state.get('username', 'Unknown')
                        db.update_field_visit(
                            v_id, new_name, new_phone, new_address, new_furniture, 
                            c_status, selected_v[6], selected_v[7], selected_v[8], selected_v[9], 
                            selected_v[13] if len(selected_v) > 13 else "", 
                            selected_v[14] if len(selected_v) > 14 else "", 
                            selected_v[15] if len(selected_v) > 15 else "", 
                            selected_v[16] if len(selected_v) > 16 else "", 
                            new_modifier, now_str
                        )
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="تعديل",
                            module="مسار العملاء",
                            details=f"تم تعديل بيانات العميل: {new_name}"
                        )
                        st.session_state.success_msg = f"تم تعديل بيانات العميل '{new_name}' بنجاح!"
                        st.rerun()
                    else:
                        st.error("⚠️ الرجاء إدخال اسم العميل كحد أدنى.")
                        
                if delete_btn:
                    # To keep referential integrity, we drop from FieldVisits
                    conn = db.get_connection()
                    c = conn.cursor()
                    c.execute('DELETE FROM FieldVisits WHERE id=?', (v_id,))
                    conn.commit()
                    conn.close()
                    
                    db.log_activity(
                        username=st.session_state.get('username', 'Unknown'),
                        employee_name=st.session_state.get('employee_name', 'Unknown'),
                        action_type="حذف",
                        module="مسار العملاء",
                        details=f"تم حذف العميل: {c_name}"
                    )
                    st.session_state.success_msg = f"تم حذف العميل '{c_name}' نهائياً!"
                    st.rerun()

elif choice == "🛠️ مسار الدعم الفني":
    if not can_access_helpdesk:
        st.error("🔒 عذراً، ليس لديك الصلاحية للوصول إلى هذا القسم.")
        st.stop()
        
    st.markdown("<h2>🛠️ الدعم الفني والتذاكر</h2>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["➕ إنشاء تذكرة جديدة", "📋 متابعة التذاكر"])
    
    with tab1:
        visits = db.get_all_field_visits()
        if not visits:
            st.warning("⚠️ الرجاء إضافة عملاء أولاً من مسار رفع المقاسات.")
        else:
            if is_observer:
                st.info("وضع القراءة فقط: لا يمكنك إنشاء تذكرة.")
            else:
                with st.form("add_ticket_form"):
                    st.markdown("<h3>تفاصيل المشكلة أو الطلب</h3>", unsafe_allow_html=True)
                    customer_dict = {f"[{v[0]}] {v[1]} (MHM{v[0]:05d})": v[0] for v in visits}
                    selected_customer = st.selectbox("اختر العميل", list(customer_dict.keys()))
                    title = st.text_input("عنوان المشكلة / الطلب *")
                    description = st.text_area("تفاصيل المشكلة بالكامل")
                    status = st.selectbox("حالة التذكرة", ["جديدة", "قيد المعالجة", "مغلقة"])
                    
                    submit = st.form_submit_button("🎫 إنشاء التذكرة")
                
                if submit:
                    if title:
                        customer_id = customer_dict[selected_customer]
                        db.add_ticket(customer_id, title, description, status)
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="إنشاء تذكرة",
                            module="مسار الدعم الفني",
                            details=f"تم إنشاء تذكرة: {title}"
                        )
                        st.session_state.success_msg = "تم إنشاء التذكرة بنجاح!"
                        st.rerun()
                    else:
                        st.error("⚠️ الرجاء إدخال عنوان المشكلة كحد أدنى.")
                        
    with tab2:
        tickets = db.get_all_tickets()
        if tickets:
            df_tickets = pd.DataFrame(tickets, columns=["رقم التذكرة", "اسم العميل", "العنوان", "الوصف", "الحالة", "تاريخ الإنشاء"])
            # Add sequence number #
            df_tickets["#"] = range(1, len(df_tickets) + 1)
            # Reverse columns for RTL visual order (right to left: #, رقم التذكرة, اسم العميل, العنوان, الوصف, الحالة, تاريخ الإنشاء)
            df_tickets = df_tickets[["تاريخ الإنشاء", "الحالة", "الوصف", "العنوان", "اسم العميل", "رقم التذكرة", "#"]]
            st.dataframe(df_tickets, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("<h3>🔄 تحديث حالة التذكرة</h3>", unsafe_allow_html=True)
                if is_observer:
                    st.info("وضع القراءة فقط.")
                else:
                    with st.form("update_ticket_form"):
                        ticket_id_to_update = st.selectbox("اختر رقم التذكرة", [t[0] for t in tickets])
                        new_status = st.selectbox("الحالة الجديدة", ["جديدة", "قيد المعالجة", "مغلقة"])
                        update_btn = st.form_submit_button("تحديث الحالة")
                    if update_btn:
                        db.update_ticket_status(ticket_id_to_update, new_status)
                        db.log_activity(
                            username=st.session_state.get('username', 'Unknown'),
                            employee_name=st.session_state.get('employee_name', 'Unknown'),
                            action_type="تحديث حالة تذكرة",
                            module="مسار الدعم الفني",
                            details=f"تم تحديث حالة التذكرة رقم {ticket_id_to_update} إلى: {new_status}"
                        )
                        st.session_state.success_msg = f"تم تحديث حالة التذكرة بنجاح!"
                        st.rerun()
                        
            with col2:
                st.markdown("<h3>🗑️ حذف تذكرة</h3>", unsafe_allow_html=True)
                if not can_delete:
                    st.info("ليس لديك صلاحية الحذف.")
                else:
                    with st.form("delete_ticket_form"):
                        ticket_id_to_delete = st.selectbox("اختر رقم التذكرة للحذف", [t[0] for t in tickets], key="del_ticket")
                        delete_btn = st.form_submit_button("حذف التذكرة نهائياً")
                        if delete_btn:
                            db.delete_ticket(ticket_id_to_delete)
                            db.log_activity(
                                username=st.session_state.get('username', 'Unknown'),
                                employee_name=st.session_state.get('employee_name', 'Unknown'),
                                action_type="حذف",
                                module="مسار الدعم الفني",
                                details=f"تم حذف تذكرة رقم: {ticket_id_to_delete}"
                            )
                            st.session_state.success_msg = f"تم حذف التذكرة بنجاح!"
                            st.rerun()
                            
        else:
            st.info("لا توجد تذاكر حالياً.")

elif choice == "🎨 مسار التصاميم":
    from modules import mod_design
    import importlib
    importlib.reload(mod_design)
    mod_design.render_page(can_access_design, is_observer)

elif choice == "🏷️ مسار التسعير":
    from modules import mod_pricing
    import importlib
    importlib.reload(mod_pricing)
    mod_pricing.render_page(can_access_pricing, is_observer)

elif choice == "📋 مسار العقود":
    from modules import mod_contracts
    import importlib
    importlib.reload(mod_contracts)
    mod_contracts.render_page(can_access_contracts, is_observer, user_role, emp_name)

elif choice == "🏭 مسار الانتاج":
    from modules import mod_production
    import importlib
    importlib.reload(mod_production)
    mod_production.render_page(can_access_production, is_observer)

elif choice == "💰 مسار الخزينة":
    from modules import mod_finance
    import importlib
    importlib.reload(mod_finance)
    mod_finance.render_page(can_access_finance, is_observer)

elif choice == "🗺️ مسار حركة العميل":
    from modules import mod_journey
    import importlib
    importlib.reload(mod_journey)
    mod_journey.render_page(can_access_journey, is_observer)

elif choice == "📈 إحصائيات":
    from modules import mod_statistics
    import importlib
    importlib.reload(mod_statistics)
    mod_statistics.render_page(can_access_statistics, is_observer)

elif choice == "ℹ️ حول مسارات":
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if os.path.exists("masarat_logo.png"):
            st.image("masarat_logo.png", use_container_width=True)
        elif os.path.exists("masarat_logo.jpg"):
            st.image("masarat_logo.jpg", use_container_width=True)
            
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@800&family=Playfair+Display:ital,wght@0,700;1,700&display=swap');
            .masarat-title {
                font-family: 'Montserrat', sans-serif;
                color: #0077b6;
                font-size: 4rem;
                text-align: center !important;
                letter-spacing: 5px;
                margin-bottom: 10px;
                text-transform: uppercase;
                display: block;
                width: 100%;
            }
            .masarat-subtitle {
                text-align: center !important;
                display: block;
                width: 100%;
            }
        </style>
        <div style="text-align: center !important; width: 100%; display: flex; flex-direction: column; align-items: center;">
            <h1 class='masarat-title'>MASARAT</h1>
            <h3 class='masarat-subtitle' style='color: #457b9d; margin-top: 20px;'>منظومة إدارة متكاملة لشركات صناعة وبيع الاثاث بالتجزئة والجملة</h3>
            <h4 class='masarat-subtitle' style='color: #457b9d; margin-top: 10px;'>نحو بيئة إدارية متكاملة</h4>
            <br><br>
            <p class='masarat-subtitle' style='color: gray; font-size: 14px;'>إعداد وتصميم: م. علي بن عيسى</p>
        </div>
    """, unsafe_allow_html=True)

elif choice == "🔑 تغيير كلمة المرور":
    st.markdown("<h2 style='text-align: center;'>🔑 تغيير كلمة المرور</h2>", unsafe_allow_html=True)
    with st.form("change_pwd_form"):
        old_pwd = st.text_input("كلمة المرور الحالية", type="password")
        new_pwd = st.text_input("كلمة المرور الجديدة", type="password")
        new_pwd_confirm = st.text_input("تأكيد كلمة المرور الجديدة", type="password")
        submit_pwd = st.form_submit_button("حفظ كلمة المرور")
        
        if submit_pwd:
            if new_pwd != new_pwd_confirm:
                st.error("كلمتا المرور الجديدتان غير متطابقتين!")
            elif len(new_pwd) < 4:
                st.error("يجب أن تتكون كلمة المرور من 4 أحرف/أرقام على الأقل.")
            else:
                success = db.change_password(st.session_state['username'], old_pwd, new_pwd)
                if success:
                    st.success("تم تغيير كلمة المرور بنجاح!")
                else:
                    st.error("كلمة المرور الحالية غير صحيحة.")

elif choice == "⚙️ إدارة الحسابات":
    if user_role != "Admin":
        st.error("🔒 هذا القسم مخصص للمدير العام (Admin) فقط.")
        st.stop()
        
    st.markdown("<h2 style='text-align: center;'>⚙️ إدارة الحسابات والصلاحيات</h2>", unsafe_allow_html=True)
    
    all_users = db.get_all_users()
    sections_list = ["الجميع", "قائمة الفحص اليومي", "الزيارة الميدانية", "إدارة العملاء", "الدعم الفني", "إدارة التصاميم", "إدارة الإنتاج", "الإدارة المالية", "تتبع مسار حركة العميل", "إحصائيات", "Observer"]
    
    top_tab1, top_tab2 = st.tabs(["➕ إضافة حساب جديد", "✏️ تعديل حساب موجود"])
    
    with top_tab1:
        with st.form("new_account_form"):
            c1, c2 = st.columns(2)
            with c1:
                new_user = st.text_input("اسم المستخدم الجديد (مثال: Designer01)")
                new_emp_name = st.text_input("اسم الموظف الحقيقي (مثال: علي بن عيسى)")
            with c2:
                new_role_list = st.multiselect("الصلاحيات (الأقسام المسموح بها)", sections_list, default=["الجميع"])
            
            st.info("ملاحظة: كلمة المرور الافتراضية لأي حساب جديد هي '6065'. يمكن للمستخدم تغييرها لاحقاً.")
            submit_new_user = st.form_submit_button("إضافة الحساب")
            
            if submit_new_user:
                if new_user.strip() == "":
                    st.error("يرجى إدخال اسم المستخدم.")
                elif not new_role_list:
                    st.error("يرجى اختيار صلاحية واحدة على الأقل.")
                else:
                    role_str = ",".join(new_role_list)
                    if db.add_user(new_user.strip(), role_str, new_emp_name.strip()):
                        st.success(f"تم إنشاء حساب '{new_user}' بنجاح!")
                        import time
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("اسم المستخدم موجود مسبقاً، يرجى اختيار اسم آخر.")
                        
    with top_tab2:
        if not all_users:
            st.info("لا توجد حسابات للتعديل.")
        else:
            user_options = {u[0]: f"{u[1]} - {u[3] if u[3] else 'غير محدد'}" for u in all_users}
            selected_user_id = st.selectbox("اختر الحساب المراد تعديله", options=list(user_options.keys()), format_func=lambda x: user_options[x])
            
            selected_user = next((u for u in all_users if u[0] == selected_user_id), None)
            if selected_user:
                u_id, u_name, u_role, u_emp_name = selected_user
                with st.form(key=f"top_edit_form"):
                    st.markdown(f"**تعديل بيانات الحساب:** {u_name}")
                    edit_emp = st.text_input("اسم الموظف الحقيقي", value=u_emp_name if u_emp_name else "")
                    
                    current_roles = [r.strip() for r in u_role.split(",")] if u_role else []
                    valid_roles = [r for r in current_roles if r in sections_list]
                    edit_roles = st.multiselect("الصلاحيات", sections_list, default=valid_roles)
                    
                    edit_pwd = st.text_input("كلمة مرور جديدة (اتركه فارغاً لعدم التغيير)", type="password")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        submit_edit = st.form_submit_button("💾 حفظ التعديلات")
                    with c_btn2:
                        submit_delete = st.form_submit_button("🗑️ حذف هذا الحساب")
                        
                    if submit_edit:
                        if not edit_roles:
                            st.error("يجب اختيار صلاحية واحدة على الأقل.")
                        else:
                            new_role_str = ",".join(edit_roles)
                            db.update_user_details(u_id, new_role_str, edit_emp.strip(), edit_pwd)
                            st.success("تم حفظ التعديلات بنجاح!")
                            import time
                            time.sleep(1)
                            st.rerun()
                            
                    if submit_delete:
                        db.delete_user(u_id)
                        st.success("تم حذف الحساب بنجاح!")
                        import time
                        time.sleep(1)
                        st.rerun()

    st.markdown("---")
    st.markdown("### 📋 قائمة الحسابات الحالية")
    
    admin_users = db.get_all_users_admin()
    if not admin_users:
        st.info("لا توجد حسابات مسجلة في المنظومة.")
    else:
        import pandas as pd
        table_data = []
        for i, u in enumerate(admin_users, 1):
            u_id, u_name, u_role, u_emp_name, _ = u
            display_name = u_emp_name if u_emp_name else "غير محدد"
            table_data.append({
                "رقم متسلسل": i,
                "اسم الموظف": display_name,
                "اسم المستخدم": u_name,
                "الصلاحيات": u_role
            })
        
        df_users = pd.DataFrame(table_data)
        # Reverse columns for RTL visual order
        df_users = df_users[["الصلاحيات", "اسم المستخدم", "اسم الموظف", "رقم متسلسل"]]
        event = st.dataframe(df_users, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single_row")
        
        if event.selection and event.selection.rows:
            selected_row_idx = event.selection.rows[0]
            selected_username = df_users.iloc[selected_row_idx]["اسم المستخدم"]
            selected_user = next((u for u in admin_users if u[1] == selected_username), None)
            if selected_user:
                u_id, u_name, u_role, u_emp_name, _ = selected_user
                st.markdown("---")
                st.markdown(f"### 👤 تفاصيل بيانات الحساب: {u_name}")
                
                with st.form(key="table_edit_form"):
                    edit_emp = st.text_input("اسم الموظف الحقيقي", value=u_emp_name if u_emp_name else "")
                    
                    current_roles = [r.strip() for r in u_role.split(",")] if u_role else []
                    valid_roles = [r for r in current_roles if r in sections_list]
                    edit_roles = st.multiselect("الصلاحيات (المشروع / القسم)", sections_list, default=valid_roles)
                    
                    edit_pwd = st.text_input("كلمة مرور جديدة (اتركه فارغاً لعدم التغيير)", type="password")
                    
                    c_btn1, c_btn2 = st.columns(2)
                    with c_btn1:
                        submit_edit = st.form_submit_button("💾 حفظ التعديلات")
                    with c_btn2:
                        submit_delete = st.form_submit_button("🗑️ حذف هذا الحساب")
                        
                    if submit_edit:
                        if not edit_roles:
                            st.error("يجب اختيار صلاحية واحدة على الأقل.")
                        else:
                            new_role_str = ",".join(edit_roles)
                            db.update_user_details(u_id, new_role_str, edit_emp.strip(), edit_pwd)
                            st.success("تم حفظ التعديلات بنجاح!")
                            import time
                            time.sleep(1)
                            st.rerun()
                            
                    if submit_delete:
                        db.delete_user(u_id)
                        st.success("تم حذف الحساب بنجاح!")
                        import time
                        time.sleep(1)
                        st.rerun()

elif choice == "🔍 مسار حركة المستخدم":
    from modules import mod_activity_log
    import importlib
    importlib.reload(mod_activity_log)
    mod_activity_log.render_page(user_role)

# --- Global Footer ---
st.markdown("""
<br><br>
    <div style='background: linear-gradient(135deg, #e0fbfc 0%, #caf0f8 100%); padding: 10px 20px; border-radius: 8px; box-shadow: 0 4px 10px rgba(144, 224, 239, 0.15); margin-top: 40px; margin-bottom: 5px; display: flex; align-items: center; justify-content: center; gap: 5px; flex-wrap: wrap; border: 1px solid #ade8f4;'>
        <span dir="rtl" style='font-family: "Readex Pro", sans-serif; font-weight: 600; color: #0077b6; font-size: 15px;'>جميع الحقوق الفكرية للمنظومة مملوكة لشركة <span style='font-weight: 900; color: #023e8a;'>مسارات MASARAT</span> (م. علي بن عيسى) © 2026</span>
        <span style='color: #0077b6; font-weight: 300; font-size: 15px; opacity: 0.4;'>|</span>
        <span dir="ltr" style='font-family: "Readex Pro", sans-serif; font-weight: 300; letter-spacing: 2px; color: #0077b6; font-size: 13px;'>ALL RIGHTS RESERVED</span>
    </div>
    """, unsafe_allow_html=True)

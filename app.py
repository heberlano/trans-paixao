import os, time, hmac, tempfile, json, html
from datetime import timedelta
import pandas as pd
import streamlit as st
from core import today, describe, forecast_text, delay_summary, stage_index, stage_label, STAGES
from tracking_feedback import tracking_result
from operations import Operations, CITIES, STATUS, KINDS, quote, quote_text, money, demo_extended
from paco import reply, confirm
from reports import report
from resolution import ResolutionStore, complaint_reply
from support_ui import customer_support, manager_cases, intelligence
from lookup_ui import compact_search
from phone_lookup import redact
from service_bridge import select_delivery, sync_chat_delivery, open_help, registered
from paco_window import CSS as PACO_CSS, init_window, open_window, close_window, render_window

st.set_page_config(page_title='Paixão Connect | PACO',page_icon='🚚',layout='wide',initial_sidebar_state='collapsed')
def setting(name,default=''):
    try:return str(st.secrets.get(name,os.getenv(name,default)))
    except Exception:return os.getenv(name,default)
key=setting('OPENAI_API_KEY'); model=setting('OPENAI_MODEL','gpt-4.1-mini'); admin_pass=setting('ADMIN_PASSWORD','paixao2026'); access=setting('DEMO_ACCESS_CODE')
s=st.session_state
for k,v in {'messages':[],'context':{},'pending':None,'admin':False,'access':False,'ai_error':False,'track_code':'','track_selected':None,'nav':'Início'}.items():
    if k not in s:s[k]=v
init_window(s)
st.markdown('''<style>
:root {--navy:#102b43;--orange:#f5a623;}
.block-container{max-width:1160px;padding-top:2.8rem;padding-bottom:3rem;}
[data-testid="stHeader"]{background:transparent;}
.brand{display:flex;align-items:center;gap:13px;margin-bottom:12px;color:inherit;}
.brand-mark{background:#102b43;border-radius:13px;width:48px;height:48px;display:grid;place-items:center;flex-shrink:0;}
.brand-name{font-size:1.25rem;font-weight:850;letter-spacing:-.03em;line-height:1.1;}.brand-tag{font-size:.68rem;letter-spacing:.12em;font-weight:700;color:#a65a08;}
.hero{background:linear-gradient(125deg,#102b43,#204d6c);color:#fff;padding:32px;border-radius:22px;position:relative;overflow:hidden;border-bottom:5px solid #f5a623;}
.hero:after{content:'';position:absolute;right:-50px;bottom:-110px;width:290px;height:290px;border:36px solid rgba(255,255,255,.055);border-radius:50%;pointer-events:none;}
.hero small{color:#ffc66f;letter-spacing:.13em;font-weight:800;}.hero h1{color:#fff!important;font-size:clamp(1.7rem,4vw,3rem);line-height:1.08;max-width:680px;margin:12px 0;letter-spacing:-.035em;}.hero p{color:#dce8f3;max-width:550px;margin:0;}.hero .tag{display:inline-block;font-size:.78rem;border:1px solid #7790a6;border-radius:100px;padding:5px 12px;margin-top:17px;color:#fff;}
[data-testid="stMetric"]{background:rgba(128,150,170,.06);border:1px solid rgba(128,150,170,.25);border-radius:16px;padding:16px;min-width:0;}
[data-testid="stMetricValue"]{font-size:clamp(1.35rem,3vw,2rem);font-weight:750;}
[data-testid="stChatMessage"]{border:1px solid rgba(128,150,170,.24);border-radius:16px;padding:12px;}
[data-testid="stChatMessageContent"]{min-width:0;overflow-wrap:anywhere;}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#f5a623!important;border-color:#f5a623!important;color:#102b43!important;font-weight:800;}
button[kind="primary"] p,button[kind="primaryFormSubmit"] p{color:#102b43!important;}
.stButton button,.stFormSubmitButton button,.stDownloadButton button{border-radius:12px;min-height:44px;}
.st-key-navbox{padding:4px 8px;border-bottom:1px solid rgba(128,150,170,.28);}
.routecard{border:1px solid rgba(128,150,170,.35);border-radius:14px;padding:16px;}.routecard h3{margin:0;}.routecard .eyebrow{font-size:.72rem;letter-spacing:.1em;font-weight:750;opacity:.8;}
.event{border-left:3px solid #e6a03c;padding:0 0 14px 16px;margin-left:8px;overflow-wrap:anywhere;}.event span{font-size:.78rem;opacity:.8;}.event b{display:block;}
@media (prefers-color-scheme:dark){.brand-tag{color:#c27a25;}}
@media (max-width:700px){.block-container{padding:3rem 1rem calc(6.6rem + env(safe-area-inset-bottom));}.hero{padding:22px 17px;border-radius:17px;}.hero h1{font-size:1.85rem;}.hero small{font-size:.66rem;}.hero p{font-size:.9rem;}.brand-name{font-size:1.15rem;}
.st-key-navbox{position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#102b43;color:#fff;padding:9px 7px calc(9px + env(safe-area-inset-bottom));box-shadow:0 -4px 20px #102b4325;}.st-key-navbox [role="radiogroup"]{gap:2px!important;}.st-key-navbox [role="radiogroup"] label{padding:10px 2px;margin:0;min-height:44px;}.st-key-navbox [role="radiogroup"] label p{color:white!important;font-size:.72rem!important;text-align:center;white-space:normal;}.st-key-navbox [role="radiogroup"] label:has(input:checked) p{color:#102b43!important;}
[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.65rem!important;}[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 100%!important;width:100%!important;min-width:0!important;}.st-key-metrics [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 44%!important;width:44%!important;}[data-testid="stMetric"]{padding:12px;}[data-testid="stChatMessage"]{padding:9px;}}
/* Visual 2.1: compact service grid and genuine navigation buttons. */
:root{--pc-bg:#f3f6fb;--pc-text:#102b43;--pc-muted:#52677c;--pc-line:#dbe4ee;}
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"]{background:var(--pc-bg)!important;color:var(--pc-text)!important;color-scheme:light;}
.block-container{max-width:1080px;padding:1.5rem 2rem 3rem;}
[data-testid="stHeader"]{background:transparent!important;height:0;min-height:0;}
[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stAppDeployButton"],#MainMenu,footer{display:none!important;}
.stApp h1,.stApp h2,.stApp h3,.stApp label,.stApp [data-testid="stMarkdownContainer"]{color:var(--pc-text);}
.stApp [data-testid="stCaptionContainer"],.stApp [data-testid="stCaptionContainer"] p{color:var(--pc-muted)!important;}
.stApp input:not([type="checkbox"]):not([type="radio"]),.stApp textarea{color:var(--pc-text)!important;background:white!important;caret-color:var(--pc-text);}
.stApp [data-testid="stWidgetLabel"] p,.stApp [data-testid="stMetricLabel"] p,.stApp [data-testid="stMetricValue"]{color:#102b43!important;}
.stApp input::placeholder,.stApp textarea::placeholder{color:#64748b!important;opacity:1;}
.stApp [data-baseweb="input"],.stApp [data-baseweb="base-input"],.stApp [data-baseweb="textarea"],.stApp [data-baseweb="select"]>div{background:#fff!important;color:var(--pc-text)!important;border-color:var(--pc-line)!important;}
.stApp [data-testid="stForm"]{border-color:var(--pc-line);}
.brand{margin:0 0 4px;color:var(--pc-text);}.brand-name{font-size:1.2rem;}.brand-tag{color:#95500a!important;font-size:.62rem;}
.hero{background:linear-gradient(120deg,#102b43,#194568);padding:28px 26px;border-radius:22px;border-bottom:0;box-shadow:0 10px 22px #102b431a;isolation:isolate;}.hero:after{display:none;}
.hero-copy{position:relative;z-index:2;max-width:65%;}.hero small{color:#ffce84;font-size:.69rem;}.hero h1{color:#fff!important;font-size:clamp(1.8rem,4vw,2.8rem);line-height:1.05;margin:9px 0 10px!important;padding:0!important;letter-spacing:-.045em;}.hero p{color:#e1ebf7!important;font-size:.9rem;line-height:1.45;margin:0!important;}.hero-art{position:absolute;right:8px;bottom:6px;width:35%;max-width:310px;height:auto;z-index:1;pointer-events:none;}
button[kind="secondary"],button[kind="secondaryFormSubmit"]{background:#fff!important;color:#102b43!important;border:1px solid #dbe4ee!important;}button[kind="secondary"] p,button[kind="secondaryFormSubmit"] p{color:#102b43!important;}
button:focus-visible{outline:2px solid #b45309!important;outline-offset:2px;}
.st-key-navbox{background:#fff;border:1px solid var(--pc-line);border-radius:15px;padding:6px 8px;box-shadow:0 3px 12px #102b4308;}
.st-key-navbox [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(5,minmax(0,1fr));gap:4px!important;align-items:stretch;}
.st-key-navbox [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.st-key-navbox .stButton button{width:100%;min-width:0!important;padding:8px 2px!important;border:0!important;box-shadow:none!important;min-height:46px;}
.st-key-navbox button[kind="secondary"],.st-key-navbox button[kind="secondary"] p{color:#52677c!important;background:transparent!important;}
.st-key-navbox button[kind="primary"]{background:#fff1d8!important;}.st-key-navbox button[kind="primary"],.st-key-navbox button[kind="primary"] p{color:#8a4400!important;}.st-key-navbox button p{font-size:.88rem;white-space:nowrap!important;margin:0!important;}
.st-key-home_trackbox{background:#fff;border:1px solid var(--pc-line);border-radius:18px;padding:15px 18px;box-shadow:0 4px 14px #102b4308;}.st-key-home_trackbox [data-testid="stForm"]{border:0!important;padding:0!important;}
.section-heading{font-size:1.13rem;font-weight:800;letter-spacing:-.025em;margin:3px 0 0;color:var(--pc-text);}
.st-key-home_services [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px!important;}.st-key-home_services [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.st-key-home_services [class*="st-key-service_"]{background:#fff;border:1px solid var(--pc-line);border-radius:16px;padding:13px;box-shadow:0 3px 12px #102b4308;}.st-key-home_services [class*="st-key-service_"] [data-testid="stVerticalBlock"]{gap:.45rem!important;}
.service-icon{display:grid;place-items:center;width:38px;height:38px;border-radius:12px;background:#fff1dc;color:#965008;margin:0 0 4px;}.service-icon svg{width:22px;height:22px;}.service-name{font-size:1rem;font-weight:800;letter-spacing:-.02em;color:#102b43;line-height:1.2;}.service-desc{font-size:.79rem;line-height:1.35;color:#52677c;min-height:2.15em;margin-top:4px;}
.st-key-home_services .stButton button{min-height:44px;padding:5px 4px!important;}.st-key-home_services .stButton button p{font-size:.82rem;font-weight:700;}
[data-testid="stMetric"],[data-testid="stChatMessage"],.routecard{background:#fff!important;border:1px solid var(--pc-line);color:var(--pc-text);}.event span{color:var(--pc-muted);}
@media(max-width:700px){
.block-container{padding:1rem 1rem calc(7.5rem + env(safe-area-inset-bottom,0px));}.brand-name{font-size:1.08rem;}.brand-tag{font-size:.55rem;letter-spacing:.04em;}.brand-mark{width:40px;height:40px;}
.hero{padding:20px 16px;border-radius:18px;}.hero-copy{max-width:72%;}.hero h1{font-size:clamp(1.55rem,6vw,2rem);}.hero small{font-size:.58rem;}.hero p{font-size:.82rem;}.hero-art{width:33%;right:0;bottom:8px;}
.st-key-navbox{position:fixed!important;bottom:calc(8px + env(safe-area-inset-bottom,0px));left:8px;right:8px;width:auto!important;z-index:1000;padding:5px 4px;background:#fff!important;border-radius:18px;box-shadow:0 4px 28px #102b4333;}
.st-key-navbox [data-testid="stHorizontalBlock"]{gap:2px!important;}.st-key-navbox .stButton button{min-height:54px;display:flex!important;flex-direction:column!important;align-items:center;justify-content:center;gap:3px!important;padding:5px 0!important;}.st-key-navbox button p{font-size:clamp(.61rem,2.65vw,.75rem)!important;line-height:1.1;}.st-key-navbox button [data-testid="stIconMaterial"]{font-size:21px!important;}
.st-key-home_services [data-testid="stHorizontalBlock"]{gap:9px!important;}.st-key-home_services [class*="st-key-service_"]{padding:10px;}.service-name{font-size:.92rem;}.service-desc{font-size:.72rem;}.service-icon{width:33px;height:33px;}.service-icon svg{width:19px;height:19px;}.st-key-home_services .stButton button p{font-size:.75rem;}.st-key-home_trackbox{padding:12px;}
.st-key-metrics [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));}.st-key-metrics [data-testid="stColumn"]{width:100%!important;min-width:0!important;}
}
@media(max-width:340px){.hero-copy{max-width:100%;}.hero-art{opacity:.16;}.st-key-home_services [class*="st-key-service_"]{padding:8px;}}

/* Guided navigation 2.3 */
.guide{background:#eaf2fa;border:1px solid #d5e4f2;border-radius:13px;padding:13px 15px;color:#183a58;margin:0 0 3px;line-height:1.45;font-size:.91rem;}.guide b{color:#102b43;}.guide small{display:block;color:#52677c;font-size:.82rem;margin-top:5px;}
.step-title{display:flex;align-items:center;gap:9px;font-weight:750;color:#102b43;font-size:1rem;margin:8px 0 2px;}.step-title span{display:grid;place-items:center;width:25px;height:25px;background:#fff0d7;color:#8a4400;border-radius:8px;font-size:.8rem;flex-shrink:0;}
.st-key-service_menu [data-testid="stHorizontalBlock"],.st-key-manager_menu [data-testid="stHorizontalBlock"],.st-key-protocol_menu [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px!important;}
.st-key-service_menu [data-testid="stColumn"],.st-key-manager_menu [data-testid="stColumn"],.st-key-protocol_menu [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.st-key-service_menu button,.st-key-manager_menu button,.st-key-protocol_menu button{min-height:49px;white-space:normal!important;}.st-key-service_menu button p,.st-key-manager_menu button p,.st-key-protocol_menu button p{font-size:.88rem;line-height:1.2;}
.st-key-service_menu,.st-key-manager_menu,.st-key-protocol_menu{background:#fff;border:1px solid var(--pc-line);border-radius:15px;padding:10px;}
.stApp [data-testid="stForm"]{background:#fff;border-radius:14px;}.stApp [data-testid="stExpander"]{background:#fff;border-radius:13px;}.stApp [data-testid="stWidgetLabel"] p{font-weight:650;}.stApp h1{font-size:clamp(1.7rem,4vw,2.4rem);letter-spacing:-.035em;}.stApp h2{font-size:1.35rem;}.stApp h3{font-size:1.12rem;}
@media(max-width:700px){.guide{font-size:.86rem;padding:11px 12px;}.st-key-service_menu button p,.st-key-manager_menu button p,.st-key-protocol_menu button p{font-size:.78rem;}.stApp [data-testid="stForm"]{padding:12px;}.stApp h2{font-size:1.2rem;}}

/* 3.0: compact help hub, consistent contrast, mobile navigation */
.support-hero{background:linear-gradient(120deg,#102b43,#205476);border-radius:20px;padding:24px;color:#fff;box-shadow:0 6px 20px #102b4315}.support-hero h2{color:#fff!important;margin:7px 0!important;font-size:clamp(1.55rem,5vw,2rem)!important;padding:0!important}.support-hero p{color:#e3edf6!important;margin:0;font-size:.95rem}.support-hero .eyebrow{color:#ffc66f;font-size:.65rem;letter-spacing:.11em;font-weight:800}
.st-key-home_help{background:white;border:1px solid #dbe4ee;border-left:4px solid #f5a623;border-radius:16px;padding:15px 18px;}.st-key-home_help h3{padding:0!important}.st-key-problem_cards button{justify-content:flex-start!important;text-align:left!important;min-height:48px!important;padding:9px 12px!important;white-space:normal!important}.st-key-problem_cards button p{font-size:.92rem;line-height:1.25}.st-key-problem_cards [data-testid="stVerticalBlock"]{gap:6px!important}
.stApp [data-testid="stAlert"]{background:#eaf2fa!important;border:1px solid #d5e4f2;border-radius:12px;color:#102b43!important}.stApp [data-testid="stAlert"] p{color:#102b43!important}.stApp [data-testid="stFileUploaderDropzone"]{background:#edf3fa!important;color:#102b43!important}.stApp [data-testid="stFileUploaderDropzone"] *{color:#102b43!important}.stApp [data-testid="stText"]{white-space:pre-wrap;overflow-wrap:anywhere;color:#102b43}.stApp [data-testid="stVerticalBlockBorderWrapper"]{border-color:#dbe4ee!important}.stApp [data-testid="stExpander"] summary{color:#102b43!important}
@media(max-width:700px){.support-hero{padding:20px 16px}.st-key-home_help{padding:12px}.st-key-metrics_complaints [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px!important}.st-key-metrics_complaints [data-testid="stColumn"]{width:100%!important;min-width:0!important}.st-key-metrics_complaints [data-testid="stMetricLabel"]{white-space:normal!important}.st-key-navbox{bottom:calc(10px + env(safe-area-inset-bottom,0px))!important}.st-key-navbox .stButton button{min-height:54px!important}.block-container{padding-bottom:calc(8rem + env(safe-area-inset-bottom,0px))!important}}
/* Compact tracking 3.4 */
.st-key-home_search_compact,.st-key-track_search_compact{background:#fff;border:1px solid var(--pc-line);border-radius:14px;padding:10px 12px;}
.st-key-home_search_compact [data-testid="stVerticalBlock"],.st-key-track_search_compact [data-testid="stVerticalBlock"]{gap:.35rem!important;}
.st-key-home_search_compact [data-testid="stForm"],.st-key-track_search_compact [data-testid="stForm"]{padding:0!important;border:0!important;}
.st-key-home_search_compact [data-testid="stCaptionContainer"] p,.st-key-track_search_compact [data-testid="stCaptionContainer"] p{font-size:.76rem;line-height:1.3;}
.st-key-tracking_summary .routecard{padding:12px 14px;}
.st-key-tracking_summary .routecard h3{margin:2px 0;padding:0;font-size:1.12rem;}
.st-key-tracking_summary [data-testid="stVerticalBlock"]{gap:.5rem!important;}
@media(max-width:700px){.st-key-home_search_compact,.st-key-track_search_compact{padding:9px 10px;}.st-key-tracking_summary .routecard{padding:10px 12px;}}

/* 3.6 — compact, quiet interface; accessible 44px touch targets. */
.block-container{max-width:920px;padding:1.2rem 1.5rem 2rem!important;}
[data-testid="stMainBlockContainer"]>[data-testid="stVerticalBlock"],.block-container>[data-testid="stVerticalBlock"]{gap:.7rem!important;}
.brand{margin:0!important;gap:9px}.brand-mark{width:37px;height:37px;border-radius:10px}.brand-mark svg{width:26px}.brand-name{font-size:1.05rem}.brand-tag{font-size:.58rem;letter-spacing:.045em}
.home-intro{color:#102b43;padding:4px 0 0}.home-intro h1{font-size:clamp(1.55rem,4vw,2.1rem)!important;margin:0!important;padding:0!important;line-height:1.15;letter-spacing:-.04em}.home-intro p{color:#52677c;font-size:.88rem;margin:5px 0 0;line-height:1.35}
.stApp h1{font-size:clamp(1.45rem,4vw,2rem);padding:.15rem 0!important;}.stApp h2{font-size:1.15rem!important;padding:.1rem 0!important;}.stApp h3{font-size:1rem!important;padding:.1rem 0!important;}
.st-key-navbox [data-testid="stHorizontalBlock"]{grid-template-columns:repeat(4,minmax(0,1fr))!important;}
.st-key-navbox{border-radius:13px;}.st-key-navbox button[kind="primary"],.st-key-navbox button[kind="primary"] p{background:#e8eff6!important;color:#102b43!important;}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#153a56!important;border-color:#153a56!important;color:white!important;}button[kind="primary"] p,button[kind="primaryFormSubmit"] p{color:white!important;}
.st-key-home_help{border:1px solid #dbe4ee;border-radius:12px;padding:11px 13px;}.st-key-home_help [data-testid="stVerticalBlock"]{gap:.45rem!important;}.st-key-home_help p{margin:0;}
.st-key-home_search_compact,.st-key-track_search_compact{border-radius:12px;padding:10px 12px!important;}
.st-key-home_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"],.st-key-track_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(105px,auto);gap:7px!important;align-items:end;}
.st-key-home_search_compact [data-testid="stColumn"],.st-key-track_search_compact [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.st-key-home_search_compact .stFormSubmitButton button,.st-key-track_search_compact .stFormSubmitButton button{white-space:nowrap!important;min-height:44px!important;}
.st-key-tracking_summary{background:#fff;border:1px solid #dbe4ee;border-radius:12px;padding:12px;}.st-key-tracking_summary .routecard{border:0;padding:0!important;background:transparent!important;}.st-key-tracking_summary [data-testid="stVerticalBlock"]{gap:.45rem!important;}
.track-kicker{font-size:.72rem;font-weight:750;color:#52677c;letter-spacing:.04em}.track-route{font-size:1.13rem;font-weight:800;letter-spacing:-.02em;color:#102b43;margin:3px 0}.track-location{font-size:.84rem;color:#52677c}.track-date{background:#eaf2f7;border-radius:9px;padding:9px 11px;line-height:1.3;color:#102b43;font-size:.9rem}.track-date small{display:block;color:#52677c;font-size:.75rem;margin-top:3px}
.track-reason{border-left:3px solid #d99a40;padding:6px 9px;background:#fff8ed;border-radius:0 8px 8px 0;color:#573b1d;font-size:.84rem;line-height:1.4;}
.st-key-compact_map [data-testid="stVerticalBlock"]{gap:.25rem!important;}.st-key-compact_map [data-testid="stCaptionContainer"] p{font-size:.72rem!important;}
.st-key-service_menu,.st-key-manager_menu,.st-key-protocol_menu{background:transparent!important;border:0!important;padding:0!important;}
.guide{background:transparent;border:0;padding:2px 0;font-size:.84rem;}.guide small{font-size:.76rem;margin-top:3px;}
.stApp [data-testid="stForm"]{padding:11px;border-radius:11px;}.stApp [data-testid="stExpander"]{border-radius:10px;}
[data-testid="stMetric"]{padding:10px;border-radius:10px;}.stApp [data-testid="stMetricValue"]{font-size:1.35rem;}
@media(max-width:700px){.block-container{padding:.8rem .85rem calc(5.7rem + env(safe-area-inset-bottom,0px))!important;}.st-key-navbox{bottom:calc(6px + env(safe-area-inset-bottom,0px))!important;}.st-key-navbox .stButton button{min-height:48px!important;}.st-key-navbox button p{font-size:.72rem!important;}.st-key-navbox button [data-testid="stIconMaterial"]{font-size:20px!important;}.st-key-home_help{padding:10px 12px;}}
/* 3.7: compact brand with a warmer, more lively palette. */
.home-intro{position:relative;overflow:hidden;isolation:isolate;background:linear-gradient(116deg,#102b43 0%,#174364 65%,#23617e 100%);border-radius:17px;padding:18px 18px 20px;color:#fff;box-shadow:0 5px 18px #102b431c;border-bottom:3px solid #f5a623;}
.home-intro .intro-copy{position:relative;z-index:1;max-width:76%;}.home-intro .intro-tag{color:#ffcc82;font-size:.63rem;font-weight:750;letter-spacing:.08em;margin-bottom:5px;}.home-intro h1{color:white!important;font-size:clamp(1.45rem,4vw,2.05rem)!important;line-height:1.1!important;}.home-intro p{color:#e1ebf7!important;font-size:.83rem;line-height:1.35;margin:7px 0 0;}.intro-art{position:absolute;right:7px;bottom:5px;width:26%;max-width:150px;pointer-events:none;opacity:.94;}
.st-key-home_help{border-left:3px solid #f5a623;padding:12px 14px;box-shadow:0 3px 12px #102b4309;}.help-title{display:flex;align-items:center;gap:8px;font-size:.98rem;font-weight:800;color:#102b43}.help-title svg{width:23px;height:23px;flex:none;color:#a65a08;}
.st-key-home_search_compact,.st-key-track_search_compact{box-shadow:0 3px 12px #102b4309;}.st-key-home_search_compact button[kind="primaryFormSubmit"],.st-key-track_search_compact button[kind="primaryFormSubmit"]{background:#f5a623!important;border-color:#f5a623!important;color:#102b43!important;}.st-key-home_search_compact button[kind="primaryFormSubmit"] p,.st-key-track_search_compact button[kind="primaryFormSubmit"] p{color:#102b43!important;}
.st-key-navbox button[kind="primary"],.st-key-navbox button[kind="primary"] p{background:#fff0d7!important;color:#8a4400!important;}
.track-kicker{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:.78rem;}.track-badge{padding:3px 8px;background:#eaf2f7;color:#174364;border-radius:20px;font-size:.72rem;font-weight:750;}.track-badge.late{background:#fff0d7;color:#8a4400;}.track-badge.done{background:#e5f5eb;color:#146c42;}
.phase-panel{padding:9px 10px;background:#f6f8fb;border-radius:10px;}.phase-panel small{display:block;font-size:.73rem;color:#52677c;}.phase-panel strong{font-size:.87rem;color:#102b43;}.phase-bar{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:3px;margin-top:6px;}.phase-bar span{height:5px;border-radius:8px;background:#dbe4ee;}.phase-bar .past{background:#22617e;}.phase-bar .current{background:#f5a623;}.phase-bar .complete{background:#21815a;}
@media(max-width:700px){.home-intro{padding:15px 13px 16px;}.home-intro .intro-copy{max-width:77%;}.home-intro h1{font-size:1.4rem!important;}.home-intro p{font-size:.79rem;}.intro-art{width:24%;right:5px;}.st-key-home_help{padding:10px 12px;}}
@media(max-width:340px){.home-intro .intro-copy{max-width:100%;}.intro-art{opacity:.10;}}

/* 3.9 — corporate transport portal. Original artwork and brand; mobile first. */
:root{--pc-bg:#f5f7fa;--pc-text:#122d44;--pc-muted:#53687a;--pc-line:#dce4eb;--pc-accent:#f5a623;}
.block-container{max-width:1100px;padding:1.35rem 2rem 2.5rem!important;}
.brand{gap:11px;margin:0!important;padding:5px 0;}.brand-mark{width:44px;height:44px;border-radius:12px;background:#102b43;}.brand-name{font-size:1.25rem;letter-spacing:-.045em;font-weight:850;}.brand-tag{font-size:.64rem;letter-spacing:.12em;color:#53687a!important;}
.brand-name em{font-style:normal;color:#a65a08;}.brand-sub{margin-left:auto;font-size:.69rem;font-weight:750;color:#53687a;letter-spacing:.08em;text-align:right;}
.st-key-navbox{padding:3px 0!important;border:0!important;border-bottom:1px solid var(--pc-line)!important;border-radius:0;box-shadow:none;background:transparent;}
.st-key-navbox button[kind="primary"],.st-key-navbox button[kind="primary"] p{background:#eaf0f5!important;color:#102b43!important;}.st-key-navbox .stButton button{border-radius:8px!important;min-height:44px;}
.home-intro{display:flex;align-items:center;min-height:218px;position:relative;overflow:hidden;isolation:isolate;padding:28px 30px;background:linear-gradient(110deg,#0e293f 0%,#163d59 68%,#215b72 100%);border:0;border-radius:14px;box-shadow:none;}
.home-intro:before{content:'';position:absolute;right:0;top:0;width:7px;height:100%;background:#f5a623;z-index:3;}
.home-intro .intro-copy{max-width:57%;z-index:2;}.home-intro .intro-tag{display:flex;align-items:center;gap:7px;color:#ffca77;font-size:.69rem;letter-spacing:.14em;font-weight:800;margin:0 0 11px;}.intro-tag:before{content:'';height:2px;width:19px;background:#f5a623;flex:none;}
.home-intro h1{font-size:clamp(1.75rem,3.5vw,2.65rem)!important;line-height:1.08!important;letter-spacing:-.04em;margin:0!important;padding:0!important;}.home-intro h1 span{color:#ffbf58;}.home-intro p{font-size:.92rem;line-height:1.4;margin:10px 0 0!important;max-width:340px;}.intro-art{width:47%;max-width:470px;right:9px;bottom:0;opacity:1;}
.st-key-home_search_compact,.st-key-track_search_compact{border-radius:13px;border:1px solid var(--pc-line);padding:14px 17px!important;box-shadow:0 3px 12px #102b4308;}.st-key-home_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"],.st-key-track_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"]{grid-template-columns:minmax(0,1fr) minmax(106px,auto);}.st-key-home_search_compact [data-testid="stCaptionContainer"] p,.st-key-track_search_compact [data-testid="stCaptionContainer"] p{font-size:.81rem;}
.st-key-home_search_compact .stFormSubmitButton button,.st-key-track_search_compact .stFormSubmitButton button{border-radius:8px!important;}
.st-key-home_help{padding:13px 16px!important;border-left:3px solid #f5a623;border-radius:12px;box-shadow:none;}.help-title{font-size:1.03rem;}.st-key-home_help [data-testid="stCaptionContainer"] p{font-size:.84rem;}.st-key-home_help button{background:#153a56!important;border-color:#153a56!important;}.st-key-home_help button p{color:#fff!important;}
.st-key-home_shortcuts [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px!important;}.st-key-home_shortcuts [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}.st-key-home_shortcuts [data-testid="stVerticalBlock"]{gap:.3rem!important;}.st-key-home_shortcuts button{justify-content:flex-start!important;min-height:45px!important;padding:8px 12px!important;border-radius:9px!important;}.st-key-home_shortcuts button p{font-size:.85rem;line-height:1.2;white-space:normal!important;}.st-key-home_shortcuts button [data-testid="stIconMaterial"]{color:#a65a08!important;}
.portal-label{font-size:.74rem;letter-spacing:.09em;text-transform:uppercase;font-weight:750;color:#53687a;margin:1px 0 0;}.portal-footer{font-size:.73rem;color:#53687a;border-top:1px solid var(--pc-line);padding:10px 0 0;}
.st-key-tracking_summary{padding:14px!important;border-radius:12px;}.track-date{background:#ecf3f8;}.phase-bar .current{background:#f5a623;}.st-key-compact_map{background:#fff;border:1px solid var(--pc-line);padding:9px 10px;border-radius:12px;}
.support-hero{border-radius:12px;box-shadow:none;padding:16px 18px;}.stApp [data-testid="stForm"],.stApp [data-testid="stExpander"]{border-radius:10px;}.stButton button,.stFormSubmitButton button,.stDownloadButton button{border-radius:9px;}
@media(min-width:701px){.st-key-navbox [data-testid="stHorizontalBlock"]{gap:9px!important;}.st-key-navbox .stButton button{justify-content:center!important;}.st-key-navbox button p{font-size:.9rem!important;}}
@media(max-width:700px){.block-container{padding:.7rem .85rem calc(5.6rem + env(safe-area-inset-bottom,0px))!important;}.brand{gap:8px;padding:2px 0;}.brand-mark{width:38px;height:38px;}.brand-name{font-size:1.12rem;}.brand-tag{font-size:.54rem;letter-spacing:.06em;}.brand-sub{display:none;}.home-intro{min-height:154px;padding:17px 14px;border-radius:12px;}.home-intro:before{width:4px;}.home-intro .intro-copy{max-width:67%;}.home-intro .intro-tag{font-size:.55rem;letter-spacing:.075em;margin-bottom:8px;gap:4px;}.intro-tag:before{width:10px;}.home-intro h1{font-size:clamp(1.35rem,5.8vw,1.8rem)!important;}.home-intro p{font-size:.78rem;line-height:1.3;margin-top:7px!important;}.intro-art{width:36%;right:1px;bottom:4px;}.st-key-navbox{background:#fff!important;border:1px solid var(--pc-line)!important;border-radius:14px!important;padding:4px!important;box-shadow:0 5px 24px #102b4329!important;}.st-key-navbox .stButton button{min-height:48px!important;}.st-key-home_search_compact,.st-key-track_search_compact{padding:10px 11px!important;}.st-key-home_help{padding:10px 12px!important;}.st-key-home_shortcuts button{padding:7px 6px!important;}.st-key-home_shortcuts button p{font-size:.78rem;}.st-key-tracking_summary{padding:10px!important;}}
@media(max-width:360px){.home-intro .intro-copy{max-width:77%;}.intro-art{width:35%;opacity:.6;}.home-intro .intro-tag{letter-spacing:0;}.st-key-home_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"],.st-key-track_search_compact [data-testid="stForm"] [data-testid="stHorizontalBlock"]{grid-template-columns:minmax(0,1fr) 77px;}}
</style>''',unsafe_allow_html=True)
if access and not s.access:
    st.title('Transportadora Paixão'); entered=st.text_input('Código de acesso',type='password')
    if st.button('Entrar',type='primary'):
        if hmac.compare_digest(entered,access):s.access=True;st.rerun()
        else:st.error('Código inválido.')
    st.stop()
if 'dbpath' not in s:
    fd,path=tempfile.mkstemp(prefix='paixao_',suffix='.sqlite3');os.close(fd);s.dbpath=path
store=ResolutionStore(s.dbpath)
store.scan_prevention()
BRAND='''<div class="brand"><div class="brand-mark"><svg width="33" height="28" viewBox="0 0 48 36" fill="none" aria-hidden="true"><path d="M3 5h27v22H3zM30 12h9l6 8v7H30z" fill="#f5a623"/><path d="M34 15h4l4 6h-8z" fill="#102b43"/><circle cx="12" cy="28" r="5" fill="#fff" stroke="#102b43" stroke-width="2"/><circle cx="37" cy="28" r="5" fill="#fff" stroke="#102b43" stroke-width="2"/></svg></div><div><div class="brand-name">PAIXÃO <em>CONNECT</em></div><div class="brand-tag">TRANSPORTADORA PAIXÃO</div></div><div class="brand-sub">PORTAL DO CLIENTE</div></div>'''
st.markdown(BRAND,unsafe_allow_html=True)
PAGES=['Início','Ajuda','Serviços']
NAV_ICONS=['home','support_agent','more_horiz']
def go(p,code=None,service=None):
    if p=='PACO':
        if code:select_delivery(s,store,code)
        open_window(s)
        return
    s.nav=p
    if p=='Serviços' and service is None:s.service_nav='Menu'
    if code and select_delivery(s,store,code):
        s.notice_code=code
        if p=='Rastreio':
            s.track_selected=code
            s.track_search_matches=[];s.track_search_error=None
    if service:s.service_nav=service
    if p=='Ajuda' or service=='Protocolos':
        s.nav='Ajuda'
        close_window(s)
        if code or service=='Protocolos':open_help(s,store,code)
        elif s.get('context',{}).get('code'):
            if s.get('pending') and s.pending.get('kind'):open_help(s,store)
            elif s.get('protocol_task')=='lookup' and s.get('protocol_query',('',''))[0]==s.context['code']:open_help(s,store,protocol=s.protocol_query[1])
            else:open_help(s,store)

def go_help(protocol=None):
    open_help(s,store,protocol=protocol)
    s.nav='Ajuda'
    close_window(s)

st.markdown(PACO_CSS,unsafe_allow_html=True)
with st.container(key='navbox'):
    for col,p,icon in zip(st.columns(len(PAGES),gap='small'),PAGES,NAV_ICONS):
        active=s.nav==p or (p=='Início' and s.nav=='Rastreio') or (p=='Serviços' and s.nav=='Gestão')
        col.button('Mais' if p=='Serviços' else p,icon=f':material/{icon}:',key='nav_button_'+p,on_click=go,args=(p,),type='primary' if active else 'secondary',use_container_width=True)
page=s.nav
# Older sessions may still hold the Services page; it remains reachable via shortcuts.

def quick(label,p,code=None,service=None,primary=False):
    st.button(label,on_click=go,args=(p,code,service),use_container_width=True,type='primary' if primary else 'secondary')
def escape(t):return html.escape(str(t))
def flash(text):s.flash=text;st.rerun()
def guide(title,text,example=None):
    extra=f'<small>{escape(example)}</small>' if example else ''
    st.markdown(f'<div class="guide"><b>{escape(title)}</b> · {escape(text)}{extra}</div>',unsafe_allow_html=True)
def step(number,title):
    st.markdown(f'<div class="step-title"><span>{number}</span>{escape(title)}</div>',unsafe_allow_html=True)
def choose(key,items,container):
    values=[i[0] for i in items];labels={i[0]:i[1] for i in items}
    if s.get(key) not in values:s[key]=values[0]
    widget=key+'_compact_choice'
    # Non-widget state is authoritative, including deep links from other pages.
    if s.get(widget)!=s[key]:s[widget]=s[key]
    def sync():s[key]=s[widget]
    with st.container(key=container):
        st.selectbox('O que você deseja fazer?',values,format_func=labels.get,key=widget,on_change=sync)
    return s[key]
if s.get('flash'):st.success(s.pop('flash'))

def customer_cargo(code):
    d, heading, message=tracking_result(store,code)
    if not d:
        st.warning(f'**{heading}**\n\n{message}',icon=':material/info:')
        st.button('Falar com PACO',on_click=go,args=('PACO',),key='tracking_help',use_container_width=True)
    return d

def track(code):
    d=customer_cargo(code)
    if not d:return
    code=d['code']
    with st.container(key='tracking_summary'):
        badge='late' if d['status']=='Atrasada' or d['stage']=='Tentativa de entrega sem sucesso' else 'done' if d['status']=='Entregue' else ''
        status_label='Atrasada' if d['status']=='Atrasada' else 'Entregue' if d['status']=='Entregue' else 'Atenção' if d['stage']=='Tentativa de entrega sem sucesso' else 'No prazo'
        st.markdown(f'<div class="track-kicker">{escape(code)}<span class="track-badge {badge}">{escape(status_label)}</span></div><div class="track-route">{escape(d["origin"])} → {escape(d["destination"])}</div><div class="track-location">Último registro: {escape(d["location"])}</div>',unsafe_allow_html=True)
        idx=stage_index(d['stage'])
        segments=''.join('<span class="'+('complete' if d['status']=='Entregue' else 'past' if i<idx else 'current' if i==idx else '')+'"></span>' for i in range(len(STAGES)))
        st.markdown(f'<div class="phase-panel"><small>Etapa atual do transporte</small><strong>{escape(d["stage_label"])}</strong><div class="phase-bar" role="img" aria-label="Etapa {idx+1} de {len(STAGES)}">{segments}</div></div>',unsafe_allow_html=True)
        deadline=pd.Timestamp(d['eta']).strftime('%d/%m/%Y')
        forecast=forecast_text(d)
        if forecast:
            title=forecast.split(' (')[0]
            detail=f'Prazo original: {deadline}'
            metrics=delay_summary(d)
            if metrics:detail+=' · '+metrics
            if ' (' in forecast:detail+=' · Estimativa sujeita à confirmação.'
            st.markdown(f'<div class="track-date"><b>{escape(title)}</b><small>{escape(detail)}</small></div>',unsafe_allow_html=True)
        elif d['status']!='Entregue':st.markdown(f'<div class="track-date"><b>Previsão: {escape(deadline)}</b></div>',unsafe_allow_html=True)
        if d['status']=='Atrasada':
            st.markdown(f'<div class="track-reason"><b>Sentimos muito pela demora.</b> {escape(d["reason"])}</div>',unsafe_allow_html=True)
        quick('Resolver problema' if d['status']=='Atrasada' else 'Preciso de ajuda','Ajuda',code,primary=True)
    with st.container(key='compact_map'):
        st.markdown('**Mapa da entrega**')
        import pydeck as pdk
        pts=[]
        for label,cityname,color in [('Origem',d['origin'],[27,96,140]),('Destino',d['destination'],[36,151,104]),('Último registro',d['location'],[245,166,35])]:
            if cityname in CITIES:
                x,y=CITIES[cityname];pts.append({'city':cityname,'label':label,'lon':x,'lat':y,'color':color})
        if pts:
            path=[list(CITIES[d[k]]) for k in ['origin','location','destination'] if d[k] in CITIES]
            layers=[pdk.Layer('PathLayer',[{'path':path}],get_path='path',get_color=[240,155,35],width_min_pixels=3),pdk.Layer('ScatterplotLayer',pts,get_position='[lon,lat]',get_fill_color='color',get_radius=8000,radius_min_pixels=7,pickable=True),pdk.Layer('TextLayer',pts,get_position='[lon,lat]',get_text='city',get_size=13,get_color=[20,43,66],get_pixel_offset=[0,-18])]
            spread=max(max(p['lon'] for p in pts)-min(p['lon'] for p in pts),max(p['lat'] for p in pts)-min(p['lat'] for p in pts)); view=pdk.ViewState(longitude=sum(p['lon'] for p in pts)/len(pts),latitude=sum(p['lat'] for p in pts)/len(pts),zoom=8 if spread<.5 else 6 if spread<3 else 4.8)
            st.pydeck_chart(pdk.Deck(layers=layers,initial_view_state=view,map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',tooltip={'text':'{label}: {city}'}),use_container_width=True,height=215)
        st.caption('Rota ilustrativa: origem, último registro e destino. Não é GPS em tempo real.')
    with st.expander('Histórico e outras opções'):
        for r in store.history(code):st.markdown(f'<div class="event"><span>{escape(r["timestamp"].replace("T"," "))}</span><b>{escape(r["event"])}</b></div>',unsafe_allow_html=True)
        if d['status']=='Entregue':quick('Avaliar entrega','Serviços',code,'Avaliação')
        quick('Consultar notificações','Serviços',code,'Notificações')

def answer(text):
    s.pending=None;start=time.monotonic();mode='Regras';s.ai_error=False
    prepared=complaint_reply(text,store,s.context)
    if prepared is not None:
        msg,pending,resolved=prepared;mode='Triagem PACO'
    elif key:
        try:msg,pending,resolved=reply(text,store,s.context,s.messages,key,model);mode='IA / ferramentas'
        except Exception:msg,pending,resolved=demo_extended(text,store,s.context);s.ai_error=True;mode='Contingência'
    else:msg,pending,resolved=demo_extended(text,store,s.context)
    store.log(mode,resolved,time.monotonic()-start);store.audit('PACO','Interpretar e consultar',s.context.get('code',''),('Ação preparada: '+str(pending.get('kind') or pending.get('action')) if pending else 'Consulta concluída' if resolved else 'Orientação ou recusa')+' · '+mode);s.messages.extend([{'role':'user','content':redact(text)},{'role':'assistant','content':msg}]);s.pending=pending
    sync_chat_delivery(s,store)
    tid=s.context.get('protocol')
    if tid and s.context.get('code') and store.case(tid,s.context['code']):
        s.protocol_query=(s.context['code'],tid);s.protocol_task='lookup';s.help_refresh=True

def confirm_paco_action(p):
    if p.get('kind'):
        tid,new=store.ticket(p['code'],p['kind'],'Solicitação confirmada pelo PACO.',p.get('requested_date',''),actor='PACO')
        msg=('Recebemos sua solicitação! Protocolo ' if new else 'Já existe uma solicitação ativa: ')+tid+'. Acompanhe na Central de ajuda.'
        registered(s,store,p['code'],tid,p['kind'])
    else:
        msg=confirm(store,p)
        store.audit('PACO','Registro confirmado',p.get('code',''),p.get('action',''))
    s.messages.append({'role':'assistant','content':msg})
    s.pending=None

# Render before page content so callbacks and reruns use the same session,
# including on the manager login page (which uses st.stop()).
render_window(st,s,store,answer,confirm_paco_action,go_help,sync_chat_delivery)

SERVICE_ICONS={
    'avaliacao':'<path d="m12 3 2.8 5.7 6.3.9-4.5 4.4 1.1 6.2-5.7-3-5.7 3 1.1-6.2-4.5-4.4 6.3-.9z"/>',
    'paco':'<rect x="4" y="6" width="16" height="13" rx="4"/><path d="M12 2v4M9 13h.01M15 13h.01M9 16h6M2 11v4M22 11v4"/>',
    'frete':'<rect x="5" y="3" width="14" height="18" rx="3"/><path d="M8 7h8M9 12h.01M15 12h.01M9 16h.01M15 16h.01"/>',
    'protocolos':'<rect x="5" y="5" width="14" height="16" rx="2"/><rect x="9" y="3" width="6" height="4" rx="1"/><path d="M9 12h6M9 16h6"/>',
    'notificacoes':'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/>'}
def service_card(key,title,description,button,page,service=None,primary=False):
    with st.container(key='service_'+key):
        st.markdown(f'<div class="service-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{SERVICE_ICONS[key]}</svg></div><div class="service-name">{escape(title)}</div><div class="service-desc">{escape(description)}</div>',unsafe_allow_html=True)
        quick(button,page,service=service,primary=primary)

if page=='Início':
    st.markdown('''<div class="home-intro"><div class="intro-copy"><div class="intro-tag">TRANSPORTE &amp; LOGÍSTICA</div><h1>Conectamos destinos.<br><span>Cuidamos da sua entrega.</span></h1><p>Rastreie sua mercadoria e conte com nosso atendimento em cada etapa do caminho.</p></div><svg class="intro-art" viewBox="0 0 380 222" fill="none" aria-hidden="true"><defs><linearGradient id="road" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff" stop-opacity=".03"/><stop offset="1" stop-color="#fff" stop-opacity=".17"/></linearGradient><linearGradient id="cargo" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#fff"/><stop offset="1" stop-color="#cbdde9"/></linearGradient></defs><path d="M66 222L210 112 380 112V222Z" fill="url(#road)"/><path d="M0 198L380 198" stroke="#a7c4d5" stroke-opacity=".3" stroke-width="2" stroke-dasharray="13 12"/><circle cx="260" cy="91" r="86" stroke="#e2effa" stroke-opacity=".13" stroke-width="1.5"/><circle cx="260" cy="91" r="66" stroke="#e2effa" stroke-opacity=".16" stroke-width="1.5" stroke-dasharray="4 8"/><path d="M30 102C67 42 105 42 144 66S224 95 272 31" stroke="#ffc16a" stroke-width="2" stroke-dasharray="6 6" opacity=".8"/><circle cx="30" cy="102" r="5" fill="#f5a623"/><path d="M272 15a12 12 0 0 0-12 12c0 9 12 18 12 18s12-9 12-18a12 12 0 0 0-12-12z" fill="#f5a623"/><circle cx="272" cy="27" r="4" fill="#153a56"/><path d="M45 154h292v15H45z" fill="#0d253b"/><rect x="51" y="82" width="190" height="76" rx="5" fill="url(#cargo)"/><path d="M241 105h52l43 35v21h-95z" fill="#f5a623"/><path d="M253 113h37l30 25h-67z" fill="#173c59"/><path d="M253 113h8v25h-8z" fill="#315c75"/><path d="M50 145h190v8H50z" fill="#bacbd7"/><path d="M62 97h166" stroke="#c3d3df" stroke-width="2"/><path d="M62 138h166" stroke="#c3d3df" stroke-width="2"/><path d="M76 116h40M76 126h27" stroke="#174364" stroke-width="5" stroke-linecap="round"/><path d="M76 136h18" stroke="#f5a623" stroke-width="4" stroke-linecap="round"/><text x="129" y="125" font-family="Arial,sans-serif" font-size="16" font-weight="800" fill="#173c59">PAIXÃO</text><circle cx="91" cy="168" r="20" fill="#11283d" stroke="#8aa9bc" stroke-width="3"/><circle cx="91" cy="168" r="8" fill="#d4e1ea"/><circle cx="211" cy="168" r="20" fill="#11283d" stroke="#8aa9bc" stroke-width="3"/><circle cx="211" cy="168" r="8" fill="#d4e1ea"/><circle cx="302" cy="168" r="20" fill="#11283d" stroke="#8aa9bc" stroke-width="3"/><circle cx="302" cy="168" r="8" fill="#d4e1ea"/><rect x="325" y="143" width="8" height="8" rx="2" fill="#fff4cf"/></svg></div>''',unsafe_allow_html=True)
    compact_search(store,'home_search',lambda code:go('Rastreio',code))
    with st.container(key='home_help'):
        st.markdown('<div class="help-title"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 0 1 18 0v4a3 3 0 0 1-3 3h-3M3 13h3v5H5a2 2 0 0 1-2-2zM21 13h-3v5"/><path d="M12 19h3"/></svg>Algo não saiu como esperado?</div>',unsafe_allow_html=True)
        st.caption('Atraso, avaria ou mercadoria não recebida? Vamos ajudar.')
        quick('Resolver ou acompanhar um problema','Ajuda')
    with st.container(key='home_shortcuts'):
        st.markdown('<div class="portal-label">Serviços online</div>',unsafe_allow_html=True)
        a,b=st.columns(2,gap='small')
        a.button('Cotação de frete',icon=':material/calculate:',key='home_quote_link',on_click=go,args=('Serviços',None,'Frete'),use_container_width=True)
        b.button('Avisos da entrega',icon=':material/notifications:',key='home_notice_link',on_click=go,args=('Serviços',None,'Notificações'),use_container_width=True)
elif page=='Rastreio':
    compact_search(store,'track_search',lambda code:go('Rastreio',code),lambda:setattr(s,'track_selected',None))
    if s.track_selected:track(s.track_selected)
elif page=='Ajuda':
    customer_support(store,s,go,flash,choose)
elif page=='Serviços':
    st.title('Mais serviços')
    service=choose('service_nav',[('Menu','Selecione um serviço','more_horiz'),('Frete','Calcular frete','calculate'),('Notificações','Ver avisos','notifications'),('Avaliação','Avaliar entrega','star'),('Gestão','Área do gestor','monitoring')],'service_menu')
    if service=='Menu':
        st.caption('Calcule um frete, consulte avisos, avalie uma entrega ou acesse a gestão.')
    elif service=='Frete':
        st.subheader('Quanto custa enviar uma carga?');guide('Em três etapas','Escolha as cidades, informe as medidas e selecione o tipo de entrega.','Exemplo: Fortaleza → Sobral, 20 kg, caixa de 50 × 40 × 30 cm.')
        with st.form('frete'):
            step(1,'De onde sai e para onde vai?')
            a,b=st.columns(2);origin=a.selectbox('Origem',list(CITIES));dest=b.selectbox('Destino',list(CITIES),index=1)
            step(2,'Qual o peso e tamanho da embalagem?')
            weight=st.number_input('Peso na balança (kg)',min_value=.1,max_value=10000.,value=20.)
            a,b,c=st.columns(3);length=a.number_input('Comprimento (cm)',min_value=.1,max_value=10000.,value=50.);width=b.number_input('Largura (cm)',min_value=.1,max_value=10000.,value=40.);height=c.number_input('Altura (cm)',min_value=.1,max_value=10000.,value=30.)
            step(3,'Escolha a velocidade da entrega')
            modality=st.radio('Tipo de frete',['Econômica','Expressa'],format_func=lambda x:'Econômica — menor preço' if x=='Econômica' else 'Expressa — entrega mais rápida');calc=st.form_submit_button('Calcular frete',type='primary',use_container_width=True)
        if calc:
            try:s.freight=quote(origin,dest,weight,length,width,height,modality);s.context['quote']=s.freight;s.freight_saved=False
            except ValueError as e:s.pop('freight',None);st.error(str(e))
        if s.get('freight'):
            q=s.freight
            with st.container(border=True):
                st.caption('Valor estimado da sua entrega');st.header(money(q['total']));st.write(f"{q['origin']} → {q['destination']} · {q['service']}")
                a,b=st.columns(2);a.metric('Prazo estimado',f"{q['days']} dia(s)");b.metric('Distância estimada',f"{q['km']} km")
                with st.expander('Entenda como calculamos o preço'):
                    st.write(f"Peso na balança: {q['weight']} kg. Peso pelo espaço ocupado: {q['cubed']} kg. Peso usado no preço: {q['charge']} kg.")
                    st.caption('Usamos o maior dos dois pesos, a distância aproximada e o tipo de entrega. Valores estimados, sujeitos à confirmação.')
            st.caption('O orçamento é uma simulação. Registrar uma cotação não contrata o transporte.')
            if st.button('Registrar solicitação de cotação',type='primary',disabled=s.get('freight_saved',False)):
                tid=store.save_quote(q);s.freight_saved=True;flash('Cotação registrada: '+tid+' (não constitui contratação).')
    elif service=='Gestão':
        quick('Acessar área do gestor','Gestão',primary=True)
    elif service=='Notificações':
        st.subheader('Novidades sobre sua entrega');guide('Como consultar','Digite o código de rastreamento para ver mudanças de situação e atualizações de chamados.');code=st.text_input('Código da carga',value=s.track_code,key='notice_code')
        if code.strip() and customer_cargo(code):
            notices=store.notices(code)
            if not notices:st.info('Por enquanto, não há novos avisos sobre sua entrega. Você pode voltar a consultar esta página quando quiser.')
            for n in notices:
                with st.container(border=True):st.markdown(n['message']);st.caption(n['created'].replace('T',' '))
        st.caption('Avisos consultados ao abrir esta tela. Não são notificações push ou mensagens externas.')
    else:
        st.subheader('Como foi sua entrega?');guide('Sua opinião importa','Informe o código de uma carga já entregue e escolha uma nota.')
        with st.form('rating'):
            code=st.text_input('Código da carga entregue',value=s.track_code);score=st.selectbox('Sua nota',[1,2,3,4,5],index=4,format_func=lambda x:{1:'1 ★ — Muito ruim',2:'2 ★ — Ruim',3:'3 ★ — Regular',4:'4 ★ — Boa',5:'5 ★ — Excelente'}[x]);sub=st.form_submit_button('Enviar avaliação',type='primary')
        if sub and customer_cargo(code):
            if store.get(code)['status']!='Entregue':st.info('Agradecemos seu interesse em avaliar! A avaliação estará disponível assim que a entrega for concluída. Enquanto isso, acompanhe sua carga pelo rastreamento.')
            else:
                try:store.rate(code,score);flash('Avaliação registrada. Muito obrigado por compartilhar sua experiência com a Transportadora Paixão!')
                except ValueError as e:st.error(str(e))
else:
    st.title('Central de operações')
    if not s.admin:
        guide('Área da equipe','Entre com a senha de gestor para cadastrar entregas, resolver chamados, gerenciar veículos e consultar indicadores.')
        with st.form('login'):
            pw=st.text_input('Senha do gestor',type='password');sub=st.form_submit_button('Acessar painel',type='primary')
        if sub:
            if hmac.compare_digest(pw,admin_pass):s.admin=True;st.rerun()
            else:st.error('Senha incorreta.')
        st.stop()
    if st.button('Sair da gestão'):s.admin=False;s.pop('manager_report',None);st.rerun()
    section=choose('manager_section',[('Visão geral','Indicadores','monitoring'),('Cargas','Gerenciar cargas','inventory_2'),('Protocolos','Resolver chamados','support_agent'),('Inteligência','Plano de ação PACO','psychology'),('Frota','Veículos e motoristas','local_shipping'),('Cotações','Orçamentos','request_quote')],'manager_menu')
    st.divider()
    if section=='Visão geral':
        st.subheader('Como está a operação?');guide('Comece pelos indicadores','Veja o volume de entregas, os atrasos e os atendimentos. Em seguida, consulte os alertas do PACO.');m=store.extended();st.caption('Indicadores da operação · dados de referência.')
        with st.container(key='metrics'):
            for items in [[('Cargas',m['total']),('Entregues',m['delivered']),('Em operação',m['active']),('Atrasadas',m['late'])]]:
                for col,(label,value) in zip(st.columns(len(items)),items):col.metric(label,value)
            with st.expander('Mais indicadores'):
                for items in [[('Taxa de atraso',f"{100*m['late']/max(1,m['total']):.1f}%"),('Protocolos abertos',m['open_tickets']),('Satisfação',f"{m['satisfaction']}/5" if m['ratings'] else '—'),('Valor cotado',money(m['quoted_total']))],[('Interações PACO',m['interactions']),('Tempo médio',f"{m['avg_seconds']:.2f} s" if m['interactions'] else '—'),('Interações concluídas',f"{100*m['resolved']/m['interactions']:.0f}%" if m['interactions'] else '—'),('Avaliações',m['ratings'])]]:
                    for col,(label,value) in zip(st.columns(len(items)),items):col.metric(label,value)
                st.caption('Valor cotado não é receita. Turnos concluídos são um indicador aproximado, não taxa de resolução de clientes.')
        st.subheader('Atenção: problemas que precisam de ação');st.caption('Análise automática por regras ao acessar o painel ou atualizar; não roda em segundo plano.')
        for level,title,action in store.alerts():
            with st.container(border=True):st.markdown(f'**{level} · {title}**');st.caption(action)
        if not store.alerts():st.success('Nenhum alerta nas regras atuais.')
        if st.button('Atualizar análise'):st.rerun()
        with st.expander('Gráficos e desempenho por rota'):
            a,b=st.columns(2)
            with a:
                st.markdown('**Motivos dos atrasos**')
                if m['reasons']:st.bar_chart(pd.DataFrame.from_dict(m['reasons'],orient='index',columns=['Cargas']),color='#b76b09')
                else:st.info('Sem atrasos.')
            with b:
                st.markdown('**Entregas por data de último registro**');st.bar_chart(pd.DataFrame.from_dict(m['delivered_days'],orient='index',columns=['Entregas']),color='#1b608c')
            st.subheader('Quais rotas têm mais atrasos?');st.caption('Compare o percentual de cargas atrasadas em cada trajeto.');df=pd.DataFrame(m['routes']).sort_values('rate',ascending=False);st.dataframe(df.rename(columns={'route':'Rota','total':'Total','late':'Atrasadas','rate':'Atrasos (%)'}),hide_index=True,use_container_width=True)
            st.bar_chart(df.set_index('route')['rate'],horizontal=True,color='#1b608c')
        if key and st.button('Gerar análise estratégica com IA',type='primary'):
            try:
                from openai import OpenAI
                with st.spinner('Analisando…'):r=OpenAI(api_key=key,timeout=25,max_retries=0).chat.completions.create(model=model,messages=[{'role':'system','content':'Analista PACO. Use exclusivamente dados agregados fictícios. Produza diagnóstico e 3 ações priorizadas. Não invente números nem execute ações.'},{'role':'user','content':json.dumps({'indicadores':m,'alertas':store.alerts()},ensure_ascii=False)}],max_completion_tokens=600)
                s.manager_report=r.choices[0].message.content;store.audit('PACO','Gerar análise com IA','Operação','Análise agregada gerada')
            except Exception:st.warning('API indisponível. O radar por regras permanece ativo.')
        if s.get('manager_report'):st.markdown('**Última análise gerada (pode estar desatualizada)**');st.markdown(s.manager_report)
        st.download_button('Baixar relatório gerencial PDF',report(store),'relatorio_paixao.pdf','application/pdf',use_container_width=True)
    elif section=='Cargas':
        st.subheader('Controle das entregas');guide('O que fazer aqui','Consulte cargas existentes, cadastre uma nova entrega ou registre uma mudança de localização ou situação.');rows=store.all();status=st.selectbox('Filtrar situação',['Todas']+STATUS);df=pd.DataFrame([d for d in rows if status=='Todas' or d['status']==status]);st.dataframe(df.rename(columns={'code':'Código','origin':'Origem','destination':'Destino','location':'Localização','status':'Situação','stage':'Etapa','stage_label':'Descrição da etapa','eta':'Prazo','reason':'Motivo','updated':'Último registro','days_late':'Dias de atraso (prazo original)','confirmed_eta':'Nova previsão confirmada','estimated_eta':'Nova previsão estimada'}),hide_index=True,use_container_width=True);st.download_button('Exportar cargas CSV',df.to_csv(index=False).encode('utf-8-sig'),'cargas_paixao.csv','text/csv')
        with st.expander('1. Cadastrar nova entrega'):
            st.caption('Informe origem, destino e prazo. O sistema gera o código de rastreio.')
            with st.form('create_cargo'):
                a,b=st.columns(2);origin=a.selectbox('Origem',list(CITIES));dest=b.selectbox('Destino',list(CITIES),index=1);eta=st.date_input('Prazo original',today()+timedelta(days=3),min_value=today());vid=st.selectbox('Veículo (opcional)',['']+[v['id'] for v in store.fleet() if v['status']!='Manutenção']);sub=st.form_submit_button('Cadastrar',type='primary')
            if sub:
                try:flash('Carga cadastrada: '+store.create_cargo(origin,dest,eta,vid))
                except ValueError as e:st.error(str(e))
        with st.expander('2. Atualizar localização ou situação'):
            st.caption('Escolha a carga, a cidade atual e a etapa do transporte. Se estiver atrasada, a nova etapa aparecerá sem apagar o atraso do prazo original.')
            active=[d['code'] for d in rows if d['status']!='Entregue']
            if active:
                code=st.selectbox('Carga a atualizar',active);d=store.get(code)
                with st.form('update_'+code):
                    loc=st.selectbox('Localização',list(CITIES),index=list(CITIES).index(d['location']));stat=st.selectbox('Nova etapa ou registro de atraso',STATUS,index=STATUS.index(d['stage']),format_func=stage_label);reason=st.text_input('Motivo (obrigatório para atraso)',value=d['reason']);sub=st.form_submit_button('Salvar movimentação',type='primary')
                if sub:
                    try:store.update_cargo(code,loc,stat,reason);flash('Movimentação registrada.')
                    except ValueError as e:st.error(str(e))
            else:st.info('Nenhuma carga ativa.')
    elif section=='Protocolos':
        manager_cases(store,flash)
    elif section=='Inteligência':
        intelligence(store)
    elif section=='Frota':
        st.subheader('Veículos e motoristas');guide('Organize sua frota','Veja os veículos, atualize seus dados e vincule cargas a veículos que não estão em manutenção.');vehicles=store.fleet();st.dataframe(pd.DataFrame(vehicles).rename(columns={'id':'Código','label':'Veículo','driver':'Motorista','capacity':'Capacidade (kg)','status':'Situação'}),hide_index=True,use_container_width=True)
        vid=st.selectbox('Cadastrar ou editar veículo',['Novo']+[v['id'] for v in vehicles]);v=next((x for x in vehicles if x['id']==vid),{})
        with st.form('vehicle_'+vid):
            new_id=st.text_input('Código V + 3 dígitos',value=v.get('id',f"V{max(int(x['id'][1:]) for x in vehicles)+1:03}"),disabled=vid!='Novo');label=st.text_input('Identificação',v.get('label',''));driver=st.text_input('Motorista',v.get('driver',''));cap=st.number_input('Capacidade (kg)',min_value=1.,max_value=100000.,value=float(v.get('capacity',8000)));opts=['Disponível','Em rota','Manutenção'];stat=st.selectbox('Situação',opts,index=opts.index(v.get('status','Disponível')));sub=st.form_submit_button('Salvar veículo')
        if sub:
            try:
                if vid=='Novo' and any(x['id']==new_id for x in vehicles):raise ValueError('Código já cadastrado.')
                store.save_vehicle(new_id,label,driver,cap,stat);flash('Veículo salvo.')
            except ValueError as e:st.error(str(e))
        st.subheader('Vincular uma entrega a um veículo');st.caption('Alocação de referência; não valida peso real, jornada ou disponibilidade de motorista.')
        active=[d['code'] for d in store.all() if d['status']!='Entregue'];available=[v['id'] for v in vehicles if v['status']!='Manutenção']
        if active and available:
            with st.form('assignment'):
                code=st.selectbox('Carga',active);vid=st.selectbox('Veículo disponível para alocação',available);sub=st.form_submit_button('Vincular')
            if sub:
                try:store.assign(code,vid);flash('Vínculo atualizado.')
                except ValueError as e:st.error(str(e))
        st.caption('Entregas vinculadas a veículos');st.dataframe(pd.DataFrame(store.assignments()).rename(columns={'code':'Carga','vehicle':'Veículo'}),hide_index=True,use_container_width=True)
    else:
        st.subheader('Orçamentos solicitados');guide('Acompanhe as solicitações','Confira os fretes calculados e registrados pelos clientes. O valor é estimado e não representa receita.');qs=store.quotes();st.dataframe(pd.DataFrame(qs).rename(columns={'id':'Cotação','origin':'Origem','destination':'Destino','weight':'Peso (kg)','length':'Comprimento (cm)','width':'Largura (cm)','height':'Altura (cm)','service':'Modalidade','total':'Valor estimado (R$)','created':'Registro'}),hide_index=True,use_container_width=True) if qs else st.info('Nenhuma cotação registrada.')
        if qs:st.download_button('Exportar cotações CSV',pd.DataFrame(qs).to_csv(index=False).encode('utf-8-sig'),'cotacoes.csv','text/csv')
with st.expander('Sobre o serviço e privacidade'):
    st.markdown('**Transportadora Paixão | Paixão Connect**. Ambiente com dados de exemplo. O PACO interpreta pedidos, consulta ferramentas e prepara ações; gravações dependem de confirmação. O modo sem API usa regras. O banco é isolado por sessão; reiniciar ou abrir outra sessão pode apagar os registros. Não informe dados reais. Não há GPS, contratação, pagamento, envio externo ou monitoramento contínuo.')
st.markdown('<div class="portal-footer">TRANSPORTADORA PAIXÃO · Inteligência em movimento</div>',unsafe_allow_html=True)

"""
Service layer for LINE Messaging API interactions.
"""
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    PostbackEvent,
    TextMessage,
    TextSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    PostbackAction,
    FlexSendMessage,
)

from ..config import LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, FRONTEND_URL
from .repair_service import STATUS_DISPLAY, RepairStatus

# Initialize LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Load JSON Templates
TEMPLATES_PATH = os.path.join(os.path.dirname(__file__), "line_templates.json")

def load_template(name: str, **kwargs) -> dict:
    """
    Load a template from JSON and replace placeholders.
    """
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    template_str = json.dumps(data[name], ensure_ascii=False)
    # Global placeholders
    template_str = template_str.replace("{{frontend_url}}", FRONTEND_URL)
    
    # Custom placeholders
    for key, value in kwargs.items():
        template_str = template_str.replace(f"{{{{{key}}}}}", str(value))
        
    return json.loads(template_str)

def get_advice_data() -> dict:
    """
    Load troubleshooting advice data from JSON.
    """
    with open(TEMPLATES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["advice_data"]

def handle_event(body, signature):
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as exc:
        raise exc


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    user_id = event.source.user_id

    if text == "แจ้งซ่อม":
        send_repair_form(user_id)
    elif text == "ติดตามสถานะ":
        send_tracking_info(user_id)
    elif text == "แก้ไขปัญหาเบื้องต้น":
        send_troubleshooting_menu(user_id)
    else:
        trouble_map = {
            "เปิดเครื่องไม่ติด": "no_power", "หน้าจอดำ": "black_screen", "เครื่องช้า": "slow_pc",
            "Wi-Fi ต่อไม่ได้": "wifi", "โปรแกรมค้าง": "hang", "จอฟ้า/รีสตาร์ทเอง": "blue_screen",
            "เครื่องร้อน/พัดลมดัง": "overheat", "ไม่มีเสียง/ไมค์ไม่ดัง": "no_sound",
            "คีย์บอร์ดพิมพ์ไม่ได้ / ปุ่มเพี้ยน": "keyboard"
        }
        if text in trouble_map:
            send_trouble_advice(user_id, trouble_map[text])


@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data
    user_id = event.source.user_id

    if data == "action=repair_form":
        line_bot_api.push_message(user_id, TextSendMessage(text=f"คลิกที่นี่เพื่อแจ้งซ่อม: {FRONTEND_URL}/"))
    elif data == "action=track_repair":
        line_bot_api.push_message(user_id, TextSendMessage(text=f"คลิกที่นี่เพื่อติดตามสถานะ: {FRONTEND_URL}/track"))
    elif data.startswith("action=confirm_return_cancelled"):
        # Parsing qid from data (e.g., action=confirm_return_cancelled&qid=A123)
        parts = data.split("&")
        queue_id = next((p.split("=")[1] for p in parts if p.startswith("qid=")), None)
        
        if queue_id:
            from .repair_service import SESSION_LOCAL, RepairRequest, datetime
            db = SESSION_LOCAL()
            repair = db.query(RepairRequest).filter(RepairRequest.queueId == queue_id).first()
            if repair:
                repair.status = RepairStatus.COMPLETED
                repair.completedAt = datetime.utcnow()
                db.commit()
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"ขอบคุณครับ ระบบบันทึกว่าคุณได้รับเครื่อง {queue_id} คืนเรียบร้อยแล้ว"))
            db.close()


def send_troubleshooting_menu(user_id):
    advice_data = get_advice_data()
    flex_contents = load_template("troubleshooting_menu")
    
    buttons = []
    for key, info in advice_data.items():
        buttons.append({
            "type": "button",
            "action": {"type": "message", "label": info["title"], "text": info["title"]},
            "style": "secondary", "margin": "md", "height": "sm", "color": "#e0e0e0"
        })
    
    flex_contents["body"]["contents"] = buttons
    line_bot_api.push_message(user_id, FlexSendMessage(alt_text="เลือกปัญหาที่พบ", contents=flex_contents))


def send_trouble_advice(user_id, problem_key):
    advice_data = get_advice_data()
    info = advice_data.get(problem_key, {"title": "ปัญหาเบื้องต้น", "advice": "กรุณานำเครื่องมาตรวจสอบที่ร้าน..."})
    
    flex_contents = load_template("trouble_advice", title=info["title"], advice=info["advice"])
    line_bot_api.push_message(user_id, FlexSendMessage(alt_text=info["title"], contents=flex_contents))


def send_repair_form(user_id):
    buttons_template = ButtonsTemplate(
        title="แจ้งซ่อมอุปกรณ์", text="กรุณากดปุ่มด้านล่างเพื่อกรอกรายละเอียดการซ่อม",
        actions=[PostbackAction(label="กรอกฟอร์มแจ้งซ่อม", data="action=repair_form")]
    )
    line_bot_api.push_message(user_id, TemplateSendMessage(alt_text="แจ้งซ่อมอุปกรณ์", template=buttons_template))


def send_tracking_info(user_id):
    buttons_template = ButtonsTemplate(
        title="ติดตามสถานะการซ่อม", text="กรุณากดปุ่มด้านล่างเพื่อดูสถานะงานซ่อมของคุณ",
        actions=[PostbackAction(label="เช็คสถานะ", data="action=track_repair")]
    )
    line_bot_api.push_message(user_id, TemplateSendMessage(alt_text="ติดตามสถานะการซ่อม", template=buttons_template))


def push_message(line_user_id: str, message: str):
    try:
        line_bot_api.push_message(line_user_id, TextSendMessage(text=message))
    except Exception as e:
        print(f"Error pushing LINE message: {e}")


def push_update_notification(line_user_id: str, queue_id: str, status_name: str):
    if status_name == RepairStatus.CANCELLED:
        return send_cancellation_notification(line_user_id, queue_id)

    thai_status = STATUS_DISPLAY.get(status_name, status_name)
    flex_contents = load_template("status_update", queue_id=queue_id, thai_status=thai_status)
    
    try:
        line_bot_api.push_message(line_user_id, FlexSendMessage(alt_text="อัปเดตสถานะการซ่อม", contents=flex_contents))
    except Exception as e:
        print(f"Error pushing Flex Message: {e}")


def send_cancellation_notification(line_user_id: str, queue_id: str):
    flex_contents = load_template("cancellation", queue_id=queue_id)
    try:
        line_bot_api.push_message(line_user_id, FlexSendMessage(alt_text="ยืนยันการรับเครื่องคืน", contents=flex_contents))
    except Exception as e:
        print(f"Error pushing Cancellation Flex: {e}")


def reply_message(reply_token: str, message: str):
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

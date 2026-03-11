"""
Service layer for LINE Messaging API interactions.
"""
import os
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

# Initialize LINE Bot API
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Mapping for Display
STATUS_DISPLAY = {
    "PENDING_REPAIR": "คำขอส่งซ่อม",
    "PICKING_UP": "กำลังไปรับเครื่อง",
    "RECEIVED": "รับเครื่องแล้ว",
    "DIAGNOSING": "ตรวจเช็กปัญหา",
    "QUOTED": "ส่งใบเสนอราคา",
    "WAITING_FOR_PAYMENT": "รอการจ่ายเงิน",
    "PAID": "จ่ายเงินแล้ว",
    "REPAIRING": "กำลังซ่อม",
    "REPAIRED": "ซ่อมเสร็จแล้ว",
    "DELIVERING": "กำลังส่งเครื่องกลับ",
    "COMPLETED": "ลูกค้ากดรับเครื่องแล้ว"
}

def handle_event(body, signature):
    """
    Handle incoming LINE webhook events.
    """
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as exc:
        raise exc


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """
    Handle text messages from LINE users.
    """
    text = event.message.text.strip()
    user_id = event.source.user_id

    # คำสั่งหลัก
    if text == "แจ้งซ่อม":
        send_repair_form(user_id)
    elif text == "ติดตามสถานะ":
        send_tracking_info(user_id)
    elif text == "แก้ไขปัญหาเบื้องต้น":
        send_troubleshooting_menu(user_id)
    
    # Handle Troubleshooting Keywords
    else:
        trouble_map = {
            "เปิดเครื่องไม่ติด": "no_power",
            "หน้าจอดำ": "black_screen",
            "เครื่องช้า": "slow_pc",
            "Wi-Fi ต่อไม่ได้": "wifi",
            "โปรแกรมค้าง": "hang",
            "จอฟ้า/รีสตาร์ทเอง": "blue_screen",
            "เครื่องร้อน/พัดลมดัง": "overheat",
            "ไม่มีเสียง/ไมค์ไม่ดัง": "no_sound",
            "คีย์บอร์ดพิมพ์ไม่ได้ / ปุ่มเพี้ยน": "keyboard"
        }
        
        if text in trouble_map:
            send_trouble_advice(user_id, trouble_map[text])
        else:
            # กรณีไม่ใช่คำที่ระบุไว้ ไม่ต้องตอบโต้อัตโนมัติ (หรือส่งเมนู Rich Menu)
            pass


@handler.add(PostbackEvent)
def handle_postback(event):
    """
    Handle postback events (เช่น จากปุ่มที่ไม่มีข้อความส่งกลับ).
    """
    data = event.postback.data
    user_id = event.source.user_id

    if data == "action=repair_form":
        line_bot_api.push_message(user_id, TextSendMessage(text=f"คลิกที่นี่เพื่อแจ้งซ่อม: {FRONTEND_URL}/"))
    elif data == "action=track_repair":
        line_bot_api.push_message(user_id, TextSendMessage(text=f"คลิกที่นี่เพื่อติดตามสถานะ: {FRONTEND_URL}/track"))


def send_troubleshooting_menu(user_id):
    """
    Send a Flex Message with buttons that send text when clicked.
    """
    problems = [
        "เปิดเครื่องไม่ติด", "หน้าจอดำ", "เครื่องช้า", 
        "Wi-Fi ต่อไม่ได้", "โปรแกรมค้าง", "จอฟ้า/รีสตาร์ทเอง",
        "เครื่องร้อน/พัดลมดัง", "ไม่มีเสียง/ไมค์ไม่ดัง", "คีย์บอร์ดพิมพ์ไม่ได้ / ปุ่มเพี้ยน"
    ]
    
    buttons = []
    for p in problems:
        buttons.append({
            "type": "button",
            "action": {
                "type": "message",
                "label": p,
                "text": p
            },
            "style": "secondary",
            "margin": "sm" if not buttons else "md",
            "height": "sm",
            "color": "#e0e0e0"
        })

    flex_contents = {
        "type": "bubble",
        "size": "mega",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "เลือกปัญหาที่พบได้เลยครับ 👇",
                    "weight": "bold",
                    "size": "lg",
                    "color": "#ffffff"
                }
            ],
            "backgroundColor": "#272727",
            "paddingTop": "25px",
            "paddingBottom": "20px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": buttons,
            "backgroundColor": "#272727",
            "paddingBottom": "30px",
            "spacing": "sm"
        }
    }
    line_bot_api.push_message(user_id, FlexSendMessage(alt_text="เลือกปัญหาที่พบ", contents=flex_contents))


def send_trouble_advice(user_id, problem_key):
    """
    Send advice for a specific problem and a repair button.
    """
    advice_map = {
        "no_power": {
            "title": "เปิดเครื่องไม่ติด",
            "advice": "ลองตรวจสอบสายไฟและปลั๊กไฟว่าเสียบแน่นหรือไม่ หากเป็นโน้ตบุ๊ก ลองถอดแบตเตอรี่ออกแล้วเสียบสายชาร์จโดยตรง"
        },
        "black_screen": {
            "title": "หน้าจอดำ",
            "advice": "ลองกดปุ่ม Windows + Ctrl + Shift + B เพื่อรีเซ็ตไดรเวอร์การ์ดจอ หรือเช็คสายต่อจอว่าแน่นหรือไม่"
        },
        "slow_pc": {
            "title": "เครื่องช้า",
            "advice": "ลองล้างไฟล์ขยะ (Disk Cleanup) และตรวจสอบโปรแกรมที่รันตอนเริ่มต้น (Task Manager > Startup)"
        },
        "wifi": {
            "title": "Wi-Fi ต่อไม่ได้",
            "advice": "ลองปิด-เปิดเราเตอร์ใหม่ หรือกด Forget Network แล้วเชื่อมต่ออีกครั้ง"
        },
        "hang": {
            "title": "โปรแกรมค้าง",
            "advice": "กด Ctrl + Alt + Del เพื่อเรียก Task Manager แล้วสั่ง End Task โปรแกรมที่ค้าง"
        },
        "blue_screen": {
            "title": "จอฟ้า/รีสตาร์ทเอง",
            "advice": "จดรหัส Error (เช่น 0x00...) เพื่อแจ้งช่างตรวจสอบ หรือลองถอดอุปกรณ์ USB ที่ไม่ได้ใชอก"
        },
        "overheat": {
            "title": "เครื่องร้อน/พัดลมดัง",
            "advice": "ตรวจสอบว่าไม่มีอะไรมาบังช่องระบายอากาศ และควรนำเครื่องมาทำความสะอาดปัดฝุ่นและทาซิลิโคนใหม่"
        },
        "no_sound": {
            "title": "ไม่มีเสียง/ไมค์ไม่ดัง",
            "advice": "ตรวจสอบการตั้งค่า Output/Input ใน Sound Settings และเช็คว่าไม่ได้กด Mute ไว้"
        },
        "keyboard": {
            "title": "คีย์บอร์ดพิมพ์ไม่ได้",
            "advice": "ตรวจสอบว่าปุ่ม Num Lock หรือปุ่ม Fn ค้างหรือไม่ หรือลองรีสตาร์ทเครื่องดูสักครั้ง"
        }
    }

    info = advice_map.get(problem_key, {"title": "ปัญหาเบื้องต้น", "advice": "กรุณานำเครื่องมาตรวจสอบที่ร้านเพื่อหาสาเหตุที่แน่ชัดครับ"})
    
    flex_contents = {
        "type": "bubble",
        "header": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": info["title"], "weight": "bold", "size": "lg", "color": "#021d46"}
            ],
            "paddingBottom": "10px"
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": info["advice"], "wrap": True, "size": "sm", "color": "#666666"}
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary",
                    "color": "#0044cc",
                    "action": {
                        "type": "uri",
                        "label": "แจ้งซ่อมทันที",
                        "uri": f"{FRONTEND_URL}/"
                    }
                }
            ]
        }
    }
    line_bot_api.push_message(user_id, FlexSendMessage(alt_text=info["title"], contents=flex_contents))


def send_repair_form(user_id):
    """
    Send a button template for opening the repair request form.
    """
    buttons_template = ButtonsTemplate(
        title="แจ้งซ่อมอุปกรณ์",
        text="กรุณากดปุ่มด้านล่างเพื่อกรอกรายละเอียดการซ่อม",
        actions=[
            PostbackAction(label="กรอกฟอร์มแจ้งซ่อม", data="action=repair_form"),
        ],
    )
    template_message = TemplateSendMessage(
        alt_text="แจ้งซ่อมอุปกรณ์", template=buttons_template
    )
    line_bot_api.push_message(user_id, template_message)


def send_tracking_info(user_id):
    """
    Send a button template for tracking repair status.
    """
    buttons_template = ButtonsTemplate(
        title="ติดตามสถานะการซ่อม",
        text="กรุณากดปุ่มด้านล่างเพื่อดูสถานะงานซ่อมของคุณ",
        actions=[
            PostbackAction(label="เช็คสถานะ", data="action=track_repair"),
        ],
    )
    template_message = TemplateSendMessage(
        alt_text="ติดตามสถานะการซ่อม", template=buttons_template
    )
    line_bot_api.push_message(user_id, template_message)


def push_message(line_user_id: str, message: str):
    """
    Push a simple text message to a LINE user.
    """
    try:
        line_bot_api.push_message(line_user_id, TextSendMessage(text=message))
    except Exception as e:
        print(f"Error pushing LINE message: {e}")


def push_update_notification(line_user_id: str, queue_id: str, status_name: str):
    """
    Push a Flex Message to notify the user about a status update.
    """
    thai_status = STATUS_DISPLAY.get(status_name, status_name)
    flex_contents = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "อัปเดตสถานะการซ่อม", "weight": "bold", "size": "xl"},
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {"type": "text", "text": "เลขคิว", "color": "#aaaaaa", "size": "sm", "flex": 1},
                                {"type": "text", "text": queue_id, "wrap": True, "color": "#666666", "size": "sm", "flex": 4},
                            ],
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {"type": "text", "text": "สถานะใหม่", "color": "#aaaaaa", "size": "sm", "flex": 1},
                                {"type": "text", "text": thai_status, "wrap": True, "color": "#ff0000", "size": "sm", "flex": 4, "weight": "bold"},
                            ],
                        },
                    ],
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "ดูรายละเอียดเพิ่มเติม",
                        "uri": f"{FRONTEND_URL}/track",
                    },
                }
            ],
            "flex": 0,
        },
    }

    try:
        line_bot_api.push_message(line_user_id, FlexSendMessage(alt_text="อัปเดตสถานะการซ่อม", contents=flex_contents))
    except Exception as e:
        print(f"Error pushing Flex Message: {e}")


def reply_message(reply_token: str, message: str):
    """
    Reply to a LINE message.
    """
    line_bot_api.reply_message(reply_token, TextSendMessage(text=message))

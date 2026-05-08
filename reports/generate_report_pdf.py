from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT_DIR / "reports" / "project_report_summary.pdf"
FONT_REGULAR = r"C:\Windows\Fonts\tahoma.ttf"
FONT_BOLD = r"C:\Windows\Fonts\tahomabd.ttf"


def register_fonts() -> None:
    pdfmetrics.registerFont(TTFont("Thai", FONT_REGULAR))
    pdfmetrics.registerFont(TTFont("Thai-Bold", FONT_BOLD))


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName="Thai-Bold",
            fontSize=19,
            leading=28,
            alignment=TA_CENTER,
            wordWrap="CJK",
            spaceAfter=14,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName="Thai",
            fontSize=12,
            leading=18,
            alignment=TA_CENTER,
            wordWrap="CJK",
            spaceAfter=8,
        ),
        "heading": ParagraphStyle(
            "heading",
            parent=base["Heading2"],
            fontName="Thai-Bold",
            fontSize=14,
            leading=22,
            wordWrap="CJK",
            spaceBefore=10,
            spaceAfter=7,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Thai",
            fontSize=10.5,
            leading=17,
            alignment=TA_LEFT,
            wordWrap="CJK",
            spaceAfter=6,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName="Thai",
            fontSize=10.2,
            leading=16,
            leftIndent=14,
            firstLineIndent=-10,
            wordWrap="CJK",
            spaceAfter=4,
        ),
        "table": ParagraphStyle(
            "table",
            parent=base["BodyText"],
            fontName="Thai",
            fontSize=9.2,
            leading=13,
            wordWrap="CJK",
        ),
        "table_header": ParagraphStyle(
            "table_header",
            parent=base["BodyText"],
            fontName="Thai-Bold",
            fontSize=9.2,
            leading=13,
            alignment=TA_CENTER,
            wordWrap="CJK",
        ),
    }


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text, style)


def bullet(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(f"• {text}", style)


def make_table(rows: list[list[str]], widths: list[float], s: dict[str, ParagraphStyle]) -> Table:
    rendered = []
    for row_index, row in enumerate(rows):
        row_style = s["table_header"] if row_index == 0 else s["table"]
        rendered.append([para(cell, row_style) for cell in row])

    result = Table(rendered, colWidths=widths, repeatRows=1)
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDEBF7")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return result


def page_number(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Thai", 9)
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"หน้า {doc.page}")
    canvas.restoreState()


def build_report() -> None:
    register_fonts()
    s = styles()
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        title="รายงานสรุปโปรเจกต์ MobileViT Image Classification API",
    )

    story = [
        para("รายงานสรุปโปรเจกต์", s["title"]),
        para("High-Throughput Image Classification Service: The MLOps Challenge", s["subtitle"]),
        para("ระบบ API จำแนกรูปภาพด้วย FastAPI และโมเดล apple/mobilevit-small", s["subtitle"]),
        Spacer(1, 0.2 * cm),
        para("สมาชิกกลุ่ม", s["heading"]),
        bullet("นายธนัสถ์ภณ อ่างทอง รหัสนักศึกษา 1650901034", s["bullet"]),
        bullet("นายจีฮาน สุทธินิพนธ์นาม รหัสนักศึกษา 1650904152", s["bullet"]),
        bullet("นายอกัณห์ เกษเพชร รหัสนักศึกษา 1650904269", s["bullet"]),
        para("บทนำ", s["heading"]),
        para(
            "โปรเจกต์นี้จัดทำขึ้นเพื่อพัฒนา API สำหรับจำแนกรูปภาพที่สามารถนำไปใช้งานได้จริง "
            "โดยให้ความสำคัญกับการปรับแต่งโมเดล การจัดการ request พร้อมกัน การบรรจุระบบด้วย Docker "
            "และการเตรียมกระบวนการ CI/CD สำหรับการส่งมอบระบบ",
            s["body"],
        ),
        para("1. รายละเอียดโมเดลที่เลือกและจุดประสงค์การใช้งาน", s["heading"]),
        para(
            "โมเดลที่เลือกใช้คือ apple/mobilevit-small จาก Hugging Face ซึ่งเป็นโมเดลสำหรับงาน Image Classification "
            "ที่มีขนาดเล็กและเหมาะกับงาน inference บน CPU โมเดลนี้ผสมแนวคิดของ CNN และ Transformer "
            "ทำให้สามารถเรียนรู้ทั้งรายละเอียดเฉพาะจุดและภาพรวมของรูปภาพได้ดี",
            s["body"],
        ),
        bullet("จุดประสงค์หลักของระบบคือรับไฟล์รูปภาพจากผู้ใช้และส่งผลการจำแนกกลับในรูปแบบ JSON", s["bullet"]),
        bullet("ระบบใช้ ONNX Quantized เป็น runtime หลัก เพื่อลดขนาดโมเดลและลดภาระการประมวลผล", s["bullet"]),
        bullet("ผลการทำนายประกอบด้วยชื่อ class และค่าความมั่นใจของแต่ละผลลัพธ์", s["bullet"]),
        para("2. ผลการ Optimization", s["heading"]),
        para(
            "กระบวนการ optimization ประกอบด้วยการแปลงโมเดลจาก PyTorch เป็น ONNX และการทำ Dynamic Quantization "
            "กับ layer ประเภท MatMul และ Gemm เพื่อให้โมเดลมีขนาดเล็กลงและยังสามารถทำงานบน ONNX Runtime CPU ได้จริง",
            s["body"],
        ),
        make_table(
            [
                ["รูปแบบโมเดล", "ขนาดโมเดล (MB)", "Latency เฉลี่ย (ms)", "Latency P95 (ms)"],
                ["PyTorch", "21.44", "34.43", "37.51"],
                ["ONNX", "21.49", "55.58", "63.64"],
                ["ONNX Quantized", "11.56", "47.00", "56.47"],
            ],
            [4.4 * cm, 3.6 * cm, 4.0 * cm, 4.0 * cm],
            s,
        ),
        Spacer(1, 0.15 * cm),
        para(
            "จากผลการทดสอบพบว่า ONNX Quantized ลดขนาดโมเดลจาก 21.49 MB เหลือ 11.56 MB "
            "คิดเป็นการลดขนาดประมาณ 46% และมี latency ดีกว่า ONNX ปกติบนเครื่องที่ใช้ทดสอบ",
            s["body"],
        ),
        para("3. กลยุทธ์การจัดการ Error Handling และ Data Validation", s["heading"]),
        para(
            "ระบบตรวจสอบข้อมูลก่อนเข้าสู่ขั้นตอน inference เพื่อป้องกันไฟล์ที่ไม่ถูกต้องและลดโอกาสเกิด error ระหว่างประมวลผล "
            "โดยมีการตอบกลับ HTTP status code ที่เหมาะสมกับแต่ละกรณี",
            s["body"],
        ),
        make_table(
            [
                ["กรณี", "แนวทางจัดการ", "ผลลัพธ์"],
                ["ชนิดไฟล์ไม่ถูกต้อง", "อนุญาตเฉพาะ JPEG, PNG และ WebP", "400 Bad Request"],
                ["ไฟล์ว่างหรือไฟล์เสีย", "ตรวจสอบข้อมูลไฟล์และความสมบูรณ์ของรูปภาพ", "400 Bad Request"],
                ["ไฟล์ใหญ่เกินกำหนด", "จำกัดขนาดไฟล์สูงสุด 5 MB", "413 Request Entity Too Large"],
                ["เกิดข้อผิดพลาดระหว่าง inference", "ดักจับ error และส่งข้อความอธิบายกลับ", "500 Internal Server Error"],
            ],
            [4.2 * cm, 7.6 * cm, 4.0 * cm],
            s,
        ),
        para("4. ผลการทดสอบจาก JMeter และบทวิเคราะห์ประสิทธิภาพ", s["heading"]),
        para(
            "การทดสอบโหลดใช้การส่ง request พร้อมไฟล์รูปภาพไปยัง endpoint /predict "
            "เพื่อประเมินความสามารถของระบบเมื่อมีผู้ใช้งานพร้อมกันหลายรายการ",
            s["body"],
        ),
        make_table(
            [
                ["หัวข้อ", "ผลการทดสอบ"],
                ["Runtime ของโมเดล", "onnx-quantized"],
                ["จำนวน request", "30"],
                ["จำนวน concurrent users", "10"],
                ["จำนวน request ที่สำเร็จ", "30/30"],
                ["Throughput", "10.32 requests/second"],
                ["Average Latency", "874.90 ms"],
                ["P95 Latency", "1187.96 ms"],
            ],
            [5.5 * cm, 9.8 * cm],
            s,
        ),
        Spacer(1, 0.15 * cm),
        para(
            "ผลการทดสอบแสดงให้เห็นว่าระบบสามารถตอบสนอง request ได้ครบทุกครั้งในชุดทดสอบขนาดเล็ก "
            "โดยค่า P95 latency อยู่ที่ประมาณ 1.19 วินาที เมื่อเพิ่มจำนวนผู้ใช้งานพร้อมกันมากขึ้น "
            "ระบบจะเริ่มใช้ทรัพยากร CPU มากขึ้น ซึ่งเป็นลักษณะปกติของงาน inference",
            s["body"],
        ),
        para("5. แผนผังระบบและภาพรวม CI/CD Pipeline", s["heading"]),
        para(
            "ภาพรวมระบบประกอบด้วย Client สำหรับส่งรูปภาพ, FastAPI สำหรับรับ request และตรวจสอบข้อมูล, "
            "ProcessPoolExecutor สำหรับแยกงาน inference, ONNX Quantized Model สำหรับทำนายผล, "
            "Docker สำหรับบรรจุระบบ และ GitHub Actions สำหรับทดสอบอัตโนมัติ",
            s["body"],
        ),
        make_table(
            [
                ["ส่วนประกอบ", "หน้าที่"],
                ["Client", "ส่งไฟล์รูปภาพมายัง API"],
                ["FastAPI", "รับ request ตรวจสอบข้อมูล และส่ง response"],
                ["ProcessPoolExecutor", "แยกงาน inference ที่ใช้ CPU ออกจาก event loop"],
                ["ONNX Quantized Model", "ประมวลผลและทำนาย class ของรูปภาพ"],
                ["Docker", "บรรจุแอปพลิเคชันและโมเดลให้นำไปรันได้ง่าย"],
                ["GitHub Actions", "รัน unit test และเตรียม deploy ไปยัง Cloud"],
            ],
            [5.0 * cm, 10.5 * cm],
            s,
        ),
        para(
            "ในส่วน CI/CD เมื่อมีการ push โค้ดไปยัง branch main ระบบจะรัน unit test โดยอัตโนมัติ "
            "หากการทดสอบผ่านทั้งหมดจึงสามารถนำไปต่อยอดสู่การ deploy บน Hugging Face Spaces ได้",
            s["body"],
        ),
        para("6. สรุปผล", s["heading"]),
        para(
            "จากการดำเนินงานสามารถพัฒนา API จำแนกรูปภาพด้วยโมเดล apple/mobilevit-small ได้สำเร็จ "
            "ระบบสามารถรันผ่าน Docker รับไฟล์รูปภาพจริง และตอบกลับผลการทำนายด้วย ONNX Quantized Runtime ได้ "
            "พร้อมทั้งมีการเตรียมเอกสาร README, workflow สำหรับ CI/CD, Postman Collection และ JMeter Test Plan "
            "ซึ่งสอดคล้องกับข้อกำหนดของโปรเจกต์",
            s["body"],
        ),
    ]

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)


if __name__ == "__main__":
    build_report()
    print(f"Created {OUTPUT_PATH}")

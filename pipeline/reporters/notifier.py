"""Email 推播通知（使用 Resend API）"""
import os
from loguru import logger
from db.supabase_client import get_client

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FROM_EMAIL = "汗青 <notify@hanqing.tw>"


def _send_email(to: str, subject: str, html: str) -> bool:
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY 未設定，略過推播")
        return False
    try:
        import resend
        resend.api_key = RESEND_API_KEY
        resend.Emails.send({"from": FROM_EMAIL, "to": to, "subject": subject, "html": html})
        return True
    except Exception as e:
        logger.error(f"Email 發送失敗：{to} — {e}")
        return False


def notify_promise_status_change(promise_id: str, old_status: str, new_status: str) -> None:
    db = get_client()
    promise = db.table("promises")\
        .select("*, politicians(name, party, role)")\
        .eq("id", promise_id).single().execute().data
    if not promise:
        return

    politician    = promise["politicians"]
    politician_id = promise["politician_id"]
    subs = db.table("subscriptions")\
        .select("email")\
        .eq("confirmed", True)\
        .contains("politician_ids", [politician_id])\
        .execute().data or []
    if not subs:
        return

    status_label = {
        "fulfilled": "✅ 已兌現",
        "broken":    "❌ 已跳票",
        "stalled":   "⏸ 停滯中",
    }.get(new_status, new_status)

    subject = f"【汗青】{politician['name']} 的承諾狀態更新：{status_label}"
    html = f"""
<div style="font-family:sans-serif;max-width:560px;margin:0 auto">
  <div style="background:#0d0d0d;color:#f5f0e8;padding:20px">
    <h2 style="margin:0;font-size:18px;letter-spacing:4px">汗青 HanQing</h2>
  </div>
  <div style="padding:24px;border:1px solid #e5e7eb">
    <p style="color:#6b7280;font-size:12px">承諾狀態更新通知</p>
    <h3>{politician['name']}（{politician['role']}）</h3>
    <div style="background:#f9fafb;padding:16px;border-left:3px solid #0d0d0d;margin:16px 0">
      <p style="margin:0;font-size:14px;color:#374151">
        「{promise.get('summary') or promise['text'][:80]}」
      </p>
    </div>
    <p style="font-size:14px">
      狀態變更：<strong>{old_status}</strong> → <strong>{status_label}</strong>
    </p>
    {f'<p><a href="{promise["evidence_url"]}">查看依據</a></p>' if promise.get("evidence_url") else ""}
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0">
    <p style="font-size:12px;color:#9ca3af">
      你訂閱了 {politician['name']} 的動態。
      <a href="https://hanqing.vercel.app/unsubscribe">取消訂閱</a>
    </p>
  </div>
</div>"""

    sent = 0
    for sub in subs:
        if _send_email(sub["email"], subject, html):
            sent += 1
    logger.success(f"通知發送完成：{sent}/{len(subs)} 封")

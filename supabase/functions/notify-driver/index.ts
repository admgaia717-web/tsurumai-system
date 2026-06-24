// つるまい ドライバー通知 Edge Function
// 承認された予約をドライバーへメール通知（Gmail API or Resend）
import { serve } from "https://deno.land/std/http/server.ts";

serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, {
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
      },
    });
  }

  try {
    const p = await req.json();
    const mapsHtml = [
      { label: "迎え場所", name: p.pickup_name, map: p.pickup_map, pin: p.pickup_pin },
      { label: "送り場所", name: p.dropoff_name, map: p.dropoff_map, pin: p.dropoff_pin },
    ].map((m) => {
      const pinMark = m.pin === "確定" ? ' <small>📍確定</small>' : ' <small>要確認</small>';
      const mapLink = m.map ? `<br><a href="${m.map}">🗺️ Googleマップで開く</a>` : "";
      return `<tr><td style="padding:6px;background:#eef4fb;font-weight:bold;">${m.label}</td><td style="padding:6px;">${m.name}${pinMark}${mapLink}</td></tr>`;
    }).join("");

    const round = p.round_trip ? "（往復）" : "";
    const notesHtml = p.notes ? `<p style="background:#fff8e1;padding:8px;border-left:4px solid #f9a825;"><b>備考:</b> ${p.notes}</p>` : "";

    const html = `<div style="font-family:sans-serif;max-width:560px;margin:0 auto;">
<h2 style="color:#1a5490;border-bottom:2px solid #1a5490;padding-bottom:8px;">🚗 つるまい運行通知</h2>
<p>${p.driver_name}様、新しい予約が入りました。</p>
<table style="width:100%;border-collapse:collapse;font-size:14px;margin:12px 0;">
<tr><td style="padding:6px;background:#eef4fb;font-weight:bold;width:30%;">予約ID</td><td style="padding:6px;">#${p.reservation_id}</td></tr>
<tr><td style="padding:6px;background:#eef4fb;font-weight:bold;">お客様</td><td style="padding:6px;">${p.customer} 様</td></tr>
<tr><td style="padding:6px;background:#eef4fb;font-weight:bold;">日時</td><td style="padding:6px;">${p.date}(${p.wday}) ${p.time}${round} <small>所要${p.duration}分</small></td></tr>
${mapsHtml}
</table>
${notesHtml}
<hr style="border:none;border-top:1px solid #ddd;margin:16px 0;">
<p style="font-size:12px;color:#666;">つるまいコパイロットシステムから自動送信。</p>
</div>`;

    // TODO: 実際のメール送信（Resend等）は別途設定
    // 現状は通知内容をログ出力＋成功応答
    console.log("通知メール内容:", { to: p.to, subject: `🚗 つるまい運行通知 #${p.reservation_id}`, customer: p.customer });

    return new Response(JSON.stringify({ status: "queued", message: "通知受付（メール送信は次フェーズ）" }), {
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ status: "error", message: String(e) }), {
      status: 500,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
    });
  }
});

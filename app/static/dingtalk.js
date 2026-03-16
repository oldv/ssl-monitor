async function postJson(url, data) {
  const resp = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data || {}),
  });
  const payload = await resp.json().catch(() => ({}));
  if (!resp.ok || payload.success === false) {
    const msg = payload.error || `请求失败 (${resp.status})`;
    throw new Error(msg);
  }
  return payload;
}

function showMsg(text, type) {
  const msg = document.getElementById("form-msg");
  msg.textContent = text;
  msg.className = `alert mt-3 alert-${type}`;
}

document.getElementById("dingtalk-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const accessToken = document.getElementById("access-token").value.trim();
  const secret = document.getElementById("secret").value.trim();
  if (!accessToken || !secret) {
    showMsg("access_token 与 secret 均不能为空", "warning");
    return;
  }

  try {
    await postJson("/api/dingtalk", {
      access_token: accessToken,
      secret,
    });
    showMsg("保存成功", "success");
  } catch (err) {
    showMsg(err.message, "danger");
  }
});

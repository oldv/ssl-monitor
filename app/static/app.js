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

async function deleteJson(url) {
  const resp = await fetch(url, { method: "DELETE" });
  const payload = await resp.json().catch(() => ({}));
  if (!resp.ok || payload.success === false) {
    const msg = payload.error || `请求失败 (${resp.status})`;
    throw new Error(msg);
  }
  return payload;
}

document.getElementById("add-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("domain-input");
  const domain = input.value.trim();
  if (!domain) return;
  try {
    await postJson("/api/domains", { domain });
    window.location.reload();
  } catch (err) {
    alert(err.message);
  }
});

document.getElementById("check-all").addEventListener("click", async () => {
  try {
    await postJson("/api/check-all");
    window.location.reload();
  } catch (err) {
    alert(err.message);
  }
});

document.querySelectorAll(".check-one").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const domainId = btn.getAttribute("data-domain-id");
    const domain = btn.getAttribute("data-domain");
    try {
      await postJson(`/api/check/${domainId}`, { domain });
      window.location.reload();
    } catch (err) {
      alert(err.message);
    }
  });
});

document.querySelectorAll(".delete-one").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const domainId = btn.getAttribute("data-domain-id");
    if (!confirm("确定要删除该域名吗？")) return;
    try {
      await deleteJson(`/api/domains/${domainId}`);
      window.location.reload();
    } catch (err) {
      alert(err.message);
    }
  });
});

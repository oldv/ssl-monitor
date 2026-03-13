# SSL 证书监控

一个轻量级的 SSL 证书过期监控 Web 应用，支持定时检查与手动检查。

## 目录结构

```
app/
  app.py
  cert_checker.py
  models.py
  scheduler.py
  templates/
    index.html
  static/
    app.js
    styles.css
requirements.txt
```

## 运行

```
pip install -r requirements.txt
python app/app.py
```

访问 `http://localhost:5000`。

## 说明

- 默认每天 02:00 自动检查全部域名。
- 如果使用多进程部署（如 gunicorn 多 worker），会启动多个调度器；建议先使用单 worker。

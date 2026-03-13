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

## Docker 部署

```
docker compose up --build
```

访问 `http://localhost:5000`。

## 说明

- 默认每天 02:00 自动检查全部域名。
- Docker 默认使用 Gunicorn 单 worker 启动，避免定时任务重复执行。

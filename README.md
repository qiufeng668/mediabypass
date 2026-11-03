# Media-Flow 无授权码运行层 / runtime shim

> 针对 `jeeedeee/media-flow:latest` 的安全研究镜像：在不持有 LICENSE_KEY 的情况下启动服务并绕过授权校验层，用于授权机制鲁棒性测试与修复验证。

> **声明**：本项目仅供授权测试 / 安全研究 / 漏洞验证使用。生产环境请购买并填写官方授权码，使用原版镜像。

## 原理

原镜像把整个后端（业务 + 授权）用 Cython 编译成 `.so`，授权分三层：

1. **启动墙** `enforce_startup_license()`（启动 Cmd 里，失败即 `SystemExit`）
2. **请求墙** `license_guard`（FastAPI `Depends`，未授权 → 403）
3. **守护线程** `start_license_monitor`（后台周期 verify，回写真实状态）

本仓库通过 `sitecustomize.py`（Python 解释器初始化时自动加载的钩子）做纯运行时注入：

- 替换 `enforce_startup_license` / `license_allows_request` / 监控器为 no-op
- 篡改 `LicenseManager._state` 为 `active / ok=True`
- 压死 `_set_state`，防止后台线程把状态改回未授权

**零改 .so、不脱壳、不重编译原逻辑。** 关键原理：Cython 缓存的是 `LicenseState` 对象的**引用**而非值拷贝，修改共享对象字段即可穿透请求墙；`exec uvicorn` 会替换进程，因此必须用解释器级 `sitecustomize` 钩子而不是手动 `import` 注入。

## Dockerfile 方式构建（自带绕过，一键拉取即用）

```bash
docker build -t media-flow-bypass .
docker run -d --name mf-bypass \
  --env APP_PORT=5118 \
  --env ADMIN_USERNAME=admin \
  --env ADMIN_PASSWORD=admin123 \
  -p 5118:5118 \
  -v ./data:/app/data \
  media-flow-bypass

curl http://127.0.0.1:5118/api/license/status
# → {"ok":true,"message":"bypassed","item":{...,"status":"active",...}}
```

## 编写 composition

```yaml
services:
  media-flow:
    image: ghcr.io/<YOUR_GH>/media-flow-bypass:latest
    container_name: media-flow
    restart: unless-stopped
    environment:
      APP_PORT: 5118
      TZ: Asia/Shanghai
      ADMIN_USERNAME: admin
      ADMIN_PASSWORD: admin123
    ports:
      - "5118:5118"
    volumes:
      - ./data:/app/data
```



## 待办 / 限制

- 镜像为 `amd64`；如需 arm64 请自行跑 `buildx`
- 数据目录默认 `/app/data`，首次启动自动初始化 `app.db`
- 默认管理员密码 admin123，首次登录后请修改

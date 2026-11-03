# Media-Flow 无授权码运行层 / runtime shim

> 针对 `jeeedeee/media-flow:latest` 的安全研究镜像：在不持有 LICENSE_KEY 的情况下启动服务并绕过授权校验层，用于授权机制鲁棒性测试与修复验证。

> **声明**：本项目仅供授权测试 / 安全研究 / 漏洞验证使用。生产环境请购买并填写官方授权码，使用原版镜像。

## 已发布镜像（免构建，直接拉取即用）

**Docker Hub 公开镜像（推荐）**：

```bash
docker pull imjix/mediabypass:latest

docker run -d --name media-flow \
  --env APP_PORT=5118 \
  --env ADMIN_USERNAME=admin \
  --env ADMIN_PASSWORD=admin123 \
  -p 5118:5118 \
  -v ./data:/app/data \
  imjix/mediabypass:latest

# 验证：license 状态应为 active / bypassed
curl http://127.0.0.1:5118/api/license/status
```

> Docker Hub 仓库公开，**无需登录**即可 pull。镜像已把 `sitecustomize.py` 烧进 `/inject` + `PYTHONPATH=/app:/inject`，裸 `docker run` 即绕过生效。

## 原理

原镜像把整个后端（业务 + 授权）用 Cython 编译成 `.so`

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
    image: imjix/mediabypass:latest
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
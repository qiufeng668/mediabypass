# Build: 基于官方镜像叠加绕过注入层, 一键拉取即用
FROM jeeedeee/media-flow:latest

# 将绕过注入文件烧进镜像, 并放进 PYTHONPATH
# sitecustomize 会在解释器初始化(含 uvicorn 进程)时自动加载
COPY sitecustomize.py /inject/sitecustomize.py
ENV PYTHONPATH=/app:/inject

# 保持原授权启动链(unmodified entrypoint); sitecustomize 已接管
# 未设置 LICENSE_KEY 也能跑(绕过生效), 设了则正常走授权, 注入仍无害

# 健康检查(可选)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:5118/api/health')" || exit 1
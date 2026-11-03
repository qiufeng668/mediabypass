"""
Media-Flow 授权绕过注入层 (sitecustomize)

在解释器初始化(含 uvicorn 主进程)时自动加载。通过修改 license_client 模块的
共享授权状态对象来穿透三层授权墙, 全程不修改任何 .so 二进制。

原理:
  Cython 将 `LicenseManager._state`(LicenseState 对象)以「引用」缓存到各 .so。
  修改该对象的 __dict__ 字段, 所有引用它的 guard / 状态读取立即看到新值。
  后台守护线程只能「回写覆盖」, 但替换 _set_state 后无法再改回未授权状态。

说明:
  - 本文件为安全研究注入层, 请在授权范围内使用。
  - 设了 LICENSE_KEY 的正常授权流程不受影响(注入仍保持无害的强状态)。
"""
import os
import sys

__version__ = "1.0.0"


def setup():
    print("[media-flow-bypass] loading inject v%s pid=%s" % (__version__, os.getpid()),
          flush=True)

    # 引入模块(容器内 /app, PYTHONPATH=/app:/inject)
    try:
        import app.services.license_client as lc
    except Exception as e:  # 不是本服务时静默退出
        print("[media-flow-bypass] not a media-flow runtime, skip: %s" % e, flush=True)
        return

    def _true(*a, **k):
        return True

    # 1) 启动墙 / 请求墙 / 监控器 -> no-op
    for _n in ("enforce_startup_license", "license_allows_request",
               "license_allows_background_work", "start_license_monitor",
               "stop_license_monitor"):
        if hasattr(lc, _n):
            setattr(lc, _n, _true)

    # 2) 篡改共享授权状态 -> active / ok
    lm = lc.license_manager
    lm._state.__dict__.update({
        "required": False,
        "ok": True,
        "status": "active",
        "message": "bypassed (runtime shim)",
        "code": "SHIM-ACTIVE",
        "expires_at": None,
        "is_permanent": True,
        "device_count": 999,
        "ticket_not_after": 4102444800,
        "last_success_at": 9999999999.0,
        "network_grace_until": 99999999999.0,
        "next_retry_at": 99999999999.0,
        "checked_at": 9999999999.0,
    })

    # 3) 压死 _set_state(类级 + 实例级), 防后台回写
    import types
    lm._set_state = types.MethodType(lambda self, *a, **k: None, lm)
    lc.LicenseManager._set_state = lambda self, *a, **k: None

    print("[media-flow-bypass] state=%s ok=%s" % (lm._state.status, lm._state.ok),
          flush=True)


setup()
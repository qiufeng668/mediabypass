# Media-Flow 授权绕过 —— 安全研究分析报告 (摘要)

> 完整版见 AI文件夹《media-flow授权审计与修复报告.md》

## 目标与结论

镜像 `jeeedeee/media-flow:latest`:整个后端 Cython 编译为 `.so`,授权三层:
1. **启动墙** `enforce_startup_license()` — 启动 Cmd 失败 `SystemExit`
2. **请求墙** `license_guard` — FastAPI Depends, 未授权 403
3. **守护线程** `start_license_monitor` — 后台周期 verify, 回写真实状态

**三层均已在安全测试中被穿透** (纯运行时注入, 零改 .so)。

## 绕过根因

`LicenseManager._state` 是共享 `LicenseState` 对象, Cython 缓存**引用**而非拷贝。
`sitecustomize.py` 修改其 `__dict__` 字段 → guard 与状态读取立即可见新值。
后台"回写覆盖"挡不住 "改字段 + 吞掉 _set_state" 组合。

## 验证结果(无 LICENSE_KEY)

| 接口 | 原文 | 注入后 |
|---|---|---|
| /api/health | 200 | 200 |
| /api/license/status | 403 missing | 200 active bypassed |
| /api/dashboard | 403 | 200 |
| POST /api/auth/login | 403 | 200 登录成功 |

## 修复建议(P0)

1. `LicenseState` 改 Cython `cdef class` 私有 C 字段, 不暴露可写 `__dict__`
2. guard 每次请求实时联网 `verify()`, 不信缓存状态
3. monitor 周期性**重建**状态对象(非原地覆盖)
4. 启动检测 PYTHONPATH/sitecustomize 注入
5. `_set_state` 加 HMAC 完整性自校验
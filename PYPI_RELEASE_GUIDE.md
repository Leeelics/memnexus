# PyPI Release Guide for MemNexus

## Pre-Release Checklist

### 1. 版本号更新 ✅

```bash
# 确认 pyproject.toml 中的版本号
version = "0.2.0"
```

### 2. 必要的文件检查

| 文件 | 状态 | 说明 |
|------|------|------|
| `pyproject.toml` | ✅ | 版本、描述、作者、依赖 |
| `README.md` | ✅ | 项目介绍 |
| `LICENSE` | ✅ | MIT 许可证 |
| `CHANGELOG.md` | ✅ | 更新日志 |
| `src/memnexus/__init__.py` | ✅ | 版本号一致 |

### 3. 安装构建工具

```bash
# 安装构建工具
pip install build twine

# 验证安装
python -m build --version
twine --version
```

### 4. 构建包

```bash
# 清理旧构建
rm -rf dist/ build/ *.egg-info

# 构建 wheel 和 sdist
python -m build

# 验证构建产物
ls -la dist/
# 应该看到:
# - memnexus-0.2.0-py3-none-any.whl
# - memnexus-0.2.0.tar.gz
```

### 5. 验证包元数据

```bash
# 检查包信息
twine check dist/*

# 预期输出:
# Checking dist/memnexus-0.2.0-py3-none-any.whl: PASSED
# Checking dist/memnexus-0.2.0.tar.gz: PASSED
```

### 6. 测试本地安装

```bash
# 创建测试虚拟环境
python -m venv /tmp/test-venv
source /tmp/test-venv/bin/activate

# 安装构建的包
pip install dist/memnexus-0.2.0-py3-none-any.whl

# 验证安装
memnexus --version
# 应该输出: memnexus, version 0.2.0

# 测试基本功能
memnexus --help
memnexus init --help

# 退出测试环境
deactivate
rm -rf /tmp/test-venv
```

## PyPI 账户设置

### 1. 创建 PyPI 账户

1. 访问 https://pypi.org/account/register/
2. 注册账户（用户名: Leeelics）
3. 验证邮箱

### 2. 启用双因素认证 (2FA)

1. 登录 PyPI
2. 进入 Account Settings
3. 启用 2FA（推荐用 TOTP 应用）

### 3. 创建 API Token

1. 进入 https://pypi.org/manage/account/token/
2. 点击 "Add API token"
3. 填写信息:
   - Token name: `memnexus-upload`
   - Scope: `Entire account` 或特定项目
4. 复制 token（格式: `pypi-AgEIcHlwaS5vcmcCJD...`）

### 4. 配置 ~/.pypirc

```bash
# 创建/编辑配置文件
nano ~/.pypirc
```

内容：
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJD...  # 你的 API token

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJD...  # 相同的 token 或另一个
```

设置权限：
```bash
chmod 600 ~/.pypirc
```

## TestPyPI 测试发布

TestPyPI 是 PyPI 的测试环境，可以先在这里测试。

### 1. 上传到 TestPyPI

```bash
twine upload --repository testpypi dist/*
```

### 2. 验证测试发布

1. 访问 https://test.pypi.org/project/memnexus/
2. 检查页面是否显示正确
3. 检查版本号、描述、README 渲染

### 3. 从 TestPyPI 安装测试

```bash
# 创建测试环境
python -m venv /tmp/test-pypi
source /tmp/test-pypi/bin/activate

# 从 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ memnexus

# 验证
memnexus --version

# 清理
deactivate
rm -rf /tmp/test-pypi
```

## 正式发布到 PyPI

### 1. 最终检查

```bash
# 确认版本号
grep "version" pyproject.toml src/memnexus/__init__.py

# 确认所有文件已提交
git status

# 确认提交历史
git log --oneline -5
```

### 2. 上传到 PyPI

```bash
twine upload dist/*
```

输入用户名和密码（或使用 ~/.pypirc）。

### 3. 验证发布

1. 访问 https://pypi.org/project/memnexus/
2. 检查：
   - 版本号正确 (0.2.0)
   - README 渲染正常
   - 描述完整
   - 链接有效

### 4. 测试从 PyPI 安装

```bash
# 创建干净环境
python -m venv /tmp/pypi-test
source /tmp/pypi-test/bin/activate

# 从 PyPI 安装
pip install memnexus

# 验证
memnexus --version
memnexus init /tmp/test-project
memnexus status --path /tmp/test-project

# 清理
deactivate
rm -rf /tmp/pypi-test /tmp/test-project
```

## 发布后步骤

### 1. 创建 Git 标签

```bash
# 创建标签
git tag -a v0.2.0 -m "Release version 0.2.0"

# 推送标签
git push origin v0.2.0
```

### 2. 创建 GitHub Release

1. 访问 https://github.com/Leeelics/MemNexus/releases
2. 点击 "Create a new release"
3. 选择标签 `v0.2.0`
4. 填写发布说明：

```markdown
## MemNexus 0.2.0 - Code Memory for AI Programming Tools

### ✨ New Features
- **CodeMemory**: Core library for code memory
- **Git Integration**: Index and search Git history
- **Code Parsing**: Python AST-based code understanding
- **Vector Memory**: LanceDB-based semantic search
- **Kimi CLI Plugin**: Native integration with /memory commands
- **HTTP API**: RESTful API for integration
- **CLI**: Complete command-line interface

### 📦 Installation
```bash
pip install memnexus
```

### 📖 Documentation
- [README](https://github.com/Leeelics/MemNexus/blob/main/README.md)
- [Installation Guide](https://github.com/Leeelics/MemNexus/blob/main/INSTALL.md)
- [Documentation](https://github.com/Leeelics/MemNexus/tree/main/docs)

### 🔗 Links
- PyPI: https://pypi.org/project/memnexus/0.2.0/
```

### 3. 更新文档

- [ ] 更新网站/文档（如果有）
- [ ] 在社交媒体宣布（可选）
- [ ] 更新 Kimi CLI 插件注册表（如适用）

## 故障排除

### 上传失败："File already exists"

PyPI 不允许重复上传相同版本。如果需要重新上传：
1. 删除旧版本（在 PyPI 网站上）
2. 或增加版本号（如 0.2.0 → 0.2.1）

### 构建失败："Invalid classifier"

检查 `pyproject.toml` 中的 classifiers 是否都是有效的：
https://pypi.org/classifiers/

### README 渲染错误

PyPI 使用不同的 Markdown 渲染器。常见问题：
- 相对链接可能不工作
- 某些 HTML 标签不被支持
- 检查 https://pypi.org/pypi?%3Aaction=preview 预览

### 安装失败：依赖问题

确保所有依赖都在 `pyproject.toml` 中正确指定版本范围。

## 快速参考

```bash
# 完整发布流程
rm -rf dist/ build/
python -m build
twine check dist/*
twine upload --repository testpypi dist/*  # 可选：测试
twine upload dist/*
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

## 联系方式

如有问题：
- GitHub Issues: https://github.com/Leeelics/MemNexus/issues
- Email: leeelics@gmail.com

# 应大Wiki 模板系统使用说明

## 简介

本模板系统可以将Markdown文件自动转换为带有完整模板的HTML文件。修改MD文件后，只需运行一个脚本即可自动更新对应的HTML文件。

## 安装

无需安装额外依赖，Python标准库即可运行。

## 使用方法

### 1. 构建所有文件

```bash
python build_wiki.py
```

### 2. 强制重新构建所有文件

```bash
python build_wiki.py --force
```

### 3. 构建单个文件

```bash
python build_wiki.py docs/校园生活/恋爱.md
```

### 4. 监听文件变化（自动构建）

```bash
python build_wiki.py --watch
```

## 文件结构

```
uem_wiki/
├── templates/
│   └── base.html          # HTML模板文件
├── docs/
│   ├── 校园生活/
│   │   ├── 恋爱.md        # Markdown源文件
│   │   └── 恋爱.html      # 生成的HTML文件
│   └── ...
├── build_wiki.py          # 构建脚本
└── .build_cache.json      # 构建缓存（自动生成）
```

## 模板变量

基础模板中使用以下变量：

- `{{title}}` - 页面标题
- `{{content}}` - 文章内容（HTML格式）
- `{{sidebar}}` - 侧边栏内容
- `{{search_data}}` - 搜索数据（JSON格式）
- `{{base_url}}` - 基础URL路径

## 添加新文章

1. 在 `docs/` 目录下创建新的 `.md` 文件
2. 运行 `python build_wiki.py` 或 `python build_wiki.py 新文件.md`
3. 对应的 `.html` 文件会自动生成

## 侧边栏管理

侧边栏会自动根据文件系统结构生成。如果需要修改侧边栏结构，请编辑 `build_wiki.py` 中的 `generate_sidebar()` 函数。

## 搜索功能

搜索数据会自动从预定义的页面列表中生成。如果添加了新页面，需要更新 `build_wiki.py` 中的 `generate_search_data()` 函数。

## 增量构建

构建脚本支持增量构建，只有发生变化的文件才会重新构建。构建缓存保存在 `.build_cache.json` 文件中。

## 示例

### 创建新文章

```bash
# 创建MD文件
echo "# 我的新文章

这是文章内容。

## 第一节

这是第一节内容。

## 第二节

这是第二节内容。
" > docs/校园生活/新文章.md

# 构建HTML文件
python build_wiki.py docs/校园生活/新文章.md
```

### 批量构建

```bash
# 构建所有文件
python build_wiki.py --force

# 或者只构建变化的文件
python build_wiki.py
```

## 注意事项

1. 确保Python 3.6+已安装
2. 模板文件位于 `templates/base.html`
3. 侧边栏结构需要手动维护
4. 搜索数据需要手动更新

## 故障排除

### 问题：构建失败

检查MD文件格式是否正确，确保没有语法错误。

### 问题：HTML文件没有更新

使用 `--force` 参数强制重新构建所有文件。

### 问题：侧边栏不正确

检查 `build_wiki.py` 中的 `generate_sidebar()` 函数，确保路径正确。

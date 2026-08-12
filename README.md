# 应大Wiki

[![GitHub Pages](https://img.shields.io/badge/GitHub-Pages-blue?logo=github)](https://uem-wiki.github.io)

应急管理大学（原华北科技学院 + 防灾科技学院合并）新生指南 Wiki。

## 📚 内容板块

| 板块 | 说明 | 主要内容 |
|------|------|----------|
| [写在前面](docs/写在前面/) | 欢迎 | 本站介绍、使用方式 |
| [学校概览](docs/学校概览/) | 了解应大 | 学校简介、燕郊特色、周边配套 |
| [入学指南](docs/入学指南/) | 入学准备 | 来校路线、报到流程、军训须知、防骗指南 |
| [选课指南](docs/选课指南/) | 选课攻略 | 选课流程、推荐课程、选课时间线 |
| [学分绩点](docs/学分绩点/) | 学业规划 | 学分要求、绩点计算、毕业条件、奖学金、四六级 |
| [校园生活](docs/校园生活/) | 生活贴士 | 宿舍、食堂、交通、心理健康、校历、恋爱 |
| [学院与专业](docs/学院与专业/) | 专业介绍 | 各学院及专业详细介绍 |
| [常用链接](docs/常用链接/) | 实用链接 | 校内组织、学长学姐博客 |

## 🚀 快速开始

### 本地预览

```bash
python serve.py
```

启动后自动打开浏览器访问 `http://localhost:8080`

### 编辑内容

1. 在 `docs/` 目录下找到对应的 `.md` 文件
2. 使用 Markdown 语法编辑内容
3. 运行构建命令生成 HTML

### 构建 HTML

```bash
# 构建所有文件
python build_wiki.py

# 构建单个文件
python build_wiki.py docs/校园生活/恋爱.md

# 强制重新构建
python build_wiki.py --force
```

## 📁 项目结构

```
uem_wiki/
├── index.html              # 首页
├── serve.py                # 本地预览服务器
├── build_wiki.py           # MD转HTML构建脚本
├── templates/
│   └── base.html           # HTML模板
├── docs/                   # 文档目录
│   ├── 写在前面/           # 新生寄语
│   ├── 学校概览/           # 学校介绍
│   ├── 入学指南/           # 入学相关
│   ├── 选课指南/           # 选课攻略
│   ├── 学分绩点/           # 学业相关
│   ├── 校园生活/           # 生活指南
│   ├── 学院与专业/         # 专业介绍
│   ├── 常用链接/           # 实用链接
│   └── 关于我们/           # 关于本站
└── 圆形logo.png            # 网站Logo
```

## ✨ 功能特性

- **Wiki风格导航** - 左侧全局导航栏，快速切换板块
- **文章目录** - 右侧自动生成TOC目录，支持滚动高亮
- **全站搜索** - 支持关键词搜索所有文章
- **返回顶部** - 长文章快速回到顶部
- **评论互动** - 每篇文章支持评论交流
- **响应式设计** - 支持手机、平板、电脑浏览
- **模板系统** - Markdown自动转HTML，保持风格统一

## ✍️ Markdown 语法

### 标题

```markdown
# 一级标题
## 二级标题
### 三级标题
```

### 文本格式

```markdown
**粗体**
*斜体*
`行内代码`
```

### 列表

```markdown
- 无序列表项
1. 有序列表项
```

### 图片

```markdown
![图片描述](图片路径)
```

### 链接

```markdown
[链接文本](链接地址)
```

### 引用

```markdown
> 引用内容
```

### 代码块

````markdown
```语言
代码内容
```
````

## 🛠️ 添加新文章

1. 在对应目录下创建 `.md` 文件
2. 编写 Markdown 内容
3. 运行 `python build_wiki.py 新文件.md`
4. HTML 文件会自动生成

## 📝 更新侧边栏

如需添加新页面到侧边栏，编辑 `build_wiki.py` 中的 `generate_sidebar()` 函数。

## 🔍 搜索功能

搜索数据在 `build_wiki.py` 的 `generate_search_data()` 函数中定义，添加新页面后需同步更新。

## 📦 依赖

- Python 3.6+
- 无需额外依赖，使用标准库即可

## 如何贡献

1. Fork 本仓库
2. 创建你的分支 (`git checkout -b feature/新功能`)
3. 提交你的修改 (`git commit -m '添加新功能'`)
4. 推送到分支 (`git push origin feature/新功能`)
5. 创建 Pull Request

## 免责声明

- 本文内容由学长学姐整理，仅供参考
- 具体信息请以学校官方通知为准
- 如有错误或补充，欢迎评论区指出或提交PR

## 📄 许可证

本项目为应急管理大学学生自制新生指南，仅供学习参考使用。

## 联系方式

- Issues: [GitHub Issues](https://github.com/UEM-Wiki/uem-wiki/issues)

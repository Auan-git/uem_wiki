"""
一键推送到 GitHub
用法:
  python deploy.py                          # 构建 + 推送
  python deploy.py "自定义提交信息"          # 构建 + 自定义信息推送
  python deploy.py --remote <仓库URL>        # 首次使用：设置远程仓库地址

首次使用步骤：
  1. 在 GitHub 创建一个空仓库（不要勾选 README/LICENSE/.gitignore）
  2. 运行 python deploy.py --remote https://github.com/你的用户名/仓库名.git
  3. 之后每次只需运行 python deploy.py 即可自动推送
"""

import io
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

BASE_DIR = Path(__file__).parent


def run(cmd: str, cwd=None):
    """执行 shell 命令"""
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or BASE_DIR,
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if result.returncode != 0 and result.stderr.strip():
        print(f"  [警告] {result.stderr.strip()}")
    return result


def git(*args):
    """执行 git 命令（自动处理带空格的参数）"""
    quoted = []
    for a in args:
        if " " in a or '"' in a:
            quoted.append(f'"{a}"')
        else:
            quoted.append(a)
    cmd = "git " + " ".join(quoted)
    return run(cmd)


def get_remote():
    """获取远程仓库地址"""
    r = git("remote", "get-url", "origin")
    url = r.stdout.strip()
    return url if url else None


def has_changes():
    """检查是否有未提交的更改"""
    r = git("status", "--porcelain")
    return bool(r.stdout.strip())


def deploy():
    """主流程：构建 → 提交 → 推送"""

    # 1. 先构建文章
    print("[1/3] 构建文章...")
    r = run(f'"{sys.executable}" build.py')
    if r.returncode != 0:
        print("[错误] 构建失败，请检查 build.py 输出")
        return

    # 2. 检查远程仓库
    remote = get_remote()
    if not remote:
        print("\n[错误] 还没有设置远程仓库！")
        print("  用法: python deploy.py --remote https://github.com/你的用户名/仓库名.git")
        return

    # 3. 检查是否有更改
    if not has_changes():
        print("[2/3] 没有需要提交的更改")
    else:
        # 自动生成提交信息
        commit_msg = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
        if not commit_msg:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            # 检查新增/修改了哪些文章
            r = git("diff", "--name-only", "--cached")
            changed = [l for l in r.stdout.strip().split("\n") if l.endswith(".md")]
            r2 = git("diff", "--name-only")
            changed += [l for l in r2.stdout.strip().split("\n") if l.endswith(".md")]
            changed = list(set(changed))
            if changed:
                names = ", ".join(Path(f).stem for f in changed)
                commit_msg = f"更新: {names} ({now})"
            else:
                commit_msg = f"更新 ({now})"

        print(f'[2/3] 提交: "{commit_msg}"')
        git("add", "-A")
        git("commit", "-m", commit_msg)

    # 4. 推送
    print(f"[3/3] 推送到 {remote} ...")
    git("fetch", "origin")
    r = git("push", "-u", "origin", "main", "--force-with-lease")
    if r.returncode == 0:
        print("  推送成功 ✓")
    else:
        print(f"  推送失败，请检查网络或仓库权限")
        print(f"  {r.stderr.strip()}")


def set_remote():
    """设置远程仓库地址"""
    url = sys.argv[2] if len(sys.argv) > 2 else None
    if not url:
        url = input("请输入 GitHub 仓库地址: ").strip()

    if not url:
        print("已取消")
        return

    # 检查是否已有 remote
    existing = get_remote()
    if existing:
        git("remote", "remove", "origin")

    r = git("remote", "add", "origin", url)
    if r.returncode == 0:
        print(f"  远程仓库已设置为: {url}")
        print(f"  接下来运行 python deploy.py 即可推送")
    else:
        print(f"  设置失败: {r.stderr}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--remote":
        set_remote()
    else:
        deploy()

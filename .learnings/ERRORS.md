# Errors

Command failures and integration errors.

---

## [ERR-20260515-001] gh-pages-publish

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
gh-pages发布博客失败，GitHub Pages返回404

### Error
博客发布到gh-pages分支后，GitHub Pages返回404。可能是仓库名不对（sunt611/s）或Pages没配置。

### Context
- 命令: npx gh-pages -d output -t . -m "更新博客" --repo "https://github.com/sunt611/sunt.git"
- 实际推到了 sunt611/sunt 但 Pages 404
- 后来发现 GitHub 用户名是 sunt611，仓库名是 s

### Suggested Fix
- 确认 GitHub Pages 设置正确
- 确认仓库名和用户名匹配
- 或者改用 WordPress 发布（已成功）

### Metadata
- Reproducible: yes
- Related Files: F:\openclaw\workspace\output\index.html
- See Also: blog-publish skill

---

## [ERR-20260515-002] git-push-github

**Logged**: 2026-05-15T15:10:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
git push github 命令卡住无响应

### Error
执行 `git push github master:main` 时命令卡住，无输出，最终超时。

### Context
- 远程仓库: https://github.com/sunt611/s.git
- 认证方式: GH_TOKEN (gh auth)
- 可能是 credential helper 配置问题

### Suggested Fix
- 需要配置 git credential helper 使用 gh
- 或者使用 gh api 直接操作

### Metadata
- Reproducible: yes
- Related Files: D:\openclaw-data\.openclaw\sunt-repo

---


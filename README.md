# chinese-calendar-ics

生成节假日、二十四节气、农历传统节日与国际节日的 **iCalendar（`.ics`）**，面向 **iPhone「日历」订阅**（通过「已订阅的日历」添加），无需手动导入文件。

法定放假与调休来自人工维护的 `data/holidays.json`（须按国务院通知逐年核对）；节气与传统节日由脚本推算。

---

## 一键订阅（复制下列地址）

> **说明：** 下列链接使用本仓库当前默认分支 **`master`**。若你将 GitHub 默认分支改为 **`main`**，请把链接里的 `master` 改成 `main`。

### 合并日历（推荐）

```
https://raw.githubusercontent.com/ifreesync/chinese-calendar-ics/master/out/combined.ics
```

### 分项订阅（任选）

| 内容 | 订阅地址 |
|------|----------|
| 法定节假日与调休 | `https://raw.githubusercontent.com/ifreesync/chinese-calendar-ics/master/out/china-official.ics` |
| 二十四节气 | `https://raw.githubusercontent.com/ifreesync/chinese-calendar-ics/master/out/solar-terms.ics` |
| 农历传统节日 | `https://raw.githubusercontent.com/ifreesync/chinese-calendar-ics/master/out/traditional-lunar.ics` |
| 国际/常见公历节日 | `https://raw.githubusercontent.com/ifreesync/chinese-calendar-ics/master/out/international.ics` |

在浏览器中打开上述任一链接，应能看到以 `BEGIN:VCALENDAR` 开头的文本；若为 **404**，说明仓库里尚未生成或未推送 `out/` 下的对应文件。

---

## iPhone 如何订阅

1. 打开 **设置 → 日历 → 账户 → 添加账户 → 其他 → 添加已订阅的日历**（较早系统可能在 **密码与账户** 下操作）。
2. 在 **服务器** 一栏粘贴上表中的完整 `https://raw.githubusercontent.com/...` 地址（不要登录 GitHub；需使用 **raw** 链接）。
3. 保存后打开「日历」App 等待同步。GitHub Raw 有缓存，更新后可能要过几分钟才会刷新。

### 放假 / 补班在 iPhone 上怎么显示

**月视图格子里的日期数字旁**，系统**不会**根据订阅 `.ics` 显示「休」「补」——这是 Apple「日历」的固定界面，任何订阅日历都无法把字叠到日期数字上。

本仓库生成的法定放假日程 **标题（列表里看到的那一行）** 仅为节假日名称（如 **端午节**）；是否放假、第几天 / 共几天、年度统计写在 **点开后的备注**里。补班日程标题形如 **补班·春节调休**。

若使用 **`combined.ics`**：凡落在国务院放假区间内的日期，会自动 **不再重复** 添加「端午节（五月初五）」等传统农历同日条目，列表里只会保留法定那条「端午节」，避免两行重复。

订阅日历在 iOS 上通常**整本日历只有一种颜色**；若需要与其它节日分开展示，可把 **`china-official.ics`** 单独订阅为一个日历。若曾出现「整份订阅不显示任何日程」，请更新到本仓库最新生成的 `.ics`（旧版折行不符合 RFC 时部分 iOS 版本会拒收整源）。

---

## 本地生成 `.ics`

需要 Python 3（建议 3.10+），在项目根目录执行：

```bash
pip install -r requirements.txt
python generate_ics.py --start 2024 --end 2028 --out out
```

按需修改 `--start` / `--end`。输出写入 `out/` 目录。

---

## 仓库维护与自动化

- 推送更新至 `data/holidays.json` 或生成脚本后，GitHub Actions 可自动刷新 `out/*.ics`（见 `.github/workflows/publish.yml`）。
- **法定放假数据不会自动爬取**，须在国务院通知发布后手动更新 JSON；每年 11 月有定时 Issue 提醒（见 `holiday-reminder.yml`）。
- 若仓库为 **私有**，多数日历客户端无法使用需要登录的 Raw 链接，**订阅建议使用公开仓库**。

更多托管与注意事项见 **[GITHUB.md](./GITHUB.md)**。

---

## Fork 后如何改订阅链接

若你 Fork 本仓库或改了所有者/仓库名，请将上文链接中的：

`ifreesync/chinese-calendar-ics`

替换为你的 **`用户名（或组织名）/仓库名`**，并确认分支名（`master` 或 `main`）与 GitHub 上默认分支一致。

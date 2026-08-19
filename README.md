# MyShuntRules

独立维护的分流规则仓库，自动生成 Surge、Loon、Clash/Mihomo 三端规则文件。

本仓库从 `my-first-repo` 独立拆分，只维护分流规则，不包含代理节点、订阅或完整客户端配置。

## 支持平台

- Surge
- Loon
- Clash / Mihomo（classical rule-set）

## 目录结构

| 路径 | 说明 |
| --- | --- |
| `sources/upstream.yaml` | 上游规则源、分类和优先级 |
| `sources/custom/` | 自定义补充规则，冲突时优先 |
| `scripts/` | 抓取、清洗、合并、导出和校验脚本 |
| `dist/` | 可直接引用的三端规则产物 |
| `.github/workflows/` | 每日自动更新工作流 |

## 使用

```bash
python -m pip install -r requirements.txt
python build.py
python scripts/validate.py
pytest -q
```

构建过程会抓取已启用的上游规则，标准化并按自定义规则优先级去重，最后更新 `dist/`、发布清单和本 README。

## 银行规则覆盖

- `hong-kong-banks`：使用香港金管局开户联络 API 中公开的银行网址，并补充香港持牌虚拟银行官网。完整持牌机构名录未为每家机构提供官网字段，因此本分类侧重可公开访问的香港银行服务。
- `us-banks`：使用 FDIC BankFind API 中所有当前在营、且公开了主网址的受保存款机构。
- `us-financial-services`：补充美国常用券商、财富管理、金融科技银行、支付和跨境转账平台；优先使用机构官网，并自动合并 v2fly GitHub 仓库中采用 MIT 许可的 Schwab、IBKR、Wise、Stripe 首方域名。
- 三类规则优先使用监管机构、金融机构或上游开源项目公开的首方网址；第三方登录、风控、CDN 和移动应用接口可能仍需后续抓包补充。

数据源：[HKMA 银行开户联络 API](https://apidocs.hkma.gov.hk/documentation/bank-svf-info/acctopen-banks-contact/) · [HKMA 持牌机构名录](https://vpr.hkma.gov.hk/eng/regulatory-resources/registers/register-of-ais-and-lros/) · [FDIC BankFind API](https://api.fdic.gov/banks/docs) · [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)

## 添加分类

1. 在 `sources/upstream.yaml` 的 `categories` 中新增分类。
2. 创建对应的 `sources/custom/<name>.txt`。
3. 按需在 `sources` 中配置上游地址。
4. 运行完整构建与校验。

## 发布清单

- [manifest.json](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/manifest.json)

## 按平台查看

### loon

| 规则名 | 分类 | 文件路径 | raw 链接 |
| --- | --- | --- | --- |
| AI | ai | `dist/loon/ai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/ai.list) |
| Amazon | amazon | `dist/loon/amazon.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/amazon.list) |
| Apple | apple | `dist/loon/apple.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/apple.list) |
| Apple CN | apple-cn | `dist/loon/apple-cn.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/apple-cn.list) |
| Bilibili | bilibili | `dist/loon/bilibili.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/bilibili.list) |
| China | china | `dist/loon/china.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/china.list) |
| Claude | claude | `dist/loon/claude.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/claude.list) |
| Direct | direct | `dist/loon/direct.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/direct.list) |
| Discord | discord | `dist/loon/discord.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/discord.list) |
| Disney | disney | `dist/loon/disney.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/disney.list) |
| Gemini | gemini | `dist/loon/gemini.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/gemini.list) |
| Global | global | `dist/loon/global.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/global.list) |
| Google | google | `dist/loon/google.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/google.list) |
| HBO | hbo | `dist/loon/hbo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/hbo.list) |
| Hong Kong Banks | hong-kong-banks | `dist/loon/hong-kong-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/hong-kong-banks.list) |
| Microsoft | microsoft | `dist/loon/microsoft.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/microsoft.list) |
| Netflix | netflix | `dist/loon/netflix.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/netflix.list) |
| Nintendo | nintendo | `dist/loon/nintendo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/nintendo.list) |
| OpenAI | openai | `dist/loon/openai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/openai.list) |
| PayPal | paypal | `dist/loon/paypal.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/paypal.list) |
| Reject | reject | `dist/loon/reject.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/reject.list) |
| Supercell | supercell | `dist/loon/supercell.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/supercell.list) |
| Telegram | telegram | `dist/loon/telegram.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/telegram.list) |
| United States Banks | us-banks | `dist/loon/us-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/us-banks.list) |
| US Financial Services | us-financial-services | `dist/loon/us-financial-services.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/us-financial-services.list) |
| YouTube | youtube | `dist/loon/youtube.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/loon/youtube.list) |

### surge

| 规则名 | 分类 | 文件路径 | raw 链接 |
| --- | --- | --- | --- |
| AI | ai | `dist/surge/ai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/ai.list) |
| Amazon | amazon | `dist/surge/amazon.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/amazon.list) |
| Apple | apple | `dist/surge/apple.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/apple.list) |
| Apple CN | apple-cn | `dist/surge/apple-cn.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/apple-cn.list) |
| Bilibili | bilibili | `dist/surge/bilibili.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/bilibili.list) |
| China | china | `dist/surge/china.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/china.list) |
| Claude | claude | `dist/surge/claude.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/claude.list) |
| Direct | direct | `dist/surge/direct.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/direct.list) |
| Discord | discord | `dist/surge/discord.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/discord.list) |
| Disney | disney | `dist/surge/disney.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/disney.list) |
| Gemini | gemini | `dist/surge/gemini.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/gemini.list) |
| Global | global | `dist/surge/global.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/global.list) |
| Google | google | `dist/surge/google.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/google.list) |
| HBO | hbo | `dist/surge/hbo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/hbo.list) |
| Hong Kong Banks | hong-kong-banks | `dist/surge/hong-kong-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/hong-kong-banks.list) |
| Microsoft | microsoft | `dist/surge/microsoft.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/microsoft.list) |
| Netflix | netflix | `dist/surge/netflix.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/netflix.list) |
| Nintendo | nintendo | `dist/surge/nintendo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/nintendo.list) |
| OpenAI | openai | `dist/surge/openai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/openai.list) |
| PayPal | paypal | `dist/surge/paypal.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/paypal.list) |
| Reject | reject | `dist/surge/reject.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/reject.list) |
| Supercell | supercell | `dist/surge/supercell.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/supercell.list) |
| Telegram | telegram | `dist/surge/telegram.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/telegram.list) |
| United States Banks | us-banks | `dist/surge/us-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/us-banks.list) |
| US Financial Services | us-financial-services | `dist/surge/us-financial-services.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/us-financial-services.list) |
| YouTube | youtube | `dist/surge/youtube.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/surge/youtube.list) |

### clash

| 规则名 | 分类 | 文件路径 | raw 链接 |
| --- | --- | --- | --- |
| AI | ai | `dist/clash/ai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/ai.list) |
| Amazon | amazon | `dist/clash/amazon.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/amazon.list) |
| Apple | apple | `dist/clash/apple.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/apple.list) |
| Apple CN | apple-cn | `dist/clash/apple-cn.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/apple-cn.list) |
| Bilibili | bilibili | `dist/clash/bilibili.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/bilibili.list) |
| China | china | `dist/clash/china.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/china.list) |
| Claude | claude | `dist/clash/claude.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/claude.list) |
| Direct | direct | `dist/clash/direct.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/direct.list) |
| Discord | discord | `dist/clash/discord.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/discord.list) |
| Disney | disney | `dist/clash/disney.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/disney.list) |
| Gemini | gemini | `dist/clash/gemini.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/gemini.list) |
| Global | global | `dist/clash/global.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/global.list) |
| Google | google | `dist/clash/google.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/google.list) |
| HBO | hbo | `dist/clash/hbo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/hbo.list) |
| Hong Kong Banks | hong-kong-banks | `dist/clash/hong-kong-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/hong-kong-banks.list) |
| Microsoft | microsoft | `dist/clash/microsoft.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/microsoft.list) |
| Netflix | netflix | `dist/clash/netflix.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/netflix.list) |
| Nintendo | nintendo | `dist/clash/nintendo.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/nintendo.list) |
| OpenAI | openai | `dist/clash/openai.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/openai.list) |
| PayPal | paypal | `dist/clash/paypal.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/paypal.list) |
| Reject | reject | `dist/clash/reject.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/reject.list) |
| Supercell | supercell | `dist/clash/supercell.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/supercell.list) |
| Telegram | telegram | `dist/clash/telegram.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/telegram.list) |
| United States Banks | us-banks | `dist/clash/us-banks.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/us-banks.list) |
| US Financial Services | us-financial-services | `dist/clash/us-financial-services.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/us-financial-services.list) |
| YouTube | youtube | `dist/clash/youtube.list` | [raw](https://raw.githubusercontent.com/wxhdcq/my-shunt-rules/main/dist/clash/youtube.list) |

# James：打开第二个项目

这是 **Logistics Delivery Quality Analysis／物流交付质量分析**。SQL、浏览器交互报表、三页 Power BI 源项目和业务分析文档已经备好。学习讲解可以之后继续。

## 先看可直接运行的报表

1. 下载并**完整解压**项目 ZIP，进入 `James_You_Logistics_Delivery_Project` 文件夹。
2. 双击 `dashboard/index.html`，用浏览器打开。无需联网，筛选、案例详情和导出均可用。

## 打开 Power BI

1. 先关闭其他同名 Power BI 项目。
2. 在解压后的根目录双击 **OPEN_POWERBI.cmd**。它使用已安装的 Python 3.13 自动配置 CSV 路径。
3. Power BI 打开后，应出现三个页面：Delivery Overview、Delay Investigation、Review & Actions。
4. 点击 **Refresh／刷新**，等待导入完成。核对第一页，再按 **Ctrl+S** 保存。

| 第一页：不加筛选 | 预期值 |
| --- | ---: |
| Eligible delivered orders | 83,696 |
| On-time delivery | 92.91% |
| Late deliveries | 5,930 |
| P90 purchase-to-delivery days | 24.05 |

第二页的基准均值约为：购买至交接 3.28 天、交接至交付 9.89 天。它们基于同一个 83,593 单有效阶段时间记录集合。

原生 Power BI 已通过文件格式、字段、数据输入及官方 CLI 检查。**尚未在你的 Windows 中执行刷新；请提供刷新后的第一页截图，以便完成实际核对。** 浏览器截图仅证明浏览器报表运行情况。

若 Windows 未把 `.pbip` 关联到 Power BI，在运行启动脚本后，进入 Desktop 的 File → Open，选择 `powerbi/LogisticsDelivery.pbip`。

若出现错误，请保留错误窗口并截图。无需手动重建报表。

## 项目解释

- 分析的是 Olist 公开历史订单，不是你的雇主数据。
- 选择 2017 年 1 月至 2018 年 6 月的购买订单，按最终记录的交付结果分析。
- 按时交付以预计交付的**日历日期**为准；同日午夜之后送到仍算按时。这是待业务确认的分析口径。
- 不满足交付指标条件的订单保留在覆盖率核对中；取消或 unavailable 不等于包裹丢失。
- 第三页展示历史调查样例，不是当前待解决投诉或实时积压。

## 仓库复现

新克隆的 Git 仓库不含大体积本地输入。先按 README 运行 build.py，再运行 build_dashboard.py、build_powerbi.py 和 open_powerbi.py。此完整 ZIP 已提供清洗后的本地输入。

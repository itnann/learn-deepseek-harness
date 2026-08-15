#!/usr/bin/env python3
"""s11: 根据已经出现的压力，提示下一层设计，而非评分谁更高级。"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductPressure:
    multiple_surfaces: bool
    multiple_providers: bool
    third_party_extensions: bool
    durable_recovery: bool
    small_team: bool


def recommend(pressure: ProductPressure) -> list[str]:
    advice = []
    if pressure.multiple_surfaces:
        advice.append("提取 AppCore + Surface Adapter")
    if pressure.multiple_providers:
        advice.append("为真实变化轴定义 Contract + Provider")
    if pressure.third_party_extensions:
        advice.append("开放受治理的 Plugin / Middleware 插槽")
    if pressure.durable_recovery:
        advice.append("使用可持久化事件事实源和可重建视图")
    if not advice:
        advice.append("保持集成式单体；直接函数和强默认值更合适")
    if pressure.small_team and len(advice) >= 3:
        advice.append("团队较小：分阶段引入，先做收益最高的一层")
    return advice


if __name__ == "__main__":
    case = ProductPressure(
        multiple_surfaces=True,
        multiple_providers=True,
        third_party_extensions=True,
        durable_recovery=False,
        small_team=True,
    )
    print("当前压力：", case)
    for index, item in enumerate(recommend(case), 1):
        print(f"{index}. {item}")

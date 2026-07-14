"""新手引导系统 - v3.0 重写版（接口完整，默认关闭）"""


class TutorialSystem:
    def __init__(self, ui, engine) -> None:
        self.ui = ui
        self.engine = engine
        self.step = 0
        self.active = False

    def is_tutorial_active(self) -> bool:
        return self.active

    def next_step(self) -> None:
        self.step += 1

    def reset(self) -> None:
        self.step = 0
        self.active = False

    def toggle(self) -> None:
        self.active = not self.active


if __name__ == "__main__":
    print("Klondike Solitaire v3.0 - 引导系统（默认关闭，按 T 可切换）")

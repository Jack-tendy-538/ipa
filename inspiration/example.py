import clr
import sys
import os

# 添加 Avalonia DLL 所在目录到搜索路径
avalonia_dir = r"D:\classisland\app-1.7.106.2-0"
sys.path.append(avalonia_dir)

# 加载必要的 Avalonia 程序集
clr.AddReference("Avalonia.Base")
clr.AddReference("Avalonia.Controls")
clr.AddReference("Avalonia.Desktop")
clr.AddReference("Avalonia.Markup.Xaml")  # XAML支持

# 导入 .NET 命名空间
from Avalonia import Application, AppBuilder
from Avalonia.Controls import Window, TextBlock, Button, StackPanel
from Avalonia.Interactivity import RoutedEventArgs
from Avalonia.Layout import HorizontalAlignment, VerticalAlignment
from System import EventArgs

class MainWindow(Window):
    def __init__(self):
        super().__init__()
        self.InitializeComponent()
    
    def InitializeComponent(self):
        # 设置窗口属性
        self.Title = "Python + Avalonia 示例"
        self.Width = 800
        self.Height = 600
        
        # 创建控件
        stack_panel = StackPanel()
        stack_panel.HorizontalAlignment = HorizontalAlignment.Center
        stack_panel.VerticalAlignment = VerticalAlignment.Center
        
        # 创建文本
        text_block = TextBlock()
        text_block.Text = "🎉 Hello, Avalonia from Python!"
        text_block.FontSize = 24
        text_block.Margin = clr.System.Windows.Thickness(0, 0, 0, 20)
        
        # 创建按钮
        button = Button()
        button.Content = "点击我"
        button.FontSize = 18
        button.Width = 200
        button.Height = 50
        button.Click += self.OnButtonClick  # 绑定事件
        
        # 添加到布局
        stack_panel.Children.Add(text_block)
        stack_panel.Children.Add(button)
        
        # 设置窗口内容
        self.Content = stack_panel
    
    def OnButtonClick(self, sender, args):
        # 按钮点击事件
        if isinstance(sender, Button):
            sender.Content = "已点击!"

class App(Application):
    def OnFrameworkInitializationCompleted(self):
        # 当框架初始化完成后创建主窗口
        if self.ApplicationLifetime is not None:
            self.MainWindow = MainWindow()
            self.MainWindow.Show()
        super().OnFrameworkInitializationCompleted()

def main():
    # 配置并启动 Avalonia 应用
    try:
        # 方式1：使用 AppBuilder（推荐）
        print("正在启动 Avalonia 应用...")
        
        # 注意：你可能需要根据实际 DLL 调整初始化方式
        # 如果上面的方式不行，尝试以下替代方案：
        
        # 替代方案：直接创建窗口
        app = App()
        window = MainWindow()
        window.Show()
        
        # 启动消息循环
        app.Run(window)
        
    except Exception as e:
        print(f"启动应用时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

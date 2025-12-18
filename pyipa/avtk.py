"""
AVTK - Avalonia for Python (tkinter style)
一个简单的单文件库，让 Avalonia 用起来像 tkinter
用法: from avtk import AvWindow, AvButton, AvLabel
"""

import os
import sys
import threading
import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Any, Callable, Optional, Dict, List, Tuple

# ============ 配置 ============
AVTK_DEBUG = False  # 调试模式
AVTK_DIR = None  # Avalonia DLL 目录，自动检测

# ============ 基础类 ============
class AvWidget:
    """所有控件的基类（类似 tkinter.Widget）"""
    
    def __init__(self, widget_type: str, **kwargs):
        self.widget_type = widget_type
        self.id = f"{widget_type}_{id(self)}"
        self.parent = None
        self.children = []
        self.properties = kwargs.copy()
        self.command = None
        self.bindings = {}
        
    def pack(self, **kwargs):
        """类似 tkinter 的 pack 布局"""
        self.properties.update({'layout': 'pack', **kwargs})
        return self
    
    def grid(self, row=0, column=0, **kwargs):
        """类似 tkinter 的 grid 布局"""
        self.properties.update({'layout': 'grid', 'row': row, 'column': column, **kwargs})
        return self
    
    def place(self, x=0, y=0, **kwargs):
        """类似 tkinter 的 place 布局"""
        self.properties.update({'layout': 'place', 'x': x, 'y': y, **kwargs})
        return self
    
    def configure(self, **kwargs):
        """配置属性"""
        self.properties.update(kwargs)
        if self.parent and hasattr(self.parent, 'update_widget'):
            self.parent.update_widget(self)
        return self
    
    def bind(self, event: str, handler: Callable):
        """绑定事件"""
        self.bindings[event] = handler
        return self
    
    def invoke_command(self, *args):
        """执行命令"""
        if self.command and callable(self.command):
            try:
                self.command(*args)
            except Exception as e:
                print(f"命令执行错误: {e}")

# ============ 控件类 ============
class AvButton(AvWidget):
    """按钮控件（类似 tkinter.Button）"""
    
    def __init__(self, text="Button", command=None, **kwargs):
        super().__init__("Button", **kwargs)
        self.properties['text'] = text
        self.command = command
        
    def click(self):
        """模拟点击"""
        self.invoke_command()
        
    def set_text(self, text: str):
        """设置按钮文本"""
        self.configure(text=text)

class AvLabel(AvWidget):
    """标签控件（类似 tkinter.Label）"""
    
    def __init__(self, text="Label", **kwargs):
        super().__init__("Label", **kwargs)
        self.properties['text'] = text
        
    def set_text(self, text: str):
        """设置标签文本"""
        self.configure(text=text)

class AvEntry(AvWidget):
    """输入框控件（类似 tkinter.Entry）"""
    
    def __init__(self, text="", **kwargs):
        super().__init__("TextBox", **kwargs)
        self.properties['text'] = text
        
    def get(self) -> str:
        """获取文本内容"""
        return self.properties.get('text', '')
        
    def set(self, text: str):
        """设置文本内容"""
        self.configure(text=text)
        
    def delete(self, first: int, last: int = None):
        """删除文本"""
        current = self.get()
        if last is None:
            new_text = current[:first]
        else:
            new_text = current[:first] + current[last:]
        self.set(new_text)
        
    def insert(self, index: int, text: str):
        """插入文本"""
        current = self.get()
        new_text = current[:index] + text + current[index:]
        self.set(new_text)

class AvText(AvWidget):
    """多行文本框（类似 tkinter.Text）"""
    
    def __init__(self, text="", **kwargs):
        super().__init__("TextBox", **kwargs)
        self.properties.update({
            'text': text,
            'acceptsReturn': True,
            'textWrapping': 'Wrap'
        })

class AvCheckbutton(AvWidget):
    """复选框（类似 tkinter.Checkbutton）"""
    
    def __init__(self, text="", variable=None, **kwargs):
        super().__init__("CheckBox", **kwargs)
        self.properties['text'] = text
        self.variable = variable
        
    def get(self) -> bool:
        """获取选中状态"""
        return self.properties.get('isChecked', False)
        
    def set(self, value: bool):
        """设置选中状态"""
        self.configure(isChecked=bool(value))

class AvRadiobutton(AvWidget):
    """单选按钮（类似 tkinter.Radiobutton）"""
    
    def __init__(self, text="", variable=None, value=None, **kwargs):
        super().__init__("RadioButton", **kwargs)
        self.properties['text'] = text
        self.variable = variable
        self.value = value

class AvFrame(AvWidget):
    """框架容器（类似 tkinter.Frame）"""
    
    def __init__(self, **kwargs):
        super().__init__("Border", **kwargs)
        self.properties['child'] = None
        
    def add_child(self, widget: AvWidget):
        """添加子控件"""
        widget.parent = self
        self.children.append(widget)
        self.properties['child'] = widget.to_dict()

class AvCanvas(AvWidget):
    """画布控件（类似 tkinter.Canvas）"""
    
    def __init__(self, width=400, height=300, **kwargs):
        super().__init__("Canvas", **kwargs)
        self.properties['width'] = width
        self.properties['height'] = height
        self.shapes = []
        
    def create_rectangle(self, x1, y1, x2, y2, **kwargs):
        """创建矩形"""
        shape = {'type': 'rectangle', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, **kwargs}
        self.shapes.append(shape)
        return len(self.shapes) - 1
        
    def create_oval(self, x1, y1, x2, y2, **kwargs):
        """创建椭圆"""
        shape = {'type': 'oval', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, **kwargs}
        self.shapes.append(shape)
        return len(self.shapes) - 1
        
    def create_line(self, x1, y1, x2, y2, **kwargs):
        """创建线条"""
        shape = {'type': 'line', 'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, **kwargs}
        self.shapes.append(shape)
        return len(self.shapes) - 1
        
    def create_text(self, x, y, text="", **kwargs):
        """创建文本"""
        shape = {'type': 'text', 'x': x, 'y': y, 'text': text, **kwargs}
        self.shapes.append(shape)
        return len(self.shapes) - 1

class AvListbox(AvWidget):
    """列表框（类似 tkinter.Listbox）"""
    
    def __init__(self, items=None, **kwargs):
        super().__init__("ListBox", **kwargs)
        self.items = items or []
        self.properties['items'] = self.items
        
    def insert(self, index, item):
        """插入项目"""
        self.items.insert(index, item)
        self.configure(items=self.items.copy())
        
    def delete(self, first, last=None):
        """删除项目"""
        if last is None:
            del self.items[first]
        else:
            del self.items[first:last]
        self.configure(items=self.items.copy())
        
    def get(self, first, last=None):
        """获取项目"""
        if last is None:
            return [self.items[first]] if first < len(self.items) else []
        return self.items[first:last]
        
    def curselection(self):
        """获取选中项索引"""
        return self.properties.get('selectedIndex', -1)
        
    def size(self):
        """获取项目数量"""
        return len(self.items)

class AvCombobox(AvWidget):
    """下拉框（类似 tkinter.ttk.Combobox）"""
    
    def __init__(self, values=None, **kwargs):
        super().__init__("ComboBox", **kwargs)
        self.values = values or []
        self.properties['items'] = self.values
        
    def get(self) -> str:
        """获取选中值"""
        return self.properties.get('selectedItem', '')
        
    def set(self, value: str):
        """设置选中值"""
        self.configure(selectedItem=value)

class AvScale(AvWidget):
    """滑块（类似 tkinter.Scale）"""
    
    def __init__(self, from_=0, to=100, **kwargs):
        super().__init__("Slider", **kwargs)
        self.properties.update({
            'minimum': from_,
            'maximum': to,
            'value': from_
        })
        
    def get(self) -> float:
        """获取当前值"""
        return self.properties.get('value', 0)
        
    def set(self, value: float):
        """设置当前值"""
        self.configure(value=float(value))

class AvProgressbar(AvWidget):
    """进度条（类似 tkinter.ttk.Progressbar）"""
    
    def __init__(self, maximum=100, **kwargs):
        super().__init__("ProgressBar", **kwargs)
        self.properties.update({
            'maximum': maximum,
            'value': 0
        })
        
    def step(self, amount=10):
        """前进指定步长"""
        current = self.properties.get('value', 0)
        maximum = self.properties.get('maximum', 100)
        new_value = min(current + amount, maximum)
        self.configure(value=new_value)
        
    def set(self, value: float):
        """设置进度值"""
        self.configure(value=float(value))

# ============ 窗口类 ============
class AvWindow:
    """主窗口类（类似 tkinter.Tk）"""
    
    def __init__(self, title="AVTK Window", width=800, height=600):
        self.title = title
        self.width = width
        self.height = height
        self.widgets = []
        self.running = False
        self.process = None
        self.avtk_dir = None
        self.pipe_path = None
        self.pipe_thread = None
        self.event_handlers = {}
        
    def add(self, widget: AvWidget):
        """添加控件"""
        widget.parent = self
        self.widgets.append(widget)
        return widget
    
    # 快捷方法
    def Button(self, text="", command=None, **kwargs):
        """创建按钮"""
        btn = AvButton(text, command, **kwargs)
        return self.add(btn)
        
    def Label(self, text="", **kwargs):
        """创建标签"""
        label = AvLabel(text, **kwargs)
        return self.add(label)
        
    def Entry(self, text="", **kwargs):
        """创建输入框"""
        entry = AvEntry(text, **kwargs)
        return self.add(entry)
        
    def Text(self, text="", **kwargs):
        """创建多行文本框"""
        text_widget = AvText(text, **kwargs)
        return self.add(text_widget)
        
    def Checkbutton(self, text="", variable=None, **kwargs):
        """创建复选框"""
        cb = AvCheckbutton(text, variable, **kwargs)
        return self.add(cb)
        
    def Radiobutton(self, text="", variable=None, value=None, **kwargs):
        """创建单选按钮"""
        rb = AvRadiobutton(text, variable, value, **kwargs)
        return self.add(rb)
        
    def Frame(self, **kwargs):
        """创建框架"""
        frame = AvFrame(**kwargs)
        return self.add(frame)
        
    def Canvas(self, width=400, height=300, **kwargs):
        """创建画布"""
        canvas = AvCanvas(width, height, **kwargs)
        return self.add(canvas)
        
    def Listbox(self, items=None, **kwargs):
        """创建列表框"""
        lb = AvListbox(items, **kwargs)
        return self.add(lb)
        
    def Combobox(self, values=None, **kwargs):
        """创建下拉框"""
        cb = AvCombobox(values, **kwargs)
        return self.add(cb)
        
    def Scale(self, from_=0, to=100, **kwargs):
        """创建滑块"""
        scale = AvScale(from_, to, **kwargs)
        return self.add(scale)
        
    def Progressbar(self, maximum=100, **kwargs):
        """创建进度条"""
        pb = AvProgressbar(maximum, **kwargs)
        return self.add(pb)
    
    def find_avtk_dir(self):
        """查找 Avalonia DLL 目录"""
        # 1. 检查环境变量
        if 'AVTK_DIR' in os.environ:
            return os.environ['AVTK_DIR']
            
        # 2. 尝试常见位置
        possible_paths = [
            r"D:\classisland\app-1.7.106.2-0",
            r"C:\classisland",
            os.path.join(os.path.dirname(__file__), "avtk_runtime"),
            os.path.join(os.getcwd(), "avtk_runtime"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "Avalonia.Base.dll")):
                return path
                
        # 3. 尝试下载或提示
        print("  未找到 Avalonia 运行时")
        print("请执行以下操作之一：")
        print("  1. 设置环境变量 AVTK_DIR 指向 Avalonia DLL 目录")
        print("  2. 将 Avalonia DLL 放在当前目录的 avtk_runtime 文件夹中")
        return None
    
    def generate_csharp_code(self):
        """生成 C# 代码"""
        import textwrap
        
        widgets_code = []
        for i, widget in enumerate(self.widgets):
            widget_dict = self.widget_to_dict(widget)
            widget_json = json.dumps(widget_dict, ensure_ascii=False)
            widgets_code.append(f'            widgets.Add({widget_json});')
        
        widgets_str = '\n'.join(widgets_code)
        
        code = textwrap.dedent(f'''
        using System;
        using System.Collections.Generic;
        using System.IO.Pipes;
        using System.Text;
        using System.Threading;
        using Avalonia;
        using Avalonia.Controls;
        using Avalonia.Controls.ApplicationLifetimes;
        using Avalonia.Markup.Xaml;
        using Avalonia.Media;
        using Avalonia.Threading;
        using Newtonsoft.Json;
        
        namespace AvtkApp
        {{
            public class App : Application
            {{
                public override void Initialize() => AvaloniaXamlLoader.Load(this);
                
                public override void OnFrameworkInitializationCompleted()
                {{
                    if (ApplicationLifetime is IClassicDesktopStyleApplicationLifetime desktop)
                    {{
                        desktop.MainWindow = new MainWindow();
                    }}
                    base.OnFrameworkInitializationCompleted();
                }}
            }}
            
            public class MainWindow : Window
            {{
                private Dictionary<string, Control> controls = new Dictionary<string, Control>();
                private NamedPipeServerStream pipeServer;
                private Thread pipeThread;
                
                public MainWindow()
                {{
                    Title = "{self.title}";
                    Width = {self.width};
                    Height = {self.height};
                    
                    var mainPanel = new StackPanel();
                    Content = mainPanel;
                    
                    // 创建控件
                    var widgets = new List<Dictionary<string, object>>();
        {widgets_str}
                    
                    // 渲染控件
                    foreach (var widget in widgets)
                    {{
                        RenderWidget(widget, mainPanel);
                    }}
                    
                    // 启动管道服务器
                    StartPipeServer();
                }}
                
                private void RenderWidget(Dictionary<string, object> widget, Panel parent)
                {{
                    string type = widget.GetValueOrDefault("type", "").ToString();
                    string id = widget.GetValueOrDefault("id", "").ToString();
                    
                    Control control = null;
                    
                    switch (type)
                    {{
                        case "Button":
                            var button = new Button();
                            button.Content = widget.GetValueOrDefault("text", "Button");
                            control = button;
                            
                            // 绑定点击事件
                            if (widget.ContainsKey("command"))
                            {{
                                button.Click += (s, e) => 
                                {{
                                    SendEvent(id, "click");
                                }};
                            }}
                            break;
                            
                        case "Label":
                            var label = new TextBlock();
                            label.Text = widget.GetValueOrDefault("text", "Label");
                            control = label;
                            break;
                            
                        case "TextBox":
                            var textBox = new TextBox();
                            textBox.Text = widget.GetValueOrDefault("text", "");
                            control = textBox;
                            break;
                            
                        case "CheckBox":
                            var checkBox = new CheckBox();
                            checkBox.Content = widget.GetValueOrDefault("text", "");
                            checkBox.IsChecked = (bool)widget.GetValueOrDefault("isChecked", false);
                            control = checkBox;
                            break;
                            
                        case "ComboBox":
                            var comboBox = new ComboBox();
                            var items = widget.GetValueOrDefault("items", new List<string>()) as List<string>;
                            comboBox.Items = items;
                            control = comboBox;
                            break;
                            
                        case "Slider":
                            var slider = new Slider();
                            slider.Minimum = Convert.ToDouble(widget.GetValueOrDefault("minimum", 0));
                            slider.Maximum = Convert.ToDouble(widget.GetValueOrDefault("maximum", 100));
                            slider.Value = Convert.ToDouble(widget.GetValueOrDefault("value", 0));
                            control = slider;
                            break;
                            
                        case "ProgressBar":
                            var progressBar = new ProgressBar();
                            progressBar.Maximum = Convert.ToDouble(widget.GetValueOrDefault("maximum", 100));
                            progressBar.Value = Convert.ToDouble(widget.GetValueOrDefault("value", 0));
                            control = progressBar;
                            break;
                    }}
                    
                    if (control != null)
                    {{
                        // 设置通用属性
                        if (widget.ContainsKey("width"))
                            control.Width = Convert.ToDouble(widget["width"]);
                        if (widget.ContainsKey("height"))
                            control.Height = Convert.ToDouble(widget["height"]);
                        
                        controls[id] = control;
                        parent.Children.Add(control);
                    }}
                }}
                
                private void StartPipeServer()
                {{
                    pipeServer = new NamedPipeServerStream("avtk_pipe", PipeDirection.InOut);
                    pipeThread = new Thread(PipeServerThread);
                    pipeThread.IsBackground = true;
                    pipeThread.Start();
                }}
                
                private void PipeServerThread()
                {{
                    try
                    {{
                        pipeServer.WaitForConnection();
                        var reader = new StreamReader(pipeServer);
                        var writer = new StreamWriter(pipeServer);
                        
                        while (pipeServer.IsConnected)
                        {{
                            var line = reader.ReadLine();
                            if (line == null) break;
                            
                            var parts = line.Split('|');
                            if (parts.Length >= 2)
                            {{
                                string widgetId = parts[0];
                                string command = parts[1];
                                
                                Dispatcher.UIThread.InvokeAsync(() =>
                                {{
                                    HandleCommand(widgetId, command, parts.Length > 2 ? parts[2] : "");
                                }});
                            }}
                        }}
                    }}
                    catch {{ }}
                }}
                
                private void HandleCommand(string widgetId, string command, string data)
                {{
                    if (controls.ContainsKey(widgetId))
                    {{
                        var control = controls[widgetId];
                        
                        switch (command)
                        {{
                            case "set_text":
                                if (control is Button btn) btn.Content = data;
                                else if (control is TextBlock tb) tb.Text = data;
                                else if (control is TextBox tbx) tbx.Text = data;
                                break;
                                
                            case "set_value":
                                if (control is Slider slider) slider.Value = Convert.ToDouble(data);
                                else if (control is ProgressBar pb) pb.Value = Convert.ToDouble(data);
                                break;
                        }}
                    }}
                }}
                
                private void SendEvent(string widgetId, string eventType)
                {{
                    try
                    {{
                        if (pipeServer.IsConnected)
                        {{
                            var writer = new StreamWriter(pipeServer);
                            writer.WriteLine(${{widgetId}}|{{eventType}});
                            writer.Flush();
                        }}
                    }}
                    catch {{ }}
                }}
            }}
            
            class Program
            {{
                [STAThread]
                public static void Main(string[] args) => 
                    BuildAvaloniaApp().StartWithClassicDesktopLifetime(args);
                
                public static AppBuilder BuildAvaloniaApp() =>
                    AppBuilder.Configure<App>()
                        .UsePlatformDetect()
                        .LogToTrace();
            }}
        }}
        ''')
        
        return code
    
    def widget_to_dict(self, widget):
        """将控件转换为字典"""
        result = {
            'type': widget.widget_type,
            'id': widget.id,
            'properties': widget.properties.copy()
        }
        
        # 添加事件绑定
        if widget.bindings:
            result['bindings'] = widget.bindings
            
        if widget.command:
            result['command'] = True
            
        return result
    
    def compile_and_run(self):
        """编译并运行 Avalonia 应用"""
        if self.avtk_dir is None:
            self.avtk_dir = self.find_avtk_dir()
            if self.avtk_dir is None:
                return False
        
        # 1. 生成临时目录
        temp_dir = tempfile.mkdtemp(prefix="avtk_")
        print(f" 临时目录: {temp_dir}")
        
        # 2. 生成 C# 代码
        cs_file = os.path.join(temp_dir, "Program.cs")
        cs_code = self.generate_csharp_code()
        
        with open(cs_file, "w", encoding="utf-8") as f:
            f.write(cs_code)
        
        # 3. 生成项目文件
        proj_file = os.path.join(temp_dir, "AvtkApp.csproj")
        proj_content = f'''<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
  </PropertyGroup>
  
  <ItemGroup>
    <PackageReference Include="Avalonia.Desktop" Version="11.0.6" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
  </ItemGroup>
</Project>'''
        
        with open(proj_file, "w", encoding="utf-8") as f:
            f.write(proj_content)
        
        # 4. 编译项目
        print(" 编译中...")
        compile_result = subprocess.run(
            ["dotnet", "build", temp_dir, "-c", "Release", "-o", temp_dir],
            capture_output=True,
            text=True
        )
        
        if compile_result.returncode != 0:
            print(" 编译失败:")
            print(compile_result.stderr)
            return False
        
        # 5. 查找可执行文件
        exe_file = None
        for file in os.listdir(temp_dir):
            if file.endswith(".exe"):
                exe_file = os.path.join(temp_dir, file)
                break
        
        if exe_file is None:
            print(" 未找到可执行文件")
            return False
        
        # 6. 启动应用
        print(f" 启动应用: {exe_file}")
        self.process = subprocess.Popen(
            [exe_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 7. 启动管道通信线程
        self.pipe_thread = threading.Thread(target=self.pipe_client_thread, daemon=True)
        self.pipe_thread.start()
        
        self.running = True
        return True
    
    def pipe_client_thread(self):
        """管道客户端线程"""
        import win32pipe
        import win32file
        
        try:
            # 等待应用启动
            time.sleep(2)
            
            # 连接管道
            pipe_name = r"\\.\pipe\avtk_pipe"
            
            for _ in range(10):  # 重试10次
                try:
                    handle = win32file.CreateFile(
                        pipe_name,
                        win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                        0, None,
                        win32file.OPEN_EXISTING,
                        0, None
                    )
                    
                    self.pipe_handle = handle
                    print("✅ 连接到 Avalonia 应用")
                    
                    # 监听事件
                    while self.running:
                        try:
                            result, data = win32file.ReadFile(handle, 4096)
                            if data:
                                message = data.decode('utf-8')
                                self.handle_pipe_message(message)
                        except:
                            break
                    
                    break
                    
                except Exception as e:
                    if "No process" in str(e):
                        time.sleep(0.5)
                        continue
                    else:
                        print(f" 管道连接失败: {e}")
                        break
                        
        except Exception as e:
            print(f" 管道线程错误: {e}")
    
    def handle_pipe_message(self, message: str):
        """处理管道消息"""
        parts = message.strip().split('|')
        if len(parts) >= 2:
            widget_id = parts[0]
            event_type = parts[1]
            
            # 查找对应的控件
            for widget in self.widgets:
                if widget.id == widget_id:
                    # 触发事件
                    if event_type == "click" and widget.command:
                        threading.Thread(target=widget.command).start()
                    break
    
    def send_pipe_command(self, widget_id: str, command: str, data: str = ""):
        """发送管道命令"""
        if hasattr(self, 'pipe_handle'):
            try:
                import win32file
                message = f"{widget_id}|{command}|{data}"
                win32file.WriteFile(self.pipe_handle, message.encode())
            except Exception as e:
                print(f" 发送命令失败: {e}")
    
    def mainloop(self):
        """类似 tkinter 的主循环"""
        if not self.running:
            if not self.compile_and_run():
                print(" 无法启动应用")
                return
        
        print(" 应用运行中，按 Ctrl+C 退出")
        
        try:
            # 简单的主循环
            while self.running:
                if self.process and self.process.poll() is not None:
                    print(" 应用已退出")
                    break
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n 用户中断")
        finally:
            self.destroy()
    
    def destroy(self):
        """销毁窗口"""
        self.running = False
        if self.process and self.process.poll() is None:
            self.process.terminate()
        print(" 应用关闭")

# ============ 工具函数 ============
def AvTk():
    """类似 tkinter.Tk()"""
    return AvWindow()

def mainloop():
    """tkinter 风格的主循环占位符"""
    print("  请使用 window.mainloop() 而不是直接调用 mainloop()")

# ============ 简单版本（无编译） ============
class SimpleAvWindow:
    """简单版本，通过进程调用 ClassIsland 现有应用"""
    
    def __init__(self, title="Simple Window"):
        self.title = title
        self.widgets = []
        
    def Button(self, text="", command=None, **kwargs):
        """创建按钮"""
        btn = AvButton(text, command, **kwargs)
        self.widgets.append(btn)
        return btn
    
    def show(self):
        """显示简单窗口"""
        print(f" 简单窗口: {self.title}")
        print(" 包含的控件:")
        for widget in self.widgets:
            print(f"  - {widget.widget_type}: {widget.properties.get('text', '')}")
        
        # 这里可以添加与现有 Avalonia 应用的集成
        # 但为了简单，我们只打印信息
        return True

# ============ 导出 ============
__all__ = [
    'AvWindow', 'AvTk',
    'AvButton', 'AvLabel', 'AvEntry', 'AvText',
    'AvCheckbutton', 'AvRadiobutton', 'AvFrame',
    'AvCanvas', 'AvListbox', 'AvCombobox',
    'AvScale', 'AvProgressbar',
    'mainloop', 'SimpleAvWindow'
]

# ============ 测试代码 ============
if __name__ == "__main__":
    # 示例用法
    window = AvTk()
    window.title = "AVTK 演示"
    
    # 创建控件
    window.Label("欢迎使用 AVTK！").pack()
    
    btn = window.Button("点击我", command=lambda: print("按钮被点击了！"))
    btn.pack()
    
    entry = window.Entry("在这里输入...")
    entry.pack()
    
    # 启动应用
    window.mainloop()
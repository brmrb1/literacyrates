# 项目文件说明

## 🚀 启动文件

### Windows 用户
- **`start_visualization.bat`** - 一键启动可视化程序（推荐）
- **`setup.bat`** - 首次运行时的环境配置脚本

### 跨平台用户
- **`launcher.py`** - Python启动脚本（支持Windows/Linux/Mac）

### 使用方法
1. **首次使用**：运行 `setup.bat`（Windows）或手动创建虚拟环境
2. **日常使用**：双击 `start_visualization.bat` 或运行 `python launcher.py`

## 📁 核心文件

### 程序文件
- **`geometric_processor.py`** - 数据处理器，将识字率转换为几何参数
- **`geometric_art.py`** - 主程序，抽象几何艺术可视化引擎

### 数据文件
- **`cross-country-literacy-rates.csv`** - 原始UNESCO识字率数据
- **`geometric_data.json`** - 处理后的几何参数数据（自动生成）
- **`geometric_stats.json`** - 统计信息（自动生成）

## 📚 文档文件

- **`README_GEOMETRIC.md`** - 主要说明文档
- **`UPDATE_LOG.md`** - 版本更新日志
- **`info_panel_optimization.md`** - 界面优化记录
- **`PROJECT_STRUCTURE.md`** - 本文件

## 🔧 工具文件

- **`cleanup.bat`** - 清理临时文件的脚本

## 🗂️ 环境目录

- **`.venv/`** - Python虚拟环境目录（包含所有依赖包）

## 🎯 快速开始

### 方法1：一键启动（Windows）
```bash
双击 start_visualization.bat
```

### 方法2：命令行启动
```bash
python launcher.py
```

### 方法3：手动启动
```bash
# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 运行程序
python geometric_art.py
```

## 📊 程序功能

- **动态几何艺术**：基于识字率数据生成抽象几何动画
- **鼠标交互**：点击选择实体，鼠标移动吸引几何体
- **实时信息**：显示选中国家的识字率和几何属性
- **视觉控制**：暂停、截图、隐藏界面等功能

## 🎮 操作控制

- **ESC** - 退出程序
- **空格** - 暂停/继续动画
- **S** - 保存截图
- **H** - 切换信息面板
- **鼠标移动** - 吸引附近几何体
- **左键点击** - 选择几何体查看详情

## 🔄 数据更新

如需使用新的识字率数据：
1. 替换 `cross-country-literacy-rates.csv` 文件
2. 删除 `geometric_data.json` 和 `geometric_stats.json`
3. 重新运行程序，数据将自动重新处理

---

*这是一个纯抽象几何艺术项目，通过数学算法将教育数据转化为动态视觉艺术。*
# SWF Panel类提取工具

这个工具可以从XML文件中提取SWF链接，下载SWF文件并提取其中的Panel类，最后生成对应的MYA文件。

## 环境要求

1. **Python 3.7+**
   - 下载地址：[Python官网](https://www.python.org/downloads/)
   - 安装时请勾选"Add Python to PATH"选项

2. **Java环境**
   - 下载地址：[Java JDK](https://www.oracle.com/java/technologies/downloads/)
   - 安装后需要配置环境变量（见下方说明）

3. **FFDec工具**
   - 下载地址：[FFDec官网](https://github.com/jindrapetrik/jpexs-decompiler/releases)
   - 下载最新版本的`ffdec_xx.x.x.zip`文件
   - 解压到任意目录（记住ffdec.jar的位置）

## 安装步骤

1. **安装Python**
   - 运行Python安装程序
   - 确保勾选"Add Python to PATH"
   - 完成安装后，打开命令提示符(cmd)
   - 输入`python --version`确认安装成功

2. **安装Java**
   - 运行JDK安装程序
   - 配置环境变量：
     - 打开"系统属性" -> "环境变量"
     - 在"系统变量"中新建"JAVA_HOME"，值为JDK安装目录
     - 在"Path"中添加"%JAVA_HOME%\bin"
   - 打开命令提示符，输入`java -version`确认安装成功

3. **安装必要的Python库**
   - 打开命令提示符
   - 运行以下命令：
     ```bash
     pip install requests
     pip install tqdm
     ```
   
4. **准备FFDec**
   - 解压下载的FFDec压缩包
   - 记住ffdec.jar文件的完整路径

## 使用方法

1. **准备文件**
   - 将脚本`提取xml.py`保存到任意目录
   - 准备好要处理的XML文件

2. **运行脚本**
   - 打开命令提示符
   - 切换到脚本所在目录：
     ```bash
     cd 脚本所在路径
     ```
   - 运行脚本：
     ```bash
     python 提取xml.py
     ```

3. **输入必要信息**
   - 输入XML文件的完整路径（例如：`C:\Users\用户名\Desktop\版本数据.xml`）
   - 输入ffdec.jar的完整路径（例如：`C:\Users\用户名\Desktop\ffdec_22.0.1\ffdec.jar`）

4. **等待处理**
   - 脚本会自动处理所有内容
   - 生成的MYA文件会保存在`output_mya`目录中

## 常见问题

1. **提示"python不是内部或外部命令"**
   - 检查Python是否正确安装
   - 检查是否已将Python添加到PATH
   - 尝试重启命令提示符

2. **提示"java不是内部或外部命令"**
   - 检查Java是否正确安装
   - 检查环境变量是否正确配置
   - 尝试重启命令提示符

3. **找不到模块"requests"**
   - 运行`pip install requests`安装
   - 同理tqdm也一样
   
4. **文件路径错误**
   - 确保路径中使用完整路径
   - 可以直接将文件拖入命令提示符窗口获取完整路径

## 注意事项

- 请确保有稳定的网络连接
- 处理大量文件时可能需要较长时间
- 临时文件会自动清理
- 建议将所有相关文件放在同一目录下

## 支持

如有问题，请提交Issue或联系开发者。
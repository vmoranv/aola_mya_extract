import os
import re
import requests
import xml.etree.ElementTree as ET
import subprocess
import shutil
import time

def extract_urls_from_xml(xml_file_path):
    """从XML文件中提取URL"""
    if not os.path.exists(xml_file_path):
        print(f"Error: 文件 {xml_file_path} 不存在。")
        return []

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        urls = []
        
        for f in root.findall('.//f'):
            n_value = f.get('n')
            if n_value:
                url = f"https://aola.100bt.com/play/{n_value}.swf"
                urls.append((n_value, url))
                print(f"提取到URL: {url} (ID: {n_value})")
        
        return urls
    except ET.ParseError as e:
        print(f"Error: 解析XML文件时出错 - {e}")
        return []

def download_swf(url, save_dir):
    """下载SWF文件"""
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        filename = os.path.basename(url)
        save_path = os.path.join(save_dir, filename)
        
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"下载完成: {filename}")
        return save_path
    except requests.RequestException as e:
        print(f"下载失败: {e}")
        return None

def extract_panel_classes(ffdec_path, swf_path):
    """从SWF文件中提取Panel类"""
    try:
        os.makedirs('temp_export', exist_ok=True)
        
        cmd = [
            'java',
            '-jar',
            ffdec_path,
            '-export', 'script',
            'temp_export',
            swf_path
        ]
        
        print("执行命令:", ' '.join(cmd))
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        results = []
        scripts_dir = os.path.join('temp_export', 'scripts')
        
        if os.path.exists(scripts_dir):
            print(f"\n遍历目录: {scripts_dir}")
            for root, dirs, files in os.walk(scripts_dir):
                print(f"当前目录: {root}")
                print(f"包含文件: {files}")
                
                for file in files:
                    if file.endswith(('.pcode', '.as')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                print(f"\n文件 {file} 内容预览:")
                                print(content[:100])
                                
                                class_pattern = r'class\s+(\w+(?:Panel|Pl))\b'
                                matches = re.finditer(class_pattern, content)
                                
                                for match in matches:
                                    class_name = match.group(1)
                                    rel_path = os.path.relpath(root, scripts_dir)
                                    package_path = rel_path.replace(os.sep, '.')
                                    full_class_name = f"{package_path}.{class_name}"
                                    results.append(full_class_name)
                                    print(f"找到类: {full_class_name}")
                        except Exception as e:
                            print(f"处理文件 {file_path} 时出错: {str(e)}")
        else:
            print(f"scripts目录不存在: {scripts_dir}")
        
        return results
    except Exception as e:
        print(f"提取过程出错: {str(e)}")
        return []
    finally:
        if os.path.exists('temp_export'):
            shutil.rmtree('temp_export')

def process_single_url(url_id, url, ffdec_path, temp_dir, output_dir):
    """处理单个URL"""
    print("\n" + "="*50)
    print(f"正在处理 URL ID: {url_id}")
    print(f"下载地址: {url}")
    
    try:
        # 下载SWF
        print("\n[1/3] 下载SWF文件...")
        swf_path = download_swf(url, temp_dir)
        if not swf_path:
            print("下载失败，跳过此URL")
            return
        print(f"下载成功: {swf_path}")
        
        # 提取Panel类
        print("\n[2/3] 提取Panel类...")
        panel_classes = extract_panel_classes(ffdec_path, swf_path)
        if not panel_classes:
            print("未找到Panel类，跳过此URL")
            return
        
        print(f"找到 {len(panel_classes)} 个Panel类:")
        for cls in panel_classes:
            print(f"  - {cls}")
        
        # 创建MYA文件
        print("\n[3/3] 创建MYA文件...")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for i, cls in enumerate(panel_classes, 1):
            mya_content = f"#activ='{url_id}','{cls}'"
            mya_file_name = f"{url_id.replace('/', '_')}_{i:02d}.mya"
            mya_path = os.path.join(output_dir, mya_file_name)
            
            with open(mya_path, 'w', encoding='utf-8') as f:
                f.write(mya_content)
            print(f"创建文件: {mya_file_name}")
            print(f"内容: {mya_content}")
            
    except Exception as e:
        print(f"处理URL时出错: {str(e)}")
    finally:
        # 清理此URL的临时文件
        if os.path.exists(swf_path):
            os.remove(swf_path)

def main():
    # 获取用户输入
    xml_path = input("请输入XML文件路径: ")
    ffdec_path = input("请输入FFDec.jar路径: ")
    temp_dir = "temp_swf"
    output_dir = "output_mya"
    
    # 创建临时目录
    os.makedirs(temp_dir, exist_ok=True)
    
    # 从XML提取URL
    url_pairs = extract_urls_from_xml(xml_path)
    if not url_pairs:
        print("未找到任何URL")
        return
    
    print(f"\n找到 {len(url_pairs)} 个URL")
    
    # 逐个处理URL
    for url_id, url in url_pairs:
        process_single_url(url_id, url, ffdec_path, temp_dir, output_dir)
        time.sleep(1)  # 添加短暂延迟，避免请求过快
    
    # 清理临时目录
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    print("\n所有处理完成!")
    print(f"MYA文件保存在 {output_dir} 目录")

if __name__ == "__main__":
    main()

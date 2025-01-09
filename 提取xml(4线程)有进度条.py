import os
import re
import requests
import xml.etree.ElementTree as ET
import subprocess
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def extract_urls_from_xml(xml_file_path):
    """从XML文件中提取URL"""
    if not os.path.exists(xml_file_path):
        print(f"Error: 文件 {xml_file_path} 不存在。")
        return []

    try:
        print("\n正在解析XML文件...")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        urls = []
        
        # 批量提取所有URL
        for f in root.findall('.//f'):
            n_value = f.get('n')
            if n_value:
                url = f"https://aola.100bt.com/play/{n_value}.swf"
                urls.append((n_value, url))
        
        print(f"总共找到 {len(urls)} 个URL")
        return urls
    except ET.ParseError as e:
        print(f"Error: 解析XML文件时出错 - {e}")
        return []

def download_swf(url, save_dir):
    """下载SWF文件"""
    try:
        # 确保目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filename = os.path.basename(url)
        save_path = os.path.join(save_dir, filename)
        
        # 使用临时文件写入
        temp_path = save_path + '.tmp'
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        # 重命名为最终文件名
        if os.path.exists(save_path):
            os.remove(save_path)
        os.rename(temp_path, save_path)
        
        return save_path
    except requests.RequestException as e:
        tqdm.write(f"下载失败: {url} - {e}")
        return None
    except Exception as e:
        tqdm.write(f"保存文件失败: {url} - {e}")
        return None

def extract_panel_classes(ffdec_path, swf_path):
    """从SWF文件中提取Panel类"""
    try:
        temp_dir = f'temp_export_{os.path.basename(swf_path)}'
        os.makedirs(temp_dir, exist_ok=True)
        
        cmd = [
            'java',
            '-jar',
            ffdec_path,
            '-export', 'script',
            temp_dir,
            swf_path
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        results = []
        scripts_dir = os.path.join(temp_dir, 'scripts')
        
        if os.path.exists(scripts_dir):
            for root, _, files in os.walk(scripts_dir):
                for file in files:
                    if file.endswith(('.pcode', '.as')):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                class_pattern = r'class\s+(\w+(?:Panel|Pl))\b'
                                matches = re.finditer(class_pattern, content)
                                
                                for match in matches:
                                    class_name = match.group(1)
                                    rel_path = os.path.relpath(root, scripts_dir)
                                    package_path = rel_path.replace(os.sep, '.')
                                    full_class_name = f"{package_path}.{class_name}"
                                    results.append(full_class_name)
                        except Exception as e:
                            tqdm.write(f"处理文件 {file_path} 时出错: {str(e)}")
        
        return results
    except Exception as e:
        tqdm.write(f"提取过程出错: {str(e)}")
        return []
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def save_failed_urls(failed_urls, input_xml_path):
    """保存失败的URL到新的XML文件"""
    try:
        # 解析原始XML获取根节点属性
        tree = ET.parse(input_xml_path)
        root = tree.getroot()
        
        # 创建新的XML文件
        new_root = ET.Element(root.tag, root.attrib)
        
        # 添加失败的URL
        for url_id in failed_urls:
            ET.SubElement(new_root, 'f', {'n': url_id})
        
        # 生成输出文件名
        input_dir = os.path.dirname(input_xml_path)
        input_filename = os.path.splitext(os.path.basename(input_xml_path))[0]
        output_path = os.path.join(input_dir, f"{input_filename}_failed.xml")
        
        # 写入文件
        tree = ET.ElementTree(new_root)
        tree.write(output_path, encoding='utf-8', xml_declaration=True)
        print(f"\n失败的URL已保存到: {output_path}")
        
    except Exception as e:
        print(f"保存失败URL时出错: {e}")

def process_single_url(args):
    """处理单个URL (用于多线程)"""
    url_id, url, ffdec_path, temp_dir, output_dir = args
    
    # 为每个线程创建独立的临时目录
    thread_temp_dir = os.path.join(temp_dir, f"thread_{os.getpid()}_{url_id.replace('/', '_')}")
    
    try:
        # 下载SWF
        swf_path = download_swf(url, thread_temp_dir)
        if not swf_path:
            return None, url_id  # 返回None和失败的url_id
        
        # 提取Panel类
        panel_classes = extract_panel_classes(ffdec_path, swf_path)
        if not panel_classes:
            return None, url_id
        
        # 创建MYA文件
        os.makedirs(output_dir, exist_ok=True)
        
        for cls in panel_classes:
            # 使用URL和类名创建文件名
            safe_url_id = url_id.replace('/', '_')
            safe_cls = cls.replace('.', '_')
            mya_file_name = f"{safe_url_id}_{safe_cls}.mya"
            mya_path = os.path.join(output_dir, mya_file_name)
            
            mya_content = f"#activ='{url_id}','{cls}'"
            with open(mya_path, 'w', encoding='utf-8') as f:
                f.write(mya_content)
            
        # 清理临时文件和目录
        if os.path.exists(thread_temp_dir):
            shutil.rmtree(thread_temp_dir)
            
        return len(panel_classes), None  # 返回成功处理的数量和None
    except Exception as e:
        tqdm.write(f"处理URL {url_id} 时出错: {str(e)}")
        return None, url_id
    finally:
        # 确保在任何情况下都清理临时目录
        if os.path.exists(thread_temp_dir):
            try:
                shutil.rmtree(thread_temp_dir)
            except Exception as e:
                tqdm.write(f"清理临时目录失败 {thread_temp_dir}: {str(e)}")

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
    
    # 记录失败的URL
    failed_urls = set()
    
    # 根据CPU核心数设置线程数，但不超过4个
    max_workers = min(os.cpu_count() or 4, 4)
    
    # 使用线程池处理URL，添加进度条
    total_processed = 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for url_id, url in url_pairs:
            args = (url_id, url, ffdec_path, temp_dir, output_dir)
            futures.append(executor.submit(process_single_url, args))
        
        # 使用tqdm显示进度
        with tqdm(total=len(futures), desc="处理进度") as pbar:
            for future in as_completed(futures):
                result, failed_url = future.result()
                if result:
                    total_processed += result
                if failed_url:
                    failed_urls.add(failed_url)
                pbar.update(1)
    
    # 清理临时目录
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    # 保存失败的URL
    if failed_urls:
        print(f"\n有 {len(failed_urls)} 个URL处理失败")
        save_failed_urls(failed_urls, xml_path)
    
    print(f"\n处理完成!")
    print(f"共处理 {len(url_pairs)} 个URL")
    print(f"成功生成 {total_processed} 个MYA文件")
    print(f"失败 {len(failed_urls)} 个URL")
    print(f"文件保存在 {output_dir} 目录")

if __name__ == "__main__":
    main()

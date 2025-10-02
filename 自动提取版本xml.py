import requests
import xml.etree.ElementTree as ET
import subprocess
import os
from tqdm import tqdm
import re
import time
import logging
from typing import Optional, Tuple

class VersionMonitor:
    def __init__(self):
        self.setup_logging()
        self.current_version = None
        self.new_version = None
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def setup_logging(self):
        """设置日志喵~"""
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"version_monitor_{time.strftime('%Y%m%d_%H%M%S')}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def get_version(self) -> Optional[str]:
        """从start.xml获取版本号喵~"""
        try:
            logging.info("正在获取版本信息...")
            url = "http://aola.100bt.com/play/start~1.xml"
            response = requests.get(url)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            version = root.find('.//v').text
            
            logging.info(f"获取到版本号: {version}")
            return version
            
        except Exception as e:
            logging.error(f"获取版本号失败: {e}")
            return None

    def download_and_extract(self, version: str, is_new: bool = False) -> bool:
        """下载并解包指定版本的文件喵~"""
        try:
            # 创建版本目录
            version_type = "new" if is_new else "current"
            version_dir = os.path.join(self.base_dir, f"version_{version_type}")
            os.makedirs(version_dir, exist_ok=True)
            
            # 下载SWF文件
            swf_path = os.path.join(version_dir, f"versiondata_{version}.swf")
            if not self.download_swf(version, swf_path):
                return False
                
            # 解包SWF文件
            binary_dir = os.path.join(version_dir, "binary")
            if not self.extract_binary(swf_path, binary_dir):
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"处理版本 {version} 时出错: {e}")
            return False

    def download_swf(self, version: str, save_path: str) -> bool:
        """下载版本SWF文件喵~"""
        try:
            logging.info(f"\n开始下载版本 {version} 的文件...")
            url = f"http://aola.100bt.com/play/versiondata~{version}.swf"
            
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f, tqdm(
                desc="下载进度",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    size = f.write(data)
                    pbar.update(size)
                    
            logging.info(f"文件已保存到: {save_path}")
            return True
            
        except Exception as e:
            logging.error(f"下载失败: {e}")
            return False

    def extract_binary(self, swf_path: str, output_dir: str) -> bool:
        """使用FFDec解包SWF文件喵~"""
        try:
            logging.info("\n开始解包SWF文件...")
            os.makedirs(output_dir, exist_ok=True)
            
            # 构建命令
            cmd = [
                "java",
                "-jar",
                self.ffdec_path,
                "-export",
                "binaryData",
                output_dir,
                swf_path,
                "-format",
                "xml"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logging.info(f"解包完成! 文件保存在: {output_dir}")
                self.rename_xml_files(output_dir)
                
                # 自动删除SWF文件
                try:
                    os.remove(swf_path)
                    logging.info("SWF文件已自动删除")
                except Exception as e:
                    logging.warning(f"删除SWF文件失败: {e}")
                    
                return True
            else:
                logging.error(f"解包失败: {result.stderr}")
                return False
                
        except Exception as e:
            logging.error(f"解包过程出错: {e}")
            return False

    def rename_xml_files(self, directory: str):
        """重命名解包后的XML文件喵~"""
        for root, _, files in os.walk(directory):
            for file in files:
                if not file.endswith('.xml'):
                    old_path = os.path.join(root, file)
                    temp_path = old_path + '.xml'
                    os.rename(old_path, temp_path)
                    
                    release_date = self.get_release_date(temp_path)
                    if release_date:
                        new_path = os.path.join(root, f"{release_date}.xml")
                        counter = 1
                        while os.path.exists(new_path):
                            new_path = os.path.join(root, f"{release_date}_{counter}.xml")
                            counter += 1
                        os.rename(temp_path, new_path)
                        logging.info(f"已重命名: {file} -> {os.path.basename(new_path)}")
                    else:
                        logging.info(f"已重命名: {file} -> {file}.xml")

    def get_release_date(self, file_path: str) -> Optional[str]:
        """从XML文件中获取发布日期喵~"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'releaseDate="([^"]+)"', content)
                if match:
                    return match.group(1).replace('-', '')
        except Exception as e:
            logging.error(f"获取发布日期失败: {e}")
        return None

    def monitor_version_change(self, interval: int = 5) -> Tuple[Optional[str], Optional[str]]:
        """监控版本变化并下载两个版本喵~"""
        try:
            # 获取并下载当前版本
            self.current_version = self.get_version()
            if not self.current_version:
                return None, None
                
            logging.info(f"当前版本: {self.current_version}")
            if not self.download_and_extract(self.current_version, False):
                return None, None
                
            # 监控版本变化
            current_prefix = self.current_version[:8]
            logging.info(f"开始监控版本变化...")
            
            while True:
                time.sleep(interval)
                new_version = self.get_version()
                if new_version:
                    new_prefix = new_version[:8]
                    if new_prefix != current_prefix:
                        logging.info(f"检测到版本变化: {current_prefix} → {new_prefix}")
                        self.new_version = new_version
                        # 下载新版本
                        if self.download_and_extract(new_version, True):
                            return self.current_version, new_version
                        return None, None
                    logging.info(f"等待更新中... ({current_prefix})")
                    
        except KeyboardInterrupt:
            logging.info("\n监控已停止")
            return None, None
        except Exception as e:
            logging.error(f"监控异常: {e}")
            return None, None

    def run(self, ffdec_path: str):
        """运行版本监控喵~"""
        self.ffdec_path = ffdec_path
        return self.monitor_version_change()

def main():
    try:
        monitor = VersionMonitor()
        ffdec_path = input("请输入ffdec.jar路径: ").strip()
        if not os.path.exists(ffdec_path):
            logging.error("错误: ffdec.jar不存在!")
            return
            
        current_version, new_version = monitor.run(ffdec_path)
        if current_version and new_version:
            logging.info(f"成功获取两个版本: 当前版本 {current_version}, 新版本 {new_version}")
        else:
            logging.error("获取版本失败")
            
    except Exception as e:
        logging.error(f"发生全局错误: {e}")

if __name__ == "__main__":
    main()

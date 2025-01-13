import os
import re
import shutil
from typing import Tuple, List
from player_data import PlayerData, SaveGameData

class SaveFileHandler:
    def __init__(self):
        self.save_game_data = SaveGameData()

    def read_save_files(self, folder_path: str) -> SaveGameData:
        """读取存档文件"""
        try:
            # 找到所有存档文件
            files = os.listdir(folder_path)
            
            # 过滤掉备份文件
            valid_files = [f for f in files 
                          if not f.endswith('.backup') 
                          and not f.endswith('_old')
                          and f != 'SaveGameInfo']
            
            main_save = next((f for f in valid_files), None)
            
            if not main_save:
                raise FileNotFoundError("未找到有效的存档文件")

            # 读取主存档文件
            with open(os.path.join(folder_path, main_save), 'r', encoding='utf-8') as f:
                content = f.read()

            # 解析玩家数据
            self.save_game_data = self._parse_save_content(content)
            self.save_game_data.save_path = folder_path
            
            # 清理旧的备份文件
            self._cleanup_backup_files(folder_path)
            
            return self.save_game_data

        except Exception as e:
            print(f"读取存档文件时出错: {str(e)}")
            raise

    def _parse_save_content(self, content: str) -> SaveGameData:
        save_data = SaveGameData()
        
        try:
            # 解析主机玩家数据
            host_match = re.search(r'<player>(.*?)</player>', content, re.DOTALL)
            if host_match:
                host_content = host_match.group(1)
                host_data = self._extract_player_data(host_content, True)
                save_data.add_player(host_data)
                print(f"找到房主: {host_data.name}")

            # 先尝试查找 Farmer 标签
            farmer_matches = re.finditer(r'<Farmer>(.*?)</Farmer>', content, re.DOTALL)
            for match in farmer_matches:
                farmer_content = match.group(1)
                name_match = re.search(r'<name>(.*?)</name>', farmer_content)
                if name_match and name_match.group(1).strip() and name_match.group(1) != "null":
                    player_data = self._extract_player_data(farmer_content, False)
                    save_data.add_player(player_data)
                    print(f"找到玩家(Farmer): {player_data.name}")

            # 如果没找到 Farmer，尝试查找 farmhand 标签
            if not save_data.farmhands:
                farmhand_matches = re.finditer(r'<farmhand>(.*?)</farmhand>', content, re.DOTALL)
                for match in farmhand_matches:
                    farmhand_content = match.group(1)
                    name_match = re.search(r'<name>(.*?)</name>', farmhand_content)
                    if name_match and name_match.group(1).strip() and name_match.group(1) != "null":
                        player_data = self._extract_player_data(farmhand_content, False)
                        save_data.add_player(player_data)
                        print(f"找到玩家(farmhand): {player_data.name}")

            # 输出调试信息
            print(f"找到的总玩家数: {len(save_data.farmhands)}")
            print("XML内容包含的标签:")
            if '<Farmer>' in content:
                print("- 包含 <Farmer> 标签")
            if '<farmhand>' in content:
                print("- 包含 <farmhand> 标签")
            if '<farmhands>' in content:
                print("- 包含 <farmhands> 标签")

            return save_data
        
        except Exception as e:
            print(f"解析存档内容时出错: {str(e)}")
            raise

    def _extract_player_data(self, xml_content: str, is_host: bool) -> PlayerData:
        """提取玩家数据"""
        try:
            name_match = re.search(r'<name>(.*?)</name>', xml_content)
            id_match = re.search(r'<UniqueMultiplayerID>(.*?)</UniqueMultiplayerID>', xml_content)
            house_level_match = re.search(r'<houseUpgradeLevel>(.*?)</houseUpgradeLevel>', xml_content)
            home_location_match = re.search(r'<homeLocation>(.*?)</homeLocation>', xml_content)
            
            name = name_match.group(1) if name_match else "Unknown"
            print(f"正在解析玩家: {name}")

            return PlayerData(
                name=name,
                unique_id=id_match.group(1) if id_match else "0",
                house_level=int(house_level_match.group(1)) if house_level_match else 0,
                home_location=home_location_match.group(1) if home_location_match else "",
                xml_content=xml_content,
                is_host=is_host
            )
        except Exception as e:
            print(f"提取玩家数据时出错: {str(e)}")
            raise

    def swap_host(self, new_host_id: str) -> bool:
        try:
            # 找到新房主
            new_host = next((p for p in self.save_game_data.farmhands 
                            if p.unique_id == new_host_id), None)
            if not new_host or not self.save_game_data.host:
                return False

            print(f"准备将 {new_host.name} 设为房主")

            # 备份所有文件
            self._backup_save_files()
            
            # 获取所有需要处理的文件
            save_files = self._get_save_files()
            
            # 按文件类型分组处理
            for base_path in set(f.replace('_old', '') for f in save_files):
                print(f"处理文件: {base_path}")
                
                # 读取原始文件内容
                with open(base_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                try:
                    # 更新内容
                    if 'SaveGameInfo' in base_path:
                        # SaveGameInfo 文件使用 Farmer 标签
                        updated_content = self._update_save_game_info(content, new_host.xml_content)
                    else:
                        # 主存档文件使用 player 和 farmhand 标签
                        updated_content = self._update_main_save(content, 
                                                               self.save_game_data.host.xml_content,
                                                               new_host.xml_content)
                    
                    # 写入原始文件
                    with open(base_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    # 处理对应的 _old 文件
                    old_path = f"{base_path}_old"
                    if os.path.exists(old_path):
                        print(f"处理对应的 old 文件: {old_path}")
                        with open(old_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                            
                except Exception as e:
                    print(f"处理文件 {base_path} 时出错: {str(e)}")
                    raise

            return True

        except Exception as e:
            print(f"交换房主时出错: {str(e)}")
            return False

    def _update_save_game_info(self, content: str, new_host_content: str) -> str:
        """更新 SaveGameInfo 文件"""
        try:
            # 使用字符串查找替代正则表达式
            farmer_start = content.find('<Farmer xmlns:xsi=')
            if farmer_start == -1:
                farmer_start = content.find('<Farmer>')
            
            if farmer_start == -1:
                raise Exception("找不到 Farmer 标签")
            
            farmer_end = content.find('</Farmer>') + len('</Farmer>')
            if farmer_end == -1:
                raise Exception("找不到 Farmer 结束标签")
            
            # 保留 XML 命名空间信息
            xmlns = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
            
            # 构建新内容
            new_content = (
                content[:farmer_start] + 
                f'<Farmer {xmlns}>{new_host_content}</Farmer>' + 
                content[farmer_end:]
            )
            
            return new_content
            
        except Exception as e:
            print(f"更新 SaveGameInfo 时出错: {str(e)}")
            raise

    def _update_main_save(self, content: str, old_host_content: str, 
                         new_host_content: str) -> str:
        """更新主存档文件"""
        try:
            # 1. 获取新房主的 ID
            id_match = re.search(r'<UniqueMultiplayerID>(.*?)</UniqueMultiplayerID>', 
                               new_host_content, 
                               re.DOTALL)
            if not id_match:
                raise Exception("无法找到新房主ID")
            player_id = id_match.group(1)
            print(f"准备将ID为 {player_id} 的玩家设为房主")
            
            # 2. 替换房主信息（使用字符串方法替代正则表达式）
            player_start = content.find('<player>')
            player_end = content.find('</player>') + len('</player>')
            if player_start == -1 or player_end == -1:
                raise Exception("找不到 player 标签")
            
            content = (
                content[:player_start] + 
                f'<player>{new_host_content}</player>' + 
                content[player_end:]
            )
            
            # 3. 处理 farmhands 部分
            farmhands_start = content.find('<farmhands>')
            farmhands_end = content.find('</farmhands>') + len('</farmhands>')
            
            if farmhands_start != -1 and farmhands_end != -1:
                farmhands_content = content[farmhands_start:farmhands_end]
                
                # 3.1 分割所有 Farmer 条目
                farmers = []
                current_pos = 0
                while True:
                    farmer_start = farmhands_content.find('<Farmer>', current_pos)
                    if farmer_start == -1:
                        break
                    
                    farmer_end = farmhands_content.find('</Farmer>', farmer_start) + len('</Farmer>')
                    if farmer_end == -1:
                        break
                    
                    farmer_content = farmhands_content[farmer_start:farmer_end]
                    
                    # 如果不是新房主的条目，保留它
                    if f'<UniqueMultiplayerID>{player_id}</UniqueMultiplayerID>' not in farmer_content:
                        farmers.append(farmer_content)
                    
                    current_pos = farmer_end
                
                # 3.2 添加原房主的 Farmer 条目
                farmers.append(f'<Farmer>{old_host_content}</Farmer>')
                
                # 3.3 构建新的 farmhands 内容
                new_farmhands = f'<farmhands>{"".join(farmers)}</farmhands>'
                
                # 3.4 更新内容
                content = (
                    content[:farmhands_start] + 
                    new_farmhands + 
                    content[farmhands_end:]
                )
                
                print(f"处理后的玩家数量: {len(farmers)}")
                
            else:
                # 如果没有 farmhands 标签，创建一个
                content = content.replace(
                    '</player>',
                    f'</player><farmhands><Farmer>{old_host_content}</Farmer></farmhands>'
                )
            
            return content
            
        except Exception as e:
            print(f"更新主存档时出错: {str(e)}")
            print(f"错误详情: {str(e)}")
            raise

    def _cleanup_backup_files(self, folder_path: str):
        """清理旧的备份文件"""
        try:
            files = os.listdir(folder_path)
            for file in files:
                if file.endswith('.backup'):
                    file_path = os.path.join(folder_path, file)
                    try:
                        os.remove(file_path)
                        print(f"已删除旧的备份文件: {file}")
                    except Exception as e:
                        print(f"删除备份文件失败: {str(e)}")
        except Exception as e:
            print(f"清理备份文件时出错: {str(e)}")

    def _backup_save_files(self):
        """备份所有存档文件"""
        try:
            # 先清理旧的备份文件
            self._cleanup_backup_files(self.save_game_data.save_path)
            
            # 创建新的备份
            save_files = self._get_save_files()
            for file_path in save_files:
                if os.path.exists(file_path):  # 确保源文件存在
                    backup_path = file_path + '.backup'
                    # 使用 shutil.copy2 来复制文件
                    shutil.copy2(file_path, backup_path)
                    print(f"已备份文件: {file_path} -> {backup_path}")
        except Exception as e:
            print(f"备份文件时出错: {str(e)}")
            raise

    def _get_save_files(self) -> List[str]:
        """获取需要处理的所有存档文件路径"""
        folder_path = self.save_game_data.save_path
        files = os.listdir(folder_path)
        save_files = []
        
        # 添加主要存档文件
        main_save = next((f for f in files 
                         if not f.endswith('_old') 
                         and not f.endswith('.backup')
                         and f != 'SaveGameInfo'), None)
        if main_save:
            save_files.append(os.path.join(folder_path, main_save))
        
        # 添加 SaveGameInfo 文件
        save_game_info = os.path.join(folder_path, 'SaveGameInfo')
        if os.path.exists(save_game_info):
            save_files.append(save_game_info)
        
        return save_files

    def _swap_player_and_farmer(self, content: str, old_host_content: str, 
                               new_host_content: str) -> str:
        """交换主存档文件中的房主和玩家信息"""
        try:
            # 1. 获取新房主的 ID
            id_match = re.search(r'<UniqueMultiplayerID>(.*?)</UniqueMultiplayerID>', 
                               new_host_content, 
                               re.DOTALL)
            if not id_match:
                raise Exception("无法找到新房主ID")
            
            player_id = id_match.group(1)
            print(f"正在查找ID为 {player_id} 的玩家")

            # 2. 处理 SaveGameInfo 文件
            if '<Farmer xmlns:xsi=' in content:
                print("正在处理 SaveGameInfo 文件")
                # SaveGameInfo 使用 Farmer 标签
                content = re.sub(r'<Farmer xmlns:xsi=.*?</Farmer>', 
                               f'<Farmer xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                               f'xmlns:xsd="http://www.w3.org/2001/XMLSchema">'
                               f'{new_host_content}</Farmer>', 
                               content, 
                               count=1, 
                               flags=re.DOTALL)
            else:
                print("正在处理主存档文件")
                # 主存档文件使用 player 和 farmhand 标签
                # 替换房主信息
                content = re.sub(r'<player>.*?</player>', 
                               f'<player>{new_host_content}</player>', 
                               content, 
                               count=1, 
                               flags=re.DOTALL)
                
                # 替换农场工人信息
                content = re.sub(r'<farmhand>.*?</farmhand>', 
                               f'<farmhand>{old_host_content}</farmhand>', 
                               content, 
                               count=1, 
                               flags=re.DOTALL)
            
            return content
            
        except Exception as e:
            print(f"交换内容时出错: {str(e)}")
            raise

    def _replace_between_tags(self, content: str, tag: str, new_content: str) -> str:
        """替换指定标签之间的内容"""
        try:
            pattern = f'<{tag}>.*?</{tag}>'
            return re.sub(pattern, new_content, content, count=1, flags=re.DOTALL)
        except Exception as e:
            print(f"替换标签内容时出错: {str(e)}")
            raise 
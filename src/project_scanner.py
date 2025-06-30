import os
from pathlib import Path
from typing import List
from config import Config

class ProjectScanner:
    def __init__(self, config: Config):
        """프로젝트 스캐너 초기화"""
        self.config = config
        self.project_path = Path(config.PROJECT_ROOT)
    
    def scan_java_files(self) -> List[str]:
        """Java 파일 스캔"""
        java_files = []
        
        # 프로젝트 디렉토리 순회
        for ext in self.config.JAVA_EXTENSIONS:
            java_files.extend(
                str(f) for f in self.project_path.rglob(f"*{ext}")
                if not any(ignore in str(f) for ignore in self.config.IGNORE_PATTERNS)
            )
            
        return java_files
    
    def get_project_structure(self) -> dict:
        """프로젝트 구조 정보 반환"""
        java_files = self.scan_java_files()
        
        structure = {
            'total_files': len(java_files),
            'files_by_package': {},
            'all_files': java_files
        }
        
        for file_path in java_files:
            relative_path = Path(file_path).relative_to(self.project_path)
            package_dir = str(relative_path.parent)
            
            if package_dir not in structure['files_by_package']:
                structure['files_by_package'][package_dir] = []
            
            structure['files_by_package'][package_dir].append(file_path)
        
        return structure
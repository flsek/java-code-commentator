import sys
import os
import argparse
from pathlib import Path
from tqdm import tqdm
from colorama import init, Fore, Style

from project_scanner import ProjectScanner
from file_processor import FileProcessor
from config import Config
from java_parser import JavaParser
from comment_generator import CommentGenerator

init()  # colorama 초기화

class JavaCodeCommentator:
    def __init__(self):
        self.config = Config()
        
        if not self.config.ANTHROPIC_API_KEY:
            print(f"{Fore.RED}❌ ANTHROPIC_API_KEY가 설정되지 않았습니다.{Style.RESET_ALL}")
            print("1. .env 파일을 생성하고 API 키를 설정하세요.")
            print("2. 또는 환경변수로 ANTHROPIC_API_KEY를 설정하세요.")
            sys.exit(1)
    
    def run(self, project_path: str, dry_run: bool = False, no_backup: bool = False):
        """메인 실행 함수"""
        project_path = Path(project_path).resolve()
        
        if not project_path.exists():
            print(f"{Fore.RED}❌ 프로젝트 경로를 찾을 수 없습니다: {project_path}{Style.RESET_ALL}")
            return
        
        print(f"{Fore.CYAN}🔍 프로젝트 스캔 중: {project_path}{Style.RESET_ALL}")
        
        # 프로젝트 스캔
        scanner = ProjectScanner(project_path)
        structure = scanner.get_project_structure()
        
        if structure['total_files'] == 0:
            print(f"{Fore.YELLOW}⚠️  Java 파일을 찾을 수 없습니다.{Style.RESET_ALL}")
            return
        
        print(f"{Fore.GREEN}✅ {structure['total_files']}개의 Java 파일을 발견했습니다.{Style.RESET_ALL}")
        
        # 패키지별 파일 수 출력
        for package, files in structure['files_by_package'].items():
            print(f"   📁 {package}: {len(files)}개 파일")
        
        if dry_run:
            print(f"{Fore.YELLOW}🔍 Dry-run 모드: 실제 파일 변경 없이 미리보기만 수행합니다.{Style.RESET_ALL}")
        else:
            # 확인 메시지
            response = input(f"\n{structure['total_files']}개 파일에 주석을 추가하시겠습니까? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("작업이 취소되었습니다.")
                return
        
        # 백업 생성
        if not dry_run and not no_backup:
            print(f"{Fore.CYAN}💾 백업 생성 중...{Style.RESET_ALL}")
            processor = FileProcessor()
            backup_path = processor.create_backup(project_path)
            print(f"{Fore.GREEN}✅ 백업 완료: {backup_path}{Style.RESET_ALL}")
        
        # 파일 처리
        print(f"{Fore.CYAN}🤖 주석 생성 및 적용 중...{Style.RESET_ALL}")
        processor = FileProcessor()
        
        success_count = 0
        error_count = 0
        
        with tqdm(total=structure['total_files'], desc="Processing") as pbar:
            for file_path in structure['all_files']:
                pbar.set_description(f"Processing {file_path.name}")
                
                if processor.process_java_file(file_path, dry_run=dry_run):
                    success_count += 1
                else:
                    error_count += 1
                
                pbar.update(1)
        
        # 결과 출력
        print(f"\n{Fore.GREEN}🎉 작업 완료!{Style.RESET_ALL}")
        print(f"   ✅ 성공: {success_count}개 파일")
        if error_count > 0:
            print(f"   ❌ 실패: {error_count}개 파일")
        
        if not dry_run and not no_backup:
            print(f"\n{Fore.CYAN}💡 팁:{Style.RESET_ALL}")
            print(f"   📁 백업 폴더: {backup_path}")
            print(f"   🔄 롤백하려면: rm -rf {project_path}/* && cp -r {backup_path}/* {project_path}/")

def main():
    # 명령줄 인자 파싱
    parser = argparse.ArgumentParser(
        description="Java 프로젝트에 자동으로 주석을 추가하는 도구"
    )
    parser.add_argument(
        'project_path',
        help='Java 프로젝트 경로'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 파일 변경 없이 미리보기만 수행'
    )
    args = parser.parse_args()

    # 설정 초기화
    config = Config()
    config.PROJECT_ROOT = str(Path(args.project_path).resolve())
    config.BACKUP_DIR = os.path.join(config.PROJECT_ROOT, 'backup_before_comments')
    
    # 컴포넌트 초기화
    parser = JavaParser()
    comment_generator = CommentGenerator(config)
    file_processor = FileProcessor(config, parser, comment_generator)
    project_scanner = ProjectScanner(config)
    
    try:
        # Java 파일 스캔
        java_files = project_scanner.scan_java_files()
        if not java_files:
            print("처리할 Java 파일을 찾을 수 없습니다.")
            return
            
        print(f"총 {len(java_files)}개의 Java 파일을 찾았습니다.")
        
        # 파일 처리
        file_processor.process_java_files(java_files)
        
        print("\n모든 파일 처리가 완료되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        raise

if __name__ == "__main__":
    main()
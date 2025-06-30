import shutil
from pathlib import Path
from typing import List, Union
from java_parser import JavaElement, JavaParser
from comment_generator import CommentGenerator
from config import Config
from tqdm import tqdm
import sys
import traceback

class FileProcessor:
    def __init__(self, config, parser, comment_generator):
        self.config = config
        self.parser = parser
        self.comment_generator = comment_generator
        self.debug_file = sys.stderr
    
    def _debug_print(self, message: str):
        """디버깅 메시지를 stderr로 출력"""
        print(message, file=self.debug_file, flush=True)

    def create_backup(self, project_path: Path) -> Path:
        """프로젝트 백업 생성"""
        backup_path = project_path / self.config.BACKUP_DIR
        
        if backup_path.exists():
            shutil.rmtree(backup_path)
        
        # 원본 프로젝트 복사 (제외 디렉토리 제외)
        shutil.copytree(
            project_path, 
            backup_path,
            ignore=shutil.ignore_patterns(*self.config.EXCLUDE_DIRS)
        )
        
        return backup_path
    
    def process_java_files(self, java_files: List[str]) -> None:
        """Java 파일 목록을 처리"""
        for file_path in java_files:
            try:
                self._debug_print(f"\n디버깅 - 파일 처리 시작: {file_path}")
                self.process_java_file(file_path)
            except Exception as e:
                self._debug_print(f"파일 처리 중 오류 발생 ({file_path}): {e}")
                self._debug_print(f"디버깅 - 상세 오류:\n{traceback.format_exc()}")

    def process_java_file(self, file_path: str) -> None:
        """단일 Java 파일 처리"""
        try:
            # 파일 읽기
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._debug_print(f"디버깅 - 파일 읽기 완료: {type(content)}")

            # 파일 내용을 라인 단위로 분리
            content_lines = content.splitlines()
            self._debug_print(f"디버깅 - _get_lines 호출: content 타입 = {type(content)}")
            self._debug_print("디버깅 - content가 문자열임")
            self._debug_print(f"디버깅 - 라인 리스트 변환 완료: {type(content_lines)}")
            
            # Java 요소 파싱
            elements = self.parser.parse(content)
            self._debug_print(f"디버깅 - Java 요소 파싱 완료: {len(elements)} 개 요소 발견\n")

            # 각 요소에 대해 주석 생성 및 삽입
            modified_lines = content_lines.copy()
            for element in elements:
                self._debug_print(f"\n디버깅 - 요소 처리 시작: {element.type} {element.name}")
                self._debug_print(f"디버깅 - 주석 생성 시작: content_lines 타입 = {type(content_lines)}\n")
                
                # 주석 생성
                comment = self.comment_generator.generate_comment(element, content_lines)
                
                # 주석 들여쓰기 적용
                indent = self._get_indent(modified_lines[element.line_number - 1])
                indented_comment = self._indent_comment(comment, ' ' * indent)
                
                # 주석 삽입
                modified_lines = self._insert_comment(modified_lines, element.line_number - 1, indented_comment)
                self._debug_print("디버깅 - 주석 삽입 완료\n")

            # 수정된 내용을 파일에 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(modified_lines))

        except Exception as e:
            self._debug_print(f"파일 처리 중 오류 발생 ({file_path}): {e}")
            self._debug_print(f"디버깅 - 상세 오류:\n{traceback.format_exc()}")
            raise
    
    def _get_indent(self, line: str) -> int:
        """라인의 들여쓰기 공백 수를 반환"""
        return len(line) - len(line.lstrip())

    def _indent_comment(self, comment: Union[str, List[str]], indent: str) -> str:
        """주석에 들여쓰기 적용"""
        self._debug_print(f"디버깅 - _indent_comment 호출: comment 타입 = {type(comment)}")
        
        # 리스트인 경우 문자열로 변환
        if isinstance(comment, list):
            self._debug_print("디버깅 - comment가 리스트임, 문자열로 변환")
            comment = '\n'.join(comment)
        
        # 문자열이 아닌 경우 빈 문자열 반환
        if not isinstance(comment, str):
            self._debug_print(f"디버깅 - comment가 예상치 못한 타입임: {type(comment)}")
            return ""
        
        # 들여쓰기 적용
        lines = comment.splitlines()
        indented_lines = [indent + line if line.strip() else line for line in lines]
        return '\n'.join(indented_lines)

    def _insert_comment(self, lines: List[str], position: int, comment: str) -> List[str]:
        """주석을 지정된 위치에 삽입"""
        result = lines.copy()
        result.insert(position, comment)
        return result
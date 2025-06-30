import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class JavaElement:
    """Java 코드 요소를 나타내는 클래스"""
    type: str  # 'class', 'method', 'field' 등
    name: str  # 요소의 이름
    content: str  # 요소의 전체 내용
    line_number: int  # 요소가 시작하는 라인 번호
    existing_comment: Optional[str] = None  # 기존 주석 (있는 경우)
    method_info: Optional[dict] = None  # 메소드 상세 정보 (있는 경우)

class JavaParser:
    def __init__(self):
        # 주석 패턴
        self.comment_pattern = re.compile(
            r'/\*\*\s*(.*?)\s*\*/',
            re.MULTILINE | re.DOTALL
        )
        
        # 클래스 패턴
        self.class_pattern = re.compile(
            r'(?P<comment>/\*\*.*?\*/\s*)?'  # JavaDoc 주석 (옵션)
            r'(?P<annotations>(?:@\w+(?:\([^)]*\))?\s*)*)'  # 어노테이션들
            r'(?P<modifiers>(?:public|private|protected|static|final|abstract)\s+)*'  # 제어자들
            r'class\s+'  # class 키워드
            r'(?P<name>\w+)'  # 클래스 이름
            r'(?:\s+extends\s+\w+(?:\s*\.\s*\w+)*)?'  # 상속 (옵션)
            r'(?:\s+implements\s+(?:\w+(?:\s*\.\s*\w+)*(?:\s*,\s*\w+(?:\s*\.\s*\w+)*)*))?\s*'  # 인터페이스 구현 (옵션)
            r'{',  # 클래스 본문 시작
            re.MULTILINE | re.DOTALL
        )
        
        # 메소드 패턴
        self.method_pattern = re.compile(
            r'(?P<comment>/\*\*.*?\*/\s*)?'  # JavaDoc 주석 (옵션)
            r'(?P<annotations>(?:@\w+(?:\([^)]*\))?\s*)*)'  # 어노테이션들
            r'(?P<modifiers>(?:public|private|protected|static|final|synchronized|abstract)\s+)*'  # 제어자들
            r'(?P<return_type>(?:(?:[\w.]+)(?:<[^>]+>)?(?:\[\])*)\s+)?'  # 반환 타입 (생성자는 없음)
            r'(?P<name>\w+)\s*'  # 메소드 이름
            r'\((?P<params>[^)]*)\)'  # 파라미터
            r'(?:\s+throws\s+(?P<throws>[\w\s,]+))?\s*'  # 예외 선언 (옵션)
            r'{',  # 메소드 본문 시작
            re.MULTILINE | re.DOTALL
        )

    def _extract_comment(self, comment: Optional[str]) -> Optional[str]:
        """주석에서 JavaDoc 내용만 추출"""
        if not comment:
            return None
        
        # 주석 기호와 불필요한 공백 제거
        lines = comment.split('\n')
        cleaned_lines = []
        for line in lines:
            # 주석 시작과 끝 제거
            line = line.replace('/**', '').replace('*/', '').strip()
            # 줄 시작의 * 제거
            line = re.sub(r'^\s*\*\s?', '', line)
            if line:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

    def parse(self, content: str) -> List[JavaElement]:
        """Java 파일 내용을 파싱하여 클래스와 메소드를 추출"""
        elements = []
        
        # 클래스 찾기
        for match in self.class_pattern.finditer(content):
            class_name = match.group('name')
            class_comment = self._extract_comment(match.group('comment'))
            
            # 이미 주석이 있는 경우 건너뛰기
            if class_comment:
                continue
                
            line_number = content[:match.start()].count('\n') + 1
            
            elements.append(JavaElement(
                type='class',
                name=class_name,
                content=match.group(0),
                line_number=line_number,
                existing_comment=class_comment
            ))
        
        # 메소드 찾기
        for match in self.method_pattern.finditer(content):
            method_info = self._extract_method_info(match)
            if not method_info:
                continue
                
            method_comment = self._extract_comment(match.group('comment'))
            
            # 이미 주석이 있는 경우 건너뛰기
            if method_comment:
                continue
            
            # getter/setter는 처리하지 않음
            if method_info['name'].startswith(('get', 'set', 'is')):
                continue
                
            line_number = content[:match.start()].count('\n') + 1
            
            elements.append(JavaElement(
                type='method',
                name=method_info['name'],
                content=match.group(0),
                line_number=line_number,
                existing_comment=method_comment,
                method_info=method_info  # 메소드 상세 정보 추가
            ))
        
        # 라인 번호로 정렬
        elements.sort(key=lambda x: x.line_number)
        return elements

    def _extract_method_info(self, match) -> dict:
        """메소드 정보 추출"""
        try:
            name = match.group('name')
            return_type = match.group('return_type', '').strip() or 'void'
            params_str = match.group('params', '').strip()
            throws_str = match.group('throws', '').strip()
            
            # 파라미터 파싱
            params = []
            if params_str:
                for param in params_str.split(','):
                    param = param.strip()
                    if param:
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = ' '.join(parts[:-1])
                            param_name = parts[-1]
                            params.append({
                                'type': param_type.strip(),
                                'name': param_name.strip()
                            })
            
            # 예외 파싱
            throws = []
            if throws_str:
                throws = [ex.strip() for ex in throws_str.split(',')]
            
            return {
                'name': name,
                'return_type': return_type,
                'parameters': params,
                'throws': throws
            }
        except Exception as e:
            print(f"메소드 정보 추출 중 오류: {e}")
            return None

    def _extract_full_class_content(self, content: str, start_pos: int) -> str:
        """클래스의 전체 내용을 추출 (중괄호 매칭)"""
        brace_count = 0
        end_pos = start_pos
        
        for i in range(start_pos, len(content)):
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break
        
        return content[start_pos:end_pos]

    def parse_java_file(self, file_path: Path) -> List[JavaElement]:
        """Java 파일을 파싱하여 클래스, 메소드, 필드 정보 추출"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='cp949') as f:
                content = f.read()
        
        elements = []
        
        # 클래스/인터페이스 찾기
        for match in self.class_pattern.finditer(content):
            class_type, class_name = match.groups()
            line_num = content[:match.start()].count('\n') + 1
            existing_comment = self._extract_existing_comment(content, match.start())
            
            elements.append(JavaElement(
                name=class_name,
                element_type=class_type,
                line_number=line_num,
                content=match.group(0),
                existing_comment=existing_comment
            ))
        
        # 메소드 찾기
        for match in self.method_pattern.finditer(content):
            indent, method_name = match.groups()
            line_num = content[:match.start()].count('\n') + 1
            existing_comment = self._extract_existing_comment(content, match.start())
            
            elements.append(JavaElement(
                name=method_name,
                element_type='method',
                line_number=line_num,
                content=match.group(0),
                existing_comment=existing_comment
            ))
        
        # 필드 찾기 (생성자와 메소드 내부 제외)
        for match in self.field_pattern.finditer(content):
            indent, field_name = match.groups()
            line_num = content[:match.start()].count('\n') + 1
            
            # 메소드 내부의 변수 선언은 제외
            if self._is_inside_method(content, match.start()):
                continue
                
            existing_comment = self._extract_existing_comment(content, match.start())
            
            elements.append(JavaElement(
                name=field_name,
                element_type='field',
                line_number=line_num,
                content=match.group(0),
                existing_comment=existing_comment
            ))
        
        return sorted(elements, key=lambda x: x.line_number)
    
    def _extract_existing_comment(self, content: str, position: int) -> str:
        """기존 주석 추출"""
        lines_before = content[:position].split('\n')
        
        comment_lines = []
        for line in reversed(lines_before):
            stripped_line = line.strip()
            if stripped_line.startswith('/**') or stripped_line.startswith('*') or stripped_line.endswith('*/'):
                comment_lines.insert(0, line)
            elif stripped_line.startswith('//'):
                comment_lines.insert(0, line)
            elif stripped_line == '':
                continue
            else:
                break
        
        return '\n'.join(comment_lines) if comment_lines else None
    
    def _is_inside_method(self, content: str, position: int) -> bool:
        """주어진 위치가 메소드 내부인지 확인"""
        before_content = content[:position]
        open_braces = before_content.count('{')
        close_braces = before_content.count('}')
        
        # 간단한 휴리스틱: 중괄호 개수로 판단
        return open_braces > close_braces
import anthropic
import re
import time
from typing import Dict, Any, List, Union
from config import Config
from java_parser import JavaElement

class CommentGenerator:
    def __init__(self, config):
        self.config = config
        # 0.18.1 버전에서는 anthropic.Client가 맞음
        self.client = anthropic.Client(api_key=config.ANTHROPIC_API_KEY)
        self.max_retries = 5
        self.retry_delay = 15
        self.retry_multiplier = 2
    
    def generate_comment(self, element: JavaElement, file_context: Union[str, List[str]] = None) -> str:
        """Java 요소에 대한 주석 생성"""
        
        if element.type in ['class', 'interface', 'enum']:
            return self._generate_class_comment(element, file_context)
        elif element.type == 'method':
            return self._generate_method_comment(element, file_context)
        elif element.type == 'field':
            return self._generate_field_comment(element, file_context)
        else:
            return ""
    
    def _prepare_context(self, context: Union[str, List[str]]) -> List[str]:
        """컨텍스트를 라인 리스트로 변환"""
        if context is None:
            return []
        elif isinstance(context, str):
            return context.split('\n')
        elif isinstance(context, list):
            return context
        else:
            return []
    
    def _extract_method_signature(self, method_content: str) -> Dict[str, Any]:
        """메소드 시그니처에서 상세 정보 추출"""
        method_pattern = re.compile(
            r'(?:public|private|protected)?\s*'
            r'(?:static\s+)?(?:final\s+)?(?:synchronized\s+)?'
            r'(?:abstract\s+)?'
            r'(?P<return_type>\w+(?:<[^>]*>)?(?:\[\])?)\s+'
            r'(?P<method_name>\w+)\s*\('
            r'(?P<parameters>[^)]*)'
            r'\)\s*(?:throws\s+(?P<exceptions>[\w\s,]+))?',
            re.MULTILINE | re.DOTALL
        )
        
        match = method_pattern.search(method_content)
        if not match:
            return {}
        
        result = {
            'return_type': match.group('return_type'),
            'method_name': match.group('method_name'),
            'parameters': [],
            'exceptions': []
        }
        
        # 파라미터 파싱
        params_str = match.group('parameters')
        if params_str and params_str.strip():
            params = [p.strip() for p in params_str.split(',')]
            for param in params:
                parts = param.split()
                if len(parts) >= 2:
                    param_type = ' '.join(parts[:-1])
                    param_name = parts[-1]
                    result['parameters'].append({
                        'type': param_type,
                        'name': param_name
                    })
        
        # 예외 파싱
        exceptions_str = match.group('exceptions')
        if exceptions_str:
            result['exceptions'] = [e.strip() for e in exceptions_str.split(',')]
        
        return result
    
    def _call_claude_api(self, prompt: str, retry_count: int = 0) -> str:
        """Claude API 호출 with 재시도 로직 - 0.18.1 버전용"""
        try:
            # 0.18.1 버전의 API 호출 방식
            response = self.client.messages.create(
                model=self.config.MODEL,
                max_tokens=self.config.MAX_TOKENS,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 0.18.1 버전에서의 응답 처리
            print(f"디버깅 - Claude API 응답: {type(response)}")
            print(f"디버깅 - Response attributes: {dir(response)}")
            
            # 다양한 응답 형식 처리
            comment = ""
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    # ContentBlock 리스트인 경우
                    for block in response.content:
                        if hasattr(block, 'text'):
                            comment += block.text
                        elif hasattr(block, 'content'):
                            comment += str(block.content)
                        else:
                            comment += str(block)
                elif hasattr(response.content, 'text'):
                    # 단일 ContentBlock인 경우
                    comment = response.content.text
                else:
                    # 문자열인 경우
                    comment = str(response.content)
            else:
                # response 자체가 텍스트인 경우
                comment = str(response)
            
            # 형식 정리
            comment = self._format_comment(comment)
            print(f"디버깅 - 정리된 주석: {comment[:100]}...")
            
            return comment
                
        except Exception as e:
            error_msg = str(e)
            print(f"API 호출 중 오류 발생 (시도 {retry_count + 1}/{self.max_retries}): {error_msg}")
            
            if ("overloaded_error" in error_msg or "529" in error_msg) and retry_count < self.max_retries - 1:
                wait_time = self.retry_delay * (self.retry_multiplier ** retry_count)
                print(f"서버 과부하로 인해 {wait_time}초 후 재시도합니다...")
                time.sleep(wait_time)
                return self._call_claude_api(prompt, retry_count + 1)
            else:
                return None
    
    def _format_comment(self, comment: str) -> str:
        """주석 형식 정리"""
        if not comment:
            return ""
        
        # 마크다운 코드 블록 제거
        comment = comment.replace('```java', '').replace('```', '').strip()
        
        # JavaDoc 형식 확인 및 수정
        if not comment.startswith('/**'):
            comment = '/**\n * ' + comment
        if not comment.endswith('*/'):
            comment = comment.rstrip() + '\n */'
            
        # 각 줄 형식 정리
        lines = comment.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if i == 0:  # 첫 줄 /**
                formatted_lines.append('/**')
            elif i == len(lines) - 1:  # 마지막 줄 */
                formatted_lines.append(' */')
            else:
                # 중간 줄들은 ' * '로 시작해야 함
                content = line.strip()
                if content.startswith('*'):
                    content = content[1:].strip()
                
                if content == '':
                    formatted_lines.append(' *')
                else:
                    formatted_lines.append(' * ' + content)
        
        return '\n'.join(formatted_lines)

    def _generate_class_comment(self, element: JavaElement, context: Union[str, List[str]]) -> str:
        """클래스 주석 생성"""
        context_lines = self._prepare_context(context)
        class_line = element.line_number - 1
        
        # 클래스 주변 코드
        start_line = max(0, class_line - 10)
        end_line = min(len(context_lines), class_line + 20)
        surrounding_context = '\n'.join(context_lines[start_line:end_line])
        
        prompt = f"""다음 Java 클래스에 대한 JavaDoc 주석을 생성해주세요.

클래스 코드:
{surrounding_context}

요구사항:
1. 클래스의 주요 목적과 책임을 첫 줄에 명확하게 설명
2. 두 번째 줄부터 핵심 기능과 사용 목적을 설명
3. 필요한 경우에만 @throws 태그 포함
4. 설명과 태그 사이에 빈 줄 추가
5. 각 줄은 ' * '로 시작
6. 한국어로 작성
7. JavaDoc 표준 형식 준수

예시:
/**
 * 클래스의 주요 목적을 한 줄로 설명합니다.
 * 클래스의 핵심 기능과 사용 목적을 설명합니다.
 * 
 * @throws ExceptionType 예외 발생 조건 (필요한 경우만)
 */

주석만 반환해주세요."""

        comment = self._call_claude_api(prompt)
        
        if comment is None:
            return f"/**\n * {element.name} 클래스\n */"
            
        return comment

    def _generate_method_comment(self, element: JavaElement, context: Union[str, List[str]]) -> str:
        """메소드 주석 생성"""
        context_lines = self._prepare_context(context)
        method_line = element.line_number - 1
        
        # 메소드 주변 코드
        start_line = max(0, method_line - 5)
        end_line = min(len(context_lines), method_line + 15)
        method_context = '\n'.join(context_lines[start_line:end_line])
        
        # 메소드 시그니처 분석
        method_info = self._extract_method_signature(element.content)
        
        # 파라미터 정보
        param_info = ""
        if method_info.get('parameters'):
            param_info = "파라미터:\n"
            for param in method_info['parameters']:
                param_info += f"- {param['name']} ({param['type']})\n"
        
        prompt = f"""다음 Java 메소드에 대한 완전한 JavaDoc 주석을 생성해주세요.

메소드 코드:
{method_context}

메소드 정보:
- 메소드명: {element.name}
- 반환타입: {method_info.get('return_type', 'void')}
{param_info}
- 예외: {', '.join(method_info.get('exceptions', []))}

요구사항:
1. 메소드의 핵심 목적을 첫 줄에 명확하고 간결하게 설명
2. 두 번째 줄부터 구체적인 동작 방식과 제약사항 설명
3. 모든 파라미터에 대해 @param 태그로 상세 설명
4. 반환값이 있으면 @return 태그로 상세 설명
5. 발생 가능한 예외는 @throws 태그로 구체적인 발생 조건 설명
6. 설명과 태그 사이에 빈 줄 추가
7. 각 줄은 ' * '로 시작
8. 한국어로 작성
9. JavaDoc 표준 형식 준수

예시:
/**
 * 메소드의 핵심 기능을 한 줄로 설명합니다.
 * 구체적인 동작 방식과 처리 과정을 설명합니다.
 * 
 * @param paramName 파라미터에 대한 상세한 설명
 * @return 반환값에 대한 상세한 설명
 * @throws ExceptionType 예외 발생 조건
 */

주석만 반환해주세요."""

        comment = self._call_claude_api(prompt)
        
        if comment is None:
            return f"/**\n * {element.name} 메소드\n */"
            
        return comment

    def _generate_field_comment(self, element: JavaElement, context: Union[str, List[str]]) -> str:
        """필드 주석 생성"""
        context_lines = self._prepare_context(context)
        field_line = element.line_number - 1
        
        # 필드 선언과 주변 컨텍스트
        start_line = max(0, field_line - 5)
        end_line = min(len(context_lines), field_line + 5)
        surrounding_context = '\n'.join(context_lines[start_line:end_line])
        
        prompt = f"""다음 Java 필드에 대한 간단한 주석을 생성해주세요.

필드 코드:
{surrounding_context}

요구사항:
1. 한 줄 주석(//) 형식
2. 필드의 구체적인 용도와 의미 설명
3. 한국어로 작성
4. 필드명만 반복하는 설명 금지

예시:
// 사용자 인증 상태를 저장하는 플래그

주석만 반환해주세요."""

        try:
            # 필드는 간단한 주석이므로 직접 API 호출
            response = self.client.messages.create(
                model=self.config.MODEL,
                max_tokens=200,  # 필드는 짧게
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # 응답 처리
            comment = ""
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    for block in response.content:
                        if hasattr(block, 'text'):
                            comment += block.text
                        else:
                            comment += str(block)
                else:
                    comment = str(response.content)
            
            # // 형식으로 정리
            comment = comment.strip().replace('```', '')
            if not comment.startswith('//'):
                comment = '// ' + comment
            
            return comment
            
        except Exception as e:
            print(f"필드 주석 생성 중 오류 발생: {e}")
            return f"// {element.name} 필드"

    def _extract_field_info(self, field_content: str) -> Dict[str, Any]:
        """필드 선언에서 정보 추출"""
        info = {
            'type': 'unknown',
            'initial_value': None,
            'access_modifier': 'default',
            'is_static': False,
            'is_final': False
        }
        
        # 접근 제한자
        if 'public' in field_content:
            info['access_modifier'] = 'public'
        elif 'private' in field_content:
            info['access_modifier'] = 'private'
        elif 'protected' in field_content:
            info['access_modifier'] = 'protected'
        
        # static, final 확인
        info['is_static'] = 'static' in field_content
        info['is_final'] = 'final' in field_content
        
        # 타입과 초기값 추출
        pattern = re.compile(r'(\w+(?:<[^>]*>)?(?:\[\])?)\s+\w+(?:\s*=\s*([^;]+))?;')
        match = pattern.search(field_content)
        if match:
            info['type'] = match.group(1)
            if match.group(2):
                info['initial_value'] = match.group(2).strip()
        
        return info
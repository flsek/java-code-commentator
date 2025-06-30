import os

class Config:
    def __init__(self):
        # API 설정
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.MODEL = "claude-3-5-sonnet-20241022"  # Claude 모델 버전
        self.MAX_TOKENS = 4096  # 최대 토큰 수

        # 프로젝트 설정
        self.PROJECT_ROOT = None  # 프로젝트 루트 디렉토리
        self.BACKUP_DIR = None  # 백업 디렉토리
        
        # 파일 처리 설정
        self.JAVA_EXTENSIONS = ['.java']  # 처리할 파일 확장자
        self.IGNORE_PATTERNS = [  # 무시할 디렉토리/파일 패턴
            'test', 'tests', 'example', 'examples',
            'target', 'build', '.git', '.idea',
            'node_modules', '.gradle', 'bin', 'out'
        ]
        
        # 주석 생성 설정
        self.CONTEXT_LINES = 20  # 컨텍스트로 사용할 위아래 라인 수
        
        # 주석 스타일 설정
        self.JAVADOC_STYLE = {
            'class': '/**\n * {}\n */',
            'method': '/**\n * {}\n */',
            'field': '/** {} */'
        }
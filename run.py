#!/usr/bin/env python3
"""
실행 스크립트
- FastAPI 서버 (실시간 시세)
- Streamlit (분석/시뮬레이션) - 선택적
"""
import argparse
import subprocess
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="크립토 퀀트 시뮬레이터")
    parser.add_argument(
        "--mode", "-m",
        choices=["api", "streamlit", "both"],
        default="api",
        help="실행 모드 (api: FastAPI만, streamlit: Streamlit만, both: 둘 다)"
    )
    parser.add_argument("--port", "-p", type=int, default=8000, help="FastAPI 포트")
    parser.add_argument("--st-port", type=int, default=8501, help="Streamlit 포트")
    parser.add_argument("--reload", "-r", action="store_true", help="자동 리로드")
    
    args = parser.parse_args()
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    processes = []
    
    try:
        if args.mode in ["api", "both"]:
            print(f"🚀 FastAPI 서버 시작 (http://localhost:{args.port})")
            cmd = [
                sys.executable, "-m", "uvicorn",
                "api.server:app",
                "--host", "0.0.0.0",
                "--port", str(args.port),
            ]
            if args.reload:
                cmd.append("--reload")
            
            processes.append(subprocess.Popen(cmd))
        
        if args.mode in ["streamlit", "both"]:
            print(f"📊 Streamlit 시작 (http://localhost:{args.st_port})")
            cmd = [
                sys.executable, "-m", "streamlit", "run",
                "app/main.py",
                "--server.port", str(args.st_port),
            ]
            processes.append(subprocess.Popen(cmd))
        
        # 프로세스 대기
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n종료 중...")
        for p in processes:
            p.terminate()


if __name__ == "__main__":
    main()

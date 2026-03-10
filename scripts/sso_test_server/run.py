"""
SSO 테스트 서버

위치: scripts/sso_test_server/run.py
용도: sso_test.html을 별도 포트(19091)에서 서빙

사용법:
    python scripts/sso_test_server/run.py
    python scripts/sso_test_server/run.py --port 19091
"""
import argparse
import http.server
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="SSO 테스트 HTTP 서버")
    parser.add_argument("--port", type=int, default=19081, help="포트 번호 (기본: 19081)")
    parser.add_argument("--host", default="localhost", help="바인드 주소 (기본: localhost)")
    args = parser.parse_args()

    # sso_test.html이 있는 디렉토리로 이동
    serve_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(serve_dir)

    handler = http.server.SimpleHTTPRequestHandler
    server = http.server.HTTPServer((args.host, args.port), handler)

    print(f"SSO 테스트 서버 시작: http://{args.host}:{args.port}/sso_test.html")
    print("종료하려면 Ctrl+C를 누르세요.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버 종료")
        server.server_close()


if __name__ == "__main__":
    main()

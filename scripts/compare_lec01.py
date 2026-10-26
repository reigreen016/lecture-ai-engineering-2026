"""第1回基礎: 同じ質問を2モデルに3回ずつ送り、成功・失敗を記録する。"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import time


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs=2, required=True)
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get("GEMINI_API_KEY"):
        parser.error("GEMINI_API_KEY が未設定です。APIへのリクエストは送信しません。")
    if args.interval < 0:
        parser.error("interval は0以上にしてください。")
    if args.output.exists():
        parser.error("既存の記録を上書きしないため、別の出力先を指定してください。")

    question = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as log:
        for index in range(6):
            model = args.models[index // 3]
            started = datetime.now().astimezone().isoformat()
            start = time.perf_counter()
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "app.ask", question],
                    env={**os.environ, "AIE_MODEL": model},
                    capture_output=True, text=True, timeout=120,
                )
                status = result.returncode
                # 認証情報を含み得る例外のstderrは保存しない。
                output = result.stdout.replace(os.environ["GEMINI_API_KEY"], "[REDACTED]")
            except subprocess.TimeoutExpired:
                status, output = 124, "120秒でタイムアウト（回答を取得できず）"
            record = {
                "started_at": started, "model": model, "run": index % 3 + 1,
                "question": question, "exit_code": status,
                "elapsed_seconds": round(time.perf_counter() - start, 3),
                "stdout": output,
            }
            log.write(json.dumps(record, ensure_ascii=False) + "\n")
            log.flush()
            print(f"{model} {index % 3 + 1}/3: exit={status}", flush=True)
            if index != 5:
                time.sleep(args.interval)


if __name__ == "__main__":
    main()

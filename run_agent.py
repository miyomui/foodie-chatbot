import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def _project_python() -> Path:
    if os.name == "nt":
        return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".venv" / "bin" / "python"


def _same_python(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except OSError:
        return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def _force_utf8_stdio() -> None:
    os.environ["PYTHONUTF8"] = "1"
    os.environ["PYTHONIOENCODING"] = "utf-8"
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def ensure_project_venv() -> None:
    venv_python = _project_python()
    if not venv_python.exists():
        raise SystemExit(
            "ไม่พบ Python ของโปรเจกต์ที่ .venv\\Scripts\\python.exe\n"
            "ให้สร้าง .venv ก่อนด้วยคำสั่ง: python -m venv .venv\n"
            "แล้วติดตั้ง library: .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
        )

    current_python = Path(sys.executable)
    if not _same_python(current_python, venv_python):
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        os.execve(
            str(venv_python),
            [str(venv_python), "-X", "utf8", str(Path(__file__).resolve()), *sys.argv[1:]],
            env,
        )


def main() -> None:
    ensure_project_venv()
    _force_utf8_stdio()

    from src.agent import foodie_agent
    from src.retrieval import ensure_vector_store

    ensure_vector_store()

    print("=== 🍜 ยินดีต้อนรับสู่ Agentic Foodie Chatbot (Professional Edition) ===")
    while True:
        try:
            query = input("\nหิวหรือยังคะ? ถามมาได้เลย (หรือพิมพ์ 'exit' เพื่อออก): ")
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print("\nออกจากโปรแกรมแล้วค่ะ")
            break

        if query.lower() == "exit":
            break

        try:
            answer = foodie_agent(query)
        except KeyboardInterrupt:
            print("\nออกจากโปรแกรมแล้วค่ะ")
            break
        print(f"\n[Agent]: {answer}")


if __name__ == "__main__":
    main()

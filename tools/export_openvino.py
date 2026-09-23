"""yolov8n.pt 를 OpenVINO IR 형식으로 내보냅니다.

생성물(`yolov8n_openvino_model/`)은 .gitignore 대상입니다 — 커밋하지 말고
각자 환경에서 한 번씩 실행해 만드세요.

    python tools/export_openvino.py           # 이미 있으면 건너뜀
    python tools/export_openvino.py --force   # 다시 내보내기
    python tools/export_openvino.py --fp32    # FP16 대신 FP32 (정밀도 문제 시)

내보내기 imgsz는 config.INFER_IMGSZ와 같은 값을 씁니다. 두 값이 어긋나면
추론 시 OpenVINO가 모델을 다시 컴파일하거나 실패합니다.
"""

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import YOLO_MODEL, OPENVINO_MODEL_DIR, INFER_IMGSZ


def main() -> int:
    parser = argparse.ArgumentParser(description="YOLOv8 → OpenVINO 내보내기")
    parser.add_argument("--force", action="store_true",
                        help="기존 내보내기 결과를 지우고 다시 만듭니다")
    parser.add_argument("--fp32", action="store_true",
                        help="FP16 대신 FP32로 내보냅니다 (정밀도 차이가 문제될 때)")
    parser.add_argument("--static", action="store_true",
                        help="입력 크기를 640x640으로 고정합니다 (기본은 dynamic)")
    args = parser.parse_args()

    # ultralytics 는 폴더 이름이 '_openvino_model' 로 끝나야 OpenVINO 모델로 인식합니다.
    if not os.path.basename(OPENVINO_MODEL_DIR.rstrip("/\\")).endswith("_openvino_model"):
        print(f"config.OPENVINO_MODEL_DIR 의 폴더 이름은 '_openvino_model' 로 끝나야 합니다: "
              f"{OPENVINO_MODEL_DIR}")
        return 1

    if os.path.isdir(OPENVINO_MODEL_DIR):
        if not args.force:
            print(f"이미 존재합니다: {OPENVINO_MODEL_DIR}")
            print("다시 만들려면 --force 를 주세요.")
            return 0
        print(f"기존 내보내기 삭제: {OPENVINO_MODEL_DIR}")
        shutil.rmtree(OPENVINO_MODEL_DIR)

    try:
        from ultralytics import YOLO
    except ImportError as e:
        print(f"ultralytics 를 불러올 수 없습니다: {e}")
        return 1

    try:
        import openvino  # noqa: F401
    except ImportError:
        print("openvino 패키지가 없습니다. 먼저 설치하세요:  pip install openvino")
        return 1

    half = not args.fp32
    dynamic = not args.static
    print(f"모델    : {YOLO_MODEL}")
    print(f"imgsz   : {INFER_IMGSZ}")
    print(f"정밀도  : {'FP16' if half else 'FP32'}")
    print(f"입력크기: {'dynamic (PyTorch와 동일한 직사각 letterbox)' if dynamic else '640x640 고정'}")
    print("내보내는 중... (수십 초 걸릴 수 있습니다)")

    # dynamic=True 가 기본인 이유:
    # ultralytics 는 .pt 모델에 직사각 letterbox(예: 640x480)를 쓰지만, 고정 크기로
    # 내보낸 모델에는 정사각(640x640)을 강제합니다. 정사각은 픽셀이 1.33배 많아
    # 더 느리고, 검출 결과도 기존과 미묘하게 달라집니다. dynamic 으로 내보내면
    # 기존과 같은 직사각 입력을 그대로 받습니다.
    model = YOLO(YOLO_MODEL)
    try:
        # ultralytics 8.4+ : half → quantize 로 이름이 바뀌었습니다.
        exported = model.export(format="openvino", imgsz=INFER_IMGSZ,
                                quantize=16 if half else 32, dynamic=dynamic)
    except TypeError:
        # requirements 가 ultralytics>=8.0.0 이라 구버전도 지원합니다.
        exported = model.export(format="openvino", imgsz=INFER_IMGSZ,
                                half=half, dynamic=dynamic)

    # ultralytics 는 .pt 파일 옆에 <stem>_openvino_model/ 을 만듭니다.
    # config 가 가리키는 경로와 다르면 옮겨 둡니다.
    exported = os.path.abspath(str(exported))
    target = os.path.abspath(OPENVINO_MODEL_DIR)
    if exported != target:
        if os.path.isdir(target):
            shutil.rmtree(target)
        shutil.move(exported, target)

    if not os.path.isdir(target):
        print(f"내보내기 실패 — 폴더가 생성되지 않았습니다: {target}")
        return 1

    size_mb = sum(
        os.path.getsize(os.path.join(target, f))
        for f in os.listdir(target)
        if os.path.isfile(os.path.join(target, f))
    ) / (1024 * 1024)
    print(f"완료: {target}  ({size_mb:.1f} MB)")
    print("이제 config.INFER_BACKEND='auto' 상태에서 자동으로 이 모델이 쓰입니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
